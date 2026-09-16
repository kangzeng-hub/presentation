# Wan Baseline v1 Report

## Status

All preflight checks passed and the fixed six-request experiment was executed.

Wan required asynchronous DashScope execution; the adapter used `submit → get_status → download`.

## Fixed Configuration

| Field | Value |
| --- | --- |
| Model | `wan2.7-image-pro` |
| Policy | `wan-listing-v1` |
| Requests | `generation_requests.json` |
| Reference strategy | `canonical_first` |
| Images/request | `1` |
| Sequential/group generation | `false` |
| Size | `2K` |
| Reference | `asset_p1_gold_3pcs` for every request |
| Watermark | `false` |

Preflight confirmed six request IDs: `image_01` through `image_06`. Each has a prompt and the bound `asset_p1_gold_3pcs` reference.

## 2. Generation results

| Image | Role | Generation | QA | Failure |
| --- | --- | --- | --- | --- |
| image_01 | PRODUCT_IDENTITY_MAIN | SUCCESS | NEEDS_REVIEW | `DECISION_NOT_COVERED`, `UNSUPPORTED_CLAIM`, `MISSING_VISUAL_EVIDENCE`, `UNVERIFIED_SCALE` |
| image_02 | CONTENTS_SET | SUCCESS | NEEDS_REVIEW | `MISSING_VISUAL_EVIDENCE` (label/content mismatch observation) |
| image_03 | SIZE_CHOICE_PROOF | SUCCESS | NEEDS_REVIEW | `UNVERIFIED_SCALE`, `MISSING_VISUAL_EVIDENCE`, `UNSUPPORTED_CLAIM` |
| image_04 | MATERIAL_EVIDENCE | SUCCESS | NEEDS_REVIEW | `DECISION_NOT_COVERED`, `UNVERIFIED_SCALE`, `MISSING_VISUAL_EVIDENCE`, `UNSUPPORTED_CLAIM` |
| image_05 | STRUCTURE_USE_DETAIL | SUCCESS | NEEDS_REVIEW | `DECISION_NOT_COVERED`, `MISSING_VISUAL_EVIDENCE`, `UNVERIFIED_SCALE` |
| image_06 | WEAR_STYLE_TRIPTYCH | SUCCESS | NEEDS_REVIEW | `UNVERIFIED_SCALE`, `MISSING_VISUAL_EVIDENCE` |

Each output is PNG at `2913 × 1439`, with per-image metadata, prompt hash, request hash, reference hash, provider request ID, attempt, latency, and output SHA-256.

## 3. QA result

Qwen-VL was called for all six images. The raw outputs are saved under `output/wan_baseline_v1/qa/raw/`. They are valid JSON but use shorthand values such as string `"UNKNOWN"`, string `"PARTIAL"`, arrays of observations, and arrays of violation strings. The robust parser now normalizes these into `VisionEvaluation` before deterministic QA evaluation.

```text
overall_status: NEEDS_REVIEW (all six)
failure_types: see `qa_summary.json`
```

No image-level product, template, evidence, or decision judgment is claimed.

Summary: `6` generated, `0` generation failures, `0` PASS, `0` FAIL, `6` NEEDS_REVIEW.

## 4. Failure modes

Observed failure distribution: `MISSING_VISUAL_EVIDENCE` 6, `UNVERIFIED_SCALE` 5, `DECISION_NOT_COVERED` 3, `UNSUPPORTED_CLAIM` 3.

## 5. Uncertainty

The following remain unverified because Qwen-VL returned `UNKNOWN` or partial observations for these criteria:

```text
PRODUCT_FIDELITY
TEMPLATE_FIDELITY
VISUAL_EVIDENCE
DECISION_COVERAGE
```

## 6. Next step

The Qwen-VL output contract is now parseable and raw responses are preserved. The six images remain `NEEDS_REVIEW` because the model reported uncertainty/partial evidence; no generation, prompt, asset, or template changes were made.
