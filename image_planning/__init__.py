"""Strategy to Image Plan to Template resolution."""

from .models import (
    CompetitorGap,
    ImagePlan,
    ImagePlanItem,
    ResolvedTemplate,
    ValidationError,
)
from .planner import build_image_plan
from .resolver import resolve_image_plan
from .optimization import ImageOptimizationSpec, ReferencePolicy, load_optimization_registry
from .optimization_validator import validate_optimization_contract

__all__ = [
    "CompetitorGap",
    "ImagePlan",
    "ImagePlanItem",
    "ResolvedTemplate",
    "ValidationError",
    "build_image_plan",
    "resolve_image_plan",
    "ImageOptimizationSpec",
    "ReferencePolicy",
    "load_optimization_registry",
    "validate_optimization_contract",
]
