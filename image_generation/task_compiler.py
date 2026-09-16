"""Compatibility compiler from existing generation requests to ImageTask."""

from __future__ import annotations

from .models import CompositionSpec, ImageConstraints, ImageTask, QARequirements, ReferenceAsset


def image_task_from_request(request, *, resolved_template=None, product_truth=None, generation_mode="create") -> ImageTask:
    """Build the provider-independent task without changing the existing request contract."""
    resolved_template = resolved_template
    layout = getattr(resolved_template, "layout", request.template_id)
    hierarchy = list(getattr(resolved_template, "visual_hierarchy", []))
    required = list(getattr(resolved_template, "required_elements", []))
    forbidden = list(getattr(resolved_template, "forbidden_elements", [])) + list(request.negative_constraints)
    refs = []
    for asset in request.reference_assets:
        role = "product" if "product" in str(getattr(asset, "role", "")) or asset.asset_id.startswith("asset_") else "style"
        refs.append(ReferenceAsset(asset_id=asset.asset_id, path=asset.path, role=role,
                                   allowed_for_generation=(role == "product"),
                                   purpose="preserve canonical product identity" if role == "product" else "analysis-only reference"))
    preserve = list(request.required_facts)
    return ImageTask(
        task_id=request.generation_id,
        sku=request.product_id,
        role=request.role,
        objective=request.generation_goal,
        visual_strategy=request.prompt,
        product_truth=product_truth or {"required_facts": request.required_facts, "required_claims": request.required_claims},
        reference_assets=refs,
        generation_mode=generation_mode,
        composition_spec=CompositionSpec(layout=layout, visual_hierarchy=hierarchy,
                                         required_evidence=required or list(request.required_visual_evidence),
                                         forbidden_content=forbidden, reference_policy=["CANONICAL_PRODUCT"]),
        constraints=ImageConstraints(must_preserve=preserve, must_change=[], must_not_introduce=forbidden),
        qa_requirements=QARequirements(required_visual_evidence=list(request.required_visual_evidence), decision_question=request.generation_goal),
    )


def revision_instruction_from_report(task, report):
    """Turn structured QA findings into a deterministic edit instruction."""
    findings = list(getattr(report, "violations", []))
    for criterion in ("product_truth", "template_fidelity", "visual_evidence", "decision_coverage"):
        findings.extend(getattr(getattr(report, criterion, None), "findings", []) or [])
    first = findings[0] if findings else None
    instruction = getattr(first, "expected", None) or "Address the failed QA criteria while preserving product identity."
    reason = getattr(first, "failure_type", None) or "qa_revision"
    severity = getattr(first, "severity", "medium")
    return {"task_id": task.task_id, "reason_code": reason, "severity": severity,
            "instruction": instruction, "must_preserve": list(task.constraints.must_preserve),
            "must_change": list(task.constraints.must_change),
            "forbidden_changes": list(task.constraints.must_not_introduce)}
