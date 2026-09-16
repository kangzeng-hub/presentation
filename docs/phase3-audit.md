# Phase 3 Audit

Date: 2026-09-17

## Current architecture

- `backend/api/workspace.py` exposes the Workspace routes and job routes.
- `backend/services/workspace.py` orchestrates the existing demo/business modules.
- `backend/repositories/workspace.py` persists projects, artifact versions, jobs, approvals, and exports in SQLite.
- `backend/schemas/workspace.py` contains the current Pydantic API schemas.
- `backend/app.py` creates the FastAPI application and retains the legacy calibration/regeneration API.
- `frontend/src/generated/api.ts` is generated from `contracts/openapi.yaml`.

## Findings

1. Artifact versions already exist in `artifact_versions` with `artifact_version_id`, project scope, artifact type, numeric version, JSON payload, input references, and creation time. The repository currently creates new rows, but does not yet prevent mutation of an approved version or calculate a content checksum.
2. Product Truth, competitor snapshots, research, insight, strategy, listing, image plan, image generation, QA, and video plan are represented as artifact types. The current Workspace response exposes their latest payloads.
3. Approvals currently reference only `artifact_version_id` in the API payload and database. There is no exact-version approval service invariant or dedicated artifact approval route.
4. Export currently exists as a synchronous service. It writes a ZIP and an export row, but packages all project artifacts, does not require approvals, and does not include per-file SHA-256 records or a stable system version.
5. Project scope is present on repository queries. Approval and export scope checks need to be tightened so an artifact or export from another project cannot be accepted.
6. The current service contains deterministic demo copy for the jewelry SKU. A second SKU requires data/config-driven product truth and output generation for Phase 3 black-box validation.
7. Existing tests use `./scripts/test.sh` and currently cover Phase 2 persistence, API, idempotency, and core domain modules. Frontend validation uses `npm --prefix frontend run build` and the generated-client contract check.

## Phase 3 minimal implementation path

1. Extend artifact rows with checksum/source metadata and add immutable-version checks.
2. Add exact-version approval service/repository/API while preserving the existing approval endpoint as a compatibility surface.
3. Add a deterministic export builder that selects required artifact versions, rejects unapproved versions, records sources and SHA-256 file metadata, and persists an immutable manifest.
4. Add a non-jewelry synthetic SKU fixture and make the deterministic workspace service read SKU data/config rather than branch on a SKU name.
5. Add API, persistence, export integrity, approval, isolation, and second-SKU workflow tests.

## Explicit limitations to track

- Existing image generation remains offline-demo by default; Phase 3 validates the workflow without calling paid providers.
- Docker and Python 3.12 validation depend on local tool availability and are reported separately.
