from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:  # pragma: no cover
    BaseModel = None


if BaseModel is not None:
    class ProductVideoInput(BaseModel):
        model_config = ConfigDict(extra="forbid")
        product: dict[str, Any]
        selling_points: list[str] = Field(default_factory=list)
        customer_concerns: list[str] = Field(default_factory=list)
        target_scene: str = ""
        reference_images: list[Any] = Field(default_factory=list)
        video_goal: str
        video_style: str

    class VideoPrompt(BaseModel):
        model_config = ConfigDict(extra="forbid")
        prompt: str
        duration_seconds: int = 15
        shot_count: int = 3

    class VideoGenerationRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")
        model: str
        prompt: str
        duration: int = 15
        reference_images: list[Any] = Field(default_factory=list)

    class VideoGenerationResult(BaseModel):
        model_config = ConfigDict(extra="allow")
        status: str
        task_id: str | None = None
        video_path: str | None = None
        video_url: str | None = None
        error: dict[str, Any] | None = None
        request_path: str | None = None
        response_path: str | None = None

    class VideoReview(BaseModel):
        model_config = ConfigDict(extra="forbid")
        product_consistency: int = Field(default=0, ge=0, le=5)
        content_quality: int = Field(default=0, ge=0, le=5)
        visual_quality: int = Field(default=0, ge=0, le=5)
        prompt_following: int = Field(default=0, ge=0, le=5)
        usable: bool = False
        issues: list[str] = Field(default_factory=list)
else:
    @dataclass
    class ProductVideoInput:
        product: dict[str, Any]
        selling_points: list[str] = field(default_factory=list)
        customer_concerns: list[str] = field(default_factory=list)
        target_scene: str = ""
        reference_images: list[Any] = field(default_factory=list)
        video_goal: str = ""
        video_style: str = ""
        def model_dump(self): return asdict(self)
    @dataclass
    class VideoPrompt:
        prompt: str; duration_seconds: int = 15; shot_count: int = 3
        def model_dump(self): return asdict(self)
    @dataclass
    class VideoGenerationRequest:
        model: str; prompt: str; duration: int = 15; reference_images: list[Any] = field(default_factory=list)
        def model_dump(self): return asdict(self)
    @dataclass
    class VideoGenerationResult:
        status: str; task_id: str | None = None; video_path: str | None = None; video_url: str | None = None; error: dict[str, Any] | None = None; request_path: str | None = None; response_path: str | None = None
        def model_dump(self): return asdict(self)
    @dataclass
    class VideoReview:
        product_consistency: int = 0; content_quality: int = 0; visual_quality: int = 0; prompt_following: int = 0; usable: bool = False; issues: list[str] = field(default_factory=list)
        def model_dump(self): return asdict(self)
