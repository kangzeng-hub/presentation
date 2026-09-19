# AI-Native Portfolio Project Audit

Date: 2026-09-17

## Current architecture

- Frontend: React 19 + TypeScript + Vite 8. The existing UI is a single Workspace application with Overview, Research, Listing, Images, and Video Plan stages. It uses a generated OpenAPI type surface and `openapi-fetch`; there is no router library or global state library.
- Backend: FastAPI with a SQLite repository. `backend/services/workspace.py` orchestrates project state, artifacts, jobs, exact-version approvals, and export packaging.
- Domain modules: competitor ingestion, deterministic image planning, image generation adapters, Qwen-VL image QA, human calibration/regeneration, and Seedance video request construction.
- Styling: one hand-written CSS file. No component system, Tailwind, CSS Modules, or icon library existed at audit time.
- Media: generated assets are served read-only by `GET /api/assets/{asset_path}`. Vite already proxies workspace routes; the portfolio should also proxy `/api` rather than duplicate assets.

## Existing pages and reusable surfaces

- `/projects/{project_id}/overview`: project, Product Truth, current strategy, downstream output readiness.
- `/research`: competitor URL capture, evidence cards, insight generation, strategy generation.
- `/listing`: listing generation and editable generated content.
- `/images`: six-role ImagePlan, generation job state, QA/human-review labels.
- `/video`: VideoPlan generation and prompt export. This is a plan surface, not proof of successful video generation.
- Reusable backend/API surfaces: Workspace response, `/api/artifacts/runs`, `/api/assets`, calibration runs/items, image QA/history, approval, and export endpoints.

## Verified evidence

### Product and cross-border context

- Canonical demo SKU: `G23STUDIO_ASTMF136_HINGED_SEPTUM_RING_3PCS` in `data/first_party_catalog.json` and `examples/demo_sku/product.json`.
- Verified fields include product name, ASTM F136 titanium base, 18K Gold PVD finish, 18G/20G, 8mm inner diameter, three included styles, closure structure, approved placements, and source-linked claims.
- Competitor evidence exists in `examples/demo_sku/competitor_evidence.json`, `docs/competitor-visual-analysis.md`, and local `c1/`, `c2/` image sets. It is explicitly evidence for presentation patterns and customer questions, not a Product Truth source.

### Listing and strategy

- Workspace has structured ProductTruth, CompetitorInsight, PresentationStrategy, and ListingPlan schemas and persisted artifact versions.
- Listing generation is deterministic demo/config behavior in the public workspace, not evidence of a deployed LLM copy system.
- Strategy-to-listing/image/video mappings exist in the API schema and demo data.

### Image planning, generation, and QA

- A strict six-image plan exists at `examples/demo_sku/generated-fixtures/image_plan.json`, with decision question, customer need, strategy reason, required facts/evidence, constraints, and template ID per image.
- `output/wan_baseline_v1/` contains six successful 2913x1439 generated PNGs, per-image request/provider/hash/latency metadata, raw QA, normalized QA, and a summary.
- Verified QA result: 6 generated, 0 generation failures, 0 PASS, 0 FAIL, 6 NEEDS_REVIEW. Failure counts: MISSING_VISUAL_EVIDENCE 6, UNVERIFIED_SCALE 5, DECISION_NOT_COVERED 3, UNSUPPORTED_CLAIM 3.
- `output/gpt_image_2_from_wan/` and `output/gpt_image_2_new/` contain additional six-image result sets with per-image metadata. They are usable as version evidence but must not be labeled approved without a recorded approval.
- Calibration sessions exist in `output/calibration/`, but the inspected sessions are `draft`; items are pending and do not establish an approved final set.

### Video

- `video_generation/` implements typed input, prompt construction, a Seedance adapter, and result/review models.
- `output/video/` contains the source input, prompt, request, provider response, and review record.
- The recorded provider response is a 404 `ModelNotOpen`; review says unusable and no `task_id` was returned. There is no final video asset. The portfolio must present this as an experimental/blocked workflow trace, not completed video production.

### Engineering and delivery

- Artifact versions are append-only at the service boundary and include input references/checksums.
- Exact-version approval is implemented; approval does not carry to a newer version.
- Export is approval-gated and packages an immutable manifest with per-file SHA-256 records.
- API contract exists at `contracts/openapi.yaml`; TypeScript types are generated into `frontend/src/generated/api.ts`.
- The repository has 14 Python test files and 100 discovered `test_` methods at audit time. Final published counts must use actual executed test results, not discovery alone.

## Implemented capability classification

### Implemented

- Versioned Product Truth and structured cross-border product data.
- Competitor capture/normalization and evidence-linked insight structures.
- Deterministic six-role image planning.
- Provider-backed image generation adapters with recorded runs.
- Structured Qwen-VL QA parsing and deterministic QA status/failure taxonomy.
- Human evaluation, regeneration task, and image history models/APIs.
- Workspace API, persistence, job state, exact-version approval, and approval-gated export.
- Video prompt planning and provider request adapter.

### Prototype / experimental / partial

- Public demo research and Listing generation contain synthetic/deterministic behavior.
- Image provider execution is opt-in; the normal Workspace job is an offline workflow validation.
- Human calibration UI/API is implemented, but inspected sessions are draft and do not prove completed production approval.
- Video generation is experimental and the recorded run is blocked by provider model access.
- No evidence was found for production deployment, enterprise customers, revenue impact, conversion uplift, or measured speed improvement.

### Not supported as claims

- Multi-agent system, LangGraph, MCP, RAG, autonomous production agents.
- A successful/approved AI video output.
- Production-scale throughput or batch performance metrics.
- A/B testing, customer count, commercial impact, or validated efficiency ratios.
- A fully approved image set; the recorded baseline remains NEEDS_REVIEW.

## Recommended portfolio cases

1. Listing decision trace: Product Truth + competitor evidence -> customer concerns -> presentation strategy -> deterministic listing output. Label demo-generated content accurately.
2. AI image production: canonical product -> six-role ImagePlan -> Wan generation -> Qwen-VL QA -> human calibration design -> version comparison. Preserve the NEEDS_REVIEW result.
3. AI-assisted video workflow: structured product input -> demonstration sequence -> provider request -> blocked provider response -> review. Present as Experimental and show the real failure transparently.
4. Engineering delivery: artifact provenance -> immutable versions -> exact-version approval -> manifest export.

## Portfolio implementation boundary

- Keep the existing Workspace under `/projects/...`.
- Use a portfolio adapter to normalize repository evidence into UI models.
- Read media through the existing `/api/assets` endpoint and do not copy assets.
- Do not alter generation, provider, QA, calibration, database, or production pipeline code for the portfolio.
