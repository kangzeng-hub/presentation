from __future__ import annotations
import argparse, json
from pathlib import Path
from .models import CalibrationSession, now
from .store import CalibrationStore, build_items_from_run

def main(argv=None):
    parser = argparse.ArgumentParser(description="Image Calibration data tools")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="create a session from an existing run")
    init.add_argument("--session-id", required=True); init.add_argument("--sku", required=True); init.add_argument("--run-dir", required=True); init.add_argument("--run-id"); init.add_argument("--plan", default="examples/demo_sku/generated-fixtures/image_plan.json"); init.add_argument("--role", action="append", dest="roles")
    summary = sub.add_parser("summary", help="aggregate a saved session")
    summary.add_argument("session_id"); summary.add_argument("--role")
    args = parser.parse_args(argv); store = CalibrationStore()
    if args.command == "init":
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8")); roles = args.roles or sorted({item["role"] for item in plan.get("images", [])})
        session = CalibrationSession(args.session_id, args.sku, args.run_id or Path(args.run_dir).name, now(), roles, items=build_items_from_run(args.session_id, args.run_dir, plan, roles))
        store.save_session(session); print(json.dumps(session.model_dump(), ensure_ascii=False, indent=2)); return 0
    session = store.load_session(args.session_id); print(json.dumps(store.aggregate(session, args.role), ensure_ascii=False, indent=2)); return 0

if __name__ == "__main__":
    raise SystemExit(main())
