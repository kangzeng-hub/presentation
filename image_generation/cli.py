"""CLI for compiling ImagePlan into GenerationRequest JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from image_planning.models import ImagePlan, ImagePlanItem, CompetitorGap, ResolvedTemplate
from .adapters import (
    OpenAIConfigurationError,
    OpenAIImageAdapter,
    ReferenceAssetResolver,
    WanAdapter,
    WanConfigurationError,
)
from .models import GenerationRequest, GenerationRequestBatch, ModelExecutionPolicy, ReferenceAsset
from .prompt_builder import build_generation_requests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile ImagePlan and execute image generation.")
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("prompt-build")
    command.add_argument("--image-plan", default="image_plan.json")
    command.add_argument("--resolved-templates", default="resolved_templates.json")
    command.add_argument("--catalog", default="data/first_party_catalog.json")
    command.add_argument("--registry", default="templates/registry.json")
    command.add_argument("--output", default="generation_requests.json")
    generate = sub.add_parser("generate", help="Execute GenerationRequests with an image provider")
    generate.add_argument("--requests", default="generation_requests.json")
    generate.add_argument("--output-dir", default="output/gpt_image_2")
    generate.add_argument("--policy", default="config/openai_gpt_image_v2.json")
    generate.add_argument("--provider", choices=("auto", "openai", "wan"), default="auto")
    generate.add_argument("--rerun-from", help="Use prior generated image_<nn>.png files as image-to-image references")
    generate.add_argument("--image-id")
    generate.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "generate":
        return _generate(args)
    plan_data = json.loads(Path(args.image_plan).read_text(encoding="utf-8"))
    plan = _load_plan(plan_data)
    resolved = [_load_resolved(item) for item in json.loads(Path(args.resolved_templates).read_text(encoding="utf-8"))]
    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    output = build_generation_requests(plan, resolved, catalog, registry)
    Path(args.output).write_text(json.dumps(output.model_dump(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


def _generate(args) -> int:
    batch = _load_generation_batch(json.loads(Path(args.requests).read_text(encoding="utf-8")))
    rerun_from = getattr(args, "rerun_from", None)
    if rerun_from:
        _replace_references_with_prior_outputs(batch, Path(rerun_from))
    policy = ModelExecutionPolicy(**json.loads(Path(args.policy).read_text(encoding="utf-8")))
    requests = [item for item in batch.requests if not args.image_id or item.image_id == args.image_id]
    if not requests:
        raise SystemExit(f"no request matched image id: {args.image_id}")
    asset_resolver = ReferenceAssetResolver(Path(args.requests).resolve().parent)
    provider = args.provider
    if provider == "auto":
        provider = "openai" if policy.model_id == "gpt-image-2" else "wan"
    if provider == "openai":
        adapter = OpenAIImageAdapter(output_dir=args.output_dir, asset_resolver=asset_resolver)
    else:
        adapter = WanAdapter(output_dir=args.output_dir, asset_resolver=asset_resolver)
    if args.dry_run:
        for request in requests:
            payload, file_hashes = adapter.build_payload(request, policy)
            print(json.dumps({"image_id": request.image_id, "payload": payload, "policy": policy.model_dump(), "reference_file_hashes": file_hashes}, ensure_ascii=False, indent=2))
        return 0
    results = []
    for request in requests:
        try:
            result = adapter.generate(request, policy)
        except (WanConfigurationError, OpenAIConfigurationError) as exc:
            print(f"{request.image_id}: failed - {exc}")
            return 2
        results.append(result)
        print(json.dumps(result.model_dump(), ensure_ascii=False))
    print(f"generated {len(results)} image(s) with {policy.model_id}")
    return 0 if all(item.status == "succeeded" for item in results) else 1


def _replace_references_with_prior_outputs(batch, source_dir: Path):
    """Turn a prior batch's outputs into one-to-one image-edit references."""
    for item in batch.requests:
        path = source_dir / f"{item.image_id}.png"
        if not path.is_file():
            raise SystemExit(f"missing prior output for {item.image_id}: {path}")
        item.reference_assets = [ReferenceAsset(
            asset_id=f"prior_{item.image_id}",
            path=str(path),
            role="prior_wan_output_reference",
            approved_uses=["image-to-image rerun", "composition reference"],
        )]


def _load_generation_batch(data):
    requests = []
    for item in data["requests"]:
        refs = [ReferenceAsset(**ref) for ref in item.get("reference_assets", [])]
        item = {**item, "reference_assets": refs}
        requests.append(GenerationRequest(**item))
    return GenerationRequestBatch(generation_version=data["generation_version"], product_id=data["product_id"], requests=requests)


def _load_plan(data):
    return ImagePlan(plan_version=data["plan_version"], product_id=data["product_id"], strategy_summary=data["strategy_summary"], images=[ImagePlanItem(**{**item, "competitor_gap": [CompetitorGap(**gap) for gap in item["competitor_gap"]]}) for item in data["images"]])


def _load_resolved(data):
    return ResolvedTemplate(**data)


if __name__ == "__main__":
    raise SystemExit(main())
