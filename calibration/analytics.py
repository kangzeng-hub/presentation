from __future__ import annotations
from collections import Counter
from typing import Any
from .models import CalibrationSession, RoleSpec, RoleSpecRevision, now
from .store import CalibrationStore

def classify_feedback(feedback: str, problem_codes: list[str]) -> str:
    """Classify feedback before it can influence RoleSpec or provider prompts."""
    text = (feedback or "").lower()
    codes = set(problem_codes)
    if codes & {"TASK_NOT_CLEAR", "TASK_NOT_COMPLETED", "PURCHASE_POINT_NOT_SHOWN", "CONSUMER_DOUBT_UNRESOLVED"} or any(x in text for x in ("不知道为什么", "不清楚展示", "任务")):
        return "strategy"
    if codes & {"COMPOSITION_WRONG", "VISUAL_HIERARCHY_WRONG", "SUBJECT_TOO_SMALL", "BACKGROUND_TOO_BUSY", "PRODUCT_TOO_SMALL"} or any(x in text for x in ("太小", "构图", "比例", "背景")):
        return "composition"
    if codes & {"PRODUCT_WRONG", "PRODUCT_STRUCTURE_WRONG", "HALLUCINATED_ELEMENT", "COMPETITOR_LEAKAGE"} or any(x in text for x in ("改形", "变形", "额外配件", "竞品")):
        return "provider"
    return "unclassified"

def role_spec_recommendation(session: CalibrationSession, role: str) -> dict[str, Any]:
    summary = CalibrationStore.aggregate(session, role)
    items = [i for i in session.items if i.role == role and i.evaluation]
    feedback_ids = [i.evaluation.feedback_id or i.item_id for i in items]
    recs = []
    for code, count in summary["top_problems"][:5]:
        if code in {"PRODUCT_TOO_SMALL", "SUBJECT_TOO_SMALL", "VISUAL_HIERARCHY_WRONG"}: recs.append("increase product visual dominance")
        elif code in {"FEATURE_NOT_CLEAR", "PURCHASE_POINT_NOT_SHOWN"}: recs.append("make the purchase feature explicit")
        elif code in {"SCENE_NOT_RELEVANT", "STYLE_OFF_TARGET"}: recs.append("tighten scene and style to the role goal")
        elif code in {"PRODUCT_WRONG", "PRODUCT_STRUCTURE_WRONG", "HALLUCINATED_ELEMENT"}: recs.append("strengthen canonical reference and product-consistency QA")
    return {"role": role, "evaluated": summary["evaluated"], "accept_rate": (summary["accept"] / summary["evaluated"] if summary["evaluated"] else 0), "top_problems": summary["top_problems"], "recommended_changes": list(dict.fromkeys(recs)), "source_feedback_ids": feedback_ids}

def compare_role_spec_runs(store: CalibrationStore, sessions: list[CalibrationSession], role: str) -> dict[str, Any]:
    result = []
    for session in sessions:
        summary = store.aggregate(session, role)
        result.append({"session_id": session.session_id, **summary, "accept_rate": summary["accept"] / summary["evaluated"] if summary["evaluated"] else 0})
    return {"role": role, "runs": result}
