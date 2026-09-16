"""Command line interface for the image planning intermediate layer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .planner import build_image_plan
from .resolver import resolve_image_plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and resolve a six-image Amazon Listing plan.")
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("image-plan")
    command.add_argument("--catalog", default="examples/demo_sku/catalog.json")
    command.add_argument("--competitor-analysis", default="examples/demo_sku/competitor-analysis.md")
    command.add_argument("--registry", default="templates/registry.json")
    command.add_argument("--output", default="output/image_plan.json")
    command.add_argument("--resolved-output", default="output/resolved_templates.json")
    args = parser.parse_args(argv)
    if args.command == "image-plan":
        catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
        registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
        analysis = Path(args.competitor_analysis).read_text(encoding="utf-8")
        plan = build_image_plan(catalog, analysis, registry)
        resolved = resolve_image_plan(plan, registry)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.resolved_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        Path(args.resolved_output).write_text(json.dumps([item.model_dump() for item in resolved], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.output} and {args.resolved_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
