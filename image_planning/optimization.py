"""Human-authored, immutable-at-runtime optimization contracts for each image."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

try:
    from pydantic import BaseModel, ConfigDict, Field
    PYDANTIC_AVAILABLE = True
except ImportError:  # pragma: no cover
    PYDANTIC_AVAILABLE = False

Action = Literal["KEEP_LAYOUT", "REBUILD_COMPOSITION"]
ReferenceMode = Literal["NONE", "OPTIONAL", "REQUIRED"]

if PYDANTIC_AVAILABLE:
    class ReferencePolicy(BaseModel):
        model_config = ConfigDict(extra="forbid", frozen=True)
        mode: ReferenceMode
        asset_ids: list[str] = Field(default_factory=list)
        purposes: list[str] = Field(default_factory=list)
        allowed_effects: list[str] = Field(default_factory=list)
        product_identity_source: bool = False

    class ImageOptimizationSpec(BaseModel):
        model_config = ConfigDict(extra="forbid", frozen=True)
        image_id: str
        role: str
        action: Action
        objective: str
        content_focus: list[str] = Field(default_factory=list)
        must_preserve: list[str] = Field(default_factory=list)
        must_change: list[str] = Field(default_factory=list)
        reference_policy: ReferencePolicy | None = None
        copy_language: str
        copy_focus: list[str] = Field(default_factory=list)
        generation_constraints: list[str] = Field(default_factory=list)
        qa_requirements: list[str] = Field(default_factory=list)
        forbidden_topics: list[str] = Field(default_factory=list)

else:
    @dataclass(frozen=True)
    class ReferencePolicy:
        mode: str
        asset_ids: list[str]
        purposes: list[str]
        allowed_effects: list[str]
        product_identity_source: bool = False
        def model_dump(self): return asdict(self)

    @dataclass(frozen=True)
    class ImageOptimizationSpec:
        image_id: str; role: str; action: str; objective: str
        content_focus: list[str]; must_preserve: list[str]; must_change: list[str]
        reference_policy: ReferencePolicy | None; copy_language: str; copy_focus: list[str]
        generation_constraints: list[str]; qa_requirements: list[str]; forbidden_topics: list[str]
        def model_dump(self): return asdict(self)


def load_optimization_registry(data: dict[str, Any]) -> dict[str, ImageOptimizationSpec]:
    items = data.get("images", data) if isinstance(data, dict) else {}
    values = items.values() if isinstance(items, dict) else items
    specs = {}
    for raw in values:
        raw = dict(raw)
        policy = raw.get("reference_policy")
        raw["reference_policy"] = ReferencePolicy(**policy) if policy else None
        spec = ImageOptimizationSpec(**raw)
        if spec.image_id in specs:
            raise ValueError(f"duplicate optimization spec: {spec.image_id}")
        specs[spec.image_id] = spec
    if set(specs) != {f"image_{i:02d}" for i in range(1, 7)}:
        raise ValueError("optimization registry must contain image_01 through image_06")
    return specs
