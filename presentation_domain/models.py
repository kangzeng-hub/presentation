from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AsyncStatus(str, Enum):
    QUEUED = "queued"; RUNNING = "running"; COMPLETED = "completed"; FAILED = "failed"; CANCELLED = "cancelled"
class HumanStatus(str, Enum):
    PENDING_REVIEW = "pending_review"; APPROVED = "approved"; REJECTED = "rejected"; REVISION_REQUIRED = "revision_required"
class FactKind(str, Enum): FACT = "FACT"; CLAIM = "CLAIM"; INFERENCE = "INFERENCE"

def now() -> str: return datetime.now(timezone.utc).isoformat()
def _required(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value.strip(): raise ValueError(f"{name} must be a non-empty string")
def _version(value: int, name: str = "version") -> None:
    if not isinstance(value, int) or value < 1: raise ValueError(f"{name} must be a positive integer")
def _refs(refs: list[str], name: str) -> None:
    if not isinstance(refs, list) or any(not isinstance(x, str) or not x.strip() for x in refs): raise ValueError(f"{name} must contain non-empty references")

@dataclass
class ProductTruth:
    project_id: str; sku: str; product_name: str; category: str
    material: dict[str, Any]; dimensions: dict[str, Any]; variants: list[dict[str, Any]]
    package_contents: list[str]; product_features: list[str]; verified_claims: list[dict[str, Any]]
    product_images: list[str]; source: list[str]; version: int = 1
    def validate(self):
        for n in ("project_id","sku","product_name","category"): _required(getattr(self,n), n)
        _version(self.version); _refs(self.source, "source"); _refs(self.product_images, "product_images")
        for claim in self.verified_claims:
            if claim.get("kind") != FactKind.CLAIM.value or not claim.get("source"): raise ValueError("verified claims must be CLAIM entries with source")
        return self

@dataclass
class CompetitorSnapshot:
    competitor_id: str; url: str; asin: str | None = None; title: str | None = None
    bullet_points: list[str] = field(default_factory=list); description: str | None = None
    rating: float | None = None; price: float | None = None; reviews: list[dict[str, Any]] = field(default_factory=list)
    negative_reviews: list[dict[str, Any]] = field(default_factory=list); neutral_reviews: list[dict[str, Any]] = field(default_factory=list)
    positive_reviews: list[dict[str, Any]] = field(default_factory=list); images: list[str] = field(default_factory=list)
    crawl_status: str = AsyncStatus.QUEUED.value; crawled_at: str | None = None; raw_source: Any = None
    def validate(self):
        _required(self.competitor_id,"competitor_id"); _required(self.url,"url")
        if self.crawl_status not in {x.value for x in AsyncStatus}: raise ValueError("invalid crawl_status")
        if self.rating is not None and not 0 <= self.rating <= 5: raise ValueError("rating must be 0..5")
        return self

@dataclass
class EvidenceRef:
    snapshot_id: str; field: str; excerpt: str = ""
    def validate(self): _required(self.snapshot_id,"snapshot_id"); _required(self.field,"field"); return self

@dataclass
class CompetitorInsight:
    project_id: str; purchase_drivers: list[str]; customer_pain_points: list[str]; competitor_claims: list[str]
    competitor_strengths: list[str]; competitor_weaknesses: list[str]; opportunity_gaps: list[str]
    priority_ranking: list[str]; evidence: list[EvidenceRef]; confidence: float; version: int = 1
    def validate(self):
        _required(self.project_id,"project_id"); _version(self.version)
        if not 0 <= self.confidence <= 1: raise ValueError("confidence must be 0..1")
        if not self.evidence: raise ValueError("insight requires traceable evidence")
        for e in self.evidence: e.validate()
        return self

@dataclass
class PresentationStrategy:
    project_id: str; primary_purchase_drivers: list[str]; customer_pain_points: list[str]; core_differentiators: list[str]
    product_claims: list[str]; proof_points: list[str]; priority_order: list[str]
    listing_mapping: dict[str, Any]; image_mapping: dict[str, Any]; video_mapping: dict[str, Any]; version: int = 1
    def validate(self): _required(self.project_id,"project_id"); _version(self.version); return self

@dataclass
class ListingPlan:
    project_id: str; product_truth_version: int; insight_version: int; strategy_version: int
    title: str; bullet_points: list[str]; product_description: str; claims_used: list[str]; strategy_refs: list[str]
    version: int = 1; generated_content: dict[str, Any] = field(default_factory=dict); edited_content: dict[str, Any] | None = None
    approved_content: dict[str, Any] | None = None; status: str = HumanStatus.PENDING_REVIEW.value
    def validate(self):
        _required(self.project_id,"project_id"); _version(self.version); _version(self.product_truth_version,"product_truth_version"); _version(self.insight_version,"insight_version"); _version(self.strategy_version,"strategy_version"); _refs(self.strategy_refs,"strategy_refs")
        if self.status not in {x.value for x in HumanStatus}: raise ValueError("invalid listing status")
        return self

    def validate_references(self, product_truth: ProductTruth | None = None, insight: CompetitorInsight | None = None, strategy: PresentationStrategy | None = None):
        self.validate()
        if product_truth is None or product_truth.project_id != self.project_id or product_truth.version != self.product_truth_version: raise ValueError("listing references unavailable ProductTruth version")
        if insight is None or insight.project_id != self.project_id or insight.version != self.insight_version: raise ValueError("listing references unavailable CompetitorInsight version")
        if strategy is None or strategy.project_id != self.project_id or strategy.version != self.strategy_version: raise ValueError("listing references unavailable PresentationStrategy version")
        return self

@dataclass
class ImagePlanRef:
    project_id: str; strategy_version: int; image_plan: dict[str, Any]
    def validate(self): _required(self.project_id,"project_id"); _version(self.strategy_version,"strategy_version");
    
@dataclass
class ImageGenerationRef:
    project_id: str; image_id: str; version: int; model: str; prompt: str; input_refs: list[str]; strategy_version: int; created_at: str = field(default_factory=now)
    def validate(self): _required(self.project_id,"project_id"); _required(self.image_id,"image_id"); _required(self.model,"model"); _required(self.prompt,"prompt"); _version(self.version); _version(self.strategy_version,"strategy_version"); return self

@dataclass
class ImageQARef:
    project_id: str; image_id: str; qa_report: dict[str, Any]; status: str
    def validate(self):
        _required(self.project_id,"project_id"); _required(self.image_id,"image_id")
        if self.status not in {"PASS","FAIL","NEEDS_REVIEW"}: raise ValueError("invalid QA status")
        return self

@dataclass
class HumanReview:
    project_id: str; image_id: str; status: str; version: int = 1; feedback: dict[str, Any] = field(default_factory=dict); created_at: str = field(default_factory=now)
    def validate(self):
        _required(self.project_id,"project_id"); _required(self.image_id,"image_id"); _version(self.version)
        if self.status not in {x.value for x in HumanStatus}: raise ValueError("invalid human review status")
        return self

@dataclass
class VideoPlan:
    project_id: str; strategy_version: int; video_goal: str; target_audience: str; duration: int; hook: str
    selling_points: list[str]; scene_plan: list[dict[str, Any]]; visual_direction: str; narration: str
    on_screen_text: list[str]; final_prompt: str; status: str = HumanStatus.PENDING_REVIEW.value; version: int = 1
    strategy_refs: list[str] = field(default_factory=list); listing_version: int | None = None; image_plan_version: str | None = None
    def validate(self):
        for n in ("project_id","video_goal","target_audience","hook","visual_direction","narration","final_prompt"): _required(getattr(self,n),n)
        _version(self.version); _version(self.strategy_version,"strategy_version"); _refs(self.strategy_refs,"strategy_refs")
        if self.duration <= 0: raise ValueError("duration must be positive")
        if self.status not in {x.value for x in HumanStatus}: raise ValueError("invalid video status")
        return self

@dataclass
class Project:
    project_id: str; sku: str; project_name: str; overall_status: str = AsyncStatus.QUEUED.value; current_stage: str = "product_truth"
    product_truth_version: int | None = None; insight_version: int | None = None; strategy_version: int | None = None; created_at: str = field(default_factory=now)
    def validate(self):
        _required(self.project_id,"project_id"); _required(self.sku,"sku"); _required(self.project_name,"project_name")
        if self.overall_status not in {x.value for x in AsyncStatus}: raise ValueError("invalid overall_status")
        return self

def to_dict(value: Any) -> dict[str, Any]:
    return asdict(value)
