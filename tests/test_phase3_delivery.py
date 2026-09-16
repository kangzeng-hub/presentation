from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

try:
    from fastapi.testclient import TestClient
    from backend.app import create_app
    from backend.repositories.workspace import WorkspaceRepository
    from backend.services.workspace import WorkspaceService
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@unittest.skipUnless(FASTAPI_AVAILABLE, "install requirements-dev.txt for Phase 3 API tests")
class Phase3DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repository = WorkspaceRepository(Path(self.temp_dir.name) / "workspace.sqlite3")
        self.service = WorkspaceService(self.repository)
        self.client = TestClient(create_app(workspace_service=self.service))

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_flow(self, project_name: str, sku: str) -> str:
        created = self.client.post("/projects", json={"sku": sku, "project_name": project_name})
        self.assertEqual(created.status_code, 201)
        project_id = created.json()["project_id"]
        self.assertEqual(self.client.post(f"/projects/{project_id}/competitor-research", json={"urls": [f"https://example.com/{project_id}"]}).status_code, 202)
        self.assertEqual(self.client.post(f"/projects/{project_id}/competitor-insight").status_code, 202)
        self.assertEqual(self.client.post(f"/projects/{project_id}/strategy").status_code, 202)
        self.assertEqual(self.client.post(f"/projects/{project_id}/listing").status_code, 202)
        self.assertEqual(self.client.post(f"/projects/{project_id}/images/plan").status_code, 202)
        self.assertEqual(self.client.post(f"/projects/{project_id}/images/generate").status_code, 202)
        video = {
            "video_goal": "Show the product in everyday use",
            "target_audience": "Synthetic demo shoppers",
            "duration": 15,
            "hook": "See the product clearly",
            "selling_points": ["clear product identity"],
            "scene_plan": [{"scene": 1, "action": "show product"}],
            "visual_direction": "clean product demo",
            "narration": "Show the product and its key feature.",
            "on_screen_text": ["Product overview"],
            "final_prompt": "Create a concise product demonstration.",
        }
        self.assertEqual(self.client.post(f"/projects/{project_id}/video/plan", json=video).status_code, 201)
        return project_id

    def current_required_artifacts(self, project_id: str) -> list[dict]:
        required = {"product_truth", "strategy", "listing", "image_plan", "image_generation", "qa_report", "video_plan"}
        latest = {}
        for artifact in self.repository.list_artifacts(project_id):
            if artifact["artifact_type"] in required:
                latest[artifact["artifact_type"]] = artifact
        return list(latest.values())

    def approve_current(self, project_id: str) -> None:
        for artifact in self.current_required_artifacts(project_id):
            response = self.client.post(
                f"/projects/{project_id}/artifacts/{artifact['artifact_id']}/versions/{artifact['version']}/approval",
                json={"decision": "approved", "approved_by": "qa@example.com", "comment": "Approved for delivery"},
            )
            self.assertEqual(response.status_code, 201, response.text)

    def test_exact_version_approval_and_no_inheritance(self):
        project_id = self.run_flow("project-a", "DEMO-GOLD-3PCS")
        v1 = self.repository.latest_artifact(project_id, "listing")
        approved = self.client.post(f"/projects/{project_id}/artifacts/listing/versions/1/approval", json={"decision": "approved", "approved_by": "reviewer"})
        self.assertEqual(approved.status_code, 201)
        self.assertTrue(self.repository.is_artifact_version_approved(project_id, "listing", 1))
        self.service.listing(project_id)
        v2 = self.repository.latest_artifact(project_id, "listing")
        self.assertEqual(v1["version"], 1)
        self.assertEqual(v2["version"], 2)
        self.assertFalse(self.repository.is_artifact_version_approved(project_id, "listing", 2))
        approvals = self.repository.list_approvals(project_id)
        self.assertTrue(any(item["artifact_version"] == 1 and item["decision"] == "approved" for item in approvals))
        self.assertFalse(any(item["artifact_version"] == 2 and item["decision"] == "approved" for item in approvals))

    def test_unapproved_artifact_blocks_export_with_details(self):
        project_id = self.run_flow("project-a", "DEMO-GOLD-3PCS")
        response = self.client.post(f"/projects/{project_id}/export")
        self.assertEqual(response.status_code, 409)
        body = response.json()["error"]
        self.assertEqual(body["code"], "EXPORT_BLOCKED_UNAPPROVED_ARTIFACT")
        self.assertTrue(body["details"])

    def test_export_manifest_zip_and_sha256(self):
        project_id = self.run_flow("project-a", "DEMO-GOLD-3PCS")
        self.approve_current(project_id)
        response = self.client.post(f"/projects/{project_id}/exports")
        self.assertEqual(response.status_code, 200, response.text)
        manifest = response.json()
        self.assertEqual(manifest["project"]["sku"], "DEMO-GOLD-3PCS")
        self.assertEqual(manifest["system_version"], "3.0.0")
        self.assertTrue(manifest["sources"])
        archive_path = Path(manifest["file_ref"])
        self.assertTrue(archive_path.is_file())
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            for required in {"project.json", "product_truth.json", "strategy.json", "listing.json", "video_prompt.json", "manifest.json"}:
                self.assertIn(required, names)
            self.assertTrue(any(name.startswith("images/") for name in names))
            self.assertTrue(any(name.startswith("qa/") for name in names))
            embedded = json.loads(archive.read("manifest.json"))
            self.assertEqual(embedded["export_id"], manifest["export_id"])
            for record in embedded["files"]:
                content = archive.read(record["path"])
                self.assertEqual(hashlib.sha256(content).hexdigest(), record["sha256"])
                self.assertEqual(len(content), record["size"])

    def test_second_sku_full_workflow_and_project_isolation(self):
        project_a = self.run_flow("project-a", "DEMO-GOLD-3PCS")
        project_b = self.run_flow("project-b", "DEMO-DESK-ORGANIZER")
        a = self.client.get(f"/projects/{project_a}").json()
        b = self.client.get(f"/projects/{project_b}").json()
        self.assertNotEqual(a["product_truth"]["product_name"], b["product_truth"]["product_name"])
        self.assertEqual(b["product_truth"]["category"], "desk organization")
        self.assertTrue(all(item["project_id"] == project_b for item in self.repository.list_artifacts(project_b)))
        self.assertEqual(self.client.get(f"/projects/{project_a}/approvals").json(), [])
        self.approve_current(project_b)
        export = self.client.post(f"/projects/{project_b}/exports")
        self.assertEqual(export.status_code, 200, export.text)
        with zipfile.ZipFile(export.json()["file_ref"]) as archive:
            self.assertIn("DEMO-DESK-ORGANIZER", archive.read("product_truth.json").decode())
            self.assertNotIn(project_a, archive.read("manifest.json").decode())
        source = Path("backend/services/workspace.py").read_text(encoding="utf-8")
        self.assertNotIn('if project["sku"] ==', source)


if __name__ == "__main__":
    unittest.main()
