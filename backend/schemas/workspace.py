from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SchemaModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class CreateProject(SchemaModel):
    sku: str = Field(min_length=1)
    project_name: str = Field(min_length=1)


class ProductTruth(SchemaModel):
    project_id: str
    sku: str
    product_name: str
    category: str
    material: dict[str, Any]
    dimensions: dict[str, Any]
    variants: list[dict[str, Any]] = Field(default_factory=list)
    package_contents: list[str] = Field(default_factory=list)
    product_features: list[str] = Field(default_factory=list)
    verified_claims: list[dict[str, Any]] = Field(default_factory=list)
    product_images: list[str] = Field(default_factory=list)
    source: list[str] = Field(min_length=1)
    version: int = Field(ge=1)


class Project(SchemaModel):
    project_id: str
    sku: str
    project_name: str
    overall_status: Literal["queued", "running", "completed", "failed", "cancelled"] = "queued"
    current_stage: str = "product_truth"
    created_at: str
    updated_at: str | None = None


class ProjectWorkspace(Project):
    product_truth: ProductTruth | None = None
    competitors: list[dict[str, Any]] = Field(default_factory=list)
    research: dict[str, Any] | None = None
    competitor_insight: dict[str, Any] | None = None
    strategy: dict[str, Any] | None = None
    listing: dict[str, Any] | None = None
    image_plan: dict[str, Any] | None = None
    image_generation: dict[str, Any] | None = None
    qa: list["QAReport"] = Field(default_factory=list)
    video: dict[str, Any] | None = None
    approvals: list[dict[str, Any]] = Field(default_factory=list)
    active_jobs: list[dict[str, Any]] = Field(default_factory=list)


class ResearchRequest(SchemaModel):
    urls: list[str] = Field(min_length=1)


class CompetitorSnapshot(SchemaModel):
    competitor_id: str
    url: str
    title: str | None = None
    bullet_points: list[str] = Field(default_factory=list)
    description: str | None = None
    rating: float | None = None
    price: float | None = None
    reviews: list[dict[str, Any]] = Field(default_factory=list)
    negative_reviews: list[dict[str, Any]] = Field(default_factory=list)
    neutral_reviews: list[dict[str, Any]] = Field(default_factory=list)
    positive_reviews: list[dict[str, Any]] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    crawl_status: str = "completed"
    captured_at: str | None = None
    raw_source: dict[str, Any] = Field(default_factory=dict)


class EvidenceRef(SchemaModel):
    snapshot_id: str
    field: str
    excerpt: str = ""


class CompetitorInsight(SchemaModel):
    project_id: str
    purchase_drivers: list[str]
    customer_pain_points: list[str]
    competitor_claims: list[str]
    competitor_strengths: list[str]
    competitor_weaknesses: list[str]
    opportunity_gaps: list[str]
    priority_ranking: list[str]
    evidence: list[EvidenceRef]
    confidence: float
    version: int


class PresentationStrategy(SchemaModel):
    project_id: str
    primary_purchase_drivers: list[str]
    customer_pain_points: list[str]
    core_differentiators: list[str]
    product_claims: list[str]
    proof_points: list[str]
    priority_order: list[str]
    listing_mapping: dict[str, Any]
    image_mapping: dict[str, Any]
    video_mapping: dict[str, Any]
    version: int
    product_truth_version: int | None = None
    competitor_insight_version: int | None = None


class ListingPlan(SchemaModel):
    project_id: str
    product_truth_version: int
    insight_version: int
    strategy_version: int
    title: str
    bullet_points: list[str]
    product_description: str
    claims_used: list[str]
    strategy_refs: list[str]
    version: int
    generated_content: dict[str, Any] = Field(default_factory=dict)
    edited_content: dict[str, Any] | None = None
    approved_content: dict[str, Any] | None = None
    status: str


class ImagePlanRef(SchemaModel):
    project_id: str
    strategy_version: int
    version: int = 1
    image_plan: dict[str, Any]


class QAReport(SchemaModel):
    qa_version: str
    generation_id: str | None = None
    image_id: str
    product_id: str | None = None
    overall_status: str
    details: dict[str, Any] = Field(default_factory=dict)


class ArtifactVersion(SchemaModel):
    artifact_version_id: str
    project_id: str
    artifact_id: str | None = None
    artifact_type: str
    version: int
    input_refs_json: dict[str, Any]
    payload_json: dict[str, Any] | list[Any]
    created_at: str
    checksum: str | None = None
    source_ref: str | None = None
    created_by: str | None = None


class VideoPlanInput(SchemaModel):
    video_goal: str
    target_audience: str
    duration: int = Field(ge=1)
    hook: str
    selling_points: list[str]
    scene_plan: list[dict[str, Any]]
    visual_direction: str
    narration: str
    on_screen_text: list[str]
    final_prompt: str


class VideoPlan(VideoPlanInput):
    project_id: str
    strategy_version: int
    status: str
    version: int
    strategy_refs: list[str]


class Job(SchemaModel):
    job_id: str
    project_id: str
    type: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    input_version: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    attempt: int = 0
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    lease_expires_at: str | None = None
    result_ref: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class ApprovalCreate(SchemaModel):
    artifact_version_id: str = Field(min_length=1)
    status: Literal["pending", "approved", "rejected"]
    reviewer: str = Field(min_length=1)
    comment: str = ""


class ArtifactApprovalCreate(SchemaModel):
    decision: Literal["approved", "rejected"]
    approved_by: str = Field(min_length=1)
    comment: str = ""


class Approval(ApprovalCreate):
    approval_id: str
    project_id: str
    created_at: str
    updated_at: str
    artifact_id: str | None = None
    artifact_version: int | None = None
    decision: Literal["pending", "approved", "rejected"] | None = None
    approved_by: str | None = None
    approved_at: str | None = None


class ExportManifest(SchemaModel):
    export_id: str
    project_id: str
    status: Literal["pending", "completed", "failed"]
    file_ref: str | None = None
    source_versions: dict[str, Any] = Field(default_factory=dict)
    artifact_versions: list[ArtifactVersion] = Field(default_factory=list)
    generated_files: list[str] = Field(default_factory=list)
    qa_reports: list[str] = Field(default_factory=list)
    approval_state: list[dict[str, Any]] = Field(default_factory=list)
    project: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    approvals: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[dict[str, Any] | str] = Field(default_factory=list)
    files: list[dict[str, Any]] = Field(default_factory=list)
    exported_at: str | None = None
    system_version: str = ""
    created_at: str
    completed_at: str | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | list[dict[str, Any]] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorBody
