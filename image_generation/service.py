"""Unified single-image and batch generation orchestration."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from image_planning.planner import build_image_plan
from image_planning.resolver import resolve_image_plan
from .prompt_builder import build_generation_requests
from .execution import load_policy
from .adapters import OpenAIImageAdapter, WanAdapter

ROOT = Path(__file__).resolve().parents[1]

def build_context():
    catalog = json.loads((ROOT / "examples/demo_sku/catalog.json").read_text())
    registry = json.loads((ROOT / "templates/registry.json").read_text())
    analysis = (ROOT / "examples/demo_sku/competitor-analysis.md").read_text()
    plan = build_image_plan(catalog, analysis, registry)
    resolved = resolve_image_plan(plan, registry)
    batch = build_generation_requests(plan, resolved, catalog, registry)
    return catalog, registry, plan, batch

def generate_image(image_id: str, *, revision_instruction: str = "", provider: str = "auto", output_root: str | Path = "output") -> dict[str, Any]:
    catalog, registry, plan, batch = build_context()
    request = next((r for r in batch.requests if r.image_id == image_id), None)
    if request is None: raise ValueError(f"unknown image_id: {image_id}")
    if revision_instruction:
        request.prompt = request.prompt + "\n[HUMAN REVISION]\n" + revision_instruction
    policy = load_policy(ROOT / "config/openai_gpt_image_v2.json")
    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S")
    run_dir = Path(output_root) / run_id; run_dir.mkdir(parents=True, exist_ok=True)
    from .adapters import ReferenceAssetResolver
    resolver = ReferenceAssetResolver(ROOT)
    selected = provider if provider != "auto" else ("openai" if policy.model_id == "gpt-image-2" else "wan")
    adapter = OpenAIImageAdapter(output_dir=run_dir, asset_resolver=resolver) if selected == "openai" else WanAdapter(output_dir=run_dir, asset_resolver=resolver)
    result = adapter.generate(request, policy)
    record = result.model_dump(); record.update({"run_id": run_id, "role": request.role, "action": request.action, "optimization_spec": request.optimization_contract, "reference_bindings": [x.model_dump() if hasattr(x, "model_dump") else x for x in request.reference_bindings], "prompt": request.prompt, "revision_instruction": revision_instruction})
    (run_dir / f"{image_id}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    return record

def generate_batch(*, provider: str = "auto", output_root: str | Path = "output") -> list[dict[str, Any]]:
    _, _, plan, _ = build_context()
    return [generate_image(item.image_id, provider=provider, output_root=output_root) for item in plan.images]
