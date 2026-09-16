"""Opt-in real API smoke test; disabled unless RUN_WAN_INTEGRATION=1."""
import json
import os
import unittest
from pathlib import Path

from image_generation.cli import _load_generation_batch
from image_generation.adapters.wan import WanAdapter
from image_generation.models import ModelExecutionPolicy


@unittest.skipUnless(os.getenv("RUN_WAN_INTEGRATION") == "1", "set RUN_WAN_INTEGRATION=1 to call Wan API")
class WanIntegrationTests(unittest.TestCase):
    def test_image_01_real_generation(self):
        root = Path(__file__).resolve().parents[1]
        batch = _load_generation_batch(json.loads((root / "examples/demo_sku/generated-fixtures/generation_requests.json").read_text(encoding="utf-8")))
        policy = ModelExecutionPolicy(**json.loads((root / "config/wan_listing_v1.json").read_text(encoding="utf-8")))
        result = WanAdapter(output_dir=root / "output/wan").generate(batch.requests[0], policy)
        self.assertEqual(result.status, "succeeded")


if __name__ == "__main__":
    unittest.main()
