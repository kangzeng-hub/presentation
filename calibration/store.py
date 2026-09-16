from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from typing import Any
from .models import CalibrationItem, CalibrationSession, HumanEvaluation, RoleSpec, RoleSpecRevision, GoldenExample, RegenerationTask, ImageVersion, now

def _read(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

class CalibrationStore:
    def __init__(self, root: str | Path = "output/calibration"):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
    def _save(self, name: str, value: Any):
        path = self.root / name; path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    def save_session(self, session: CalibrationSession):
        self._save(f"session_{session.session_id}.json", session.model_dump()); return session
    def load_session(self, session_id: str) -> CalibrationSession:
        data = _read(self.root / f"session_{session_id}.json", None)
        if data is None: raise FileNotFoundError(session_id)
        items = []
        for item in data.pop("items", []):
            evaluation = HumanEvaluation(**item["evaluation"]) if item.get("evaluation") else None
            evaluations = [HumanEvaluation(**value) for value in item.get("evaluations", [])]
            items.append(CalibrationItem(**{**item, "evaluation": evaluation, "evaluations": evaluations}))
        return CalibrationSession(**data, items=items)
    def list_sessions(self):
        return [_read(path, {}) for path in sorted(self.root.glob("session_*.json"))]
    def save_role_spec(self, spec: RoleSpec):
        self._save(f"role_spec_{spec.role}_v{spec.version}.json", spec.model_dump()); return spec
    def list_role_specs(self, role: str | None = None):
        paths = sorted(self.root.glob("role_spec_*_v*.json"));
        if role: paths = [p for p in paths if p.name.startswith(f"role_spec_{role}_v")]
        return [_read(p, {}) for p in paths]
    def save_revision(self, revision: RoleSpecRevision):
        revisions = _read(self.root / "role_spec_revisions.json", []); revisions.append(revision.model_dump()); self._save("role_spec_revisions.json", revisions)
    def save_golden(self, example: GoldenExample):
        values = _read(self.root / "golden_examples.json", []); values.append(example.model_dump()); self._save("golden_examples.json", values)
    def save_task(self, task: RegenerationTask):
        self._save(f"regeneration_{task.task_id}.json", task.model_dump()); return task
    def load_task(self, task_id: str) -> RegenerationTask:
        data = _read(self.root / f"regeneration_{task_id}.json", None)
        if data is None: raise FileNotFoundError(task_id)
        return RegenerationTask(**data)
    def list_tasks(self, item_id: str | None = None):
        values = [_read(path, {}) for path in sorted(self.root.glob("regeneration_*.json"))]
        return [value for value in values if item_id is None or value.get("calibration_item_id") == item_id]
    def save_image_version(self, version: ImageVersion):
        self._save(f"image_version_{version.image_id}.json", version.model_dump()); return version
    def list_image_versions(self, logical_image_id: str):
        values = [_read(path, {}) for path in sorted(self.root.glob("image_version_*.json"))]
        return sorted((v for v in values if v.get("logical_image_id") == logical_image_id), key=lambda v: v.get("version", 0))
    def find_item(self, item_id: str) -> tuple[CalibrationSession, CalibrationItem]:
        for summary in self.list_sessions():
            session = self.load_session(summary["session_id"])
            for item in session.items:
                if item.item_id == item_id: return session, item
        raise FileNotFoundError(item_id)
    def save_evaluation(self, item_id: str, evaluation: HumanEvaluation):
        session, item = self.find_item(item_id)
        item.evaluation = evaluation
        item.evaluations.append(evaluation)
        item.status = "accepted" if evaluation.verdict == "accept" else "reviewed"
        item.final_verdict = evaluation.verdict
        self.save_session(session)
        return item
    @staticmethod
    def aggregate(session: CalibrationSession, role: str | None = None):
        items = [i for i in session.items if (role is None or i.role == role) and i.evaluation]
        verdicts = Counter(i.evaluation.verdict for i in items)
        problems = Counter(code for i in items for code in i.evaluation.primary_problem_codes)
        return {"evaluated": len(items), "accept": verdicts["accept"], "partial": verdicts["partial"], "reject": verdicts["reject"], "top_problems": problems.most_common()}

def build_items_from_run(session_id: str, run_dir: str | Path, image_plan: dict[str, Any], roles: list[str] | None = None) -> list[CalibrationItem]:
    root = Path(run_dir); qa_root = root / "qa"; selected = set(roles or [])
    by_id = {item["image_id"]: item for item in image_plan.get("images", [])}
    items = []
    for image_json in sorted(root.glob("image_*.json")):
        record = _read(image_json, {}); image_id = record.get("image_id")
        plan = by_id.get(image_id)
        if not plan or (selected and plan.get("role") not in selected): continue
        output = record.get("output_assets") or []
        image_path = output[0].get("path") if output else str(root / f"{image_id}.png")
        qa = _read(qa_root / f"{image_id}.qa.json", None)
        metadata = record.get("generation_metadata", {})
        items.append(CalibrationItem(item_id=f"{session_id}_{image_id}", session_id=session_id, image_path=image_path, role=plan["role"], image_plan_snapshot=plan, qa_snapshot=qa, image_id=image_id, active_image_id=image_id, role_spec_version=metadata.get("role_spec_version"), provider=record.get("provider")))
    return items
