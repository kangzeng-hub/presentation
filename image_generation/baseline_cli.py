"""Run the fixed GPT Image 2 baseline with experiment metadata.

This command intentionally stops before network execution when the required
API key is absent. It does not alter requests, prompts, policy, or retry rules.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .baseline import finish_experiment, start_experiment, write_baseline_summary
from .cli import _generate, _load_generation_batch
from .models import ModelExecutionPolicy


def main(argv=None):
    parser = argparse.ArgumentParser(description="Execute the fixed GPT Image 2 baseline experiment.")
    parser.add_argument("--requests", default="generation_requests.json")
    parser.add_argument("--output-dir", default="output/gpt_image_2_baseline")
    parser.add_argument("--policy", default="config/openai_gpt_image_v2.json")
    args = parser.parse_args(argv)
    return run(args)


def run(args):
    requests_path = Path(args.requests)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    batch = _load_generation_batch(json.loads(requests_path.read_text(encoding="utf-8")))
    policy = ModelExecutionPolicy(**json.loads(Path(args.policy).read_text(encoding="utf-8")))
    experiment_path = output_dir / "experiment.json"
    start_experiment(experiment_path, experiment_id="gpt-image-2-baseline", model=policy.model_id, policy_id=policy.policy_id, product_id=batch.product_id, source=str(requests_path), image_count=len(batch.requests))
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("SUB2API_API_KEY")):
        finish_experiment(experiment_path, status="blocked")
        write_baseline_summary(output_dir / "manifest.json", experiment_id="gpt-image-2-baseline", total_images=len(batch.requests), generation_succeeded=0, generation_failed=0, status="blocked")
        print("BASELINE_BLOCKED: OPENAI_API_KEY or SUB2API_API_KEY not configured")
        return 2
    # Reuse the existing Wan CLI implementation; no request/prompt mutation.
    code = _generate(argparse.Namespace(requests=str(requests_path), output_dir=str(output_dir), policy=str(args.policy), image_id=None, provider="auto", dry_run=False))
    generation_records = []
    for item in batch.requests:
        metadata = output_dir / f"{item.image_id}.json"
        if metadata.exists():
            try:
                generation_records.append(json.loads(metadata.read_text(encoding="utf-8")))
            except ValueError:
                pass
    succeeded = sum(item.get("status") == "succeeded" for item in generation_records)
    failed = sum(item.get("status") == "failed" for item in generation_records)
    write_baseline_summary(output_dir / "manifest.json", experiment_id="gpt-image-2-baseline", total_images=len(batch.requests), generation_succeeded=succeeded, generation_failed=failed, status="succeeded" if code == 0 else "failed")
    finish_experiment(experiment_path, status="succeeded" if code == 0 else "failed")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
