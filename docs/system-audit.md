# Unified Presentation Workspace: Phase 1 Audit

## Scope inspected

- Runtime and API entry points: `app.py`, `backend/app.py`, `backend/main.py`
- Product source of truth: `data/first_party_catalog.json`
- Competitor ingestion: `competitor_ingestion/*`, `docs/competitor-ingestion-mvp.md`
- Image planning: `image_planning/*`, `image_plan.json`, `schemas/image_role.json`, `schemas/image_template.json`, `templates/registry.json`
- Image generation: `image_generation/*`, `generation_requests.json`
- Image QA and human review: `image_qa/*`, `calibration/*`, `tests/test_image_qa.py`, `tests/test_calibration.py`
- Video prompt models: `video_generation/models.py`, `video_generation/prompt_builder.py`
- Frontend and scripts: `frontend/src/main.tsx`, `frontend/package.json`

No `AGENTS.md`, repository README, or OpenAPI contract currently exists at the workspace root.

## Current architecture

The repository is primarily a Python library/CLI workspace with a thin FastAPI application. Product facts and approved claims are catalog-backed. Competitor ingestion calls a replaceable Apify provider, normalizes product data and 1-3 star reviews, and writes provider-independent JSON artifacts. Image planning deterministically converts catalog facts plus narrative competitor analysis and the template registry into a strict six-image `ImagePlan`. Image generation compiles typed requests/tasks and preserves canonical product references. Image QA produces structured `QAReport` values with PASS/FAIL/NEEDS_REVIEW states. Calibration stores generation snapshots, human evaluations, regeneration tasks, and image version history.

The HTTP API currently exposes artifact discovery, calibration sessions, image assets, run/calibration data, QA snapshots, regeneration, role specs, and problem codes. The React frontend is a calibration-only run browser and review form. Video code currently supports prompt construction and provider-specific generation models, but there is no workspace-level VideoPlan API or UI.

## Reusable modules

| Capability | Existing source | Reuse decision |
|---|---|---|
| Product truth, claims, canonical assets | `data/first_party_catalog.json` | Treat as the canonical source; wrap with a Project/SKU reference, do not copy facts into feature modules. |
| Competitor capture and normalization | `competitor_ingestion/models.py`, `normalize.py`, `provider.py`, `storage.py` | Reuse provider and normalized product/review model; add orchestration/status persistence around it. |
| ImagePlan | `image_planning.models.py`, `planner.py`, `resolver.py` | Reuse unchanged as the image planning engine; add strategy/project provenance at the boundary. |
| Image generation | `image_generation.models.py`, `task_compiler.py`, `execution.py` | Reuse typed request/task compilation and provider execution; do not create a second generator. |
| Image QA | `image_qa.models.py`, `evaluator.py`, `validator.py` | Reuse QA report/state model and validation. |
| Human review and revisions | `calibration.models.py`, `store.py`, `regeneration.py`, current FastAPI routes | Reuse evaluation, regeneration, version history, and decision behavior. |
| Video prompt construction | `video_generation.models.py`, `prompt_builder.py` | Reuse prompt builder concepts; add a non-generating VideoPlan that records source references. |

## New modules required

1. Domain models and persistence for `Project`, `ProductTruth` reference, `CompetitorSnapshot`, `CompetitorReview`, `CompetitorInsight`, `PresentationStrategy`, `ListingPlan`/versions, and `VideoPlan`.
2. Research orchestration with explicit `queued`, `running`, `completed`, and `failed` state transitions; the frontend must consume persisted backend state.
3. Strategy derivation service that consumes ProductTruth and CompetitorInsight once and is referenced by Listing, ImagePlan, and VideoPlan.
4. Listing generation/edit/version service retaining generated and edited content plus source strategy.
5. Workspace-level API routes and a persistence adapter (file-backed is consistent with this repository's current storage approach).
6. `contracts/openapi.yaml`, generated TypeScript client, mock API adapter, contract tests, and an end-to-end smoke flow.
7. Unified React workspace navigation and source-context sidebar around the existing review UI.

## Contract and schema gaps

- `contracts/openapi.yaml` is absent; no API source of truth or generated client exists.
- Existing Pydantic/dataclass models are module-local and not a unified domain model.
- `CompetitorProduct` has a review list but no persisted positive/neutral/negative buckets; these should be derived deterministically in the domain response rather than changing the ingestion contract unnecessarily.
- Existing `ImagePlan` requires exactly six images and uses registry role names (`product_identity`, `contents`, etc.), while the requested UI labels are presentation roles. Use an explicit mapping/display label rather than changing the planner's role IDs.
- Existing calibration `status` values and QA states are separate concerns; the workspace needs a documented aggregate stage/status enum.
- Existing video models include generation request/result types even though the requested scope stops at Strategy/Script/Prompt. Keep those provider models isolated and expose only `VideoPlan`/prompt export in the workspace API.

## Potential conflict points

- Do not duplicate ProductTruth, claims, or competitor-derived selling points in Listing/Image/Video payloads; use project-level IDs and strategy snapshots.
- Do not replace `image_plan.json`, generation requests, QA reports, or calibration history with frontend-specific shapes.
- Avoid changing existing role IDs, six-image validation, QA statuses, or human evaluation fields without an explicit contract migration.
- Apify ingestion is synchronous at the provider layer; research orchestration must persist job state and handle provider errors without making the browser infer progress.
- Existing backend paths are `/api/runs`, `/api/images`, and `/api/calibration/*`; new workspace routes must avoid ambiguous collisions and preserve these routes for the current calibration UI.

## Recommended implementation order

1. Add domain models and file-backed stores while keeping current module models intact.
2. Define and lint `contracts/openapi.yaml` for workspace, research, insight, strategy, listing, image, QA/review, and video-plan operations.
3. Generate the TypeScript client from that contract.
4. Build the frontend against a mock implementation of the generated client.
5. Connect routes to existing ingestion/planning/generation/QA/calibration services.
6. Add contract/API tests, then one full smoke flow from project creation through video prompt export.

