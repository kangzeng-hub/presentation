import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "templates" / "registry.json"
CATALOG_PATH = ROOT / "examples" / "demo_sku" / "catalog.json"


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def assert_required(testcase, obj, fields, label):
    for field in fields:
        testcase.assertIn(field, obj, f"{label} is missing required field: {field}")


def validate_instance(testcase, instance, schema, label):
    schema_type = schema.get("type")
    if schema_type == "object":
        testcase.assertIsInstance(instance, dict, label)
        required = schema.get("required", [])
        for field in required:
            testcase.assertIn(field, instance, f"{label} is missing required field: {field}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            testcase.assertEqual(
                set(instance) - set(properties),
                set(),
                f"{label} has an undeclared field",
            )
        for field, value in instance.items():
            if field in properties:
                validate_instance(testcase, value, properties[field], f"{label}.{field}")
    elif schema_type == "array":
        testcase.assertIsInstance(instance, list, label)
        if "minItems" in schema:
            testcase.assertGreaterEqual(len(instance), schema["minItems"], label)
        if "items" in schema:
            for index, value in enumerate(instance):
                validate_instance(testcase, value, schema["items"], f"{label}[{index}]")
    elif schema_type == "string":
        testcase.assertIsInstance(instance, str, label)
        if "minLength" in schema:
            testcase.assertGreaterEqual(len(instance), schema["minLength"], label)
        if "pattern" in schema:
            import re
            testcase.assertRegex(instance, re.compile(schema["pattern"]), label)
    elif schema_type == "boolean":
        testcase.assertIsInstance(instance, bool, label)
    else:
        testcase.fail(f"Unsupported schema type in test validator: {schema_type}")
    if "enum" in schema:
        testcase.assertIn(instance, schema["enum"], label)


class VisualTemplateSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_json(REGISTRY_PATH)
        cls.catalog = load_json(CATALOG_PATH)
        cls.role_schema = load_json(ROOT / "schemas" / "image_role.json")
        cls.template_schema = load_json(ROOT / "schemas" / "image_template.json")
        cls.reference_schema = load_json(ROOT / "schemas" / "reference_policy.json")

    def test_schema_files_are_json_schema_documents(self):
        for schema in (self.role_schema, self.template_schema, self.reference_schema):
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema["type"], "object")

    def test_every_role_has_consumer_question(self):
        self.assertGreater(len(self.registry["roles"]), 0)
        for role in self.registry["roles"]:
            self.assertTrue(role.get("consumer_question", "").strip(), role.get("role_id"))

    def test_roles_contain_schema_required_fields(self):
        for role in self.registry["roles"]:
            assert_required(self, role, self.role_schema["required"], role["role_id"])

    def test_registry_roles_validate_against_image_role_schema(self):
        for role in self.registry["roles"]:
            validate_instance(self, role, self.role_schema, role["role_id"])

    def test_every_template_binds_to_an_image_role(self):
        role_ids = {role["role_id"] for role in self.registry["roles"]}
        for template in self.registry["templates"]:
            self.assertIn(template["role_id"], role_ids, template["template_id"])

    def test_every_template_has_product_reference_policy(self):
        allowed = {"CANONICAL_PRODUCT", "LAYOUT_REFERENCE", "STYLE_REFERENCE", "INFORMATION_REFERENCE"}
        for template in self.registry["templates"]:
            policy = template.get("product_reference", {}).get("policy")
            self.assertIn(policy, allowed, template["template_id"])

    def test_competitor_identity_cannot_be_canonical_product(self):
        for template in self.registry["templates"]:
            product_reference = template["product_reference"]
            self.assertNotEqual(product_reference["policy"], "COMPETITOR_PRODUCT_IDENTITY")
            self.assertNotIn("COMPETITOR_PRODUCT_IDENTITY", product_reference["identity_source"])
            for source in product_reference["forbidden_identity_sources"]:
                self.assertNotIn("canonical", source.lower())

    def test_model_layer_does_not_own_product_identity_proof(self):
        for template in self.registry["templates"]:
            model = template["model_layer"]
            self.assertFalse(model["product_identity_proof"], template["template_id"])
            if template["role_id"] == "product_identity":
                self.assertEqual(model["policy_id"], "NONE")
                self.assertFalse(model["required"])

    def test_information_text_is_marked_programmatic_or_generative(self):
        modes = {"programmatic", "generative"}
        for template in self.registry["templates"]:
            for item in template["information_layer"]["text_rendering"]:
                self.assertIn(item["mode"], modes, template["template_id"])
                self.assertTrue(item["source_requirement"].strip(), template["template_id"])

    def test_every_template_has_acceptance_checks(self):
        for template in self.registry["templates"]:
            self.assertGreater(len(template.get("acceptance_checks", [])), 0, template["template_id"])
            assert_required(self, template, self.template_schema["required"], template["template_id"])

    def test_registry_templates_validate_against_image_template_schema(self):
        for template in self.registry["templates"]:
            validate_instance(self, template, self.template_schema, template["template_id"])

    def test_registry_reference_policies_validate_against_schema(self):
        for policy in self.registry["reference_policies"]:
            validate_instance(self, policy, self.reference_schema, policy["policy_id"])

    def test_reference_policy_registry_covers_schema_enum(self):
        policy_ids = {item["policy_id"] for item in self.registry["reference_policies"]}
        schema_ids = set(self.reference_schema["properties"]["policy_id"]["enum"])
        self.assertEqual(policy_ids, schema_ids)
        for policy in self.registry["reference_policies"]:
            assert_required(self, policy, self.reference_schema["required"], policy["policy_id"])

    def test_selection_rules_point_to_registered_templates(self):
        template_ids = {template["template_id"] for template in self.registry["templates"]}
        model_ids = {item["policy_id"] for item in self.registry["model_layers"]}
        for rule in self.registry["selection_rules"]:
            self.assertIn(rule["select_template_id"], template_ids)
            self.assertIn(rule["model_layer"], model_ids)

    def test_first_party_catalog_is_registered_and_resolvable(self):
        self.assertEqual(self.registry["source_status"]["first_party_product_assets"], "available")
        self.assertEqual(self.registry["source_status"]["existing_strategy"], "available")
        asset = next(item for item in self.catalog["assets"] if item["asset_id"] == "asset_p1_gold_3pcs")
        self.assertTrue((ROOT / asset["path"]).is_file())
        self.assertEqual(asset["dimensions_px"], {"width": 900, "height": 500})

    def test_catalog_has_three_approved_configurations_and_priority_plan(self):
        self.assertEqual(self.catalog["product"]["included_set"], ["classic hoop", "double-layer hoop", "CZ accent hoop"])
        priorities = {item["priority"] for item in self.catalog["priority_plan"]}
        self.assertEqual(priorities, {"P0", "P1", "P2"})
        template_ids = {item["template_id"] for item in self.registry["templates"]}
        for item in self.catalog["priority_plan"]:
            self.assertTrue(set(item["template_ids"]).issubset(template_ids))


if __name__ == "__main__":
    unittest.main()
