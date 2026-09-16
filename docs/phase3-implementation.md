# Phase 3 Implementation

## ArtifactVersion

`artifact_versions` is append-only from the service perspective. Each row is scoped by `project_id`, has a logical `artifact_id`/`artifact_type`, a numeric `version`, immutable payload and input references, creation metadata, and a SHA-256 payload checksum. Updating Product Truth, Listing, Strategy, or another artifact creates the next version; it does not update the existing row.

## Approval lifecycle

Approval is stored against `project_id + artifact_id + artifact_version` and retains the original `artifact_version_id`, reviewer, decision, comment, and timestamps. The exact-version endpoint is:

`POST /projects/{project_id}/artifacts/{artifact_id}/versions/{version}/approval`

Approval is never inherited. `WorkspaceService.approve_artifact` resolves the exact row before recording a decision, and `is_artifact_version_approved` is the only eligibility check used by export. A second approval of an already-approved version is rejected with `ALREADY_APPROVED`.

## Export lifecycle

`POST /projects/{project_id}/exports` (and the Phase 2 compatibility alias `/export`) resolves the current required artifact version for the project, validates every exact-version approval, collects existing payloads and source assets, and packages them synchronously. It never calls a provider or regenerates business content. Missing or unapproved versions return `EXPORT_BLOCKED_UNAPPROVED_ARTIFACT` with artifact/version details.

The ZIP contains `project.json`, `product_truth.json`, `strategy.json`, `listing.json`, `images/`, `qa/`, `video_prompt.json` when present, and `manifest.json`. The manifest is persisted in SQLite with the ZIP reference, so a later project change cannot change a completed export.

## Manifest and checksums

`ExportBuilder` is the single packaging boundary. It records project/SKU, artifact IDs and versions, approvals, source references, system version from `VERSION`, and one SHA-256 plus byte size for every non-manifest file in the ZIP. The manifest itself is included in the ZIP but excluded from its own file hash list to avoid a recursive checksum.

## SKU configuration

Project creation resolves `examples/*/product.json` by SKU. The second fixture, `examples/demo_desk_organizer/`, is a synthetic desk-organizer SKU with its own product data and asset. Strategy, listing, and generic image-plan output use Product Truth data; no second workflow implementation or SKU/category branch is copied.

## Error handling

Phase 2 structured errors are reused. Phase 3 adds `ARTIFACT_VERSION_NOT_FOUND`, `INVALID_APPROVAL_DECISION`, `ALREADY_APPROVED`, and `EXPORT_BLOCKED_UNAPPROVED_ARTIFACT`. Project and artifact lookups remain project-scoped.

## Verification

Run:

```bash
./scripts/test.sh
NPM_CONFIG_CACHE=/tmp/presentation-npm-cache npm --prefix frontend ci
npm --prefix frontend run build
./scripts/check_api_contract.sh
./scripts/secret_scan.sh
```

Phase 3 tests are in `tests/test_phase3_delivery.py`.
