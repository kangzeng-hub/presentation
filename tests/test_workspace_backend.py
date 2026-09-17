from __future__ import annotations

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    from fastapi.testclient import TestClient
    from backend.app import create_app
    from backend.repositories.workspace import WorkspaceRepository
    from backend.services.workspace import WorkspaceService
    from backend.workers.runner import InlineJobRunner
    FASTAPI_AVAILABLE = True
except ImportError:  # The stdlib-only test runner remains usable without runtime extras.
    TestClient = None
    FASTAPI_AVAILABLE = False


@unittest.skipUnless(FASTAPI_AVAILABLE, "install requirements-dev.txt for FastAPI API tests")
class WorkspaceBackendTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        repository = WorkspaceRepository(Path(self.temp_dir.name) / "workspace.sqlite3")
        self.service = WorkspaceService(repository)
        self.client = TestClient(create_app(workspace_service=self.service))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_demo_project_is_persistent_across_service_restart(self):
        project = self.client.get("/projects/demo-project")
        self.assertEqual(project.status_code, 200)
        self.assertEqual(project.json()["product_truth"]["version"], 1)
        self.service.repository.save_artifact("demo-project", "test_artifact", {"value": "persisted"}, {"product_truth": "pt-v1"})
        replacement = WorkspaceService(WorkspaceRepository(self.service.repository.db_path))
        self.assertEqual(replacement._artifact("demo-project", "test_artifact")["value"], "persisted")

    def test_workspace_flow_and_artifact_input_refs(self):
        self.assertEqual(self.client.post("/projects/demo-project/competitor-research", json={"urls": ["https://example.com/a"]}, headers={"Idempotency-Key": "research-1"}).status_code, 202)
        self.assertEqual(self.client.post("/projects/demo-project/competitor-insight").status_code, 202)
        self.assertEqual(self.client.post("/projects/demo-project/strategy").status_code, 202)
        self.assertEqual(self.client.post("/projects/demo-project/listing").status_code, 202)
        self.assertEqual(self.client.post("/projects/demo-project/images/plan").status_code, 202)
        self.assertEqual(self.client.post("/projects/demo-project/images/generate").status_code, 202)
        self.assertGreater(len(self.client.get("/projects/demo-project/qa").json()), 0)
        image_plan = self.service.repository.latest_artifact("demo-project", "image_plan")
        self.assertIn("product_truth", image_plan["input_refs_json"])
        for artifact in self.service.repository.list_artifacts("demo-project"):
            if artifact["artifact_type"] in {"product_truth", "strategy", "listing", "image_plan", "image_generation", "qa_report"}:
                approved = self.client.post(f"/projects/demo-project/artifacts/{artifact['artifact_id']}/versions/{artifact['version']}/approval", json={"decision": "approved", "approved_by": "phase2-test"})
                self.assertEqual(approved.status_code, 201)
        export = self.client.post("/projects/demo-project/export")
        self.assertEqual(export.status_code, 200)
        self.assertTrue(Path(export.json()["file_ref"]).is_file())

    def test_idempotency_returns_same_job(self):
        self.client.post("/projects/demo-project/competitor-research", json={"urls": ["https://example.com/a"]}, headers={"Idempotency-Key": "same"})
        first = self.client.post("/projects/demo-project/images/plan")
        self.assertEqual(first.status_code, 202)
        one = self.client.post("/projects/demo-project/images/generate", headers={"Idempotency-Key": "same-image"}).json()
        two = self.client.post("/projects/demo-project/images/generate", headers={"Idempotency-Key": "same-image"}).json()
        self.assertEqual(one["job_id"], two["job_id"])

    def test_error_response_is_structured(self):
        response = self.client.get("/projects/does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(set(response.json()["error"]), {"code", "message", "details"})
        self.assertEqual(response.json()["error"]["code"], "RESOURCE_NOT_FOUND")

    def test_unknown_sku_is_rejected_without_orphan_project(self):
        before = {item["project_id"] for item in self.service.repository.list_projects()}
        response = self.client.post("/projects", json={"sku": "UNKNOWN-SKU", "project_name": "invalid"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "SKU_NOT_REGISTERED")
        after = {item["project_id"] for item in self.service.repository.list_projects()}
        self.assertEqual(before, after)

    def test_product_truth_sku_must_match_project(self):
        truth = self.client.get("/projects/demo-project/product-truth").json()
        truth["sku"] = "DEMO-DESK-ORGANIZER"
        response = self.client.put("/projects/demo-project/product-truth", json=truth)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "PRODUCT_TRUTH_SKU_MISMATCH")

    def test_missing_project_collections_return_structured_404(self):
        for path in ("/projects/missing/approvals", "/projects/missing/exports"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["error"]["code"], "RESOURCE_NOT_FOUND")

    def test_concurrent_artifact_versions_are_unique_and_contiguous(self):
        def save(index: int) -> int:
            return self.service.repository.save_artifact("demo-project", "concurrent", {"index": index})["version"]

        with ThreadPoolExecutor(max_workers=8) as executor:
            versions = sorted(executor.map(save, range(12)))
        self.assertEqual(versions, list(range(1, 13)))

    def test_job_retry_runs_registered_handler_once_more(self):
        calls = []
        runner = InlineJobRunner(self.service.repository)
        first = runner.submit("demo-project", "test_retry", {"version": 1}, "retry-key", lambda: (_ for _ in ()).throw(RuntimeError("temporary")))
        self.assertEqual(first["status"], "failed")
        retried = runner.retry("%s" % first["job_id"], lambda: calls.append("called"))
        self.assertEqual(retried["status"], "completed")
        self.assertEqual(retried["attempt"], 2)
        self.assertEqual(calls, ["called"])


if __name__ == "__main__":
    unittest.main()
