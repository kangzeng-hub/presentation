# Image Calibration & Regeneration Workbench

## Run

Backend (Python 3.12):

```bash
python -m pip install -r requirements-workbench.txt
uvicorn backend.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to the backend in deployment; for local use
set `server.proxy` in `vite.config.ts` or serve behind the same origin.

## Data flow

`Run -> ImagePlan snapshot -> generated artifact -> QA snapshot -> HumanEvaluation -> RegenerationTask -> structured GenerationRequest -> existing provider -> new ImageVersion -> QA -> human decision`.

Human fields are persisted in `human_feedback_snapshot` and only affect the
current task. RoleSpec files are never mutated by regeneration. Analytics can
produce a revision suggestion; a human must call the RoleSpec revision endpoint
before a new approved version is used.

## API

`GET /api/artifacts/runs` discovers existing generation directories and
`POST /api/calibration/sessions` snapshots one into a reviewable calibration
session. The latter accepts `run_id`/`run_dir`, optional `session_id`, `sku`,
and `roles` (defaults to every role in `examples/demo_sku/generated-fixtures/image_plan.json`).

`GET /api/runs`, `GET /api/runs/{run_id}`, `GET /api/runs/{run_id}/calibration`,
`GET /api/calibration/items/{item_id}`,
`POST /api/calibration/items/{item_id}/evaluation`,
`POST /api/calibration/items/{item_id}/regenerate`,
`GET /api/regeneration/{task_id}`,
`POST /api/regeneration/{task_id}/decision`,
`POST /api/regeneration/{task_id}/cancel`,
`GET /api/images/{image_id}`, `/qa`, `/history`,
`GET /api/problem-codes`, `GET /api/rolespecs`, `GET /api/rolespecs/{role}`,
`GET /api/runs/{run_id}/roles/{role}/insight`,
`POST /api/rolespecs/{role}/revision`.

## Example RegenerationTask

```json
{
  "task_id": "regen_cal_image_03_2",
  "calibration_item_id": "cal_image_03",
  "source_image_id": "image_03",
  "role": "product_benefit",
  "role_spec_version": "v1",
  "preserve": ["exact product structure", "3PCS quantity"],
  "change": ["increase product scale", "clarify hierarchy"],
  "dont_introduce": ["competitor styling", "unsupported claims"],
  "status": "ready_for_review",
  "output_image_ids": ["image_03_v2"]
}
```

Each `ImageVersion` stores its source image, prompt snapshot, provider,
generation metadata, QA result, and eventual human evaluation, so v1 → v2 → v3
can be audited without overwriting the previous artifact.
