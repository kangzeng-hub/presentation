"""Contract-based QA orchestration.

The default evaluator consumes explicit visual observations (from a mock or a
vision model). It never treats prompt text as visual evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from image_generation.models import GenerationRequest, GenerationResult

from .models import FailureType, QACriterion, QAFinding, QAReport, QAStatus, parse_qa_report
from .parser import VisionEvaluation, parse_qwen_response


class VisionQAEvaluator:
    def __init__(self, provider=None, *, qa_model: str = "contract-heuristic-v1"):
        self.provider = provider
        self.qa_model = qa_model

    def qa(self, request: GenerationRequest, result: GenerationResult, *, observations: dict[str, Any] | None = None, template_requirements: list[str] | None = None, canonical_asset: str | None = None) -> QAReport:
        if result.image_id != request.image_id or result.generation_id != request.generation_id:
            return self._invalid_contract_report(request, result, "GenerationResult does not match GenerationRequest")
        if result.status != "succeeded" or not result.output_assets:
            return self._invalid_contract_report(request, result, "generated image is unavailable")
        if self.provider is not None and observations is None:
            try:
                observations = self.provider.evaluate(request, result, canonical_asset=canonical_asset, template_requirements=template_requirements)
            except Exception as exc:
                return self._invalid_model_report(request, result, str(exc))
        if observations is None:
            return self._needs_review_report(request, result, "No visual observations/provider supplied; image content was not guessed")
        if isinstance(observations, VisionEvaluation):
            if observations.parse_status != "SUCCESS":
                return self._invalid_model_report(request, result, observations.parse_error or "invalid vision evaluation")
            observations = observations.model_dump()
        if not isinstance(observations, dict):
            return self._invalid_model_report(request, result, "provider output is not an object")
        try:
            if {"product_truth", "template_fidelity", "visual_evidence", "decision_coverage"} <= set(observations):
                return self._from_observations(request, result, observations, template_requirements or [])
            return self._from_observations(request, result, observations, template_requirements or [])
        except (TypeError, ValueError, KeyError) as exc:
            return self._invalid_model_report(request, result, str(exc))

    def evaluate_task(self, task, image_result, *, observations=None):
        """Provider-neutral QA entry point; adapts ImageResult to the legacy contract."""
        from image_generation.models import GenerationRequest, GenerationResult, OutputAsset, LegacyReferenceAsset
        request = GenerationRequest(generation_id=task.task_id, image_id=task.task_id.replace("gen_", ""), role=task.role,
            template_id=task.composition_spec.layout, product_id=task.sku, reference_assets=[], generation_goal=task.objective,
            prompt=task.visual_strategy, negative_constraints=task.constraints.must_not_introduce,
            required_visual_evidence=task.qa_requirements.required_visual_evidence, required_facts=task.constraints.must_preserve,
            required_claims=[], asset_limitations=[], generation_metadata={})
        result = GenerationResult(generation_id=task.task_id, image_id=request.image_id, provider=image_result.provider,
            model=image_result.model, status="succeeded", output_assets=[OutputAsset(path=image_result.image_path, sha256="")],
            request_id=image_result.metadata.get("request_id"), latency_ms=0, attempt=1, policy_id="task")
        return self.qa(request, result, observations=observations, template_requirements=task.composition_spec.required_evidence)

    def _from_observations(self, request, result, obs, requirements):
        product = self._criterion(request, obs.get("product_truth", {}), "product identity")
        template = self._criterion(request, obs.get("template_fidelity", {}), "template requirements")
        visual = self._evidence(request, obs.get("visual_evidence", {}))
        decision = self._decision(request, obs.get("decision_coverage", {}))
        violations = [self._finding(item) for item in obs.get("violations", [])]
        # Explicit constraint observations are accepted only when backed by the provider.
        for item in obs.get("constraint_violations", []):
            violations.append(self._finding({**item, "failure_type": item.get("failure_type", FailureType.UNSUPPORTED_CLAIM.value)}))
        failures = []
        for finding in [*product.findings, *template.findings, *visual.findings, *decision.findings, *violations]:
            if finding.failure_type and finding.failure_type not in failures:
                failures.append(finding.failure_type)
        critical = any(f.severity == "critical" for f in violations)
        hard = [product, template, visual]
        # A fully specified observation is authoritative; absent optional
        # findings do not downgrade an explicit PASS to NEEDS_REVIEW.
        if critical or any(c.status == QAStatus.FAIL.value for c in hard):
            overall = QAStatus.FAIL.value
        elif any(c.status in {QAStatus.NEEDS_REVIEW.value, QAStatus.PARTIAL.value} for c in [*hard, decision]):
            overall = QAStatus.NEEDS_REVIEW.value
        else:
            overall = QAStatus.PASS.value
        metadata = {"qa_model": self.qa_model, "generation_request_hash": _request_hash(request), "request_id": result.request_id, "output_path": result.output_assets[0].path}
        if "parse_status" in obs:
            metadata["parse_status"] = obs["parse_status"]
        if "raw_model_output" in obs:
            metadata["raw_model_output_sha256"] = hashlib.sha256(str(obs["raw_model_output"]).encode("utf-8")).hexdigest()
        return QAReport(qa_version="1.0.0", generation_id=request.generation_id, image_id=request.image_id, product_id=request.product_id, overall_status=overall, product_truth=product, template_fidelity=template, visual_evidence=visual, decision_coverage=decision, violations=violations, failure_types=failures, review_notes=list(obs.get("review_notes", [])), metadata=metadata)

    def _criterion(self, request, value, label):
        status = value.get("status", QAStatus.NEEDS_REVIEW.value) if isinstance(value, dict) else QAStatus.NEEDS_REVIEW.value
        if isinstance(value, dict) and status == "UNKNOWN":
            status = QAStatus.NEEDS_REVIEW.value
        findings = [self._finding({**item, "criterion": item.get("criterion", label)}) for item in (value.get("findings", []) if isinstance(value, dict) else [])]
        if isinstance(value, dict) and value.get("finding") and status == QAStatus.NEEDS_REVIEW.value and not findings:
            findings = [QAFinding(criterion=label, observed=str(value["finding"]), expected="reliable visual observation", severity="medium", evidence="provider returned uncertainty")]
        return QACriterion(status=status, score=value.get("score") if isinstance(value, dict) else None, findings=findings, finding=value.get("finding") if isinstance(value, dict) else None)

    def _evidence(self, request, value):
        if not isinstance(value, dict):
            return QACriterion(status=QAStatus.NEEDS_REVIEW.value, finding="Visual evidence observations are unavailable")
        missing = list(value.get("missing", []))
        findings = [self._finding(item) for item in value.get("findings", [])]
        for item in missing:
            findings.append(QAFinding(criterion=item, observed="not visibly established", expected=item, severity="high", evidence="provider marked required evidence missing", failure_type=FailureType.MISSING_VISUAL_EVIDENCE.value))
        status = value.get("status", QAStatus.FAIL.value if missing else QAStatus.NEEDS_REVIEW.value)
        if status == "UNKNOWN":
            status = QAStatus.NEEDS_REVIEW.value
        return QACriterion(status=status, score=value.get("score"), findings=findings, missing=missing)

    def _decision(self, request, value):
        if not isinstance(value, dict):
            return QACriterion(status=QAStatus.NEEDS_REVIEW.value, finding="Decision coverage is unavailable")
        status = value.get("status", QAStatus.NEEDS_REVIEW.value)
        if status == "UNKNOWN":
            status = QAStatus.NEEDS_REVIEW.value
        findings = [self._finding({**item, "failure_type": item.get("failure_type", FailureType.DECISION_NOT_COVERED.value)}) for item in value.get("findings", [])]
        if status == QAStatus.PARTIAL.value and not findings:
            findings = [QAFinding(criterion="decision question", observed=value.get("finding", "partial coverage"), expected=request.generation_goal, severity="medium", evidence="provider marked partial", failure_type=FailureType.DECISION_NOT_COVERED.value)]
        return QACriterion(status=status, score=value.get("score"), findings=findings, finding=value.get("finding"))

    @staticmethod
    def _finding(item):
        if isinstance(item, str):
            return QAFinding(criterion="visual QA", observed=item, expected="request contract", severity="medium")
        return QAFinding(criterion=item.get("criterion", "visual QA"), observed=item.get("observed", ""), expected=item.get("expected", ""), severity=item.get("severity", "medium"), evidence=item.get("evidence", ""), failure_type=item.get("failure_type"))

    def _needs_review_report(self, request, result, note):
        criterion = QACriterion(status=QAStatus.NEEDS_REVIEW.value, finding=note)
        return QAReport("1.0.0", request.generation_id, request.image_id, request.product_id, QAStatus.NEEDS_REVIEW.value, criterion, criterion, criterion, criterion, review_notes=[note], metadata={"qa_model": self.qa_model, "request_id": result.request_id})

    def _invalid_model_report(self, request, result, note):
        report = self._needs_review_report(request, result, note)
        report.failure_types = [FailureType.QA_MODEL_OUTPUT_INVALID.value]
        report.violations = [QAFinding("QA model output", note, "strict JSON object", "high", note, FailureType.QA_MODEL_OUTPUT_INVALID.value)]
        return report

    def _invalid_contract_report(self, request, result, note):
        report = self._needs_review_report(request, result, note)
        report.failure_types = [FailureType.COMPOSITION_FAILURE.value]
        return report


def evaluate_request(request, result, **kwargs):
    return VisionQAEvaluator().qa(request, result, **kwargs)


def _request_hash(request):
    return hashlib.sha256(json.dumps(request.model_dump(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
