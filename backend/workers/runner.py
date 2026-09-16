from __future__ import annotations

from collections.abc import Callable
from typing import Any

from backend.repositories.workspace import WorkspaceRepository


class InlineJobRunner:
    """A persistent single-worker runner for the first production backend.

    Jobs are written before execution, so a restart never loses the request.
    A future process worker can replace this class without changing the API.
    """

    def __init__(self, repository: WorkspaceRepository):
        self.repository = repository
        self._handlers: dict[str, Callable[[], str | None]] = {}

    def submit(self, project_id: str, job_type: str, input_version: dict[str, Any], idempotency_key: str | None, handler: Callable[[], str | None]) -> dict[str, Any]:
        job, created = self.repository.create_job(project_id, job_type, input_version, idempotency_key)
        if not created or job["status"] in {"completed", "failed", "cancelled"}:
            return job
        self._handlers[job["job_id"]] = handler
        return self._execute(job["job_id"])

    def _execute(self, job_id: str) -> dict[str, Any]:
        job = self.repository.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        handler = self._handlers.get(job_id)
        if handler is None:
            return job
        job = self.repository.transition_job(job_id, "running", attempt=int(job["attempt"]) + 1)
        try:
            result_ref = handler()
            return self.repository.transition_job(job_id, "completed", result_ref=result_ref)
        except Exception as exc:  # persisted and surfaced by the Job API
            return self.repository.transition_job(job_id, "failed", error_code="JOB_FAILED", error_message=str(exc))

    def retry(self, job_id: str, handler: Callable[[], str | None] | None = None) -> dict[str, Any]:
        job = self.repository.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        if job["status"] != "failed":
            return job
        if handler is not None:
            self._handlers[job_id] = handler
        self.repository.transition_job(job_id, "queued", error_code=None, error_message=None)
        return self._execute(job_id)

    def recover(self, handler_factory: Callable[[dict[str, Any]], Callable[[], str | None] | None] | None = None) -> list[dict[str, Any]]:
        recovered = []
        for job in self.repository.list_recoverable_jobs():
            if job["job_id"] not in self._handlers and handler_factory is not None:
                handler = handler_factory(job)
                if handler is not None:
                    self._handlers[job["job_id"]] = handler
            if job["job_id"] in self._handlers:
                recovered.append(self._execute(job["job_id"]))
        return recovered

    def cancel(self, job_id: str) -> dict[str, Any]:
        job = self.repository.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        if job["status"] == "queued":
            return self.repository.transition_job(job_id, "cancelled")
        return job
