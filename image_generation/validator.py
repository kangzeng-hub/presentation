"""Structural and second-layer prompt validation for generation requests."""

from __future__ import annotations

from typing import Any

from .models import GenerationRequest, GenerationRequestBatch, GenerationValidationError


def validate_generation_request(request: GenerationRequest, plan_item: Any, resolved_template: Any, catalog: dict[str, Any], registry: dict[str, Any]) -> None:
    product = catalog["product"]
    if request.product_id != product["product_id"]:
        raise GenerationValidationError("product_id does not match catalog")
    template_ids = {item["template_id"] for item in registry["templates"]}
    if request.template_id not in template_ids:
        raise GenerationValidationError(f"unknown template_id: {request.template_id}")
    if request.template_id != plan_item.template_id or request.image_id != plan_item.image_id:
        raise GenerationValidationError("GenerationRequest is inconsistent with ImagePlan")
    claim_map = {item["claim_id"]: item for item in catalog["claims"]}
    for claim_id in request.required_claims:
        if claim_id not in claim_map:
            raise GenerationValidationError(f"unknown claim_id: {claim_id}")
    fact_values = _catalog_fact_values(catalog)
    for fact in request.required_facts:
        if fact not in fact_values:
            raise GenerationValidationError(f"unknown product fact: {fact}")
    asset_map = {item["asset_id"]: item for item in catalog["assets"]}
    for reference in request.reference_assets:
        if reference.asset_id not in asset_map:
            raise GenerationValidationError(f"unknown asset_id: {reference.asset_id}")
        asset = asset_map[reference.asset_id]
        if reference.path != asset["path"]:
            raise GenerationValidationError(f"asset path mismatch: {reference.asset_id}")
        if not reference.approved_uses:
            raise GenerationValidationError(f"asset has no approved uses: {reference.asset_id}")
    forbidden = [str(item).lower() for item in catalog["brand"]["forbidden_claims"]]
    prompt_and_negatives = (request.prompt + " " + " ".join(request.negative_constraints)).lower()
    for phrase in forbidden:
        if phrase in prompt_and_negatives:
            raise GenerationValidationError(f"forbidden claim appears in request: {phrase}")
    if request.template_id != resolved_template.template_id:
        raise GenerationValidationError("GenerationRequest is inconsistent with ResolvedTemplate")
    required_strings = [plan_item.decision_question, *plan_item.required_visual_evidence, *resolved_template.required_elements]
    for required in required_strings:
        if required not in request.prompt:
            raise GenerationValidationError(f"prompt does not contain required instruction: {required}")
    for limitation in request.asset_limitations:
        if limitation not in request.prompt and limitation not in request.negative_constraints:
            raise GenerationValidationError(f"asset limitation was ignored: {limitation}")
    for claim_id in request.required_claims:
        if claim_id not in request.prompt:
            raise GenerationValidationError(f"claim_id is not traceable in prompt: {claim_id}")


def validate_generation_requests(batch: GenerationRequestBatch, plan: Any, resolved_templates: list[Any], catalog: dict[str, Any], registry: dict[str, Any]) -> None:
    if len(batch.requests) != len(plan.images):
        raise GenerationValidationError("GenerationRequest count does not match ImagePlan")
    resolved_by_image = {item.image_id: item for item in resolved_templates}
    plan_by_image = {item.image_id: item for item in plan.images}
    if set(resolved_by_image) != set(plan_by_image):
        raise GenerationValidationError("ResolvedTemplate and ImagePlan image IDs differ")
    seen: set[str] = set()
    for request in batch.requests:
        if request.generation_id in seen:
            raise GenerationValidationError(f"duplicate generation_id: {request.generation_id}")
        seen.add(request.generation_id)
        if request.image_id not in plan_by_image:
            raise GenerationValidationError(f"unknown image_id: {request.image_id}")
        validate_generation_request(request, plan_by_image[request.image_id], resolved_by_image[request.image_id], catalog, registry)


def _catalog_fact_values(catalog: dict[str, Any]) -> set[str]:
    product = catalog["product"]
    specs = product["specifications"]
    return {product["name"], "Gold-3PCS", "3PCS", product["material"]["base"], product["material"]["gold_variant"], product["material"]["stone"], specs["inner_diameter"], specs["weight"], specs["package_dimensions"], specs["closure"], *product["included_set"], *product["approved_placements"], *specs["gauges"]}
