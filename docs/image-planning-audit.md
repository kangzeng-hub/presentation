# Image Planning Layer Audit

## Existing Inputs

1. Product Truth is read from `data/first_party_catalog.json`, which registers the product, variants, canonical asset, claims, evidence notes, and brand constraints.
2. Competitor Insight is read from `docs/competitor-visual-analysis.md`. It is currently narrative Markdown, so the planner uses only the documented patterns and records them as structured `CompetitorGap` objects.
3. Template Registry is read from `templates/registry.json`, including roles, priorities, templates, renderer policies, and acceptance rules.
4. No existing Python image-generation pipeline was found in this repository. The new layer does not modify Wan, Qwen-VL, downloading, or image generation code.
5. Existing schemas are JSON schema documents under `schemas/`; existing tests use standard-library `unittest` and a lightweight validator.
6. No existing Pydantic module or dependency is installed. The new typed models use Pydantic when available and a strict standard-library fallback otherwise.

## New Flow

```text
first_party_catalog.json
        +
competitor-visual-analysis.md
        +
templates/registry.json
        |
        v
image_planning.planner
        |
        v
ImagePlan (exactly 6 items)
        |
        v
image_planning.resolver
        |
        v
ResolvedTemplate records
```

## Reused and Protected

Reused: catalog facts and claim IDs, competitor findings, registry template layouts/styles/constraints, and the existing tests. Protected: all existing image generation, Wan configuration, Qwen-VL extraction, downloads, and competitor analysis source content.

