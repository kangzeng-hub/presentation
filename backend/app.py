from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from typing import Any

from calibration.models import HumanEvaluation
from calibration.store import CalibrationStore
from calibration.regeneration import RegenerationService

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse
except ImportError:  # pragma: no cover - optional runtime dependency
    FastAPI = None


def _json_body(value: Any) -> dict:
    if hasattr(value, "model_dump"): return value.model_dump()
    if isinstance(value, dict): return value
    return dict(value)


def _discover_run_artifacts(root: Path = Path("output")) -> list[dict[str, Any]]:
    """Return generation runs that can seed a calibration session.

    A run is intentionally discovered from its image JSON records rather than
    from a provider-specific manifest, so older and newer run layouts work the
    same way. The returned paths are workspace-relative and safe to send back
    to the browser.
    """
    if not root.exists():
        return []
    plan_path = Path("examples/demo_sku/generated-fixtures/image_plan.json")
    plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.exists() else {"images": []}
    by_id = {item.get("image_id"): item for item in plan.get("images", [])}
    result: list[dict[str, Any]] = []
    for run_dir in sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.name):
        records = sorted(run_dir.glob("image_*.json"))
        if not records:
            continue
        image_ids = []
        providers = set()
        for record_path in records:
            try:
                record = json.loads(record_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            image_id = record.get("image_id")
            if image_id:
                image_ids.append(image_id)
            if record.get("provider"):
                providers.add(record["provider"])
        if not image_ids:
            continue
        roles = sorted({by_id[image_id].get("role") for image_id in image_ids if image_id in by_id and by_id[image_id].get("role")})
        result.append({
            "run_id": run_dir.name,
            "run_dir": str(run_dir),
            "sku": plan.get("product_id", ""),
            "image_count": len(image_ids),
            "image_ids": image_ids,
            "roles": roles,
            "has_qa": (run_dir / "qa").is_dir() and any((run_dir / "qa").glob("*.qa.json")),
            "providers": sorted(providers),
        })
    return result


def create_app(store: CalibrationStore | None = None, regeneration_service: RegenerationService | None = None):
    if FastAPI is None:
        raise RuntimeError("FastAPI is required to run the API. Install fastapi and uvicorn.")
    app = FastAPI(title="Image Calibration & Regeneration Workbench", version="1.0.0")
    store = store or CalibrationStore()
    regeneration_service = regeneration_service or RegenerationService(store)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "presentation-python-api"}

    @app.get("/api/artifacts/runs")
    def artifact_runs():
        return _discover_run_artifacts()

    @app.post("/api/calibration/sessions")
    def create_calibration_session(payload: dict):
        """Create a calibration session by snapshotting an existing run."""
        from calibration.models import CalibrationSession, now

        run_dir_value = payload.get("run_dir") or (Path("output") / str(payload.get("run_id", "")))
        run_dir = Path(run_dir_value)
        if not run_dir.exists() or not run_dir.is_dir():
            raise HTTPException(400, "run_dir does not exist")
        plan_path = Path(payload.get("plan_path", "examples/demo_sku/generated-fixtures/image_plan.json"))
        if not plan_path.exists():
            raise HTTPException(400, "image plan not found")
        try:
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(400, f"invalid image plan: {exc}")
        run_id = str(payload.get("run_id") or run_dir.name)
        session_id = str(payload.get("session_id") or f"cal_{run_id}")
        if any(summary.get("session_id") == session_id for summary in store.list_sessions()):
            raise HTTPException(409, f"calibration session already exists: {session_id}")
        roles = payload.get("roles")
        if roles is None:
            roles = sorted({item.get("role") for item in plan.get("images", []) if item.get("role")})
        if not isinstance(roles, list) or not roles:
            raise HTTPException(400, "at least one image role is required")
        sku = str(payload.get("sku") or plan.get("product_id", ""))
        items = build_items_from_run(session_id, run_dir, plan, [str(role) for role in roles])
        if not items:
            raise HTTPException(400, "no generated images match the selected roles")
        session = CalibrationSession(session_id=session_id, sku=sku, run_id=run_id, created_at=now(), roles=[str(role) for role in roles], items=items)
        store.save_session(session)
        return session.model_dump()

    @app.get("/api/assets/{asset_path:path}")
    def asset(asset_path: str):
        """Serve generated assets from this workspace for the review UI."""
        workspace = Path.cwd().resolve()
        candidate = (workspace / asset_path).resolve()
        try:
            candidate.relative_to(workspace)
        except ValueError:
            raise HTTPException(404, "asset not found")
        if not candidate.is_file():
            raise HTTPException(404, "asset not found")
        return FileResponse(candidate, media_type=mimetypes.guess_type(candidate.name)[0] or "application/octet-stream")

    @app.get("/api/runs")
    def runs():
        result = []
        for summary in store.list_sessions():
            session = store.load_session(summary["session_id"])
            counts = {key: sum(1 for i in session.items if i.final_verdict == key or (i.evaluation and i.evaluation.verdict == key)) for key in ("accept", "partial", "reject")}
            result.append({"run_id": session.run_id or session.session_id, "session_id": session.session_id, "sku": session.sku, "created_at": session.created_at, "image_count": len(session.items), "calibration_progress": sum(bool(i.evaluation) for i in session.items), **counts, "last_updated": session.created_at})
        return result

    @app.get("/api/runs/{run_id}")
    def run(run_id: str):
        for summary in store.list_sessions():
            if summary.get("run_id") == run_id or summary.get("session_id") == run_id:
                return store.load_session(summary["session_id"]).model_dump()
        raise HTTPException(404, "run not found")

    @app.get("/api/runs/{run_id}/calibration")
    def calibration(run_id: str):
        data = run(run_id)
        return {"session_id": data["session_id"], "items": data["items"], "progress": {"reviewed": sum(bool(i.get("evaluation")) for i in data["items"]), "total": len(data["items"])}}

    @app.get("/api/calibration/items/{item_id}")
    def item(item_id: str):
        try: return store.find_item(item_id)[1].model_dump()
        except FileNotFoundError: raise HTTPException(404, "calibration item not found")

    @app.post("/api/calibration/items/{item_id}/evaluation")
    def evaluation(item_id: str, payload: dict):
        try:
            value = HumanEvaluation(**payload)
            return store.save_evaluation(item_id, value).model_dump()
        except (ValueError, TypeError, FileNotFoundError) as exc: raise HTTPException(400, str(exc))

    @app.post("/api/calibration/items/{item_id}/regenerate")
    def regenerate(item_id: str, payload: dict):
        try:
            session, current = store.find_item(item_id)
            evaluation_value = HumanEvaluation(**payload.get("evaluation", payload))
            return regeneration_service.create_task(current, evaluation_value, role_spec_version=str(payload.get("role_spec_version", current.role_spec_version or "v1")), provider=payload.get("provider"), execute=bool(payload.get("execute", False))).model_dump()
        except (ValueError, TypeError, FileNotFoundError) as exc: raise HTTPException(400, str(exc))

    @app.get("/api/regeneration/{task_id}")
    def regeneration(task_id: str):
        try: return store.load_task(task_id).model_dump()
        except FileNotFoundError: raise HTTPException(404, "regeneration task not found")

    @app.post("/api/regeneration/{task_id}/cancel")
    def cancel(task_id: str):
        try:
            task = store.load_task(task_id); task.status = "rejected"; store.save_task(task); return task.model_dump()
        except FileNotFoundError: raise HTTPException(404, "regeneration task not found")

    @app.post("/api/regeneration/{task_id}/decision")
    def regeneration_decision(task_id: str, payload: dict):
        try:
            evaluation = HumanEvaluation(**payload["evaluation"]) if payload.get("evaluation") else None
            return regeneration_service.decide(task_id, payload["verdict"], evaluation).model_dump()
        except (KeyError, ValueError, TypeError, FileNotFoundError) as exc: raise HTTPException(400, str(exc))

    @app.get("/api/images/{image_id}")
    def image(image_id: str):
        for summary in store.list_sessions():
            session = store.load_session(summary["session_id"])
            for current in session.items:
                if current.image_id == image_id or current.active_image_id == image_id:
                    return {"image_id": image_id, "path": current.image_path, "role": current.role, "version": current.generation_version, "qa": current.qa_snapshot, "history": store.list_image_versions(current.image_id or current.item_id)}
        raise HTTPException(404, "image not found")

    @app.get("/api/images/{image_id}/qa")
    def image_qa(image_id: str):
        for summary in store.list_sessions():
            session = store.load_session(summary["session_id"])
            for current in session.items:
                if current.image_id == image_id or current.active_image_id == image_id: return current.qa_snapshot or {}
        raise HTTPException(404, "image not found")

    @app.get("/api/images/{image_id}/history")
    def image_history(image_id: str): return store.list_image_versions(image_id)

    @app.get("/api/images")
    def image_catalog():
        from image_generation.service import build_context
        _, _, plan, _ = build_context()
        return [{"image_id": x.image_id, "role": x.role, "action": x.action, "optimization_spec": x.optimization_contract} for x in plan.images]

    @app.post("/api/images/{image_id}/generate")
    def generate_image(image_id: str, payload: dict | None = None):
        from image_generation.service import generate_image
        payload = payload or {}
        try:
            return generate_image(image_id, revision_instruction=str(payload.get("revision_instruction", "")), provider=str(payload.get("provider", "auto")))
        except Exception as exc:
            raise HTTPException(400, str(exc))

    @app.post("/api/images/generate-all")
    def generate_all(payload: dict | None = None):
        from image_generation.service import generate_batch
        try: return generate_batch(provider=str((payload or {}).get("provider", "auto")))
        except Exception as exc: raise HTTPException(400, str(exc))

    @app.get("/api/problem-codes")
    def problem_codes():
        from calibration.models import PROBLEM_CODES
        return PROBLEM_CODES

    @app.get("/api/rolespecs")
    def rolespecs(): return store.list_role_specs()

    @app.get("/api/rolespecs/{role}")
    def rolespec(role: str):
        values = store.list_role_specs(role)
        if not values: raise HTTPException(404, "role spec not found")
        return values[-1]

    @app.get("/api/runs/{run_id}/roles/{role}/insight")
    def role_insight(run_id: str, role: str):
        from calibration.analytics import role_spec_recommendation
        session = store.load_session(next(s["session_id"] for s in store.list_sessions() if s.get("run_id") == run_id or s.get("session_id") == run_id))
        return role_spec_recommendation(session, role)

    @app.post("/api/rolespecs/{role}/revision")
    def revision(role: str, payload: dict):
        from calibration.models import RoleSpecRevision, now
        current = store.list_role_specs(role)
        from_version = int(current[-1].get("version", 1)) if current else 1
        revision = RoleSpecRevision(role=role, from_version=from_version, to_version=from_version + 1, change_reason=payload.get("change_reason", "Human-approved calibration insight"), changed_by=payload.get("changed_by"), created_at=now(), source_feedback_ids=list(payload.get("source_feedback_ids", [])))
        store.save_revision(revision)
        return revision.model_dump()

    return app


app = create_app() if FastAPI is not None else None
