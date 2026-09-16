"""Structured, auditable regeneration orchestration.

Human feedback is scoped to one CalibrationItem.  This module never mutates a
RoleSpec and compiles a fresh request through the existing generation contract.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable

from image_generation.models import GenerationRequest, ModelExecutionPolicy
from image_qa.evaluator import VisionQAEvaluator
from .models import CalibrationItem, HumanEvaluation, RegenerationTask, ImageVersion, now
from .store import CalibrationStore


@dataclass
class GenerationRequestContext:
    sku: str
    role: str
    image_task: dict[str, Any]
    product_truth: dict[str, Any]
    role_spec_version: str
    preserve: list[str] = field(default_factory=list)
    change: list[str] = field(default_factory=list)
    dont_introduce: list[str] = field(default_factory=list)
    human_instruction: str = ""
    provider: str = "openai_compatible"

    def model_dump(self): return asdict(self)


def compile_regeneration_prompt(context: GenerationRequestContext) -> str:
    """Compile structured sections; no string concatenation with the old prompt."""
    truth = context.product_truth or {}
    plan = context.image_task or {}
    preserve = [f"- {v}" for v in context.preserve] or ["- Preserve all verified product facts and structure."]
    change = [f"- {v}" for v in context.change] or ["- Apply no unrequested changes."]
    dont = [f"- {v}" for v in context.dont_introduce] or ["- No unsupported products, claims, materials, or accessories."]
    lines = [
        "[PRODUCT TRUTH]", json.dumps(truth, ensure_ascii=False, sort_keys=True),
        "[IMAGE PLAN]", json.dumps(plan, ensure_ascii=False, sort_keys=True),
        "[ROLE SPEC]", f"Approved RoleSpec version: {context.role_spec_version}",
        "[CURRENT IMAGE CONTEXT]", "Edit the supplied source image context; preserve product identity.",
        "[MUST PRESERVE]", *preserve,
        "[MUST CHANGE]", *change,
        "[DO NOT INTRODUCE]", *dont,
        "[HUMAN REGENERATION INSTRUCTION]", context.human_instruction.strip() or "Address the requested changes.",
        "Product Truth has priority over human styling requests. Do not invent or alter verified facts.",
    ]
    return "\n".join(lines)


def build_generation_request(item: CalibrationItem, context: GenerationRequestContext, task_id: str) -> GenerationRequest:
    plan = item.image_plan_snapshot
    refs = []
    for asset in plan.get("reference_assets", []):
        refs.append({"asset_id": asset.get("asset_id", "canonical"), "path": asset.get("path", ""), "role": "product", "approved_uses": ["product identity"]})
    from image_generation.models import LegacyReferenceAsset
    return GenerationRequest(
        generation_id=f"gen_{item.image_id or 'image_01'}",
        # Keep the legacy image_NN contract; version identity is carried by the
        # regeneration task and ImageVersion record, never by an invalid ID.
        image_id=item.image_id or "image_01",
        role=item.role,
        template_id=plan.get("template_id", "CALIBRATION_REGENERATION"),
        product_id=context.sku,
        reference_assets=[LegacyReferenceAsset(**ref) for ref in refs],
        generation_goal=plan.get("decision_question", "Improve the image according to human calibration."),
        prompt=compile_regeneration_prompt(context),
        negative_constraints=list(dict.fromkeys([*plan.get("forbidden_elements", []), *context.dont_introduce])),
        required_visual_evidence=plan.get("required_visual_evidence", []),
        required_facts=plan.get("required_product_facts", []),
        required_claims=plan.get("required_claims", []),
        asset_limitations=[],
        generation_metadata={"source_image_id": item.active_image_id or item.image_id, "role_spec_version": context.role_spec_version, "regeneration_task_id": task_id, "compiler": "structured_calibration_v1"},
    )


class RegenerationService:
    def __init__(self, store: CalibrationStore, provider=None, qa_evaluator: VisionQAEvaluator | None = None, *, policy: ModelExecutionPolicy | None = None, product_truth_loader: Callable[[str], dict[str, Any]] | None = None):
        self.store = store
        self.provider = provider
        self.qa = qa_evaluator or VisionQAEvaluator()
        self.policy = policy or ModelExecutionPolicy(policy_id="calibration-regeneration", model_id="gpt-image-2")
        self.product_truth_loader = product_truth_loader or (lambda sku: {"product_id": sku})

    def create_task(self, item: CalibrationItem, evaluation: HumanEvaluation, *, role_spec_version: str = "v1", provider: str | None = None, execute: bool = False) -> RegenerationTask:
        task_id = f"regen_{item.item_id}_{item.generation_version + 1}"
        session = self.store.find_item(item.item_id)[0]
        sku = item.image_plan_snapshot.get("product_id", "") or session.sku
        context = GenerationRequestContext(sku=sku, role=item.role, image_task=item.image_plan_snapshot, product_truth=self.product_truth_loader(sku), role_spec_version=role_spec_version, preserve=evaluation.preserve, change=evaluation.change, dont_introduce=evaluation.dont_introduce, human_instruction=evaluation.regeneration_instruction or evaluation.suggested_change, provider=provider or item.provider or "openai_compatible")
        request = build_generation_request(item, context, task_id)
        task = RegenerationTask(task_id=task_id, calibration_item_id=item.item_id, source_image_id=item.active_image_id or item.image_id or item.item_id, role=item.role, role_spec_version=role_spec_version, preserve=list(evaluation.preserve), change=list(evaluation.change), dont_introduce=list(evaluation.dont_introduce), instruction=context.human_instruction, prompt_snapshot=context.model_dump(), provider=context.provider, status="queued" if execute else "draft", human_feedback_snapshot=evaluation.model_dump(), generation_request=request.model_dump(), compiled_prompt=request.prompt)
        self.store.save_task(task)
        if execute: self.execute(task, item, request)
        return task

    def execute(self, task: RegenerationTask, item: CalibrationItem | None = None, request: GenerationRequest | None = None) -> RegenerationTask:
        item = item or self.store.find_item(task.calibration_item_id)[1]
        if request is None:
            payload = dict(task.generation_request)
            from image_generation.models import LegacyReferenceAsset
            payload["reference_assets"] = [LegacyReferenceAsset(**ref) if isinstance(ref, dict) else ref for ref in payload.get("reference_assets", [])]
            request = GenerationRequest(**payload)
        task.status = "generating"; self.store.save_task(task)
        try:
            if self.provider is None: raise RuntimeError("No generation provider configured")
            result = self.provider.generate(request, self.policy)
            task.generation_metadata = result.model_dump()
            if result.status != "succeeded" or not result.output_assets: raise RuntimeError("generation failed")
            task.status = "qa_running"; self.store.save_task(task)
            report = self.qa.qa(request, result)
            task.qa_result = report.model_dump(); task.status = "ready_for_review"; task.completed_at = now()
            asset = result.output_assets[0]
            new_image_id = request.image_id
            version_path = asset.path
            source_path = Path(asset.path)
            if source_path.is_file():
                version_path = str(source_path.with_name(f"{source_path.stem}_v{item.generation_version + 1}{source_path.suffix}"))
                if version_path != asset.path: shutil.copyfile(source_path, version_path)
            version = ImageVersion(image_id=f"{new_image_id}_v{item.generation_version + 1}", logical_image_id=item.image_id or item.item_id, version=item.generation_version + 1, path=version_path, source_image_id=task.source_image_id, role=item.role, role_spec_version=task.role_spec_version, provider=task.provider, generation_metadata=result.model_dump(), prompt_snapshot=task.prompt_snapshot, qa_result=task.qa_result)
            self.store.save_image_version(version)
            item.generation_version = version.version; item.active_image_id = version.image_id; item.image_path = version.path; item.qa_snapshot = task.qa_result; item.status = "ready_for_review"
            task.output_image_ids = [version.image_id]; self.store.save_session(self.store.find_item(item.item_id)[0])
        except Exception as exc:
            task.status = "failed"; task.error = str(exc); task.completed_at = now()
        self.store.save_task(task)
        return task

    def decide(self, task_id: str, verdict: str, evaluation: HumanEvaluation | None = None):
        if verdict not in {"accept", "partial", "reject"}: raise ValueError("invalid verdict")
        task = self.store.load_task(task_id); task.status = "accepted" if verdict == "accept" else "rejected"; self.store.save_task(task)
        if evaluation is not None: self.store.save_evaluation(task.calibration_item_id, evaluation)
        return task


__all__ = ["GenerationRequestContext", "compile_regeneration_prompt", "build_generation_request", "RegenerationService"]
