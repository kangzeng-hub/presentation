"""Baseline experiment bookkeeping without changing generation semantics."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def start_experiment(path: str | Path, *, experiment_id: str, model: str, policy_id: str, product_id: str, source: str, image_count: int) -> dict:
    value = {
        "experiment_id": experiment_id,
        "model": model,
        "policy_id": policy_id,
        "product_id": product_id,
        "generation_request_source": source,
        "started_at": utc_now(),
        "finished_at": None,
        "image_count": image_count,
        "status": "running",
    }
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


def finish_experiment(path: str | Path, *, status: str, image_count: int | None = None) -> dict:
    target = Path(path)
    value = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
    value["finished_at"] = utc_now()
    value["status"] = status
    if image_count is not None:
        value["image_count"] = image_count
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value


def write_baseline_summary(path: str | Path, *, experiment_id: str, total_images: int, generation_succeeded: int, generation_failed: int, qa_counts: dict[str, int] | None = None, failure_counts: dict[str, int] | None = None, failure_types: list[str] | None = None, status: str = "blocked") -> dict:
    qa_counts = qa_counts or {"pass": 0, "fail": 0, "needs_review": 0}
    value = {
        "experiment_id": experiment_id,
        "total_images": total_images,
        "generation": {"succeeded": generation_succeeded, "failed": generation_failed},
        "qa": qa_counts,
        "failure_counts": failure_counts or {},
        "failure_types": failure_types or [],
        "status": status,
    }
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return value
