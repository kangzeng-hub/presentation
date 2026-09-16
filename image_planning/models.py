"""Typed Image Plan models with optional Pydantic integration.

The repository intentionally has no dependency lockfile. When Pydantic is
installed, these classes use it; otherwise the small strict fallback keeps
the CLI and validation usable with the Python standard library alone.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, ClassVar, Literal
from .optimization import ImageOptimizationSpec, ReferencePolicy

try:  # pragma: no cover - exercised only when the optional dependency exists
    from pydantic import BaseModel, ConfigDict, Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback is covered by repository tests
    PYDANTIC_AVAILABLE = False


class ValidationError(ValueError):
    """Raised when a plan violates product, claim, template, or planning rules."""


Priority = Literal["P0", "P1", "P2"]


if PYDANTIC_AVAILABLE:

    class CompetitorGap(BaseModel):
        model_config = ConfigDict(extra="forbid")
        dimension: str = Field(min_length=1)
        competitor_pattern: str = Field(min_length=1)
        our_opportunity: str = Field(min_length=1)


    class ImagePlanItem(BaseModel):
        model_config = ConfigDict(extra="forbid")
        image_id: str = Field(pattern=r"^image_[0-9]{2}$")
        role: str = Field(min_length=1)
        priority: Priority
        decision_question: str = Field(min_length=1)
        customer_need: str = Field(min_length=1)
        strategy_reason: str = Field(min_length=1)
        required_product_facts: list[str]
        required_claims: list[str]
        required_visual_evidence: list[str]
        competitor_gap: list[CompetitorGap]
        template_id: str = Field(pattern=r"^[A-Z][A-Z0-9_]+$")
        forbidden_elements: list[str]
        selection_reason: str = Field(min_length=1)
        optimization_spec: ImageOptimizationSpec | None = None
        action: Literal["KEEP_LAYOUT", "REBUILD_COMPOSITION"] | None = None
        reference_policy: ReferencePolicy | None = None
        optimization_contract: dict[str, Any] = Field(default_factory=dict)


    class ImagePlan(BaseModel):
        model_config = ConfigDict(extra="forbid")
        plan_version: str = Field(min_length=1)
        product_id: str = Field(min_length=1)
        strategy_summary: str = Field(min_length=1)
        images: list[ImagePlanItem] = Field(min_length=6, max_length=6)

        @field_validator("images")
        @classmethod
        def unique_image_ids(cls, value):
            ids = [item.image_id for item in value]
            if len(ids) != len(set(ids)):
                raise ValueError("image_id values must be unique")
            pairs = [(item.role, item.decision_question) for item in value]
            if len(pairs) != len(set(pairs)):
                raise ValueError("role + decision_question pairs must be unique")
            return value


    class ResolvedTemplate(BaseModel):
        model_config = ConfigDict(extra="forbid")
        image_id: str = Field(pattern=r"^image_[0-9]{2}$")
        template_id: str = Field(pattern=r"^[A-Z][A-Z0-9_]+$")
        layout: str = Field(min_length=1)
        composition: str = Field(min_length=1)
        visual_hierarchy: list[str]
        required_elements: list[str]
        allowed_style_elements: list[str]
        forbidden_elements: list[str]

else:

    @dataclass
    class CompetitorGap:
        dimension: str
        competitor_pattern: str
        our_opportunity: str

        def __post_init__(self):
            _require_strings(self, ("dimension", "competitor_pattern", "our_opportunity"))

        def model_dump(self):
            return asdict(self)


    @dataclass
    class ImagePlanItem:
        image_id: str
        role: str
        priority: str
        decision_question: str
        customer_need: str
        strategy_reason: str
        required_product_facts: list[str]
        required_claims: list[str]
        required_visual_evidence: list[str]
        competitor_gap: list[CompetitorGap]
        template_id: str
        forbidden_elements: list[str]
        selection_reason: str
        optimization_spec: ImageOptimizationSpec | None = None
        action: str | None = None
        reference_policy: ReferencePolicy | None = None
        optimization_contract: dict[str, Any] | None = None

        def __post_init__(self):
            _require_strings(self, ("image_id", "role", "decision_question", "customer_need", "strategy_reason", "template_id", "selection_reason"))
            if self.priority not in {"P0", "P1", "P2"}:
                raise ValidationError("priority must be P0, P1, or P2")
            if not self.image_id.startswith("image_"):
                raise ValidationError("image_id must use image_NN format")

        def model_dump(self):
            result = asdict(self)
            result["competitor_gap"] = [gap.model_dump() for gap in self.competitor_gap]
            return result


    @dataclass
    class ImagePlan:
        plan_version: str
        product_id: str
        strategy_summary: str
        images: list[ImagePlanItem]

        def __post_init__(self):
            _require_strings(self, ("plan_version", "product_id", "strategy_summary"))
            if len(self.images) != 6:
                raise ValidationError("ImagePlan must contain exactly 6 images")
            ids = [item.image_id for item in self.images]
            if len(ids) != len(set(ids)):
                raise ValidationError("image_id values must be unique")
            pairs = [(item.role, item.decision_question) for item in self.images]
            if len(pairs) != len(set(pairs)):
                raise ValidationError("role + decision_question pairs must be unique")

        def model_dump(self):
            return {"plan_version": self.plan_version, "product_id": self.product_id, "strategy_summary": self.strategy_summary, "images": [item.model_dump() for item in self.images]}


    @dataclass
    class ResolvedTemplate:
        image_id: str
        template_id: str
        layout: str
        composition: str
        visual_hierarchy: list[str]
        required_elements: list[str]
        allowed_style_elements: list[str]
        forbidden_elements: list[str]

        def __post_init__(self):
            _require_strings(self, ("image_id", "template_id", "layout", "composition"))

        def model_dump(self):
            return asdict(self)


def _require_strings(instance: Any, fields: tuple[str, ...]) -> None:
    for field in fields:
        if not isinstance(getattr(instance, field), str) or not getattr(instance, field).strip():
            raise ValidationError(f"{field} must be a non-empty string")
