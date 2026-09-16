"""Public execution-layer types and policy loading helpers."""

from __future__ import annotations

import json
from pathlib import Path

from .models import GenerationResult, ModelExecutionPolicy, OutputAsset


def load_policy(path: str | Path) -> ModelExecutionPolicy:
    return ModelExecutionPolicy(**json.loads(Path(path).read_text(encoding="utf-8")))


__all__ = ["GenerationResult", "ModelExecutionPolicy", "OutputAsset", "load_policy"]
