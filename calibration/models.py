from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

Verdict = Literal["accept", "partial", "reject"]
ItemStatus = Literal["pending", "reviewed", "regenerating", "ready_for_review", "accepted", "rejected"]
SessionStatus = Literal["draft", "in_progress", "completed"]

PROBLEM_CODES: dict[str, str] = {
    "TASK_NOT_CLEAR": "Task: task unclear", "TASK_NOT_COMPLETED": "Task: task incomplete",
    "PRODUCT_WRONG": "Product: wrong product", "PRODUCT_TOO_SMALL": "Product: too small",
    "PRODUCT_COUNT_WRONG": "Product: wrong count", "PRODUCT_STRUCTURE_WRONG": "Product: wrong structure",
    "FEATURE_NOT_CLEAR": "Business: feature unclear", "PURCHASE_POINT_NOT_SHOWN": "Business: purchase point missing",
    "CONSUMER_DOUBT_UNRESOLVED": "Business: consumer doubt unresolved", "COMPOSITION_WRONG": "Composition: wrong composition",
    "VISUAL_HIERARCHY_WRONG": "Composition: hierarchy", "SUBJECT_TOO_SMALL": "Composition: subject too small",
    "BACKGROUND_TOO_BUSY": "Composition: busy background", "SCENE_NOT_RELEVANT": "Style: scene irrelevant",
    "STYLE_OFF_TARGET": "Style: off target", "INFORMATION_TOO_DENSE": "Information: too dense",
    "INFORMATION_TOO_SPARSE": "Information: too sparse", "COMPETITOR_LEAKAGE": "Leakage: competitor leakage",
    "HALLUCINATED_ELEMENT": "Leakage: hallucinated element", "OTHER": "Other",
}

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class HumanEvaluation:
    verdict: Verdict
    task_alignment: int
    product_accuracy: int
    visual_hierarchy: int
    purchase_value: int
    execution_quality: int
    primary_problem_codes: list[str] = field(default_factory=list)
    human_feedback: str = ""
    suggested_change: str = ""
    preserve: list[str] = field(default_factory=list)
    change: list[str] = field(default_factory=list)
    dont_introduce: list[str] = field(default_factory=list)
    regeneration_instruction: str = ""
    image_id: str | None = None
    created_at: str = field(default_factory=now)
    classified_as: Literal["strategy", "composition", "provider", "mixed", "unclassified"] = "unclassified"
    feedback_id: str | None = None

    def __post_init__(self):
        if self.verdict not in {"accept", "partial", "reject"}: raise ValueError("invalid verdict")
        for name in ("task_alignment", "product_accuracy", "visual_hierarchy", "purchase_value", "execution_quality"):
            value = getattr(self, name)
            if not isinstance(value, int) or not 1 <= value <= 5: raise ValueError(f"{name} must be 1..5")
        unknown = set(self.primary_problem_codes) - set(PROBLEM_CODES)
        if unknown: raise ValueError(f"unknown problem codes: {sorted(unknown)}")

    def model_dump(self): return asdict(self)

@dataclass
class CalibrationItem:
    item_id: str
    session_id: str
    image_path: str
    role: str
    image_plan_snapshot: dict[str, Any]
    qa_snapshot: dict[str, Any] | None = None
    status: ItemStatus = "pending"
    evaluation: HumanEvaluation | None = None
    image_id: str | None = None
    generation_version: int = 1
    role_spec_version: str | None = None
    provider: str | None = None
    active_image_id: str | None = None
    final_verdict: Verdict | None = None
    evaluations: list[HumanEvaluation] = field(default_factory=list)
    def model_dump(self):
        value = asdict(self)
        return value

@dataclass
class RegenerationTask:
    task_id: str
    calibration_item_id: str
    source_image_id: str
    role: str
    role_spec_version: str
    preserve: list[str]
    change: list[str]
    dont_introduce: list[str]
    instruction: str
    prompt_snapshot: dict[str, Any]
    provider: str
    status: Literal["draft", "queued", "generating", "qa_running", "ready_for_review", "accepted", "rejected", "failed"] = "draft"
    created_at: str = field(default_factory=now)
    completed_at: str | None = None
    output_image_ids: list[str] = field(default_factory=list)
    human_feedback_snapshot: dict[str, Any] = field(default_factory=dict)
    generation_request: dict[str, Any] = field(default_factory=dict)
    compiled_prompt: str = ""
    generation_metadata: dict[str, Any] = field(default_factory=dict)
    qa_result: dict[str, Any] | None = None
    error: str | None = None

    def model_dump(self): return asdict(self)

@dataclass
class ImageVersion:
    image_id: str
    logical_image_id: str
    version: int
    path: str
    source_image_id: str | None
    role: str
    role_spec_version: str | None
    provider: str | None
    generation_metadata: dict[str, Any] = field(default_factory=dict)
    prompt_snapshot: dict[str, Any] = field(default_factory=dict)
    qa_result: dict[str, Any] | None = None
    human_evaluation: dict[str, Any] | None = None
    created_at: str = field(default_factory=now)

    def model_dump(self): return asdict(self)

@dataclass
class CalibrationSession:
    session_id: str
    sku: str
    run_id: str | None
    created_at: str
    roles: list[str]
    status: SessionStatus = "draft"
    items: list[CalibrationItem] = field(default_factory=list)
    def model_dump(self): return asdict(self)

@dataclass
class RoleSpec:
    role: str
    version: int
    business_goal: str
    consumer_question: str
    must_show: list[str]
    visual_priority: list[str]
    must_avoid: list[str]
    composition_rules: list[str] = field(default_factory=list)
    preferred_generation_mode: str = "generate"
    qa_requirements: list[str] = field(default_factory=list)
    change_reason: str = ""
    changed_by: str | None = None
    created_at: str = field(default_factory=now)
    source_feedback_ids: list[str] = field(default_factory=list)
    def model_dump(self): return asdict(self)

@dataclass
class RoleSpecRevision:
    role: str
    from_version: int
    to_version: int
    change_reason: str
    changed_by: str | None
    created_at: str
    source_feedback_ids: list[str]
    def model_dump(self): return asdict(self)

@dataclass
class GoldenExample:
    image_path: str
    role: str
    reason: str
    approved_by: str | None = None
    created_at: str = field(default_factory=now)
    kind: Literal["golden", "failure"] = "golden"
    def model_dump(self): return asdict(self)

# Problem codes are persisted as stable strings; PROBLEM_CODES is the canonical
# registry and this alias keeps annotations readable for callers.
ProblemCode = str
