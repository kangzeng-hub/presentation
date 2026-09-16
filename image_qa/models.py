"""Stable, evidence-first schemas for generated-image QA."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class QAStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    PARTIAL = "PARTIAL"


class FailureType(str, Enum):
    PRODUCT_DRIFT = "PRODUCT_DRIFT"
    COUNT_MISMATCH = "COUNT_MISMATCH"
    EXTRA_PRODUCT = "EXTRA_PRODUCT"
    MISSING_PRODUCT = "MISSING_PRODUCT"
    STRUCTURE_DRIFT = "STRUCTURE_DRIFT"
    COLOR_DRIFT = "COLOR_DRIFT"
    VARIANT_CONFUSION = "VARIANT_CONFUSION"
    TEMPLATE_FAILURE = "TEMPLATE_FAILURE"
    MISSING_VISUAL_EVIDENCE = "MISSING_VISUAL_EVIDENCE"
    DECISION_NOT_COVERED = "DECISION_NOT_COVERED"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    TEXT_ERROR = "TEXT_ERROR"
    FAKE_CERTIFICATE_RISK = "FAKE_CERTIFICATE_RISK"
    UNVERIFIED_SCALE = "UNVERIFIED_SCALE"
    COMPOSITION_FAILURE = "COMPOSITION_FAILURE"
    QA_MODEL_OUTPUT_INVALID = "QA_MODEL_OUTPUT_INVALID"


@dataclass
class QAFinding:
    criterion: str
    observed: str
    expected: str
    severity: str = "medium"
    evidence: str = ""
    failure_type: str | None = None

    def model_dump(self):
        return asdict(self)


@dataclass
class QACriterion:
    status: str = QAStatus.NEEDS_REVIEW.value
    score: float | None = None
    findings: list[QAFinding] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    finding: str | None = None

    def model_dump(self):
        value = asdict(self)
        value["findings"] = [item.model_dump() for item in self.findings]
        return value


@dataclass
class QAReport:
    qa_version: str
    generation_id: str
    image_id: str
    product_id: str
    overall_status: str
    product_truth: QACriterion
    template_fidelity: QACriterion
    visual_evidence: QACriterion
    decision_coverage: QACriterion
    violations: list[QAFinding] = field(default_factory=list)
    failure_types: list[str] = field(default_factory=list)
    review_notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def model_dump(self):
        value = asdict(self)
        for key in ("product_truth", "template_fidelity", "visual_evidence", "decision_coverage"):
            value[key] = getattr(self, key).model_dump()
        value["violations"] = [item.model_dump() for item in self.violations]
        return value


def parse_qa_report(data: dict[str, Any]) -> QAReport:
    """Strictly parse a provider result; missing/invalid fields are errors."""
    required = {"qa_version", "generation_id", "image_id", "product_id", "overall_status", "product_truth", "template_fidelity", "visual_evidence", "decision_coverage"}
    missing = required - set(data)
    if missing:
        raise ValueError(f"QA report missing fields: {sorted(missing)}")
    if data["overall_status"] not in {QAStatus.PASS.value, QAStatus.FAIL.value, QAStatus.NEEDS_REVIEW.value}:
        raise ValueError("invalid overall_status")
    def criterion(value):
        if not isinstance(value, dict) or value.get("status") not in {item.value for item in QAStatus}:
            raise ValueError("invalid criterion status")
        findings = [QAFinding(**item) for item in value.get("findings", [])]
        return QACriterion(status=value["status"], score=value.get("score"), findings=findings, missing=value.get("missing", []), finding=value.get("finding"))
    return QAReport(qa_version=data["qa_version"], generation_id=data["generation_id"], image_id=data["image_id"], product_id=data["product_id"], overall_status=data["overall_status"], product_truth=criterion(data["product_truth"]), template_fidelity=criterion(data["template_fidelity"]), visual_evidence=criterion(data["visual_evidence"]), decision_coverage=criterion(data["decision_coverage"]), violations=[QAFinding(**item) for item in data.get("violations", [])], failure_types=list(data.get("failure_types", [])), review_notes=list(data.get("review_notes", [])), metadata=dict(data.get("metadata", {})))
