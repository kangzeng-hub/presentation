from calibration.analytics import classify_feedback, role_spec_recommendation
from calibration.models import CalibrationItem, CalibrationSession, HumanEvaluation

def test_feedback_classification():
    assert classify_feedback("产品太小，构图需要调整", ["PRODUCT_TOO_SMALL"]) == "composition"
    assert classify_feedback("根本不知道为什么展示这个", ["TASK_NOT_CLEAR"]) == "strategy"
    assert classify_feedback("模型把产品改形了", ["PRODUCT_WRONG"]) == "provider"

def test_role_spec_recommendation():
    s = CalibrationSession("s", "sku", "run", "now", ["storefront_2"], items=[
        CalibrationItem("i", "s", "x.png", "storefront_2", {}, evaluation=HumanEvaluation("reject", 2, 2, 2, 2, 2, ["PRODUCT_TOO_SMALL"], feedback_id="f1"), status="reviewed")
    ])
    rec = role_spec_recommendation(s, "storefront_2")
    assert rec["recommended_changes"] == ["increase product visual dominance"]
