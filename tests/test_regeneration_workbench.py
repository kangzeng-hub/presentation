import json
import tempfile
import unittest
from pathlib import Path
from image_generation.models import GenerationResult, OutputAsset
from calibration.models import CalibrationItem, CalibrationSession, HumanEvaluation, RoleSpec
from calibration.store import CalibrationStore
from calibration.regeneration import GenerationRequestContext, RegenerationService, compile_regeneration_prompt


def make_item():
    return CalibrationItem("s_image_01", "s", "old.png", "product_benefit", {"product_id":"sku", "template_id":"TEMPLATE", "decision_question":"why", "required_product_facts":["gold"], "required_visual_evidence":[], "required_claims":[], "forbidden_elements":[]}, image_id="image_01", active_image_id="image_01")


class RegenerationWorkbenchTests(unittest.TestCase):
    def test_prompt_compilation_is_structured_and_traceable(self):
        prompt = compile_regeneration_prompt(GenerationRequestContext("sku", "role", {"decision_question":"q"}, {"finish":"gold"}, "v1", ["shape"], ["scale"], ["competitor"], "Make it larger"))
        self.assertIn("[PRODUCT TRUTH]", prompt); self.assertIn("[MUST PRESERVE]", prompt); self.assertIn("Make it larger", prompt)
        self.assertLess(prompt.index("[PRODUCT TRUTH]"), prompt.index("[HUMAN REGENERATION INSTRUCTION]"))

    def test_regeneration_task_creation_and_rolespec_isolation(self):
        with tempfile.TemporaryDirectory() as root:
            store = CalibrationStore(root)
            session = CalibrationSession("s", "sku", "run", "now", ["product_benefit"], items=[make_item()]); store.save_session(session)
            store.save_role_spec(RoleSpec(role="product_benefit", version=1, business_goal="x", consumer_question="y", must_show=["gold"], visual_priority=[], must_avoid=[]))
            ev = HumanEvaluation("partial",3,4,2,2,3, ["PRODUCT_TOO_SMALL"], preserve=["gold"], change=["scale"], dont_introduce=["competitor"], regeneration_instruction="Increase subject scale")
            task = RegenerationService(store).create_task(session.items[0], ev)
            self.assertEqual(task.status, "draft"); self.assertEqual(task.source_image_id, "image_01")
            self.assertEqual(task.human_feedback_snapshot["change"], ["scale"])
            self.assertEqual(store.list_role_specs("product_benefit")[0]["version"], 1)

    def test_evaluation_save_and_accept_flow(self):
        with tempfile.TemporaryDirectory() as root:
            store = CalibrationStore(root)
            item = make_item(); session = CalibrationSession("s", "sku", "run", "now", ["product_benefit"], items=[item]); store.save_session(session)
            saved = store.save_evaluation(item.item_id, HumanEvaluation("accept",4,5,4,4,5))
            self.assertEqual(saved.status, "accepted"); self.assertEqual(len(saved.evaluations), 1)

    def test_execute_attaches_qa_and_creates_version(self):
        class FakeProvider:
            def generate(self, request, policy):
                return GenerationResult(generation_id=request.generation_id, image_id=request.image_id, provider="fake", model="fake", status="succeeded", output_assets=[OutputAsset(path="/tmp/generated.png", sha256="x")], request_id="req", latency_ms=1, attempt=1, policy_id="p")
        with tempfile.TemporaryDirectory() as root:
            store = CalibrationStore(root); item = make_item(); store.save_session(CalibrationSession("s", "sku", "run", "now", ["product_benefit"], items=[item]))
            ev = HumanEvaluation("partial",3,3,3,3,3, change=["scale"])
            task = RegenerationService(store, FakeProvider()).create_task(item, ev, execute=True)
            self.assertEqual(task.status, "ready_for_review"); self.assertIsNotNone(task.qa_result)
            self.assertEqual(store.list_image_versions("image_01")[0]["version"], 2)
