import json
from calibration.models import CalibrationSession, HumanEvaluation, RoleSpec
from calibration.store import CalibrationStore, build_items_from_run

def test_evaluation_validation_and_roundtrip(tmp_path):
    evaluation = HumanEvaluation("reject", 2, 4, 2, 2, 3, ["PRODUCT_TOO_SMALL"], preserve=["shape"], change=["scale"], dont_introduce=["extra jewelry"])
    session = CalibrationSession("cal_1", "sku", "run", "2026-01-01", ["main_image"], items=[])
    store = CalibrationStore(tmp_path); store.save_session(session)
    assert store.load_session("cal_1").session_id == "cal_1"
    assert evaluation.model_dump()["verdict"] == "reject"

def test_build_items_keeps_plan_and_qa_snapshot(tmp_path):
    run = tmp_path / "run"; (run / "qa").mkdir(parents=True)
    (run / "image_01.json").write_text(json.dumps({"image_id":"image_01", "output_assets":[{"path":"x.png"}]}))
    (run / "qa" / "image_01.qa.json").write_text(json.dumps({"overall_status":"PASS"}))
    plan = {"images":[{"image_id":"image_01", "role":"main_image", "decision_question":"q"}]}
    items = build_items_from_run("s", run, plan, ["main_image"])
    assert items[0].image_plan_snapshot["decision_question"] == "q"
    assert items[0].qa_snapshot["overall_status"] == "PASS"
