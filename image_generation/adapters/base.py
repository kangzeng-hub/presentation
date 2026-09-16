"""Provider-neutral execution interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import GenerationRequest, GenerationResult, ModelExecutionPolicy


class ImageGenerationProvider(ABC):
    def generate_task(self, task):
        """Provider-neutral entry point; legacy adapters may override this."""
        raise NotImplementedError
    @abstractmethod
    def generate(self, request: GenerationRequest, policy: ModelExecutionPolicy) -> GenerationResult:
        """Execute one request according to an explicit execution policy."""
        raise NotImplementedError

    def submit(self, payload: dict, *, timeout: float | None = None):
        raise NotImplementedError

    def get_status(self, task_id: str, *, timeout: float | None = None):
        raise NotImplementedError

    def download(self, url: str, *, timeout: float | None = None):
        raise NotImplementedError
