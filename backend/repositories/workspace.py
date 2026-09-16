from __future__ import annotations

import json
import hashlib
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkspaceRepository:
    """Small SQLite repository; business decisions stay in the service layer."""

    def __init__(self, db_path: str | Path | None = None):
        configured = db_path or os.getenv("PRESENTATION_DB_PATH", "output/workspace.sqlite3")
        self.db_path = Path(configured)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _init_schema(self) -> None:
        with self._connection() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    sku TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_stage TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS artifact_versions (
                    artifact_version_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    artifact_id TEXT,
                    artifact_type TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    input_refs_json TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    checksum TEXT,
                    source_ref TEXT,
                    created_by TEXT
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_version_json TEXT NOT NULL,
                    idempotency_key TEXT,
                    attempt INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    lease_expires_at TEXT,
                    result_ref TEXT,
                    error_code TEXT,
                    error_message TEXT,
                    UNIQUE(project_id, type, idempotency_key)
                );
                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    artifact_id TEXT,
                    artifact_version INTEGER,
                    artifact_version_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reviewer TEXT NOT NULL,
                    comment TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    decision TEXT,
                    approved_by TEXT,
                    approved_at TEXT
                );
                CREATE TABLE IF NOT EXISTS exports (
                    export_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    artifact_version_id TEXT,
                    status TEXT NOT NULL,
                    file_ref TEXT,
                    manifest_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_artifact_project_type ON artifact_versions(project_id, artifact_type, version);
                CREATE INDEX IF NOT EXISTS idx_jobs_project ON jobs(project_id, created_at);
                """
            )
            self._ensure_column(db, "artifact_versions", "artifact_id", "TEXT")
            self._ensure_column(db, "artifact_versions", "checksum", "TEXT")
            self._ensure_column(db, "artifact_versions", "source_ref", "TEXT")
            self._ensure_column(db, "artifact_versions", "created_by", "TEXT")
            self._ensure_column(db, "approvals", "artifact_id", "TEXT")
            self._ensure_column(db, "approvals", "artifact_version", "INTEGER")
            self._ensure_column(db, "approvals", "decision", "TEXT")
            self._ensure_column(db, "approvals", "approved_by", "TEXT")
            self._ensure_column(db, "approvals", "approved_at", "TEXT")
            db.execute("UPDATE artifact_versions SET artifact_id = artifact_type WHERE artifact_id IS NULL")
            db.execute("""UPDATE approvals
                         SET artifact_id = COALESCE(artifact_id, (SELECT artifact_type FROM artifact_versions WHERE artifact_versions.artifact_version_id = approvals.artifact_version_id)),
                             artifact_version = COALESCE(artifact_version, (SELECT version FROM artifact_versions WHERE artifact_versions.artifact_version_id = approvals.artifact_version_id)),
                             decision = COALESCE(decision, CASE WHEN status = 'approved' THEN 'approved' WHEN status = 'rejected' THEN 'rejected' ELSE 'pending' END),
                             approved_by = COALESCE(approved_by, reviewer),
                             approved_at = COALESCE(approved_at, CASE WHEN status = 'approved' THEN updated_at ELSE NULL END)
                         WHERE artifact_id IS NULL OR artifact_version IS NULL OR decision IS NULL""")

    @staticmethod
    def _ensure_column(db: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        columns = {row[1] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _decode(row: sqlite3.Row | None, json_fields: tuple[str, ...] = ()) -> dict[str, Any] | None:
        if row is None:
            return None
        value = dict(row)
        for field in json_fields:
            if value.get(field) is not None:
                value[field] = json.loads(value[field])
        return value

    def _decode_job(self, row: sqlite3.Row | None) -> dict[str, Any] | None:
        value = self._decode(row, ("input_version_json",))
        if value is not None:
            value["input_version"] = value.pop("input_version_json")
        return value

    def create_project(self, project_id: str, name: str, sku: str, status: str = "queued", stage: str = "product_truth") -> dict[str, Any]:
        timestamp = utc_now()
        with self._connection() as db:
            db.execute("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?)", (project_id, name, sku, status, stage, timestamp, timestamp))
        return self.get_project(project_id)  # type: ignore[return-value]

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        with self._connection() as db:
            return self._decode(db.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,)).fetchone())

    def list_projects(self) -> list[dict[str, Any]]:
        with self._connection() as db:
            return [dict(row) for row in db.execute("SELECT * FROM projects ORDER BY created_at").fetchall()]

    def update_project(self, project_id: str, *, status: str | None = None, stage: str | None = None) -> None:
        current = self.get_project(project_id)
        if current is None:
            raise KeyError(project_id)
        with self._connection() as db:
            db.execute("UPDATE projects SET status = ?, current_stage = ?, updated_at = ? WHERE project_id = ?", (status or current["status"], stage or current["current_stage"], utc_now(), project_id))

    def save_artifact(self, project_id: str, artifact_type: str, payload: Any, input_refs: dict[str, Any] | None = None, *, source_ref: str | None = None, created_by: str = "system") -> dict[str, Any]:
        payload_bytes = self._json(payload).encode("utf-8")
        checksum = hashlib.sha256(payload_bytes).hexdigest()
        with self._connection() as db:
            row = db.execute("SELECT COALESCE(MAX(version), 0) AS version FROM artifact_versions WHERE project_id = ? AND artifact_type = ?", (project_id, artifact_type)).fetchone()
            version = int(row["version"]) + 1
            artifact_id = f"{artifact_type}-v{version}-{uuid.uuid4().hex[:8]}"
            db.execute("INSERT INTO artifact_versions (artifact_version_id, project_id, artifact_id, artifact_type, version, input_refs_json, payload_json, created_at, checksum, source_ref, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (artifact_id, project_id, artifact_type, artifact_type, version, self._json(input_refs or {}), self._json(payload), utc_now(), checksum, source_ref, created_by))
        return self.get_artifact(artifact_id)  # type: ignore[return-value]

    def get_artifact(self, artifact_version_id: str) -> dict[str, Any] | None:
        with self._connection() as db:
            return self._decode(db.execute("SELECT * FROM artifact_versions WHERE artifact_version_id = ?", (artifact_version_id,)).fetchone(), ("input_refs_json", "payload_json"))

    def get_artifact_version(self, project_id: str, artifact_id: str, version: int) -> dict[str, Any] | None:
        with self._connection() as db:
            row = db.execute("SELECT * FROM artifact_versions WHERE project_id = ? AND (artifact_id = ? OR artifact_type = ?) AND version = ?", (project_id, artifact_id, artifact_id, version)).fetchone()
        return self._decode(row, ("input_refs_json", "payload_json"))

    def latest_artifact(self, project_id: str, artifact_type: str) -> dict[str, Any] | None:
        with self._connection() as db:
            return self._decode(db.execute("SELECT * FROM artifact_versions WHERE project_id = ? AND artifact_type = ? ORDER BY version DESC LIMIT 1", (project_id, artifact_type)).fetchone(), ("input_refs_json", "payload_json"))

    def list_artifacts(self, project_id: str, artifact_type: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM artifact_versions WHERE project_id = ?"
        params: list[Any] = [project_id]
        if artifact_type:
            query += " AND artifact_type = ?"
            params.append(artifact_type)
        query += " ORDER BY created_at"
        with self._connection() as db:
            return [self._decode(row, ("input_refs_json", "payload_json")) for row in db.execute(query, params).fetchall()]  # type: ignore[list-item]

    def create_job(self, project_id: str, job_type: str, input_version: dict[str, Any], idempotency_key: str | None) -> tuple[dict[str, Any], bool]:
        timestamp = utc_now()
        job_id = f"job-{uuid.uuid4().hex}"
        try:
            with self._connection() as db:
                db.execute("INSERT INTO jobs VALUES (?, ?, ?, 'queued', ?, ?, 0, ?, NULL, NULL, NULL, NULL, NULL, NULL)", (job_id, project_id, job_type, self._json(input_version), idempotency_key, timestamp))
        except sqlite3.IntegrityError:
            with self._connection() as db:
                row = db.execute("SELECT * FROM jobs WHERE project_id = ? AND type = ? AND idempotency_key IS ?", (project_id, job_type, idempotency_key)).fetchone()
            return self._decode_job(row), False  # type: ignore[return-value]
        return self.get_job(job_id), True  # type: ignore[return-value]

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connection() as db:
            return self._decode_job(db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone())

    def get_job_by_idempotency(self, project_id: str, job_type: str, idempotency_key: str) -> dict[str, Any] | None:
        with self._connection() as db:
            return self._decode_job(db.execute("SELECT * FROM jobs WHERE project_id = ? AND type = ? AND idempotency_key = ?", (project_id, job_type, idempotency_key)).fetchone())

    def list_jobs(self, project_id: str, limit: int = 20) -> list[dict[str, Any]]:
        with self._connection() as db:
            return [self._decode_job(row) for row in db.execute("SELECT * FROM jobs WHERE project_id = ? ORDER BY created_at DESC LIMIT ?", (project_id, limit)).fetchall()]  # type: ignore[list-item]

    def list_recoverable_jobs(self) -> list[dict[str, Any]]:
        now = utc_now()
        with self._connection() as db:
            rows = db.execute(
                "SELECT * FROM jobs WHERE status = 'queued' OR (status = 'running' AND lease_expires_at IS NOT NULL AND lease_expires_at < ?) ORDER BY created_at",
                (now,),
            ).fetchall()
        return [self._decode_job(row) for row in rows]  # type: ignore[list-item]

    def transition_job(self, job_id: str, status: str, *, attempt: int | None = None, result_ref: str | None = None, error_code: str | None = None, error_message: str | None = None) -> dict[str, Any]:
        job = self.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        timestamp = utc_now()
        started = job["started_at"] or (timestamp if status == "running" else None)
        completed = timestamp if status in {"completed", "failed", "cancelled"} else job["completed_at"]
        lease = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat() if status == "running" else None
        with self._connection() as db:
            db.execute("UPDATE jobs SET status = ?, attempt = ?, started_at = ?, completed_at = ?, lease_expires_at = ?, result_ref = ?, error_code = ?, error_message = ? WHERE job_id = ?", (status, attempt if attempt is not None else job["attempt"], started, completed, lease, result_ref, error_code, error_message, job_id))
        return self.get_job(job_id)  # type: ignore[return-value]

    def save_approval(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        artifact = self.get_artifact(payload["artifact_version_id"])
        if artifact is None or artifact["project_id"] != project_id:
            raise KeyError("artifact_version")
        artifact_id = payload.get("artifact_id") or artifact.get("artifact_id") or artifact["artifact_type"]
        artifact_version = int(payload.get("artifact_version") or artifact["version"])
        decision = payload.get("decision") or payload.get("status") or "pending"
        if decision not in {"pending", "approved", "rejected"}:
            raise ValueError("INVALID_APPROVAL_DECISION")
        timestamp = utc_now()
        approval_id = f"approval-{uuid.uuid4().hex}"
        approved_at = timestamp if decision == "approved" else None
        approved_by = payload.get("approved_by") or payload.get("reviewer") or ""
        with self._connection() as db:
            db.execute("INSERT INTO approvals (approval_id, project_id, artifact_id, artifact_version, artifact_version_id, status, reviewer, comment, created_at, updated_at, decision, approved_by, approved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (approval_id, project_id, artifact_id, artifact_version, artifact["artifact_version_id"], decision, approved_by, payload.get("comment", ""), timestamp, timestamp, decision, approved_by, approved_at))
        return self.get_approval(approval_id)  # type: ignore[return-value]

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        with self._connection() as db:
            return self._decode(db.execute("SELECT * FROM approvals WHERE approval_id = ?", (approval_id,)).fetchone())

    def list_approvals(self, project_id: str) -> list[dict[str, Any]]:
        with self._connection() as db:
            return [dict(row) for row in db.execute("SELECT * FROM approvals WHERE project_id = ? ORDER BY created_at", (project_id,)).fetchall()]

    def get_approval_for_version(self, project_id: str, artifact_id: str, version: int) -> dict[str, Any] | None:
        with self._connection() as db:
            row = db.execute("SELECT * FROM approvals WHERE project_id = ? AND artifact_id = ? AND artifact_version = ? ORDER BY created_at DESC LIMIT 1", (project_id, artifact_id, version)).fetchone()
        return dict(row) if row else None

    def is_artifact_version_approved(self, project_id: str, artifact_id: str, version: int) -> bool:
        approval = self.get_approval_for_version(project_id, artifact_id, version)
        return bool(approval and (approval.get("decision") or approval.get("status")) == "approved")

    def save_export(self, project_id: str, manifest: dict[str, Any], file_ref: str | None) -> dict[str, Any]:
        export_id = manifest["export_id"]
        with self._connection() as db:
            db.execute("INSERT INTO exports VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (export_id, project_id, manifest.get("artifact_version_id"), manifest["status"], file_ref, self._json(manifest), manifest["created_at"], manifest.get("completed_at")))
        return self.get_export(export_id)  # type: ignore[return-value]

    def get_export(self, export_id: str) -> dict[str, Any] | None:
        with self._connection() as db:
            return self._decode(db.execute("SELECT * FROM exports WHERE export_id = ?", (export_id,)).fetchone(), ("manifest_json",))

    def list_exports(self, project_id: str) -> list[dict[str, Any]]:
        with self._connection() as db:
            return [self._decode(row, ("manifest_json",)) for row in db.execute("SELECT * FROM exports WHERE project_id = ? ORDER BY created_at", (project_id,)).fetchall()]  # type: ignore[list-item]
