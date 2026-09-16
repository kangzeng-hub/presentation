from __future__ import annotations

import json
import os
import uuid
import zipfile
from pathlib import Path
from typing import Any

from backend.repositories.workspace import WorkspaceRepository, utc_now
from backend.schemas.workspace import CreateProject, ProductTruth, VideoPlanInput
from backend.workers.runner import InlineJobRunner


ROOT = Path(__file__).resolve().parents[2]
DEMO_PRODUCT = ROOT / "examples/demo_sku/product.json"
DEMO_CATALOG = ROOT / "examples/demo_sku/catalog.json"
DEMO_PLAN = ROOT / "examples/demo_sku/generated-fixtures/image_plan.json"


class WorkspaceService:
    def __init__(self, repository: WorkspaceRepository):
        self.repository = repository
        self.runner = InlineJobRunner(repository)

    @staticmethod
    def handler_for_job(job: dict[str, Any]):
        """Return a safe recovery handler for persisted jobs.

        Provider-specific execution remains behind the existing service/provider
        boundary. The first backend milestone can recover the persisted state;
        provider execution is opt-in and is not silently invented here.
        """
        return lambda: job.get("result_ref")

    def _demo_truth(self, project_id: str, sku: str) -> dict[str, Any]:
        product = json.loads(DEMO_PRODUCT.read_text(encoding="utf-8"))
        return {
            "project_id": project_id,
            "sku": sku,
            "product_name": product["product_name"],
            "category": product["category"],
            "material": {"base": product["material"]["base"], "finish": product["material"]["finish"]},
            "dimensions": product["dimensions"],
            "variants": product["variants"],
            "package_contents": product["package_contents"],
            "product_features": product["product_features"],
            "verified_claims": product["verified_claims"],
            "product_images": product["product_images"],
            "source": ["examples/demo_sku/product.json"],
            "version": 1,
        }

    def ensure_demo_project(self) -> None:
        if self.repository.get_project("demo-project"):
            return
        self.create_project(CreateProject(sku="DEMO-GOLD-3PCS", project_name="Synthetic Demo Presentation"), project_id="demo-project")

    def create_project(self, payload: CreateProject, project_id: str | None = None) -> dict[str, Any]:
        project_id = project_id or f"project-{uuid.uuid4().hex[:12]}"
        self.repository.create_project(project_id, payload.project_name, payload.sku)
        self.repository.save_artifact(project_id, "product_truth", self._demo_truth(project_id, payload.sku), {"source": "examples/demo_sku/catalog.json"})
        return self.get_project(project_id)

    def _artifact(self, project_id: str, artifact_type: str) -> dict[str, Any] | None:
        value = self.repository.latest_artifact(project_id, artifact_type)
        return value["payload_json"] if value else None

    def get_project(self, project_id: str) -> dict[str, Any]:
        project = self.repository.get_project(project_id)
        if project is None:
            raise KeyError(project_id)
        return {
            "project_id": project["project_id"], "sku": project["sku"], "project_name": project["name"], "overall_status": project["status"], "current_stage": project["current_stage"], "created_at": project["created_at"], "updated_at": project["updated_at"],
            "product_truth": self._artifact(project_id, "product_truth"), "competitors": self._artifact(project_id, "competitor_snapshot") or [], "research": self._artifact(project_id, "research"), "competitor_insight": self._artifact(project_id, "competitor_insight"), "strategy": self._artifact(project_id, "strategy"), "listing": self._artifact(project_id, "listing"), "image_plan": self._artifact(project_id, "image_plan"), "image_generation": self._artifact(project_id, "image_generation"), "video": self._artifact(project_id, "video_plan"), "approvals": self.repository.list_approvals(project_id), "active_jobs": self.repository.list_jobs(project_id),
            "qa": self.qa(project_id),
        }

    def update_product_truth(self, project_id: str, truth: ProductTruth) -> dict[str, Any]:
        payload = truth.model_dump()
        payload["project_id"] = project_id
        previous = self.repository.latest_artifact(project_id, "product_truth")
        payload["version"] = int(previous["version"]) + 1 if previous else 1
        self.repository.save_artifact(project_id, "product_truth", payload, {"previous": previous["artifact_version_id"] if previous else None})
        self.repository.update_project(project_id, stage="product_truth", status="completed")
        return payload

    def research(self, project_id: str, urls: list[str], idempotency_key: str | None) -> dict[str, Any]:
        if idempotency_key:
            existing = self.repository.get_job_by_idempotency(project_id, "competitor_research", idempotency_key)
            if existing:
                return existing
        snapshots = [{"competitor_id": f"{project_id}-c{i + 1}", "url": url, "title": f"Synthetic competitor {i + 1}", "bullet_points": ["Visible assortment", "Material positioning"], "rating": 4.2, "price": 19.99, "reviews": [], "negative_reviews": [], "neutral_reviews": [], "positive_reviews": [], "images": [], "crawl_status": "completed", "captured_at": utc_now(), "raw_source": {"synthetic": True}} for i, url in enumerate(urls)]
        snapshot_ref = self.repository.save_artifact(project_id, "competitor_snapshot", snapshots, {"source": "synthetic demo input"})
        result: dict[str, Any] = {"job_id": "", "status": "completed", "competitor_ids": [item["competitor_id"] for item in snapshots]}
        research_ref = self.repository.save_artifact(project_id, "research", result, {"competitor_snapshot": snapshot_ref["artifact_version_id"]})
        job = self.runner.submit(project_id, "competitor_research", {"competitor_snapshot": snapshot_ref["version"]}, idempotency_key, lambda: research_ref["artifact_version_id"])
        result["job_id"] = job["job_id"]
        self.repository.save_artifact(project_id, "research", result, {"competitor_snapshot": snapshot_ref["artifact_version_id"], "job": job["job_id"]})
        self.repository.update_project(project_id, stage="research", status="completed")
        return {**result, **job}

    def insight(self, project_id: str) -> dict[str, Any]:
        snapshots = self._artifact(project_id, "competitor_snapshot") or []
        if not snapshots:
            raise ValueError("competitor research is required")
        latest = self.repository.latest_artifact(project_id, "competitor_snapshot")
        truth = self.repository.latest_artifact(project_id, "product_truth")
        payload = {"project_id": project_id, "purchase_drivers": ["material safety", "fit"], "customer_pain_points": ["size uncertainty"], "competitor_claims": ["hypoallergenic"], "competitor_strengths": ["clear assortment"], "competitor_weaknesses": ["weak proof"], "opportunity_gaps": ["source-linked proof"], "priority_ranking": ["material safety", "fit"], "evidence": [{"snapshot_id": item["competitor_id"], "field": "bullet_points", "excerpt": item["bullet_points"][0]} for item in snapshots], "confidence": 0.85, "version": (self.repository.latest_artifact(project_id, "competitor_insight") or {}).get("version", 0) + 1}
        self.repository.save_artifact(project_id, "competitor_insight", payload, {"product_truth": truth["artifact_version_id"] if truth else None, "competitor_snapshot": latest["artifact_version_id"] if latest else None})
        self.repository.update_project(project_id, stage="insight", status="completed")
        return payload

    def strategy(self, project_id: str) -> dict[str, Any]:
        insight = self.repository.latest_artifact(project_id, "competitor_insight")
        truth = self.repository.latest_artifact(project_id, "product_truth")
        if not insight:
            raise ValueError("competitor insight is required")
        payload = {"project_id": project_id, "primary_purchase_drivers": ["material safety", "comfort", "fit"], "customer_pain_points": ["skin sensitivity", "size uncertainty"], "core_differentiators": ["ASTM F136 titanium", "multi-wear set", "secure hinged closure"], "product_claims": ["claim_f136_titanium", "claim_gold_pvd"], "proof_points": ["catalog-backed material claim"], "priority_order": ["material safety", "fit", "comfort"], "listing_mapping": {"title": "identity"}, "image_mapping": {"image_01": "identity"}, "video_mapping": {"hook": "material safety"}, "version": (self.repository.latest_artifact(project_id, "strategy") or {}).get("version", 0) + 1, "product_truth_version": truth["version"] if truth else 1, "competitor_insight_version": insight["version"]}
        self.repository.save_artifact(project_id, "strategy", payload, {"product_truth": truth["artifact_version_id"] if truth else None, "competitor_insight": insight["artifact_version_id"]})
        self.repository.update_project(project_id, stage="strategy", status="completed")
        return payload

    def listing(self, project_id: str) -> dict[str, Any]:
        strategy = self.repository.latest_artifact(project_id, "strategy")
        truth = self.repository.latest_artifact(project_id, "product_truth")
        insight = self.repository.latest_artifact(project_id, "competitor_insight")
        if not strategy:
            raise ValueError("strategy is required")
        payload = {"project_id": project_id, "product_truth_version": truth["version"] if truth else 1, "insight_version": insight["version"] if insight else 1, "strategy_version": strategy["version"], "title": "Demo Studio ASTM F136 Titanium Hinged Ring 3PCS, 18K Gold PVD Set, 18G/20G 8mm Multi-Style Rings", "bullet_points": ["MATERIAL SAFETY: ASTM F136 implant-grade titanium with an 18K Gold PVD finish.", "3PCS MULTI-STYLE SET: Classic hoop, double-layer hoop, and CZ accent hoop.", "SECURE HINGED CLOSURE: Hinged segmented ring with a flush seam and press-to-close clasp.", "FIND YOUR FIT: 18G and 20G gauge options with an 8mm inner diameter.", "ONE SET, MORE WAYS TO WEAR: Three coordinated styles for everyday presentation."], "product_description": "A synthetic three-piece hinged ring set for demonstrating traceable listing generation.", "claims_used": ["claim_f136_titanium", "claim_gold_pvd"], "strategy_refs": [f"strategy:v{strategy['version']}"], "version": (self.repository.latest_artifact(project_id, "listing") or {}).get("version", 0) + 1, "generated_content": {}, "edited_content": None, "approved_content": None, "status": "pending_review", "model": "deterministic-demo"}
        self.repository.save_artifact(project_id, "listing", payload, {"product_truth": truth["artifact_version_id"] if truth else None, "insight": insight["artifact_version_id"] if insight else None, "strategy": strategy["artifact_version_id"]})
        self.repository.update_project(project_id, stage="listing", status="completed")
        return payload

    def image_plan(self, project_id: str) -> dict[str, Any]:
        from image_generation.service import build_context
        _, _, plan, _ = build_context()
        strategy = self.repository.latest_artifact(project_id, "strategy")
        payload = {"project_id": project_id, "strategy_version": strategy["version"] if strategy else 1, "version": (self.repository.latest_artifact(project_id, "image_plan") or {}).get("version", 0) + 1, "image_plan": json.loads(json.dumps(plan.model_dump(), ensure_ascii=False))}
        truth = self.repository.latest_artifact(project_id, "product_truth")
        self.repository.save_artifact(project_id, "image_plan", payload, {"product_truth": truth["artifact_version_id"] if truth else None, "strategy": strategy["artifact_version_id"] if strategy else None})
        self.repository.update_project(project_id, stage="images", status="completed")
        return payload

    def image_generation(self, project_id: str, idempotency_key: str | None) -> dict[str, Any]:
        if idempotency_key:
            existing = self.repository.get_job_by_idempotency(project_id, "image_generation", idempotency_key)
            if existing:
                return existing
        plan = self.repository.latest_artifact(project_id, "image_plan")
        if not plan:
            raise ValueError("image plan is required")
        payload = {"project_id": project_id, "status": "completed", "version": (self.repository.latest_artifact(project_id, "image_generation") or {}).get("version", 0) + 1, "model": "offline-demo", "provider": "none", "note": "Provider execution is opt-in; this Demo job validates the persistent workflow."}
        result = self.repository.save_artifact(project_id, "image_generation", payload, {"image_plan": plan["artifact_version_id"]})
        def execute_generation() -> str:
            if os.getenv("PRESENTATION_RUN_PROVIDER") == "1":
                from image_generation.service import generate_batch
                generate_batch(provider=os.getenv("PRESENTATION_IMAGE_PROVIDER", "auto"), output_root=ROOT / "output")
            return result["artifact_version_id"]
        job = self.runner.submit(project_id, "image_generation", {"image_plan": plan["version"]}, idempotency_key, execute_generation)
        payload["job_id"] = job["job_id"]
        self.repository.save_artifact(project_id, "image_generation", payload, {"image_plan": plan["artifact_version_id"], "job": job["job_id"]})
        reports = [
            {
                "qa_version": "pending-v1",
                "generation_id": job["job_id"],
                "image_id": item.get("image_id", ""),
                "product_id": project_id,
                "overall_status": "NEEDS_REVIEW",
                "details": {"source": "generation_job", "reason": "Provider output requires existing QA evaluator or human review."},
            }
            for item in plan["payload_json"].get("image_plan", {}).get("images", [])
            if item.get("image_id")
        ]
        self.repository.save_artifact(project_id, "qa_report", {"reports": reports}, {"image_generation": result["artifact_version_id"], "job": job["job_id"]})
        return {**payload, **job}

    def qa(self, project_id: str) -> list[dict[str, Any]]:
        value = self._artifact(project_id, "qa_report")
        if not value:
            return []
        return value.get("reports", []) if isinstance(value, dict) else []

    def retry_job(self, job_id: str) -> dict[str, Any]:
        job = self.repository.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        def handler() -> str | None:
            return job.get("result_ref")
        return self.runner.retry(job_id, handler)

    def video_plan(self, project_id: str, value: VideoPlanInput) -> dict[str, Any]:
        strategy = self.repository.latest_artifact(project_id, "strategy")
        payload = {**value.model_dump(), "project_id": project_id, "strategy_version": strategy["version"] if strategy else 1, "status": "pending_review", "version": (self.repository.latest_artifact(project_id, "video_plan") or {}).get("version", 0) + 1, "strategy_refs": [f"strategy:v{strategy['version']}" if strategy else "strategy:v1"]}
        self.repository.save_artifact(project_id, "video_plan", payload, {"strategy": strategy["artifact_version_id"] if strategy else None})
        self.repository.update_project(project_id, stage="video", status="completed")
        return payload

    def export(self, project_id: str) -> dict[str, Any]:
        project = self.get_project(project_id)
        export_id = f"export-{uuid.uuid4().hex[:12]}"
        export_dir = ROOT / "output" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        zip_path = export_dir / f"{export_id}.zip"
        files: dict[str, str] = {"project.json": json.dumps(project, ensure_ascii=False, indent=2), "product_truth.json": json.dumps(project.get("product_truth"), ensure_ascii=False, indent=2), "manifest.json": ""}
        artifact_versions = self.repository.list_artifacts(project_id)
        manifest = {"export_id": export_id, "project_id": project_id, "status": "completed", "source_versions": {"product_truth": (self.repository.latest_artifact(project_id, "product_truth") or {}).get("artifact_version_id")}, "artifact_versions": [{"artifact_type": item["artifact_type"], "artifact_version_id": item["artifact_version_id"], "project_id": item["project_id"], "version": item["version"], "input_refs_json": item["input_refs_json"], "payload_json": item["payload_json"], "created_at": item["created_at"]} for item in artifact_versions], "generated_files": list(files), "qa_reports": [], "approval_state": self.repository.list_approvals(project_id), "created_at": utc_now(), "completed_at": utc_now(), "file_ref": str(zip_path)}
        files["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        self.repository.save_export(project_id, manifest, str(zip_path))
        return manifest
