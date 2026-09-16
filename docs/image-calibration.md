# Image Calibration

The calibration layer reuses the existing `image_plan.json` and generation run layout. A run such as `output/wan_baseline_v1/` is discovered by its `image_*.json` records; its `qa/*.qa.json` files and the matching ImagePlan item are copied into immutable `CalibrationItem` snapshots.

## Storage

Calibration artifacts are written to `output/calibration/`:

- `session_<id>.json` — session, items, and human evaluations
- `role_spec_<role>_v<version>.json` — manually approved RoleSpec versions
- `role_spec_revisions.json` — revision history links
- `golden_examples.json` — approved/failure visual references

## UI

Install Streamlit in the local environment, then run:

```bash
streamlit run calibration/streamlit_app.py
```

The page supports AI QA inspection, accept/partial/reject verdicts, five 1–5 scores, up to three problem codes, Preserve/Change/Don't introduce, and free-text feedback. Feedback is classified before aggregation. RoleSpec suggestions are advisory; a human must approve a version.

## Generation integration

`image_generation.prompt_builder.build_generation_requests(..., role_specs={...})` accepts approved RoleSpec data. It emits a structured `[ROLE SPEC]` section and records `role_spec_version` in generation metadata. `calibration.task_builder.build_image_task` provides the provider-neutral structured input for future GPT Image Edit adapters.
