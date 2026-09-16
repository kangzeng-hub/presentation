"""QA schema and batch validation."""

from __future__ import annotations

from .models import QAReport, QAStatus


def validate_report(report: QAReport) -> None:
    if report.overall_status not in {QAStatus.PASS.value, QAStatus.FAIL.value, QAStatus.NEEDS_REVIEW.value}:
        raise ValueError("invalid overall status")
    for criterion in (report.product_truth, report.template_fidelity, report.visual_evidence, report.decision_coverage):
        if criterion.status not in {item.value for item in QAStatus}:
            raise ValueError("invalid criterion status")
    if report.overall_status == QAStatus.PASS.value and any(c.status != QAStatus.PASS.value for c in (report.product_truth, report.template_fidelity, report.visual_evidence)):
        raise ValueError("PASS requires core criteria to pass")


def validate_reports(reports, requests):
    expected = [request.image_id for request in requests]
    actual = [report.image_id for report in reports]
    if expected != actual:
        raise ValueError("QA reports must map one-to-one and preserve request order")
    for report in reports:
        validate_report(report)
