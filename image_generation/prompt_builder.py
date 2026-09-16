"""Deterministic compiler from planning artifacts to generation requests."""

from __future__ import annotations

from typing import Any

from .models import GenerationRequest, GenerationRequestBatch, LegacyReferenceAsset, ReferenceBinding
from .validator import validate_generation_requests
from image_planning.optimization_validator import validate_optimization_contract


def build_generation_requests(plan: Any, resolved_templates: list[Any], catalog: dict[str, Any], registry: dict[str, Any], role_specs: dict[str, dict[str, Any]] | None = None) -> GenerationRequestBatch:
    """Compile, without re-planning, one request for every ImagePlan item."""
    resolved_by_image = {item.image_id: item for item in resolved_templates}
    claims = {item["claim_id"]: item for item in catalog["claims"]}
    assets = {item["asset_id"]: item for item in catalog["assets"]}
    requests = []
    for item in plan.images:
        resolved = resolved_by_image[item.image_id]
        bound = _assets_for_item(item, assets)
        reference_assets = [_reference_asset(asset, is_product=(asset["asset_id"] == "asset_p1_gold_3pcs")) for asset in bound]
        canonical = [a["asset_id"] for a in bound if a["asset_id"] == "asset_p1_gold_3pcs"]
        bindings = [ReferenceBinding(asset_id=a["asset_id"], purpose=a.get("binding_purposes", []), allowed_effects=a.get("allowed_effects", []), product_identity_source=bool(a.get("product_identity_source", False))) for a in bound if a["asset_id"] != "asset_p1_gold_3pcs"]
        claim_records = [claims[claim_id] for claim_id in item.required_claims]
        limitations = _merge_unique(limitation for asset in _assets_for_item(item, assets) for limitation in asset["limitations"])
        role_spec = (role_specs or {}).get(item.role)
        prompt = _compose_prompt(item, resolved, catalog, claim_records, reference_assets, limitations, role_spec)
        negatives = _merge_unique([*resolved.forbidden_elements, *item.forbidden_elements, *limitations])
        requests.append(GenerationRequest(
            generation_id=f"gen_{item.image_id}",
            image_id=item.image_id,
            role=item.role,
            template_id=item.template_id,
            product_id=plan.product_id,
            reference_assets=reference_assets,
            generation_goal=item.decision_question,
            prompt=prompt,
            negative_constraints=negatives,
            required_visual_evidence=item.required_visual_evidence,
            required_facts=item.required_product_facts,
            required_claims=item.required_claims,
            asset_limitations=limitations,
            generation_metadata={"priority": item.priority, "compiler": "deterministic", "source_plan_version": plan.plan_version, "role_spec_version": role_spec.get("version") if role_spec else None}, action=item.action, reference_policy=item.reference_policy, optimization_contract=item.optimization_contract, copy_language=_spec_value(item.optimization_spec, "copy_language", None), canonical_product_assets=canonical, reference_bindings=bindings,
        ))
    batch = GenerationRequestBatch(generation_version="1.0.0", product_id=plan.product_id, requests=requests)
    for request, item in zip(batch.requests, plan.images):
        validate_optimization_contract(request, item)
    validate_generation_requests(batch, plan, resolved_templates, catalog, registry)
    return batch


