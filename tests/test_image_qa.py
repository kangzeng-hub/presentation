import json
import tempfile
import unittest
from pathlib import Path

from image_generation.cli import _load_generation_batch
from image_generation.models import GenerationResult, OutputAsset
from image_qa.evaluator import VisionQAEvaluator
from image_qa.models import FailureType, QAStatus, parse_qa_report
from image_qa.validator import validate_report, validate_reports


ROOT = Path(__file__).resolve().parents[1]


class QATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = _load_generation_batch(json.loads((ROOT / "generation_requests.json").read_text(encoding="utf-8")))

    def result(self, request, path="/tmp/image.png", status="succeeded"):
        return GenerationResult(generation_id=request.generation_id, image_id=request.image_id, provider="aliyun_dashscope", model="wan2.7-image-pro", status=status, output_assets=[OutputAsset(path=path, sha256="x")] if status == "succeeded" else [], request_id="r", latency_ms=1, attempt=1, policy_id="wan-listing-v1")

    def test_valid_pass_result(self):
        request = self.batch.requests[0]
        obs = {"product_truth": {"status": "PASS", "score": 0.95}, "template_fidelity": {"status": "PASS", "score": 0.9}, "visual_evidence": {"status": "PASS", "score": 1.0}, "decision_coverage": {"status": "PASS", "score": 0.9, "finding": "three configurations clear"}}
        result = self.result(request)
        report = VisionQAEvaluator().qa(request, result, observations=obs)
        self.assertEqual(report.overall_status, QAStatus.PASS.value)
        validate_report(report)

    def test_product_truth_mismatch_and_extra_product(self):
        request = self.batch.requests[0]
        result = self.result(request)
        obs = {"product_truth": {"status": "FAIL", "findings": [{"criterion": "count", "observed": "four products", "expected": "three products", "severity": "critical", "failure_type": "EXTRA_PRODUCT"}]}, "template_fidelity": {"status": "PASS"}, "visual_evidence": {"status": "PASS"}, "decision_coverage": {"status": "PASS"}}
        report = VisionQAEvaluator().qa(request, result, observations=obs)
        self.assertEqual(report.overall_status, QAStatus.FAIL.value)
        self.assertIn("EXTRA_PRODUCT", report.failure_types)

    def test_missing_evidence(self):
        request = self.batch.requests[0]
        result = self.result(request)
        obs = {"product_truth": {"status": "PASS"}, "template_fidelity": {"status": "PASS"}, "visual_evidence": {"status": "FAIL", "missing": ["three actual configurations shown simultaneously and clearly distinguished"]}, "decision_coverage": {"status": "PARTIAL", "finding": "ambiguous"}}
        report = VisionQAEvaluator().qa(request, result, observations=obs)
        self.assertEqual(report.overall_status, QAStatus.FAIL.value)
        self.assertEqual(report.visual_evidence.findings[0].failure_type, FailureType.MISSING_VISUAL_EVIDENCE.value)

    def test_needs_review_without_provider(self):
        request = self.batch.requests[0]
        result = self.result(request)
        report = VisionQAEvaluator().qa(request, result)
        self.assertEqual(report.overall_status, QAStatus.NEEDS_REVIEW.value)

    def test_invalid_model_json_fallback(self):
        request = self.batch.requests[0]
        result = self.result(request)
        class Provider:
            def evaluate(self, *args, **kwargs):
                return "invalid"
        report = VisionQAEvaluator(provider=Provider()).qa(request, result)
        self.assertEqual(report.overall_status, QAStatus.NEEDS_REVIEW.value)
        self.assertIn(FailureType.QA_MODEL_OUTPUT_INVALID.value, report.failure_types)

    def test_request_report_one_to_one(self):
        reports = []
        for request in self.batch.requests:
            result = self.result(request)
            reports.append(VisionQAEvaluator().qa(request, result, observations={"product_truth": {"status": "PASS"}, "template_fidelity": {"status": "PASS"}, "visual_evidence": {"status": "PASS"}, "decision_coverage": {"status": "PASS"}}))
        validate_reports(reports, self.batch.requests)
        self.assertEqual(len(reports), 6)

    def test_report_schema_parser(self):
        request = self.batch.requests[0]
        data = {"qa_version": "1.0.0", "generation_id": request.generation_id, "image_id": request.image_id, "product_id": request.product_id, "overall_status": "PASS", "product_truth": {"status": "PASS"}, "template_fidelity": {"status": "PASS"}, "visual_evidence": {"status": "PASS"}, "decision_coverage": {"status": "PASS"}}
        self.assertEqual(parse_qa_report(data).overall_status, "PASS")


if __name__ == "__main__":
    unittest.main()
