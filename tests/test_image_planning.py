import copy
import json
import unittest
from pathlib import Path

from image_planning.models import ValidationError
from image_planning.planner import build_image_plan, validate_image_plan
from image_planning.resolver import resolve_image_plan


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class ImagePlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load("data/first_party_catalog.json")
        cls.registry = load("templates/registry.json")
        cls.analysis = (ROOT / "docs/competitor-visual-analysis.md").read_text(encoding="utf-8")
        cls.plan = build_image_plan(cls.catalog, cls.analysis, cls.registry)

    def test_default_plan_has_six_decision_images(self):
        self.assertEqual(len(self.plan.images), 6)
        self.assertEqual([item.image_id for item in self.plan.images], [f"image_{i:02d}" for i in range(1, 7)])

    def test_plan_covers_required_mvp_questions(self):
        roles = {item.role for item in self.plan.images}
        self.assertEqual(roles, {"product_main_image", "on_body_wearing_scene", "size_and_piercing_guide", "material_and_craft", "multi_scene_wearing", "hinge_operation_demo"})
        self.assertNotIn("lifestyle_context", roles)

    def test_claims_and_facts_are_catalog_backed(self):
        validate_image_plan(self.plan, self.catalog, self.registry)
        self.assertIn("claim_f136_titanium", self.plan.images[3].required_claims)
        self.assertIn("18G", self.plan.images[2].required_product_facts)

    def test_resolver_returns_registry_backed_templates(self):
        resolved = resolve_image_plan(self.plan, self.registry)
        self.assertEqual(len(resolved), 6)
        self.assertEqual(resolved[0].template_id, "PRODUCT_IDENTITY_MAIN")
        self.assertTrue(resolved[0].required_elements)

    def test_invalid_claim_id(self):
        plan = copy.deepcopy(self.plan)
        plan.images[0].required_claims = ["claim_does_not_exist"]
        with self.assertRaises(ValidationError):
            validate_image_plan(plan, self.catalog, self.registry)

    def test_invalid_template_id(self):
        plan = copy.deepcopy(self.plan)
        plan.images[0].template_id = "NOT_A_TEMPLATE"
        with self.assertRaises(ValidationError):
            validate_image_plan(plan, self.catalog, self.registry)

    def test_unknown_product_fact(self):
        plan = copy.deepcopy(self.plan)
        plan.images[0].required_product_facts.append("invented size")
        with self.assertRaises(ValidationError):
            validate_image_plan(plan, self.catalog, self.registry)

    def test_duplicate_image_id(self):
        plan = copy.deepcopy(self.plan)
        plan.images[1].image_id = plan.images[0].image_id
        with self.assertRaises(ValidationError):
            validate_image_plan(plan, self.catalog, self.registry)

    def test_invalid_priority(self):
        plan = copy.deepcopy(self.plan)
        plan.images[0].priority = "P3"
        with self.assertRaises(ValidationError):
            validate_image_plan(plan, self.catalog, self.registry)

    def test_duplicate_role_and_question(self):
        plan = copy.deepcopy(self.plan)
        plan.images[1].decision_question = plan.images[0].decision_question
        plan.images[1].role = plan.images[0].role
        with self.assertRaises(ValidationError):
            validate_image_plan(plan, self.catalog, self.registry)


if __name__ == "__main__":
    unittest.main()
