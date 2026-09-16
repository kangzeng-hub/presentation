# Image Role System

## Operating Model

The role system is question-first. A role exists because a shopper must resolve a distinct uncertainty. Image count is a later production decision; a role can be omitted, repeated with a different approved fact, or promoted in the sequence when evidence demands it.

Priority meanings:

- `P0`: identity or selection blocker; should appear in the first decision-support images.
- `P1`: important confidence or objection question.
- `P2`: aspiration, enrichment, or lower-risk differentiation.

## Role Map

| role_id | image_type | decision_stage | consumer_question | priority | model | macro | text | real asset | renderer |
|---|---|---|---|---|---:|---:|---:|---:|---|
| `product_identity` | main | recognition | What exactly is the product and what variants are included? | P0 | No | Yes | No | Yes | `PRODUCT_ASSET_COMPOSITE` |
| `contents` | secondary | verification | What pieces, configurations, or included options will arrive? | P0 | No | Yes | Optional | Yes | `PRODUCT_ASSET_COMPOSITE` |
| `material_evidence` | secondary | trust | What material/finish evidence supports the approved product claim? | P1 | No | Yes | Yes | Yes | `EVIDENCE_COMPOSITE` |
| `size_choice` | secondary | selection | Which size or diameter is appropriate for my intended placement/look? | P0 | Yes | Yes | Yes | Yes | `MODEL_PROOF_COMPOSITE` |
| `structure_use` | secondary | usability | How does the product open, close, layer, or sit on the body? | P1 | No | Yes | Yes | Yes | `PRODUCT_MACRO_COMPOSITE` |
| `wear_style` | secondary | projection | What visual styles can the product create? | P1 | Yes | Yes | Yes | Yes | `MODEL_PROOF_COMPOSITE` |
| `lifestyle_context` | storefront | aspiration | Can I imagine wearing it across everyday contexts and occasions? | P2 | Yes | No | Optional | Yes | `LIFESTYLE_COMPOSITE` |
| `value_packaging` | secondary | confidence | What verified benefits justify choosing this product? | P1 | No | Optional | Yes | Yes | `PROGRAMMATIC_COMPOSITE` |

## Why Each Role Exists

### `product_identity`

- `competitor_visual_fact`: Both competitor main images isolate multiple product variants on white and add a small worn cue.
- `inference`: Identity and assortment must be resolved before claims or lifestyle context can help.
- `existing_strategy_requirement`: Variant count, finish, geometry, and hero configuration come from `data/first_party_catalog.json` and `asset_p1_gold_3pcs`.

### `contents`

- `competitor_visual_fact`: Both main images visually repeat three product presentations, while secondary images show product groupings.
- `inference`: A dedicated contents role prevents the main image from carrying every inclusion/configuration detail.
- `existing_strategy_requirement`: The exact included pieces and option taxonomy are registered in `product.included_set`.

### `material_evidence`

- `competitor_visual_fact`: `c1-s3` uses a test-report overlay; `c2-s1` uses a material headline and stacked claims.
- `inference`: Material confidence is a proof role, not a decorative style role.
- `existing_strategy_requirement`: Only registered claim IDs and supplied evidence notes may be composited; no certificate image was supplied.

### `size_choice`

- `competitor_visual_fact`: `c1-s2` uses four repeated nose close-ups with size labels; `c1-s5` distributes placement/size labels around a face.
- `inference`: Fit and diameter are selection blockers and deserve direct body-scale evidence.
- `existing_strategy_requirement`: Available sizes and placement compatibility are registered as 18G/20G, 8mm, and the approved placement list.

### `structure_use`

- `competitor_visual_fact`: `c1-s4` diagrams opening/closing and `c2-s5` shows closure, edge, layered, and stone details.
- `inference`: A macro/diagram role can answer mechanical and comfort questions without asking a model to carry the explanation.
- `existing_strategy_requirement`: The closure and construction specification is registered; a dedicated closure macro is still required for final visual proof.

### `wear_style`

- `competitor_visual_fact`: `c2-s3` presents three close-up styling states; `c1-s5` connects product size/color to facial placement.
- `inference`: Style variation is best shown through controlled close-up states that keep the product legible.
- `existing_strategy_requirement`: The three registered configurations and G23Studio styling direction define the approved styling set.

### `lifestyle_context`

- `competitor_visual_fact`: `c2-s4` uses a 2+1 portrait grid for clean, sparkle, and bold contexts.
- `inference`: Wider model scenes are useful after product identity and selection proof, because the product occupies less of the frame.
- `existing_strategy_requirement`: Model casting remains open, while styling and context constraints are supplied by the registered brand strategy.

### `value_packaging`

- `competitor_visual_fact`: `c1-s1`, `c2-s1`, and `c2-s2` organize benefit statements into repeated blocks or rows.
- `inference`: Benefits should be packaged as evidence-backed, scannable blocks rather than embedded in generated pixels.
- `existing_strategy_requirement`: Claims and numeric data resolve through the registered claim and product records; competitor comparisons remain disabled.

## Suggested Ordering

Default order for a full set:

1. `product_identity` (`P0`, main)
2. `contents` or `size_choice` (`P0`, secondary), selected by the largest known shopper blocker
3. `material_evidence` or `structure_use` (`P1`)
4. The remaining `P1` role
5. `wear_style`
6. `lifestyle_context` (storefront or late secondary)
7. `value_packaging` when approved claims are available

This ordering is a design default inferred from the competitor sequence, not a claim about conversion performance.