def _assets_for_item(item: Any, assets: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    # The only canonical product asset currently registered is the approved
    # Gold-3PCS photo. It is attached to every product-bearing request.
    asset = assets.get("asset_p1_gold_3pcs")
    if asset is None:
        raise ValueError("canonical asset asset_p1_gold_3pcs is missing")
    result = [asset]
    policy = getattr(item, "reference_policy", None)
    if policy:
        asset_ids = policy.get("asset_ids", []) if isinstance(policy, dict) else policy.asset_ids
        purposes = policy.get("purposes", []) if isinstance(policy, dict) else policy.purposes
        effects = policy.get("allowed_effects", []) if isinstance(policy, dict) else policy.allowed_effects
        for asset_id in asset_ids:
            ref = assets.get(asset_id)
            if ref is None or ref.get("asset_type") != "visual_reference" or ref.get("product_identity_source", False):
                raise ValueError(f"invalid optimization reference asset: {asset_id}")
            approved = {str(x).lower().replace(" ", "_") for x in ref.get("approved_uses", [])}
            requested = {str(x).lower().replace(" ", "_") for x in purposes}
            if not approved or not requested:
                raise ValueError(f"reference purposes not approved for {asset_id}")
            result.append({**ref, "binding_purposes": list(purposes), "allowed_effects": list(effects)})
    return result


def _reference_asset(asset: dict[str, Any], is_product: bool = True) -> LegacyReferenceAsset:
    return LegacyReferenceAsset(asset_id=asset["asset_id"], path=asset["path"], role="product_identity_reference" if is_product else "visual_reference", approved_uses=asset["approved_uses"])


def _compose_prompt(item: Any, resolved: Any, catalog: dict[str, Any], claim_records: list[dict[str, Any]], reference_assets: list[ReferenceAsset], limitations: list[str], role_spec: dict[str, Any] | None = None) -> str:
    brand = catalog["brand"]["visual_strategy"]
    lines = [
        "[ROLE]",
        f"Optimization role: {item.role}",
        f"Optimization action: {item.action}",
        f"Optimization objective: {_spec_value(item.optimization_spec, 'objective', item.customer_need)}",
        f"Compile one image whose purchase decision question is: {item.decision_question}",
        f"The customer need is: {item.customer_need}",
        *(_role_spec_lines(role_spec) if role_spec else []),
        "[PRODUCT]",
        f"Use only product {catalog['product']['product_id']}: {catalog['product']['name']}.",
        "Preserve the exact first-party product shape, count, configuration, and finish from the canonical reference.",
        "[REFERENCE]",
        *[f"Use canonical asset {asset.asset_id} at {asset.path} for product identity; do not substitute competitor or invented product geometry." for asset in reference_assets],
        "[LAYOUT]",
        f"Follow resolved template {resolved.template_id}; layout: {resolved.layout}.",
        f"Composition regions: {resolved.composition}.",
        "[VISUAL HIERARCHY]",
        *[f"{index}. {value}" for index, value in enumerate(resolved.visual_hierarchy, 1)],
        "[REQUIRED FACTS]",
        *[f"Only communicate this catalog fact: {fact}" for fact in item.required_product_facts],
        "[REQUIRED CLAIMS]",
        *[f"Use claim ID {claim['claim_id']} only with its approved wording: {claim['approved_text']}. Evidence note: {claim['evidence']}" for claim in claim_records],
        "[VISUAL EVIDENCE]",
        *[f"Visually demonstrate: {evidence}" for evidence in item.required_visual_evidence],
        "[TEMPLATE REQUIREMENTS]",
        *[f"Required template element: {element}" for element in resolved.required_elements],
        "[BRAND STYLE]",
        f"Use brand palette/direction: {', '.join(brand['primary_palette'])}.",
        f"Visual focus: {', '.join(brand['image_focus'])}.",
        f"Style constraints: {', '.join(brand['style_constraints'])}.",
        "Product Truth, then visual evidence, then template structure, has priority over styling.",
        "[ASSET LIMITATIONS]",
        *[f"Do not infer from the canonical asset: {limitation}" for limitation in limitations],
        "[NEGATIVE CONSTRAINTS]",
        *[f"Do not include: {value}" for value in _merge_unique([*resolved.forbidden_elements, *item.forbidden_elements, *limitations])],
    ]
    spec = item.optimization_spec
    if isinstance(spec, dict):
        from image_planning.optimization import ImageOptimizationSpec, ReferencePolicy
        value = dict(spec)
        if isinstance(value.get("reference_policy"), dict): value["reference_policy"] = ReferencePolicy(**value["reference_policy"])
        spec = ImageOptimizationSpec(**value)
    if spec:
        mode_lines = ["[OPTIMIZATION CONTRACT]"]
        mode_lines += ["PRESERVE_EXISTING_COMPOSITION", "Preserve current composition, product placement, visual hierarchy, and layout. Only perform explicitly requested changes."] if spec.action == "KEEP_LAYOUT" else ["REBUILD_FROM_OPTIMIZATION_SPEC", "Discard the previous composition and image role. Build a new composition from this specification and do not inherit the previous image strategy."]
        mode_lines += [f"Must preserve: {x}" for x in spec.must_preserve] + [f"Must change: {x}" for x in spec.must_change]
        if spec.reference_policy:
            mode_lines += [f"Reference asset {x}: purposes={', '.join(spec.reference_policy.purposes)}; allowed effects={', '.join(spec.reference_policy.allowed_effects)}; product identity source=false" for x in spec.reference_policy.asset_ids]
        mode_lines += [f"Copy language: {spec.copy_language}"] + [f"Forbidden topic: {x}" for x in spec.forbidden_topics]
        lines.extend(mode_lines)
    return "\n".join(lines)

def _spec_value(spec, key, default=""):
    if isinstance(spec, dict): return spec.get(key, default)
    return getattr(spec, key, default) if spec else default


def _role_spec_lines(spec: dict[str, Any]) -> list[str]:
    """Render approved RoleSpec fields as traceable generation constraints."""
    return [
        "[ROLE SPEC]",
        f"RoleSpec {spec.get('role')} v{spec.get('version')}; treat as approved role design rules.",
        f"Business goal: {spec.get('business_goal', '')}",
        f"Consumer question: {spec.get('consumer_question', '')}",
        *[f"Must show: {value}" for value in spec.get("must_show", [])],
        *[f"Visual priority: {value}" for value in spec.get("visual_priority", [])],
        *[f"Composition rule: {value}" for value in spec.get("composition_rules", [])],
        *[f"Must avoid: {value}" for value in spec.get("must_avoid", [])],
        *[f"QA requirement: {value}" for value in spec.get("qa_requirements", [])],
    ]


def _merge_unique(values):
    result = []
    seen = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
