from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


class DeliveryError(ValueError):
    def __init__(self, code: str, message: str, details: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []


class ExportBuilder:
    """Deterministic packaging boundary; it never generates business content."""

    def __init__(self, root: Path):
        self.root = root

    def build(self, *, project: dict[str, Any], artifacts: list[dict[str, Any]], approvals: list[dict[str, Any]], export_id: str, exported_at: str, system_version: str, output_path: Path) -> dict[str, Any]:
        files: dict[str, bytes] = {}
        by_type = {item["artifact_type"]: item for item in artifacts}
        files["project.json"] = json_bytes(project)
        names = {
            "product_truth": "product_truth.json",
            "strategy": "strategy.json",
            "listing": "listing.json",
            "image_plan": "images/image_plan.json",
            "image_generation": "images/image_generation.json",
            "qa_report": "qa/qa_report.json",
            "video_plan": "video_prompt.json",
        }
        for artifact_type, filename in names.items():
            artifact = by_type.get(artifact_type)
            if artifact is not None:
                files[filename] = json_bytes(artifact["payload_json"])

        product = by_type.get("product_truth", {}).get("payload_json", {})
        for index, source in enumerate(product.get("product_images", [])):
            candidate = (self.root / source).resolve()
            try:
                candidate.relative_to(self.root.resolve())
            except ValueError as exc:
                raise DeliveryError("EXPORT_BUILD_FAILED", "Product asset is outside the workspace", [{"path": source}]) from exc
            if not candidate.is_file():
                raise DeliveryError("EXPORT_BUILD_FAILED", "Product asset is missing", [{"path": source}])
            files[f"images/assets/{candidate.name}"] = candidate.read_bytes()

        file_records = [
            {"path": path, "sha256": sha256_bytes(content), "size": len(content)}
            for path, content in sorted(files.items())
        ]
        manifest = {
            "export_id": export_id,
            "project": {"project_id": project["project_id"], "sku": project["sku"], "project_name": project["project_name"]},
            "project_id": project["project_id"],
            "status": "completed",
            "artifacts": [{"artifact_id": item.get("artifact_id", item["artifact_type"]), "artifact_type": item["artifact_type"], "version": item["version"], "artifact_version_id": item["artifact_version_id"]} for item in artifacts],
            "artifact_versions": artifacts,
            "approvals": approvals,
            "approval_state": approvals,
            "sources": sorted({str(source) for item in artifacts for source in self._sources(item)}),
            "files": file_records,
            "generated_files": [record["path"] for record in file_records],
            "qa_reports": [record["path"] for record in file_records if record["path"].startswith("qa/")],
            "source_versions": {item["artifact_type"]: item["artifact_version_id"] for item in artifacts},
            "created_at": exported_at,
            "exported_at": exported_at,
            "completed_at": exported_at,
            "system_version": system_version,
            "file_ref": str(output_path),
        }
        files["manifest.json"] = json_bytes(manifest)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path, content in sorted(files.items()):
                archive.writestr(path, content)
        return manifest

    @staticmethod
    def _sources(artifact: dict[str, Any]) -> list[str]:
        refs = artifact.get("input_refs_json") or {}
        payload = artifact.get("payload_json") or {}
        values = list(refs.values()) if isinstance(refs, dict) else []
        if isinstance(payload, dict):
            values.extend(payload.get("source", []))
        return [str(value) for value in values if isinstance(value, str)]
