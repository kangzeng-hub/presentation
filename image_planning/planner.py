"""Deterministic Strategy -> Image Plan planner."""

from __future__ import annotations

from typing import Any
import json
from pathlib import Path

from .models import CompetitorGap, ImagePlan, ImagePlanItem, ValidationError
from .optimization import load_optimization_registry


def build_image_plan(catalog: dict[str, Any], competitor_analysis: str | dict[str, Any], registry: dict[str, Any], image_count: int = 6) -> ImagePlan:
    """Build the default six-image MVP plan from registered facts only."""
    if image_count != 6:
        raise ValidationError("the MVP ImagePlan requires exactly 6 images")
    product = catalog["product"]
    asset = next(item for item in catalog["assets"] if item["asset_id"] == "asset_p1_gold_3pcs")
    claims = {item["claim_id"]: item for item in catalog["claims"]}
    templates = {item["template_id"]: item for item in registry["templates"]}
    role_priorities = {item["role_id"]: item["priority"] for item in registry["roles"]}
    optimization_path = Path(__file__).resolve().parents[1] / "config" / "image_optimization_registry.json"
    optimization = load_optimization_registry(json.loads(optimization_path.read_text(encoding="utf-8")))
    if not isinstance(competitor_analysis, (str, dict)):
        raise ValidationError("competitor_analysis must be text or a mapping")

    included = product["included_set"]
    facts = {
        "identity": [product["name"], "Gold-3PCS", "3PCS", *included, product["material"]["gold_variant"]],
        "contents": ["3PCS", *included],
        "size": [*product["specifications"]["gauges"], product["specifications"]["inner_diameter"], *product["approved_placements"]],
        "material": [product["material"]["base"], product["material"]["gold_variant"], product["material"]["stone"]],
        "structure": [product["specifications"]["closure"]],
        "style": included,
    }
    gap = _competitor_gaps(competitor_analysis)
    items = [
        _item("image_01", "product_main_image", "P0", "What is the product and its included set?", "Keep the main product presentation while fixing language.", "Human optimization specification", facts["identity"], [], ["three actual configurations shown simultaneously and clearly distinguished", "color-accurate metallic finish", "product-dominant white-field presentation"], gap["identity"], "PRODUCT_IDENTITY_MAIN", ["extra jewelry", "invented variant", "competitor product identity"], "Human optimization specification.", templates, role_priorities, optimization["image_01"]),
        _item("image_02", "on_body_wearing_scene", "P0", "How does the product look when worn?", "Show realistic on-body wearing effect.", "Human optimization specification", facts["style"], [], ["on-body appearance", "realistic product-to-face relationship"], gap["style"], "WEAR_STYLE_TRIPTYCH", ["three-piece configuration explanation", "unlisted component"], "Human optimization specification.", templates, role_priorities, optimization["image_02"]),
        _item("image_03", "size_and_piercing_guide", "P0", "How should I understand 18G, 20G, and 8mm?", "Preserve the size and piercing guide while translating copy.", "Human optimization specification", facts["size"], ["claim_multiple_placements"], ["18G/20G and 8mm labels", "piercing location diagram", "gift box"], gap["size"], "SIZE_CHOICE_PROOF", ["exact worn scale inferred from p1.jpg", "unapproved anatomy claims", "extra sizes"], "Human optimization specification.", templates, role_priorities, optimization["image_03"]),
        _item("image_04", "material_and_craft", "P1", "What material and craft details are shown?", "Preserve material and craft evidence while translating copy.", "Human optimization specification", facts["material"], ["claim_f136_titanium", "claim_gold_pvd", "claim_cz"], ["ASTM F136 titanium", "PVD gold plating", "zirconia detail", "hinge structure detail"], gap["material"], "MATERIAL_EVIDENCE", ["certificate proof", "fabricated test report", "medical cure claim", "100% allergy-free claim"], "Human optimization specification.", templates, role_priorities, optimization["image_04"]),
        _item("image_05", "multi_scene_wearing", "P1", "How does the product look across real wearing scenes?", "Show multiple people, positions, and looks.", "Human optimization specification", facts["style"], [], ["multiple people", "different piercing positions", "realistic on-body appearance", "scene variation"], gap["style"], "LIFESTYLE_MOMENTS", ["hinge structure explanation", "material detail explanation"], "Human optimization specification.", templates, role_priorities, optimization["image_05"]),
        _item("image_06", "hinge_operation_demo", "P1", "How does the hinged ring open, position, and close?", "Show a clear hand-operated opening, insertion, and closing sequence.", "Human optimization specification", [product["specifications"]["closure"]], ["claim_click_top"], ["hand operation", "opening state", "closing state", "operation sequence"], gap["structure"], "STRUCTURE_USE_DETAIL", ["three-product wearing comparison"], "Human optimization specification.", templates, role_priorities, optimization["image_06"]),
    ]
    plan = ImagePlan(plan_version="1.0.0", product_id=product["product_id"], strategy_summary="以 P0 识别/内容/规格为购买证明基础，再用 P1 材质、结构和风格解决信任与选择；P2 lifestyle 暂不进入首版六张。", images=items)
    validate_image_plan(plan, catalog, registry)
    return plan


