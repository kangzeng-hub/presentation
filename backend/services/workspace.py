from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

from backend.repositories.workspace import WorkspaceRepository, utc_now
from backend.schemas.workspace import CreateProject, ProductTruth, VideoPlanInput
from backend.services.delivery import DeliveryError, ExportBuilder
from backend.workers.runner import InlineJobRunner


ROOT = Path(__file__).resolve().parents[2]
SYSTEM_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else "phase3-dev"


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

    def _fixture_dir(self, sku: str) -> Path:
        for candidate in sorted((ROOT / "examples").glob("*/product.json")):
            product = json.loads(candidate.read_text(encoding="utf-8"))
            if product.get("sku") == sku:
                return candidate.parent
        raise DeliveryError(
            "SKU_NOT_REGISTERED",
            f"No public product fixture is registered for SKU {sku}",
            [{"sku": sku}],
        )

    def _product(self, sku: str) -> tuple[dict[str, Any], Path]:
        fixture_dir = self._fixture_dir(sku)
        return json.loads((fixture_dir / "product.json").read_text(encoding="utf-8")), fixture_dir

    def _demo_truth(self, project_id: str, sku: str) -> dict[str, Any]:
        product, fixture_dir = self._product(sku)
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
            "source": [str((fixture_dir / "product.json").relative_to(ROOT))],
            "version": 1,
        }

    def ensure_demo_project(self) -> None:
        if self.repository.get_project("demo-project"):
            return
        self.create_project(CreateProject(sku="DEMO-GOLD-3PCS", project_name="Synthetic Demo Presentation"), project_id="demo-project")

    def create_project(self, payload: CreateProject, project_id: str | None = None) -> dict[str, Any]:
        project_id = project_id or f"project-{uuid.uuid4().hex[:12]}"
        # Resolve the SKU before creating the project so an invalid registration
        # cannot leave an orphan project row behind.
        _, fixture_dir = self._product(payload.sku)
        self.repository.create_project(project_id, payload.project_name, payload.sku)
        self.repository.save_artifact(project_id, "product_truth", self._demo_truth(project_id, payload.sku), {"source": str((fixture_dir / "product.json").relative_to(ROOT))}, source_ref=str(fixture_dir))
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
        project = self.repository.get_project(project_id)
        if project is None:
            raise KeyError(project_id)
        if truth.sku != project["sku"]:
            raise DeliveryError(
                "PRODUCT_TRUTH_SKU_MISMATCH",
                "Product Truth SKU must match the project SKU",
                [{"project_sku": project["sku"], "product_truth_sku": truth.sku}],
            )
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
        product, _ = self._product(self.repository.get_project(project_id)["sku"])
        feature = product.get("product_features", ["clear product configuration"])[0]
        snapshots = [{"competitor_id": f"{project_id}-c{i + 1}", "url": url, "title": f"Synthetic competitor {i + 1}", "bullet_points": [f"Comparable {feature}", "Visible assortment"], "rating": 4.2, "price": 19.99, "reviews": [], "negative_reviews": [], "neutral_reviews": [], "positive_reviews": [], "images": [], "crawl_status": "completed", "captured_at": utc_now(), "raw_source": {"synthetic": True}} for i, url in enumerate(urls)]
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
        product, _ = self._product(self.repository.get_project(project_id)["sku"])
        features = list(product.get("product_features", [])) or ["clear product identity", "reliable everyday use"]
        claims = [str(item.get("text", "")) for item in product.get("verified_claims", []) if item.get("text")]
        payload = {"project_id": project_id, "primary_purchase_drivers": features[:3], "customer_pain_points": ["selection uncertainty", "proof clarity"], "core_differentiators": features[:3], "product_claims": claims[:3], "proof_points": ["catalog-backed product claim"], "priority_order": features[:3], "listing_mapping": {"title": "identity"}, "image_mapping": {"image_01": "identity"}, "video_mapping": {"hook": features[0]}, "version": (self.repository.latest_artifact(project_id, "strategy") or {}).get("version", 0) + 1, "product_truth_version": truth["version"] if truth else 1, "competitor_insight_version": insight["version"]}
        self.repository.save_artifact(project_id, "strategy", payload, {"product_truth": truth["artifact_version_id"] if truth else None, "competitor_insight": insight["artifact_version_id"]})
        self.repository.update_project(project_id, stage="strategy", status="completed")
        return payload

    def listing(self, project_id: str) -> dict[str, Any]:
        strategy = self.repository.latest_artifact(project_id, "strategy")
        truth = self.repository.latest_artifact(project_id, "product_truth")
        insight = self.repository.latest_artifact(project_id, "competitor_insight")
        if not strategy:
            raise ValueError("strategy is required")
        product, _ = self._product(self.repository.get_project(project_id)["sku"])
        claims = [str(item.get("text", "")) for item in product.get("verified_claims", []) if item.get("text")]
        features = list(product.get("product_features", [])) or ["clear product identity"]
        payload = {"project_id": project_id, "product_truth_version": truth["version"] if truth else 1, "insight_version": insight["version"] if insight else 1, "strategy_version": strategy["version"], "title": product["product_name"], "bullet_points": features[:5], "product_description": f"Synthetic {product['category']} listing generated from versioned Product Truth.", "claims_used": claims[:5], "strategy_refs": [f"strategy:v{strategy['version']}"], "version": (self.repository.latest_artifact(project_id, "listing") or {}).get("version", 0) + 1, "generated_content": {}, "edited_content": None, "approved_content": None, "status": "pending_review", "model": "deterministic-config"}
        self.repository.save_artifact(project_id, "listing", payload, {"product_truth": truth["artifact_version_id"] if truth else None, "insight": insight["artifact_version_id"] if insight else None, "strategy": strategy["artifact_version_id"]})
        self.repository.update_project(project_id, stage="listing", status="completed")
        return payload

    def image_plan(self, project_id: str) -> dict[str, Any]:
        strategy = self.repository.latest_artifact(project_id, "strategy")
        project = self.repository.get_project(project_id)
        product, fixture_dir = self._product(project["sku"])
        configured_plan = fixture_dir / "generated-fixtures" / "image_plan.json"
        if configured_plan.is_file():
            from image_generation.service import build_context
            _, _, plan, _ = build_context()
            image_plan = json.loads(json.dumps(plan.model_dump(), ensure_ascii=False))
        else:
            image_plan = {"product_id": product["product_id"], "plan_version": "config-v1", "images": [{"image_id": f"{product['product_id']}_image_{index}", "role": role, "action": action, "prompt": f"Show the {product['product_name']} for {action}.", "generation_status": "planned", "qa_status": "pending"} for index, (role, action) in enumerate([("identity", "product identity"), ("feature", "key product feature"), ("usage", "everyday use")], start=1)]}
        payload = {"project_id": project_id, "strategy_version": strategy["version"] if strategy else 1, "version": (self.repository.latest_artifact(project_id, "image_plan") or {}).get("version", 0) + 1, "image_plan": image_plan, "source_fixture": str(fixture_dir.relative_to(ROOT))}
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

    def approve_artifact(self, project_id: str, artifact_id: str, version: int, decision: str, approved_by: str, comment: str = "") -> dict[str, Any]:
        artifact = self.repository.get_artifact_version(project_id, artifact_id, version)
        if artifact is None:
            raise DeliveryError("ARTIFACT_VERSION_NOT_FOUND", "Artifact version not found", [{"artifact_id": artifact_id, "artifact_version": version}])
        existing = self.repository.get_approval_for_version(project_id, artifact_id, version)
        if existing and (existing.get("decision") or existing.get("status")) == "approved" and decision == "approved":
            raise DeliveryError("ALREADY_APPROVED", "Artifact version is already approved", [{"artifact_id": artifact_id, "artifact_version": version}])
        return self.repository.save_approval(project_id, {"artifact_version_id": artifact["artifact_version_id"], "artifact_id": artifact.get("artifact_id") or artifact["artifact_type"], "artifact_version": version, "decision": decision, "approved_by": approved_by, "reviewer": approved_by, "comment": comment, "status": decision})

    def export(self, project_id: str) -> dict[str, Any]:
        project = self.get_project(project_id)
        export_id = f"export-{uuid.uuid4().hex[:12]}"
        export_dir = ROOT / "output" / "exports"
        zip_path = export_dir / f"{export_id}.zip"
        required_types = ["product_truth", "strategy", "listing", "image_plan", "image_generation", "qa_report"]
        if self.repository.latest_artifact(project_id, "video_plan"):
            required_types.append("video_plan")
        artifacts = []
        blocked = []
        for artifact_type in required_types:
            artifact = self.repository.latest_artifact(project_id, artifact_type)
            if artifact is None:
                blocked.append({"artifact_id": artifact_type, "artifact_version": None, "status": "missing"})
                continue
            artifacts.append(artifact)
            if not self.repository.is_artifact_version_approved(project_id, artifact.get("artifact_id") or artifact_type, artifact["version"]):
                blocked.append({"artifact_id": artifact.get("artifact_id") or artifact_type, "artifact_version": artifact["version"], "status": "unapproved"})
        if blocked:
            raise DeliveryError("EXPORT_BLOCKED_UNAPPROVED_ARTIFACT", "One or more required artifact versions are not approved", blocked)
        dependency_types = {
            "product_truth": "product_truth",
            "competitor_insight": "competitor_insight",
            "insight": "competitor_insight",
            "strategy": "strategy",
            "image_plan": "image_plan",
            "image_generation": "image_generation",
        }
        stale = []
        for artifact in artifacts:
            for ref_name, referenced_version_id in (artifact.get("input_refs_json") or {}).items():
                dependency_type = dependency_types.get(ref_name)
                if dependency_type is None or not isinstance(referenced_version_id, str):
                    continue
                latest_dependency = self.repository.latest_artifact(project_id, dependency_type)
                if latest_dependency and latest_dependency["artifact_version_id"] != referenced_version_id:
                    stale.append({
                        "artifact_id": artifact.get("artifact_id") or artifact["artifact_type"],
                        "artifact_version": artifact["version"],
                        "dependency": dependency_type,
                        "expected_version_id": latest_dependency["artifact_version_id"],
                        "referenced_version_id": referenced_version_id,
                        "status": "stale",
                    })
        if stale:
            raise DeliveryError("EXPORT_BLOCKED_STALE_ARTIFACT", "One or more artifact versions depend on stale inputs", stale)
        approvals = [self.repository.get_approval_for_version(project_id, item.get("artifact_id") or item["artifact_type"], item["version"]) for item in artifacts]
        approvals = [item for item in approvals if item]
        manifest = ExportBuilder(ROOT).build(project=project, artifacts=artifacts, approvals=approvals, export_id=export_id, exported_at=utc_now(), system_version=SYSTEM_VERSION, output_path=zip_path)
        self.repository.save_export(project_id, manifest, str(zip_path))
        return manifest
