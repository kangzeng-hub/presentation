"""Streamlit UI for human calibration. Run with: streamlit run calibration/streamlit_app.py"""
from __future__ import annotations
import json
from pathlib import Path
import streamlit as st
from .models import CalibrationSession, HumanEvaluation, PROBLEM_CODES, RoleSpec, RoleSpecRevision, now
from .analytics import classify_feedback, role_spec_recommendation
from .store import CalibrationStore, build_items_from_run

st.set_page_config(page_title="Image Calibration", layout="wide")
st.title("Image Calibration")
store = CalibrationStore()
plan_path = Path("examples/demo_sku/generated-fixtures/image_plan.json")
plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.exists() else {"images": []}
run_dirs = [p for p in sorted(Path("output").glob("*")) if p.is_dir() and (p / "image_01.json").exists()]

with st.sidebar:
    st.header("Calibration session")
    sku = st.text_input("SKU", value=plan.get("product_id", ""))
    run_label = st.selectbox("Generation run", [str(p) for p in run_dirs] or [""], index=0)
    role_options = sorted({i.get("role", "") for i in plan.get("images", [])})
    roles = st.multiselect("Image roles", role_options, default=role_options[:2])
    session_id = st.text_input("Session ID", value="cal_local_001")

if not run_label or not roles:
    st.info("Select a generation run and at least one image role.")
    st.stop()

try:
    session = store.load_session(session_id)
except FileNotFoundError:
    session = CalibrationSession(session_id=session_id, sku=sku, run_id=Path(run_label).name, created_at=now(), roles=roles, items=build_items_from_run(session_id, run_label, plan, roles))
    store.save_session(session)

session.roles = roles
items = [i for i in session.items if i.role in roles]
if not items:
    st.warning("No generated images match these roles in the selected run.")
    st.stop()

for item in items:
    with st.expander(f"{item.item_id} · {item.role} · {item.status}", expanded=item.status == "pending"):
        left, right = st.columns([1.2, 1])
        with left:
            path = Path(item.image_path)
            if path.exists(): st.image(str(path), use_container_width=True)
            else: st.warning(f"Image not found: {item.image_path}")
        with right:
            if item.qa_snapshot:
                st.subheader("AI QA")
                st.json({k: item.qa_snapshot.get(k) for k in ("overall_status", "product_truth", "decision_coverage", "failure_types") if k in item.qa_snapshot}, expanded=False)
            st.subheader("Human review")
            verdict = st.radio("Verdict", ["accept", "partial", "reject"], horizontal=True, key=f"v_{item.item_id}", index=["accept", "partial", "reject"].index(item.evaluation.verdict) if item.evaluation else 2)
            cols = st.columns(5)
            labels = ["Task alignment", "Product accuracy", "Visual hierarchy", "Purchase value", "Execution quality"]
            scores = [cols[n].slider(labels[n], 1, 5, getattr(item.evaluation, ["task_alignment", "product_accuracy", "visual_hierarchy", "purchase_value", "execution_quality"][n], 3) if item.evaluation else 3, key=f"s_{item.item_id}_{n}") for n in range(5)]
            selected = st.multiselect("Primary problems (1-3)", list(PROBLEM_CODES), format_func=lambda x: PROBLEM_CODES[x], default=(item.evaluation.primary_problem_codes if item.evaluation else []), max_selections=3, key=f"p_{item.item_id}")
            preserve = st.text_area("Preserve", ", ".join(item.evaluation.preserve if item.evaluation else []), key=f"pr_{item.item_id}")
            change = st.text_area("Change", ", ".join(item.evaluation.change if item.evaluation else []), key=f"ch_{item.item_id}")
            dont = st.text_area("Don't introduce", ", ".join(item.evaluation.dont_introduce if item.evaluation else []), key=f"di_{item.item_id}")
            feedback = st.text_area("Human feedback", item.evaluation.human_feedback if item.evaluation else "", key=f"f_{item.item_id}")
            suggested = st.text_area("Suggested change", item.evaluation.suggested_change if item.evaluation else "", key=f"sg_{item.item_id}")
            if st.button("Save calibration", key=f"save_{item.item_id}"):
                item.evaluation = HumanEvaluation(verdict=verdict, task_alignment=scores[0], product_accuracy=scores[1], visual_hierarchy=scores[2], purchase_value=scores[3], execution_quality=scores[4], primary_problem_codes=selected, preserve=[x.strip() for x in preserve.split(",") if x.strip()], change=[x.strip() for x in change.split(",") if x.strip()], dont_introduce=[x.strip() for x in dont.split(",") if x.strip()], human_feedback=feedback, suggested_change=suggested, feedback_id=item.item_id, classified_as=classify_feedback(feedback, selected))
                item.status = "reviewed"; session.status = "in_progress"; store.save_session(session); st.success("Saved")

st.divider()
st.header("Role specification")
for role in roles:
    summary = store.aggregate(session, role)
    st.subheader(role)
    st.write(f"Evaluated: {summary['evaluated']} · Accept: {summary['accept']} · Partial: {summary['partial']} · Reject: {summary['reject']}")
    st.write("Top problems:", summary["top_problems"] or "None")
    recommendation = role_spec_recommendation(session, role)
    if st.button("Generate RoleSpec revision suggestion", key=f"recommend_{role}"):
        st.session_state[f"rec_{role}"] = recommendation
    if f"rec_{role}" in st.session_state:
        rec = st.session_state[f"rec_{role}"]
        st.info("AI suggestion only — review and approve manually.")
        st.json(rec, expanded=False)
        existing = store.list_role_specs(role)
        version = (existing[-1].get("version", 0) if existing else 0) + 1
        goal = st.text_input("Business goal", value=(existing[-1].get("business_goal", "") if existing else ""), key=f"goal_{role}")
        must_show = st.text_input("Must show (comma separated)", value=", ".join(existing[-1].get("must_show", []) if existing else []), key=f"must_{role}")
        must_avoid = st.text_input("Must avoid (comma separated)", value=", ".join(existing[-1].get("must_avoid", []) if existing else []), key=f"avoid_{role}")
        reason = st.text_area("Change reason", value="; ".join(rec["recommended_changes"]), key=f"reason_{role}")
        if st.button(f"Approve RoleSpec v{version}", key=f"approve_{role}"):
            spec = RoleSpec(role=role, version=version, business_goal=goal or f"Role goal for {role}", consumer_question=(existing[-1].get("consumer_question", "") if existing else ""), must_show=[x.strip() for x in must_show.split(",") if x.strip()], visual_priority=(existing[-1].get("visual_priority", ["product", "task"]) if existing else ["product", "task"]), must_avoid=[x.strip() for x in must_avoid.split(",") if x.strip()], change_reason=reason, changed_by="human", source_feedback_ids=rec["source_feedback_ids"])
            store.save_role_spec(spec)
            if existing:
                store.save_revision(RoleSpecRevision(role=role, from_version=existing[-1].get("version", version - 1), to_version=version, change_reason=reason, changed_by="human", created_at=now(), source_feedback_ids=rec["source_feedback_ids"]))
            st.success(f"Approved {role} v{version}")
    specs = store.list_role_specs(role)
    if specs:
        st.json(specs[-1], expanded=False)
    else:
        st.caption("No RoleSpec yet. Human approval is required before creating v1/v2.")
