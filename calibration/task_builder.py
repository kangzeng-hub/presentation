from __future__ import annotations
from typing import Any

def build_image_task(*, product_truth: dict[str, Any], strategy: dict[str, Any] | str, role_spec: dict[str, Any], template: dict[str, Any] | None = None, revision_instruction: str = "") -> dict[str, Any]:
    """Compile structured inputs into an ImageTask; role rules remain data, not prompt text."""
    return {"product_truth": product_truth, "strategy": strategy, "role_spec": role_spec, "template": template or {}, "revision_instruction": revision_instruction}
