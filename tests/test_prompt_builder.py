import copy
import json
import unittest
from pathlib import Path

from image_planning.models import CompetitorGap, ImagePlan, ImagePlanItem, ResolvedTemplate
from image_planning.resolver import resolve_image_plan
from image_generation.models import GenerationRequestBatch, GenerationValidationError
from image_generation.prompt_builder import build_generation_requests
from image_generation.validator import validate_generation_request, validate_generation_requests


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class PromptBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load("data/first_party_catalog.json")
        cls.registry = load("templates/registry.json")
        plan_data = load("image_plan.json")
        cls.plan = ImagePlan(
            plan_version=plan_data["plan_version"], product_id=plan_data["product_id"], strategy_summary=plan_data["strategy_summary"],
            images=[ImagePlanItem(**{**item, "competitor_gap": [CompetitorGap(**gap) for gap in item["competitor_gap"]]}) for item in plan_data["images"]],
        )
        cls.resolved = resolve_image_plan(cls.plan, cls.registry)
        cls.batch = build_generation_requests(cls.plan, cls.resolved, cls.catalog, cls.registry)

    def test_builds_six_generation_requests(self):
        self.assertIsInstance(self.batch, GenerationRequestBatch)
        self.assertEqual(len(self.batch.requests), 6)

    def test_claim_ids_are_catalog_backed(self):
        claim_ids = {claim["claim_id"] for claim in self.catalog["claims"]}
        self.assertTrue(all(set(request.required_claims) <= claim_ids for request in self.batch.requests))

    def test_invalid_claim_id_fails(self):
        request = copy.deepcopy(self.batch.requests[0])
        request.required_claims.append("claim_invalid")
        with self.assertRaises(GenerationValidationError):
            validate_generation_request(request, self.plan.images[0], self.resolved[0], self.catalog, self.registry)

    def test_invalid_product_fact_fails(self):
        request = copy.deepcopy(self.batch.requests[0])
        request.required_facts.append("invented finish")
        with self.assertRaises(GenerationValidationError):
            validate_generation_request(request, self.plan.images[0], self.resolved[0], self.catalog, self.registry)

    def test_invalid_template_id_fails(self):
        request = copy.deepcopy(self.batch.requests[0])
        request.template_id = "NOT_REGISTERED"
        with self.assertRaises(GenerationValidationError):
            validate_generation_request(request, self.plan.images[0], self.resolved[0], self.catalog, self.registry)

    def test_missing_asset_fails(self):
        request = copy.deepcopy(self.batch.requests[0])
        request.reference_assets[0].asset_id = "missing_asset"
        with self.assertRaises(GenerationValidationError):
            validate_generation_request(request, self.plan.images[0], self.resolved[0], self.catalog, self.registry)

    def test_forbidden_claim_fails(self):
        request = copy.deepcopy(self.batch.requests[0])
        request.prompt += " 过敏100%零风险"
        with self.assertRaises(GenerationValidationError):
            validate_generation_request(request, self.plan.images[0], self.resolved[0], self.catalog, self.registry)

    def test_asset_limitations_are_preserved(self):
        request = self.batch.requests[2]
        self.assertIn("does not prove worn scale", request.asset_limitations)
        self.assertIn("does not prove worn scale", request.negative_constraints)
        self.assertIn("does not prove worn scale", request.prompt)

    def test_visual_evidence_is_compiled(self):
        for request, item in zip(self.batch.requests, self.plan.images):
            for evidence in item.required_visual_evidence:
                self.assertIn(evidence, request.prompt)
                self.assertIn(evidence, request.required_visual_evidence)

    def test_plan_and_requests_are_one_to_one(self):
        self.assertEqual([item.image_id for item in self.plan.images], [item.image_id for item in self.batch.requests])
        self.assertEqual([item.template_id for item in self.plan.images], [item.template_id for item in self.batch.requests])
        validate_generation_requests(self.batch, self.plan, self.resolved, self.catalog, self.registry)

    def test_same_input_is_stable(self):
        second = build_generation_requests(self.plan, self.resolved, self.catalog, self.registry)
        self.assertEqual(self.batch.model_dump(), second.model_dump())


if __name__ == "__main__":
    unittest.main()
