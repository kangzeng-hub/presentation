# Phase 3 Acceptance Matrix

Date: 2026-09-17

| Requirement | Status | Evidence |
| --- | --- | --- |
| Approval bound to exact version | PASS | `test_exact_version_approval_and_no_inheritance` |
| Version immutable | PASS | append-only repository; update creates Listing v2 |
| No approval inheritance | PASS | v1 approval remains false for v2 |
| Old approval retained | PASS | approval history assertion in Phase 3 test |
| Export endpoint | PASS | `POST /projects/{id}/exports` and compatibility `/export` |
| Export blocked by unapproved asset | PASS | `test_unapproved_artifact_blocks_export_with_details` |
| ZIP structure | PASS | `test_export_manifest_zip_and_sha256` |
| Manifest complete | PASS | project, artifacts, approvals, sources, files, timestamps |
| SHA-256 valid | PASS | every manifest file record is recomputed from ZIP bytes |
| System version present | PASS | `VERSION` = `3.0.0`; manifest assertion |
| Source references present | PASS | manifest source aggregation assertion |
| SKU isolation | PASS | Project A/B repository, approval, and export assertions |
| Second SKU full workflow | PASS | `DEMO-DESK-ORGANIZER` register through export |
| No SKU-specific core code | PASS | second SKU test checks no SKU branch; fixture is data-only |
| Full regression suite | PASS | `.venv/bin/pytest`: 99 passed, 1 skipped |
| Unknown SKU rejection | PASS | `test_unknown_sku_is_rejected_without_orphan_project` |
| Concurrent version allocation | PASS | `test_concurrent_artifact_versions_are_unique_and_contiguous` |
| Export snapshot immutable | PASS | `test_completed_export_is_immutable_after_new_artifact_version` |
| Missing declared asset blocks export | PASS | `test_missing_declared_product_asset_fails_export` |

## Black-box workflows

SKU A: `DEMO-GOLD-3PCS`, synthetic jewelry fixture. The test executes registration, synthetic research, insight, strategy, listing, image plan, offline generation/QA, video plan, exact-version approval, and export.

SKU B: `DEMO-DESK-ORGANIZER`, synthetic desk organization fixture. The same service and router execute registration, synthetic research, insight, strategy, listing, generic config-driven image plan, offline generation/QA, video plan, exact-version approval, and export. No workflow implementation is copied for SKU B.

## Commands and results

```text
./scripts/test.sh
96 tests, 1 skipped (automatically uses the project virtual environment)

PYTHONPATH=. PYTHONWARNINGS=error::ResourceWarning .venv/bin/pytest -q
99 passed, 1 skipped

npm --prefix frontend ci
PASS, 0 vulnerabilities

npm --prefix frontend run build
PASS

./scripts/check_api_contract.sh
PASS, FastAPI OpenAPI paths=46 schemas=24; generated client synchronized

./scripts/secret_scan.sh
PASS
```

Docker validation is not reported as passed because Docker is unavailable on the execution host. Python 3.12 execution is configured by Dockerfile/CI but was not locally available; local tests ran under the existing Python 3.14 environment.