def validate_image_plan(plan: ImagePlan, catalog: dict[str, Any], registry: dict[str, Any]) -> None:
    catalog_facts = _catalog_fact_values(catalog)
    claim_ids = {item["claim_id"] for item in catalog["claims"]}
    template_ids = {item["template_id"] for item in registry["templates"]}
    role_ids = {item["role_id"] for item in registry["roles"]}
    optimization_path = Path(__file__).resolve().parents[1] / "config" / "image_optimization_registry.json"
    optimization = load_optimization_registry(json.loads(optimization_path.read_text(encoding="utf-8")))
    if len(plan.images) != 6:
        raise ValidationError("ImagePlan must contain exactly 6 images")
    seen_ids: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    for item in plan.images:
        if item.image_id in seen_ids:
            raise ValidationError(f"duplicate image_id: {item.image_id}")
        seen_ids.add(item.image_id)
        pair = (item.role, item.decision_question)
        if pair in seen_pairs:
            raise ValidationError("duplicate role + decision_question")
        seen_pairs.add(pair)
        spec = optimization.get(item.image_id)
        if item.role not in role_ids and not (spec and item.role == spec.role):
            raise ValidationError(f"unknown role: {item.role}")
        if item.template_id not in template_ids:
            raise ValidationError(f"unknown template_id: {item.template_id}")
        if item.priority not in {"P0", "P1", "P2"}:
            raise ValidationError(f"invalid priority: {item.priority}")
        for fact in item.required_product_facts:
            if fact not in catalog_facts:
                raise ValidationError(f"unknown product fact: {fact}")
        for claim_id in item.required_claims:
            if claim_id not in claim_ids:
                raise ValidationError(f"unknown claim_id: {claim_id}")
        if spec:
            if item.action != spec.action or item.optimization_spec is None or item.optimization_spec != spec:
                raise ValidationError(f"optimization spec mismatch for {item.image_id}")
            if item.reference_policy != spec.reference_policy:
                raise ValidationError(f"reference policy mismatch for {item.image_id}")
        if role_ids and item.priority != {role_id: role_priorities for role_id, role_priorities in [(r["role_id"], r["priority"]) for r in registry["roles"]]}.get(item.role, item.priority):
            raise ValidationError(f"priority does not match registry for role: {item.role}")


def _catalog_fact_values(catalog: dict[str, Any]) -> set[str]:
    product = catalog["product"]
    specs = product["specifications"]
    values = {product["name"], "Gold-3PCS", "3PCS", product["material"]["base"], product["material"]["gold_variant"], product["material"]["stone"], specs["inner_diameter"], specs["weight"], specs["package_dimensions"], specs["closure"], *product["included_set"], *product["approved_placements"], *specs["gauges"]}
    return values


def _competitor_gaps(analysis: str | dict[str, Any]) -> dict[str, list[CompetitorGap]]:
    # These statements are grounded in the repository's competitor analysis.
    text = analysis if isinstance(analysis, str) else str(analysis)
    def make(dimension: str, pattern: str, opportunity: str) -> CompetitorGap:
        return CompetitorGap(dimension=dimension, competitor_pattern=pattern, our_opportunity=opportunity)
    return {
        "identity": [make("product_identity", "竞品主图使用白底、三件分组和小型佩戴提示。", "用我方 canonical asset 固定 Gold-3PCS 的三种真实款式。")],
        "contents": [make("contents", "竞品主图和内容图反复组织多个产品变体与标签。", "用批准的 3PCS 清单做一对一内容映射。")],
        "size": [make("size_selection", "竞品样本使用鼻部近景、重复面板和尺寸标签回答选择问题。", "用已批准的 18G/20G、8mm 和位置列表建立选择结构，但不从主图推断佩戴比例。")],
        "material": [make("material_trust", "竞品样本使用材质利益块或测试报告式证据区域。", "用已审核 claim ID 做 source-linked 材质展示；没有真实证书就不生成 certificate proof。")],
        "structure": [make("structure_use", "竞品样本使用闭合示意和 2x2 宏观细节网格。", "展示我方已登记的铰链、平接缝和按压卡扣结构，静态证据不冒充操作实拍。")],
        "style": [make("style_projection", "竞品样本使用三联近景和 2+1 人像场景承载风格投射。", "先用三款批准配置做可比较的近景风格图，P2 生活方式后置。")],
    }


def _item(image_id, role, priority, question, need, reason, facts, claims, evidence, gaps, template_id, forbidden, selection_reason, templates, role_priorities, optimization_spec=None):
    if template_id not in templates:
        raise ValidationError(f"planner references unregistered template: {template_id}")
    if role not in role_priorities and optimization_spec is None:
        raise ValidationError(f"planner references unregistered role: {role}")
    if role in role_priorities and role_priorities.get(role) != priority:
        raise ValidationError(f"planner priority mismatch for {role}")
    contract = optimization_spec.model_dump() if optimization_spec else {}
    return ImagePlanItem(image_id=image_id, role=role, priority=priority, decision_question=question, customer_need=need, strategy_reason=reason, required_product_facts=facts, required_claims=claims, required_visual_evidence=evidence, competitor_gap=gaps, template_id=template_id, forbidden_elements=forbidden, selection_reason=selection_reason, optimization_spec=optimization_spec, action=optimization_spec.action if optimization_spec else None, reference_policy=optimization_spec.reference_policy if optimization_spec else None, optimization_contract=contract)
