"""Pre-generation validation of human optimization contracts."""
from __future__ import annotations

from typing import Any

from .models import ValidationError


def validate_optimization_contract(request: Any, plan_item: Any) -> None:
    spec = getattr(plan_item, "optimization_spec", None)
    if spec is None:
        raise ValidationError(f"missing optimization spec for {plan_item.image_id}")
    def value(key, default=None):
        return spec.get(key, default) if isinstance(spec, dict) else getattr(spec, key, default)
    for field in ("image_id", "role", "action"):
        if getattr(request, field, None) != value(field):
            raise ValidationError(f"optimization {field} mismatch for {plan_item.image_id}")
    contract = getattr(request, "optimization_contract", None) or {}
    expected_contract = spec if isinstance(spec, dict) else spec.model_dump()
    if contract and contract != expected_contract:
        raise ValidationError(f"optimization contract mismatch for {plan_item.image_id}")
    expected = value("reference_policy")
    if isinstance(expected, dict):
        from .optimization import ReferencePolicy
        expected = ReferencePolicy(**expected)
    actual = getattr(request, "reference_policy", None)
    if isinstance(actual, dict):
        from .optimization import ReferencePolicy
        actual = ReferencePolicy(**actual)
    if expected is not None:
        if actual is None or actual.mode != expected.mode or list(actual.asset_ids) != list(expected.asset_ids):
            raise ValidationError(f"reference policy mismatch for {plan_item.image_id}")
        if any(getattr(ref, "asset_id", None) != "asset_p1_gold_3pcs" and getattr(ref, "asset_id", None) not in expected.asset_ids for ref in request.reference_assets):
            raise ValidationError(f"unexpected reference asset for {plan_item.image_id}")
    elif actual is not None and actual.mode != "NONE":
        raise ValidationError(f"unexpected reference policy for {plan_item.image_id}")
    if getattr(request, "copy_language", None) not in (None, value("copy_language")):
        raise ValidationError(f"copy language mismatch for {plan_item.image_id}")
    # Forbidden topics are intentionally rendered in the negative contract
    # section; structured request fields are authoritative here.
