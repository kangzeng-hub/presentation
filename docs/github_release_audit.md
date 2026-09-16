# GitHub Release Audit

Audit date: 2026-09-15

## 1. Current architecture

- `frontend/` is a React + Vite TypeScript application. The UI workflow is Overview, competitor research, listing, image planning/generation, and video planning.
- `mock-server/server.mjs` is a stateful Node HTTP demo backend implementing the frontend OpenAPI project workflow. It seeds `demo-project` and listens on `127.0.0.1:4010`.
- `backend/main.py` exposes `backend.app:app`, a FastAPI calibration/regeneration API. It discovers generation artifacts under `output/`, serves assets, and delegates image generation to the existing Python modules. It does not implement the frontend `/projects/*` contract.
- Python domain packages include `presentation_domain`, `competitor_ingestion`, `image_planning`, `image_generation`, `image_qa`, `calibration`, and `video_generation`.
- JSON contracts and registries live under `contracts/`, `schemas/`, `config/`, and `templates/`.

## 2. Runtime dependencies

Python runtime dependencies from `backend/requirements.txt`:

- FastAPI >= 0.110
- Uvicorn with standard extras >= 0.27
- Pydantic >= 2.0
- Requests >= 2.31
- Pillow >= 10.0
- python-pptx >= 0.6.23

The frontend uses the versions locked in `frontend/package-lock.json` and runs with Node/npm, Vite, React, TypeScript, and `openapi-fetch`.

The demo backend requires Node.js; the Python API requires Python 3.11+ in the documented setup. Docker is the recommended runtime. FFmpeg is not referenced by the current frontend/demo startup path; video provider code may require additional provider-specific tooling and is documented as out of the demo path.

## 3. Environment variables

Observed runtime variables:

- `DASHSCOPE_API_KEY`: optional for real Wan image generation; required only when that provider is selected.
- `APIFY_API_TOKEN`: required for real Amazon competitor ingestion.
- `APIFY_PRODUCT_ACTOR`, `APIFY_REVIEWS_ACTOR`: optional Apify actor overrides with code defaults.
- `OPENAI_API_KEY` or `SUB2API_API_KEY`: optional/required when the OpenAI image adapter is selected.
- `OPENAI_BASE_URL` or `SUB2API_BASE_URL`: optional OpenAI-compatible endpoint override.
- `RUN_WAN_INTEGRATION`: opt-in integration test flag (`1` enables external calls).
- `ARK_API_KEY`, `SEEDANCE_MODEL_ID`: used by the optional video-generation adapter.
- `VITE_API_BASE_URL`: frontend API base URL; defaults to the local demo backend when unset.
- `PORT`: demo backend port; defaults to `4010`.

The checked-in `.env.example` was incomplete and did not document all observed names. The local `.env` contains non-empty credentials and must never be published.

## 4. External services

- Apify is used by `competitor_ingestion/provider.py` for live Amazon ingestion.
- DashScope/Wan is used by `image_generation/adapters/wan.py`.
- An OpenAI-compatible image endpoint is used by `image_generation/adapters/openai.py`.
- Ark/Seedance is used by the optional video adapter.
- The frontend demo uses only the local stateful mock backend and therefore does not require external API calls to exercise the UI flow.

## 5. Local filesystem dependencies

- Runtime paths are mostly project-relative. `image_generation/service.py` resolves repository resources from its module location.
- Calibration and generated artifacts default to `output/calibration` and `output/`.
- The frontend demo references public sample assets such as `p1/p1.jpg` through the seeded project data.
- Existing local-only material includes `.venv/`, `.ppt-venv/`, `frontend/node_modules/`, `frontend/dist/`, `output/`, caches, `.DS_Store`, PPTX exports, and source/customer-like product folders. These require an explicit public repository policy.
- No source scan found hard-coded `/Users/...`, `/home/...`, `Desktop/...`, or Windows user paths outside generated/cache content.

## 6. Startup flow

Current local flow is split: run `node mock-server/server.mjs` on port 4010 for the frontend workflow, run `npm run dev` in `frontend/`, and optionally run `uvicorn backend.main:app --reload --port 8000` for the calibration API. Vite's current proxy targets port 8000, while the generated frontend client defaults to port 4010, so the setup was not reproducible as a single command.

## 7. Test flow

Tests are Python `unittest`/pytest-compatible files under `tests/`. The repository had no root `pytest.ini`, test script, or release check entrypoint. The optional Wan integration test is skipped unless `RUN_WAN_INTEGRATION=1`.

## 8. Demo flow

The stateful mock backend seeds a public `demo-project` and supports the complete UI contract: Product Truth, competitor research, insight, strategy, listing, image plan, image generation status, and video plan. Existing product catalog material is in `data/first_party_catalog.json`; no isolated public `examples/` fixture existed.

## 9. Secrets / sensitive files

- `.env` contains populated credential values and must be ignored.
- Generated outputs and logs can contain provider responses, paths, and image data and should not be tracked by default.
- Git history could not be inspected because this directory is not currently a Git worktree (`git status` reports “not a git repository”). Before the first push, scan the complete history after initializing or attaching the intended repository.

## 10. Dockerization risks

- The frontend and demo backend use different ports and were previously started manually.
- Vite must bind to `0.0.0.0` inside a container, and its API base URL must point at the browser-reachable published backend port.
- The Python API writes JSON and generated assets to relative `output/`; a volume is required if those artifacts must survive container recreation.
- Real provider calls require secrets and network access; the default demo must remain local and deterministic.

## 11. GitHub publication risks

- The directory is not yet a Git repository.
- `.env`, virtual environments, `node_modules`, build output, caches, generated assets, PPTX exports, and OS metadata are present locally.
- Several folders contain product/reference imagery and Chinese source notes; confirm licensing and business sensitivity before publishing.
- Existing `.env.example` includes only a subset of the actual variables.
- There is no license, reproducible Compose setup, doctor check, smoke test, or release check script.

## 12. Recommended changes

1. Add a complete `.gitignore` and documented `.env.example` without secrets.
2. Add public, synthetic `examples/demo_sku/` fixtures that follow the existing product/competitor/evidence shapes.
3. Add Dockerfiles/Compose for a browser-reachable frontend and stateful demo backend, with a persistent output volume.
4. Add `scripts/doctor.sh`, `scripts/test.sh`, `scripts/smoke_test.sh`, and `scripts/release_check.sh`.
5. Add a health endpoint to the demo backend and a health endpoint to the Python API.
6. Rewrite `README.md` and add `docs/github_release.md` with truthful demo limitations and provider setup.
7. Initialize Git only after the public boundary is reviewed, then run a secret scan over the resulting history before pushing.
