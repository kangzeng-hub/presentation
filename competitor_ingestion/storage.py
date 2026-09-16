from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import model_dump


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = model_dump(value) if hasattr(value, "model_dump") else value
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def save_run(output_root: str | Path, asin: str, raw_product: Any, raw_reviews: Any, competitor: Any) -> Path:
    directory = Path(output_root) / f"competitor_{asin.upper()}"
    metadata = {
        "captured_at": competitor.captured_at,
        "provider": competitor.provider,
        "asin": competitor.asin,
        "marketplace": competitor.marketplace,
    }
    # Keep object-shaped provider fields directly inspectable while adding a
    # small provenance block. List-shaped responses remain under ``data``.
    def with_metadata(raw: Any) -> Any:
        if isinstance(raw, dict):
            return {**raw, "_ingestion": metadata}
        return {"data": raw, "_ingestion": metadata}

    save_json(directory / "raw_product.json", with_metadata(raw_product))
    save_json(directory / "raw_reviews.json", with_metadata(raw_reviews))
    save_json(directory / "competitor.json", competitor)
    return directory
