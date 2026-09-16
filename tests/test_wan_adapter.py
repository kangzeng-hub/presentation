import hashlib
import json
import os
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from image_generation.adapters.wan import ReferenceAssetResolver, WanAdapter, WanConfigurationError, _HttpResponse
from image_generation.cli import _load_generation_batch
from image_generation.models import ModelExecutionPolicy


ROOT = Path(__file__).resolve().parents[1]


class FakeHTTP:
    def __init__(self, post_responses=None, status_responses=None, image_bytes=None):
        self.post_responses = list(post_responses or [])
        self.status_responses = list(status_responses or [])
        self.image_bytes = image_bytes or b"\x89PNG\r\n\x1a\n" + b"\0" * 8 + (2048).to_bytes(4, "big") + (2048).to_bytes(4, "big")
        self.post_calls = 0
        self.status_calls = 0

    def post_json(self, payload, timeout):
        self.post_calls += 1
        value = self.post_responses.pop(0)
        return value

    def get_json(self, url, timeout):
        self.status_calls += 1
        return self.status_responses.pop(0)

    def get_bytes(self, url, timeout):
        return _HttpResponse(200, self.image_bytes)


class WanAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = _load_generation_batch(json.loads((ROOT / "examples/demo_sku/generated-fixtures/generation_requests.json").read_text(encoding="utf-8")))
        cls.policy = ModelExecutionPolicy(policy_id="wan-listing-v1", model_id="wan2.7-image-pro")

    def test_payload_mapping_and_no_negative_prompt(self):
        adapter = WanAdapter(api_key="x", asset_resolver=ReferenceAssetResolver(ROOT))
        payload, _ = adapter.build_payload(self.batch.requests[0], self.policy)
        self.assertEqual(payload["model"], "wan2.7-image-pro")
        self.assertEqual(payload["parameters"], {"size": "2K", "n": 1, "watermark": False, "enable_sequential": False})
        self.assertNotIn("negative_prompt", payload)
        self.assertEqual(payload["input"]["messages"][0]["content"][0].keys(), {"image"})
        self.assertIn("[DO NOT]", payload["input"]["messages"][0]["content"][1]["text"])

    def test_reference_local_file_becomes_data_uri(self):
        asset = self.batch.requests[0].reference_assets[0]
        value, digest = ReferenceAssetResolver(ROOT).resolve(asset)
        self.assertTrue(value.startswith("data:image/svg+xml;base64,"))
        self.assertEqual(digest, hashlib.sha256((ROOT / asset.path).read_bytes()).hexdigest())

    def test_reference_order(self):
        request = self.batch.requests[0]
        request.reference_assets = [request.reference_assets[0], request.reference_assets[0]]
        payload, _ = WanAdapter(api_key="x", asset_resolver=ReferenceAssetResolver(ROOT)).build_payload(request, self.policy)
        content = payload["input"]["messages"][0]["content"]
        self.assertEqual(len(content), 3)
        self.assertEqual(content[0], content[1])

    def test_invalid_api_key_configuration(self):
        adapter = WanAdapter(api_key=None, output_dir=tempfile.mkdtemp())
        with unittest.mock.patch.dict(os.environ, {"DASHSCOPE_API_KEY": ""}, clear=False):
            with self.assertRaises(WanConfigurationError):
                adapter.generate(self.batch.requests[0], self.policy)

    def test_success_result_and_metadata(self):
        with tempfile.TemporaryDirectory() as out:
            fake = FakeHTTP([{"request_id": "req-1", "output": {"results": [{"url": "https://img"}]}}])
            result = WanAdapter(api_key="x", http_client=fake, asset_resolver=ReferenceAssetResolver(ROOT), output_dir=out).generate(self.batch.requests[0], self.policy)
            self.assertEqual(result.status, "succeeded")
            self.assertEqual(result.request_id, "req-1")
            self.assertEqual(result.output_assets[0].width, 2048)
            self.assertTrue((Path(out) / ".generation_index.json").exists())

    def test_idempotency_skips_second_call(self):
        with tempfile.TemporaryDirectory() as out:
            fake = FakeHTTP([{"request_id": "req-1", "output": {"results": [{"url": "https://img"}]}}])
            adapter = WanAdapter(api_key="x", http_client=fake, asset_resolver=ReferenceAssetResolver(ROOT), output_dir=out)
            first = adapter.generate(self.batch.requests[0], self.policy)
            second = adapter.generate(self.batch.requests[0], self.policy)
            self.assertEqual(first.model_dump(), second.model_dump())
            self.assertEqual(fake.post_calls, 1)

    def test_retry_429_then_success(self):
        with tempfile.TemporaryDirectory() as out:
            fake = FakeHTTP([_HttpResponse(429, b'{"message":"busy"}'), {"output": {"results": [{"url": "https://img"}]}}])
            policy = ModelExecutionPolicy(policy_id="p", model_id="wan2.7-image-pro", retry={"max_attempts": 2})
            with unittest.mock.patch("image_generation.adapters.wan.time.sleep"):
                result = WanAdapter(api_key="x", http_client=fake, asset_resolver=ReferenceAssetResolver(ROOT), output_dir=out).generate(self.batch.requests[0], policy)
            self.assertEqual(result.status, "succeeded")
            self.assertEqual(fake.post_calls, 2)

    def test_invalid_parameter_not_retried(self):
        with tempfile.TemporaryDirectory() as out:
            fake = FakeHTTP([_HttpResponse(400, b'{"code":"InvalidParameter"}')])
            policy = ModelExecutionPolicy(policy_id="p", model_id="wan2.7-image-pro", retry={"max_attempts": 3})
            result = WanAdapter(api_key="x", http_client=fake, asset_resolver=ReferenceAssetResolver(ROOT), output_dir=out).generate(self.batch.requests[0], policy)
            self.assertEqual(result.status, "failed")
            self.assertEqual(fake.post_calls, 1)

    def test_async_polling(self):
        with tempfile.TemporaryDirectory() as out:
            fake = FakeHTTP([{"request_id": "r", "output": {"task_id": "t"}}], [{"output": {"task_status": "RUNNING"}}, {"output": {"task_status": "SUCCEEDED", "results": [{"url": "https://img"}]}}])
            policy = ModelExecutionPolicy(policy_id="p", model_id="wan2.7-image-pro", poll_interval_seconds=0)
            result = WanAdapter(api_key="x", http_client=fake, asset_resolver=ReferenceAssetResolver(ROOT), output_dir=out).generate(self.batch.requests[0], policy)
            self.assertEqual(result.status, "succeeded")
            self.assertEqual(fake.status_calls, 2)

    def test_timeout_is_reported(self):
        with tempfile.TemporaryDirectory() as out:
            fake = FakeHTTP([{"output": {"task_id": "t"}}], [{"output": {"task_status": "RUNNING"}}] * 2)
            policy = ModelExecutionPolicy(policy_id="p", model_id="wan2.7-image-pro", timeout_seconds=0.001, poll_interval_seconds=0)
            result = WanAdapter(api_key="x", http_client=fake, asset_resolver=ReferenceAssetResolver(ROOT), output_dir=out).generate(self.batch.requests[0], policy)
            self.assertEqual(result.status, "failed")

    def test_six_requests_one_to_one(self):
        self.assertEqual([r.image_id for r in self.batch.requests], [f"image_{i:02d}" for i in range(1, 7)])

    def test_policy_isolated_from_request(self):
        self.assertFalse(hasattr(self.batch.requests[0], "size"))
        self.assertEqual(self.policy.model_id, "wan2.7-image-pro")

    def test_dry_run_does_not_require_api_key(self):
        payload, _ = WanAdapter(asset_resolver=ReferenceAssetResolver(ROOT)).build_payload(self.batch.requests[0], self.policy)
        self.assertEqual(payload["model"], "wan2.7-image-pro")


if __name__ == "__main__":
    unittest.main()
