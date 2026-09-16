"""CLI for evaluating generated images against GenerationRequests."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from image_generation.cli import _load_generation_batch
from image_generation.models import GenerationResult, OutputAsset

from .evaluator import VisionQAEvaluator
from .models import QAFinding, QACriterion, QAReport, QAStatus
from .qwen_vl import QwenVisionEvaluator
from .validator import validate_reports


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate generated images against GenerationRequests.")
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("evaluate")
    command.add_argument("--requests", default="examples/demo_sku/generated-fixtures/generation_requests.json")
    command.add_argument("--results", default="output/wan")
    command.add_argument("--output", default="output/qa")
    command.add_argument("--image-id")
    command.add_argument("--dry-run", action="store_true")
    command.add_argument("--qwen", action="store_true")
    args = parser.parse_args(argv)
    return _evaluate(args)


def _evaluate(args):
    batch = _load_generation_batch(json.loads(Path(args.requests).read_text(encoding="utf-8")))
    requests = [item for item in batch.requests if not args.image_id or item.image_id == args.image_id]
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        for request in requests:
            print(json.dumps({"image_id": request.image_id, "generation_id": request.generation_id, "criteria": {"required_facts": request.required_facts, "required_visual_evidence": request.required_visual_evidence, "negative_constraints": request.negative_constraints, "decision_question": request.generation_goal}}, ensure_ascii=False, indent=2))
        return 0
    provider = QwenVisionEvaluator(raw_dir=out / "raw") if args.qwen else None
    evaluator = VisionQAEvaluator(provider=provider, qa_model=provider.model if provider else "contract-heuristic-v1")
    reports = []
    for request in requests:
        result = _load_result(Path(args.results), request.image_id)
        report = evaluator.qa(request, result)
        (out / f"{request.image_id}.qa.json").write_text(json.dumps(report.model_dump(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        reports.append(report)
        print(json.dumps(report.model_dump(), ensure_ascii=False))
    validate_reports(reports, requests)
    counts = Counter(report.overall_status for report in reports)
    failures = Counter(item for report in reports for item in report.failure_types)
    summary = {"total": len(reports), "pass": counts[QAStatus.PASS.value], "fail": counts[QAStatus.FAIL.value], "needs_review": counts[QAStatus.NEEDS_REVIEW.value], "failure_counts": dict(failures)}
    (out / "qa_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def _load_result(results_dir, image_id):
    path = results_dir / f"{image_id}.json"
    if not path.exists():
        return GenerationResult(generation_id=f"gen_{image_id}", image_id=image_id, provider="unknown", model="unknown", status="failed", output_assets=[], request_id=None, latency_ms=0, attempt=0, policy_id="unknown")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["output_assets"] = [OutputAsset(**item) for item in data.get("output_assets", [])]
    return GenerationResult(**data)


if __name__ == "__main__":
    raise SystemExit(main())
