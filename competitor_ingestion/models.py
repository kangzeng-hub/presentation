"""Stable provider-independent competitor contract.

Pydantic is used when installed.  The small dataclass fallback keeps this MVP
usable in the repository's current lightweight virtualenv as well.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

try:
    from pydantic import BaseModel, ConfigDict, Field, conint

    PYDANTIC_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised in the current minimal env
    PYDANTIC_AVAILABLE = False


if PYDANTIC_AVAILABLE:
    class CompetitorReview(BaseModel):
        model_config = ConfigDict(extra="forbid")
        rating: conint(ge=1, le=3)
        title: str | None = None
        text: str | None = None
        date: str | None = None
        verified: bool | None = None


    class CompetitorProduct(BaseModel):
        model_config = ConfigDict(extra="forbid")
        asin: str
        marketplace: str
        captured_at: str
        provider: str
        title: str | None = None
        brand: str | None = None
        price: float | None = None
        rating: float | None = None
        review_count: int | None = None
        bullet_points: list[str] = Field(default_factory=list)
        description: str | None = None
        images: list[str] = Field(default_factory=list)
        reviews: list[CompetitorReview] = Field(default_factory=list)
else:
    @dataclass
    class CompetitorReview:
        rating: int
        title: str | None = None
        text: str | None = None
        date: str | None = None
        verified: bool | None = None

        def __post_init__(self):
            self.rating = int(self.rating)
            if not 1 <= self.rating <= 3:
                raise ValueError("review rating must be between 1 and 3")

        def model_dump(self) -> dict[str, Any]:
            return asdict(self)


    @dataclass
    class CompetitorProduct:
        asin: str
        marketplace: str
        captured_at: str
        provider: str
        title: str | None = None
        brand: str | None = None
        price: float | None = None
        rating: float | None = None
        review_count: int | None = None
        bullet_points: list[str] | None = None
        description: str | None = None
        images: list[str] | None = None
        reviews: list[CompetitorReview] | None = None

        def __post_init__(self):
            self.bullet_points = list(self.bullet_points or [])
            self.images = list(self.images or [])
            self.reviews = list(self.reviews or [])

        def model_dump(self) -> dict[str, Any]:
            value = asdict(self)
            value["reviews"] = [review.model_dump() for review in self.reviews or []]
            return value


def model_dump(value: Any) -> dict[str, Any]:
    """Pydantic v1/v2 and dataclass compatible serialization helper."""
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return asdict(value)
