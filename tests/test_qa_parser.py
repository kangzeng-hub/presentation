import json
import unittest

from image_qa.parser import parse_qwen_response


VALID = {
    "product_truth": {"status": "PASS"},
    "template_fidelity": {"status": "PASS"},
    "visual_evidence": {"status": "PASS"},
    "decision_coverage": {"status": "PASS", "finding": "clear"},
    "violations": [],
}


class QwenParserTests(unittest.TestCase):
    def test_pure_json(self):
        result = parse_qwen_response(json.dumps(VALID))
        self.assertEqual(result.parse_status, "SUCCESS")

    def test_markdown_json(self):
        result = parse_qwen_response("```json\n" + json.dumps(VALID) + "\n```")
        self.assertEqual(result.parse_status, "SUCCESS")

    def test_json_with_explanation(self):
        result = parse_qwen_response("Here is the result:\n" + json.dumps(VALID) + "\nDone.")
        self.assertEqual(result.parse_status, "SUCCESS")

    def test_invalid_json(self):
        result = parse_qwen_response("not json")
        self.assertEqual(result.parse_status, "INVALID")

    def test_missing_top_level_field(self):
        value = dict(VALID)
        del value["visual_evidence"]
        result = parse_qwen_response(value)
        self.assertEqual(result.parse_status, "INVALID")

    def test_unknown_shorthand_normalizes(self):
        value = dict(VALID)
        value["product_truth"] = "UNKNOWN"
        value["visual_evidence"] = ["hinge not visible"]
        result = parse_qwen_response(value)
        self.assertEqual(result.parse_status, "SUCCESS")
        self.assertEqual(result.product_truth["status"], "UNKNOWN")
        self.assertEqual(result.visual_evidence["status"], "NEEDS_REVIEW")

    def test_real_response_shape(self):
        raw = {"choices": [{"message": {"content": json.dumps({**VALID, "product_truth": "UNKNOWN", "template_fidelity": "UNKNOWN", "visual_evidence": ["three items visible"], "decision_coverage": "PARTIAL", "violations": ["does not prove worn scale"]})}}]}
        result = parse_qwen_response(raw)
        self.assertEqual(result.parse_status, "SUCCESS")
        self.assertEqual(result.violations[0]["failure_type"], "UNVERIFIED_SCALE")


if __name__ == "__main__":
    unittest.main()
