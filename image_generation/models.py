"""Typed generation request models.

Pydantic is used when available. The standard-library fallback is intentional:
this repository has no dependency manifest and must keep the compiler runnable
in the current environment.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

try:  # pragma: no cover - optional environment path
    from pydantic import BaseModel, ConfigDict, Field
    PYDANTIC_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised by this repository
    PYDANTIC_AVAILABLE = False


class GenerationValidationError(ValueError):
    """Raised when a generation request breaks a traceability constraint."""


ReferenceRole = Literal["product", "competitor", "style", "layout", "information"]
GenerationMode = Literal["create", "edit"]


if PYDANTIC_AVAILABLE:

    class ReferenceBinding(BaseModel):
        model_config = ConfigDict(extra="forbid")
        asset_id: str
        purpose: list[str] = Field(default_factory=list)
        allowed_effects: list[str] = Field(default_factory=list)
        product_identity_source: bool = False

    class ReferenceAsset(BaseModel):
        model_config = ConfigDict(extra="forbid")
        asset_id: str = Field(min_length=1)
        path: str = Field(min_length=1)
        role: ReferenceRole = "product"
        allowed_for_generation: bool = True
        purpose: str = Field(default="product identity", min_length=1)


    class CompositionSpec(BaseModel):
        model_config = ConfigDict(extra="forbid")
        layout: str = Field(min_length=1)
        visual_hierarchy: list[str] = Field(default_factory=list)
        required_evidence: list[str] = Field(default_factory=list)
        forbidden_content: list[str] = Field(default_factory=list)
        reference_policy: list[str] = Field(default_factory=list)
        generation_stage: str | None = None


    class ImageConstraints(BaseModel):
        model_config = ConfigDict(extra="forbid")
        must_preserve: list[str] = Field(default_factory=list)
        must_change: list[str] = Field(default_factory=list)
        must_not_introduce: list[str] = Field(default_factory=list)


    class QARequirements(BaseModel):
        model_config = ConfigDict(extra="forbid")
        required_visual_evidence: list[str] = Field(default_factory=list)
        decision_question: str = ""


    class ImageTask(BaseModel):
        model_config = ConfigDict(extra="forbid")
        task_id: str = Field(min_length=1)
        sku: str = Field(min_length=1)
        role: str = Field(min_length=1)
        objective: str = Field(min_length=1)
        visual_strategy: str = Field(min_length=1)
        product_truth: dict[str, Any] = Field(default_factory=dict)
        reference_assets: list[ReferenceAsset] = Field(default_factory=list)
        generation_mode: GenerationMode = "create"
        composition_spec: CompositionSpec
        constraints: ImageConstraints = Field(default_factory=ImageConstraints)
        qa_requirements: QARequirements = Field(default_factory=QARequirements)


    class ImageResult(BaseModel):
        model_config = ConfigDict(extra="forbid")
        task_id: str
        provider: str
        model: str
        image_path: str
        image_url: str | None = None
        generation_mode: GenerationMode
        metadata: dict[str, Any] = Field(default_factory=dict)
        raw_response_path: str | None = None


    class RevisionInstruction(BaseModel):
        model_config = ConfigDict(extra="forbid")
        task_id: str
        reason_code: str
        severity: str
        instruction: str
        must_preserve: list[str] = Field(default_factory=list)
        must_change: list[str] = Field(default_factory=list)
        forbidden_changes: list[str] = Field(default_factory=list)

else:

    @dataclass
    class ReferenceAsset:
        asset_id: str
        path: str
        role: str = "product"
        allowed_for_generation: bool = True
        purpose: str = "product identity"
        approved_uses: list[str] | None = None

        def model_dump(self): return asdict(self)

    @dataclass
    class LegacyReferenceAsset:
        asset_id: str
        path: str
        role: str
        approved_uses: list[str]

        def model_dump(self): return asdict(self)

    @dataclass
    class CompositionSpec:
        layout: str
        visual_hierarchy: list[str]
        required_evidence: list[str]
        forbidden_content: list[str]
        reference_policy: list[str]
        generation_stage: str | None = None
        def model_dump(self): return asdict(self)

    @dataclass
    class ImageConstraints:
        must_preserve: list[str]
        must_change: list[str]
        must_not_introduce: list[str]
        def model_dump(self): return asdict(self)

    @dataclass
    class QARequirements:
        required_visual_evidence: list[str]
        decision_question: str = ""
        def model_dump(self): return asdict(self)

    @dataclass
    class ImageTask:
        task_id: str
        sku: str
        role: str
        objective: str
        visual_strategy: str
        product_truth: dict[str, Any]
        reference_assets: list[LegacyReferenceAsset]
        generation_mode: str
        composition_spec: CompositionSpec
        constraints: ImageConstraints
        qa_requirements: QARequirements
        def model_dump(self):
            value = asdict(self)
            value["reference_assets"] = [item.model_dump() for item in self.reference_assets]
            return value

    @dataclass
    class ImageResult:
        task_id: str
        provider: str
        model: str
        image_path: str
        image_url: str | None
        generation_mode: str
        metadata: dict[str, Any]
        raw_response_path: str | None = None
        def model_dump(self): return asdict(self)

    @dataclass
    class RevisionInstruction:
        task_id: str
        reason_code: str
        severity: str
        instruction: str
        must_preserve: list[str]
        must_change: list[str]
        forbidden_changes: list[str]
        def model_dump(self): return asdict(self)



if PYDANTIC_AVAILABLE:

    class LegacyReferenceAsset(BaseModel):
        model_config = ConfigDict(extra="forbid")
        asset_id: str = Field(min_length=1)
        path: str = Field(min_length=1)
        role: str = Field(min_length=1)
        approved_uses: list[str]


    class GenerationRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        generation_id: str = Field(pattern=r"^gen_image_[0-9]{2}$")
        image_id: str = Field(pattern=r"^image_[0-9]{2}$")
        role: str = Field(min_length=1)
        template_id: str = Field(min_length=1)
        product_id: str = Field(min_length=1)
        reference_assets: list[LegacyReferenceAsset]
        generation_goal: str = Field(min_length=1)
        prompt: str = Field(min_length=1)
        negative_constraints: list[str]
        required_visual_evidence: list[str]
        required_facts: list[str]
        required_claims: list[str]
        asset_limitations: list[str]
        generation_metadata: dict[str, Any]
        action: str | None = None
        reference_policy: Any | None = None
        optimization_contract: dict[str, Any] = Field(default_factory=dict)
        copy_language: str | None = None
        canonical_product_assets: list[str] = Field(default_factory=list)
        reference_bindings: list[ReferenceBinding] = Field(default_factory=list)


    class GenerationRequestBatch(BaseModel):
        model_config = ConfigDict(extra="forbid")
        generation_version: str = Field(min_length=1)
        product_id: str = Field(min_length=1)
        requests: list[GenerationRequest] = Field(min_length=1)


    class RetryPolicy(BaseModel):
        model_config = ConfigDict(extra="forbid")
        max_attempts: int = Field(default=3, ge=1)


    class ModelExecutionPolicy(BaseModel):
        """Model-agnostic execution controls, deliberately separate from Product Truth."""
        model_config = ConfigDict(extra="forbid")
        policy_id: str = Field(min_length=1)
        model_id: str = Field(min_length=1)
        size: str = Field(default="2K", min_length=1)
        number_of_images: int = Field(default=1, ge=1)
        watermark: bool = False
        enable_sequential: bool = False
        thinking_mode: bool = False
        reference_strategy: str = "canonical_first"
        retry: RetryPolicy = Field(default_factory=RetryPolicy)
        timeout_seconds: int = Field(default=120, ge=1)
        poll_interval_seconds: float = Field(default=3, ge=0)
        seed: int | None = None
        experimental_hints: dict[str, Any] = Field(default_factory=dict)


    class OutputAsset(BaseModel):
        model_config = ConfigDict(extra="forbid")
        path: str
        mime_type: str = "image/png"
        width: int | None = None
        height: int | None = None
        sha256: str


    class GenerationResult(BaseModel):
        model_config = ConfigDict(extra="forbid")
        generation_id: str
        image_id: str
        provider: str = "aliyun_dashscope"
        model: str
        status: Literal["succeeded", "failed", "pending"]
        output_assets: list[OutputAsset] = Field(default_factory=list)
        request_id: str | None = None
        latency_ms: int = 0
        attempt: int = 1
        policy_id: str
        prompt_hash: str | None = None
        request_hash: str | None = None
        reference_asset_ids: list[str] = Field(default_factory=list)
        input_file_hashes: dict[str, str] = Field(default_factory=dict)
        seed: int | None = None
        size: str | None = None
        idempotency_key: str | None = None
        error: dict[str, Any] | None = None

else:

    @dataclass
    class ReferenceBinding:
        asset_id: str
        purpose: list[str]
        allowed_effects: list[str]
        product_identity_source: bool = False
        def model_dump(self): return asdict(self)

    @dataclass
    class LegacyReferenceAsset:
        asset_id: str
        path: str
        role: str
        approved_uses: list[str]

        def model_dump(self):
            return asdict(self)


    @dataclass
    class GenerationRequest:
        generation_id: str
        image_id: str
        role: str
        template_id: str
        product_id: str
        reference_assets: list[LegacyReferenceAsset]
        generation_goal: str
        prompt: str
        negative_constraints: list[str]
        required_visual_evidence: list[str]
        required_facts: list[str]
        required_claims: list[str]
        asset_limitations: list[str]
        generation_metadata: dict[str, Any]
        action: str | None = None
        reference_policy: Any | None = None
        optimization_contract: dict[str, Any] | None = None
        copy_language: str | None = None
        canonical_product_assets: list[str] | None = None
        reference_bindings: list[ReferenceBinding] | None = None

        def model_dump(self):
            result = asdict(self)
            result["reference_assets"] = [asset.model_dump() for asset in self.reference_assets]
            result["reference_bindings"] = [item.model_dump() if hasattr(item, "model_dump") else item for item in (self.reference_bindings or [])]
            return result


    @dataclass
    class GenerationRequestBatch:
        generation_version: str
        product_id: str
        requests: list[GenerationRequest]

        def model_dump(self):
            return {"generation_version": self.generation_version, "product_id": self.product_id, "requests": [item.model_dump() for item in self.requests]}


    @dataclass
    class RetryPolicy:
        max_attempts: int = 3

        def model_dump(self):
            return asdict(self)


    @dataclass
    class ModelExecutionPolicy:
        """Model-agnostic execution controls, deliberately separate from Product Truth."""
        policy_id: str
        model_id: str
        size: str = "2K"
        number_of_images: int = 1
        watermark: bool = False
        enable_sequential: bool = False
        thinking_mode: bool = False
        reference_strategy: str = "canonical_first"
        retry: RetryPolicy = None
        timeout_seconds: int = 120
        poll_interval_seconds: float = 3
        seed: int | None = None
        experimental_hints: dict[str, Any] = None

        def __post_init__(self):
            if self.retry is None:
                self.retry = RetryPolicy()
            if self.experimental_hints is None:
                self.experimental_hints = {}

        def model_dump(self):
            result = asdict(self)
            return result


    @dataclass
    class OutputAsset:
        path: str
        mime_type: str = "image/png"
        width: int | None = None
        height: int | None = None
        sha256: str = ""

        def model_dump(self):
            return asdict(self)


    @dataclass
    class GenerationResult:
        generation_id: str
        image_id: str
        provider: str
        model: str
        status: str
        output_assets: list[OutputAsset]
        request_id: str | None
        latency_ms: int
        attempt: int
        policy_id: str
        prompt_hash: str | None = None
        request_hash: str | None = None
        reference_asset_ids: list[str] = None
        input_file_hashes: dict[str, str] = None
        seed: int | None = None
        size: str | None = None
        idempotency_key: str | None = None
        error: dict[str, Any] | None = None

        def __post_init__(self):
            if self.reference_asset_ids is None:
                self.reference_asset_ids = []
            if self.input_file_hashes is None:
                self.input_file_hashes = {}

        def model_dump(self):
            result = asdict(self)
            result["output_assets"] = [item.model_dump() for item in self.output_assets]
            return result
