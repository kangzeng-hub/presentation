# Model Image Policy

## Principle

Model imagery is a layer selected by the consumer question. It does not replace product identity proof. Any template with a model must state whether the product is composited from a canonical asset or visually constrained by one, and must keep the product readable at the target display size.

## Policy Matrix

| policy_id | consumer_question | product_scale | crop | visual_priority | acceptable_generation_freedom | reference_policy |
|---|---|---|---|---|---|---|
| `NONE` | Can I inspect the product itself? | Dominant | No model | Product identity | None for human generation | `CANONICAL_PRODUCT` only if a model is absent |
| `PRODUCT_PROOF_MODEL` | What will the product look like and how large will it be on the body? | Large; product edge and opening must remain clear | Macro close-up; nose/ear/target anatomy | Product proof over expression | Low; anatomy, pose, skin, and lighting can vary within a controlled close-up | `CANONICAL_PRODUCT` for identity; `LAYOUT_REFERENCE` for panel geometry; optional `STYLE_REFERENCE` for light |
| `STYLE_MODEL` | Which styling direction can I imagine for myself? | Medium-large; still unmistakable | Half-face or controlled close-up | Product plus styling, in that order | Medium; makeup, wardrobe, and expression may vary; product geometry may not | `CANONICAL_PRODUCT` for identity; `STYLE_REFERENCE` for photographic language; `LAYOUT_REFERENCE` for triptych |
| `LIFESTYLE_MODEL` | Can I imagine wearing it in an everyday context? | Medium or small-medium, with a legibility floor | Full-face, portrait, or wider lifestyle | Context and self-projection, with product present | Higher for environment and pose; low for product shape, finish, placement, and count | `CANONICAL_PRODUCT` for identity; `STYLE_REFERENCE` for scene language; `LAYOUT_REFERENCE` for 2+1 grid |

## Non-Negotiable Rules

1. `PRODUCT_PROOF_MODEL` is mandatory for `size_choice`; do not substitute a distant lifestyle scene.
2. `STYLE_MODEL` is appropriate for `wear_style`; keep the subject close enough that the configuration can be identified.
3. `LIFESTYLE_MODEL` is appropriate for `lifestyle_context`; it may show more environment, but cannot be the only proof of product identity.
4. Model face, body, tattoos, makeup, clothing, and setting are not first-party product identity.
5. Competitor models can inform crop, pose, lighting, or information relationship only. They cannot be copied as an identity reference.
6. Generated humans must not invent extra product pieces, extra piercings, alternate closures, or unapproved configurations.
7. Product scale and anatomy relationship must be checked after compositing, not inferred from the prompt.

## QA by Model Layer

### `PRODUCT_PROOF_MODEL`

Check visible product outline, opening/closure state, placement, diameter comparison, sharpness, and natural contact with the body.

### `STYLE_MODEL`

Check that the intended style difference is visible, the product remains recognizable, the number of products/configurations is correct, and styling does not obscure the product.

### `LIFESTYLE_MODEL`

Check that the scene communicates the intended context, the product remains present and plausible, the image does not overclaim fit or performance, and the product is not reduced to an uninspectable speck.

