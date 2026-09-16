# Template System

## Template Contract

Templates are structured specifications, not prompts. The compiler should resolve:

1. role and decision question;
2. canonical product asset and approved facts from `data/first_party_catalog.json`;
3. abstract layout/style/information references;
4. model layer policy, if required;
5. renderer mode and programmatic text placement;
6. acceptance checks.

The machine-readable instances live in `templates/registry.json`. The visual region blueprints live in `templates/blueprints/`.

## Template Inventory

| template_id | role_id | image_type | decision_stage | model_layer | renderer_mode | priority |
|---|---|---|---|---|---|---|
| `PRODUCT_IDENTITY_MAIN` | `product_identity` | main | recognition | `NONE` | `PRODUCT_ASSET_COMPOSITE` | P0 |
| `CONTENTS_SET` | `contents` | secondary | verification | `NONE` | `PRODUCT_ASSET_COMPOSITE` | P0 |
| `MATERIAL_EVIDENCE` | `material_evidence` | secondary | trust | `NONE` | `EVIDENCE_COMPOSITE` | P1 |
| `SIZE_CHOICE_PROOF` | `size_choice` | secondary | selection | `PRODUCT_PROOF_MODEL` | `MODEL_PROOF_COMPOSITE` | P0 |
| `STRUCTURE_USE_DETAIL` | `structure_use` | secondary | usability | `NONE` | `PRODUCT_MACRO_COMPOSITE` | P1 |
| `WEAR_STYLE_TRIPTYCH` | `wear_style` | secondary | projection | `STYLE_MODEL` | `MODEL_PROOF_COMPOSITE` | P1 |
| `LIFESTYLE_MOMENTS` | `lifestyle_context` | storefront | aspiration | `LIFESTYLE_MODEL` | `LIFESTYLE_COMPOSITE` | P2 |
| `VALUE_PACKAGING_STACK` | `value_packaging` | secondary | confidence | `NONE` | `PROGRAMMATIC_COMPOSITE` | P1 |

## Per-Template Design Notes

### `PRODUCT_IDENTITY_MAIN`

Use a clean product-first canvas with two or three canonical product slots and an optional small worn-proof slot. Product slots dominate the frame; the worn proof is a relationship cue only. There is no text overlay. Use a product asset compositor so product geometry, finish, and count remain deterministic.

### `CONTENTS_SET`

Use a centered product grouping with separated slots or a restrained row. Each slot maps to a canonical asset ID. Labels, if needed, are typeset programmatically from approved inclusion data. Do not ask a model to invent contents.

### `MATERIAL_EVIDENCE`

Use a large product macro region plus one evidence region. An evidence document or test image is optional and must be a real first-party asset. Claims are programmatic text tied to a source record. Decorative water, icons, and competitor report styling are not identity inputs.

### `SIZE_CHOICE_PROOF`

Use two to four equal macro close-up cells or one large body close-up with controlled callouts. The model is `PRODUCT_PROOF_MODEL`: anatomy provides scale, product remains the sharpest decision evidence. Size labels and measurements are programmatic.

### `STRUCTURE_USE_DETAIL`

Use a 2x2 macro/detail grid or a macro plus line-diagram region. Show the actual closure, edge, layering, and/or fastening state. Any diagram should be generated from a verified product geometry specification, not copied from a competitor.

### `WEAR_STYLE_TRIPTYCH`

Use three equal close-up panels with one approved configuration per panel. The model is `STYLE_MODEL`: enough face/anatomy to support projection, but product contrast and edge visibility remain mandatory. Look names and descriptions are programmatic.

### `LIFESTYLE_MOMENTS`

Use a 2+1 portrait grid or three balanced lifestyle scenes. The model is `LIFESTYLE_MODEL`; product can be smaller because the task is context and self-projection. Preserve a product legibility minimum and do not let atmosphere replace product evidence.

### `VALUE_PACKAGING_STACK`

Use a product region plus four to five evidence blocks. All claims, numbers, and comparison language are programmatic and source-linked. A competitor comparison is disabled by default; use only a first-party attribute stack unless approved comparative evidence exists.

## Renderer Boundary

- `PRODUCT_ASSET_COMPOSITE`: assemble canonical product photos/renders and optional approved model proof.
- `PRODUCT_MACRO_COMPOSITE`: use canonical macro assets or deterministic product renders; generated texture is not identity evidence.
- `MODEL_PROOF_COMPOSITE`: generate or select the human scene, then composite the canonical product or constrain the scene with a canonical product reference.
- `EVIDENCE_COMPOSITE`: place real documents, photos, and source-linked labels programmatically.
- `PROGRAMMATIC_COMPOSITE`: reserve layout regions, then render exact text and icons outside the image model.
- `LIFESTYLE_COMPOSITE`: use model/lifestyle generation only for context; product identity remains canonical.
