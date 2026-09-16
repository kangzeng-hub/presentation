from __future__ import annotations
import argparse, json
from pathlib import Path
from .models import ProductVideoInput, VideoGenerationResult, VideoReview
from .prompt_builder import build_video_prompt
from .seedance_adapter import SeedanceAdapter


def _dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--input", required=True); args = ap.parse_args()
    root = Path("output/video"); root.mkdir(parents=True, exist_ok=True)
    raw = json.loads(Path(args.input).read_text(encoding="utf-8")); _dump(root / "input.json", raw)
    inp = ProductVideoInput(**raw); prompt = build_video_prompt(inp); (root / "prompt.txt").write_text(prompt, encoding="utf-8")
    adapter = SeedanceAdapter(output_dir=root); submitted = adapter.submit(prompt, inp.reference_images); _dump(root / "request.json", submitted.get("request", {})); _dump(root / "response.json", submitted)
    task_id = submitted.get("task_id")
    if not task_id:
        _dump(root / "review.json", VideoReview(issues=["Seedance submit did not return task_id"]).model_dump()); raise SystemExit("Seedance submit failed: task_id missing")
    final = adapter.wait_for_completion(task_id); _dump(root / "response.json", final)
    downloaded = adapter.download_result(final); result = VideoGenerationResult(status="succeeded" if "path" in downloaded else "failed", task_id=task_id, video_path=downloaded.get("path"), video_url=downloaded.get("url"), error=downloaded.get("error")); _dump(root / "result.json", result.model_dump())
    _dump(root / "review.json", VideoReview().model_dump())
    if result.video_path: print(result.video_path)
    else: raise SystemExit(json.dumps(result.model_dump(), ensure_ascii=False))


if __name__ == "__main__": main()
