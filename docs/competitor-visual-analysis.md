# Competitor Visual Analysis

## Scope and Evidence Labels

This analysis covers the only visual assets found in the repository at scan time:

- `c1/`: six images from competitor set 1.
- `c2/`: six images from competitor set 2.
- First-party product assets and the approved brand/product inputs are now registered in `data/first_party_catalog.json`; no existing first-party Listing image set or prior optimization analysis was supplied.

Every conclusion is tagged:

- `competitor_visual_fact`: directly observable in an image.
- `inference`: a design implication inferred from the observed image.
- `existing_strategy_requirement`: a dependency that must be confirmed by the approved first-party strategy or product data before rendering.

The competitor images are used as evidence for composition, hierarchy, photography language, information density, and human/product relationship only. They are not product identity references.

## Asset Inventory

| image_id | competitor_id | main_or_secondary | visual_subject | product_visibility | human_presence | camera_distance | crop | product_scale | composition | information_density | text_presence | information_blocks | background | lighting | props | visual_purpose | likely_consumer_question | confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `c1-m1` | `c1` | main | Three gold hoop variants plus a small nostril inset | High; three products are isolated and readable | Partial body close-up in inset | Product close-up with small macro inset | Mostly full product views, diagonal placements | Large, dominant | Three-product diagonal spread with lower-left proof inset | Low | None | Product variants; worn proof | White | Bright, shadow-controlled | None | Product identification and assortment cue | What does the set look like? | High |
| `c1-s1` | `c1` | secondary | Gold hoops resting on a hand, with inset comparison | High | Hand only | Macro/close | Hand fills frame; inset crop | Medium-large | Hand as scale/material surface, inset comparison | Medium-high | Yes | Material claim; size marker; comparison inset; worn detail | Warm peach tabletop/skin | Soft warm commercial light | Hand; inset panel | Material, size, and comparison proof | What size/material details am I buying? | High |
| `c1-s2` | `c1` | secondary | Four nostril close-ups showing 7, 8, 9, and 10 mm | High enough to compare circumference | Half-face/nose close-up | Macro close-up | Four equal quadrants | Medium | Repeated 2x2 comparison grid | Medium | Yes | Four size labels; recommendation sentence | Neutral skin and tattoo detail | Soft diffuse light | None | Size choice | Which diameter fits the look I want? | High |
| `c1-s3` | `c1` | secondary | Nickel release test report over product/water imagery | Medium; product is partly behind the document | No | Document-focused, flat composition | Full canvas with central report | Small-medium | Evidence document layered over decorative product background | High | Yes | Test title; method; result table; pass callout; sample photo | White document over blue water/product imagery | Flat document light plus decorative water highlights | Report; magnifier icon; water | Material trust and test evidence | Is the material claim supported by evidence? | High |
| `c1-s4` | `c1` | secondary | Model holding a hoop near the nose plus closure diagrams | Medium | Full-face/upper torso, face on right | Medium shot with diagram overlay | Model cropped at torso; central information panel | Small-medium | Lifestyle image used as backdrop, two-column comparison panel on top | High | Yes | Headline; subtitle; ours/others labels; two diagram rows | Neutral indoor/lifestyle scene plus pale panel | Soft natural light | Tool/hand; diagrams | Closure usability and retention comparison | How does it open, close, and stay on? | High |
| `c1-s5` | `c1` | secondary | Smiling pierced face with multiple colored placement examples | Medium | Full-face close-up | Medium close-up | Face centered with edge examples | Small-medium | Face as canvas, labels distributed around anatomy | High | Yes | Size guide title; body-placement labels; color/size callouts | Colorful but blurred background | Warm beauty light with colored accents | Multiple sample colors; typography | Placement and size education | Where can I wear it and what sizes apply? | High |
| `c2-m1` | `c2` | main | Three silver hoop variants plus a nostril inset | High; three products isolated and readable | Partial body close-up in inset | Product close-up with small macro inset | Full product views, upper inset | Large, dominant | Three-product diagonal spread with upper proof inset | Low | None | Product variants; worn proof | White | Bright, shadow-controlled | None | Product identification and assortment cue | What does the set look like? | High |
| `c2-s1` | `c2` | secondary | Silver product trio on warm surface with benefit list | High | No | Product close-up | Full vertical poster | Medium-large | Header, product row, then four stacked benefit blocks | High | Yes | Material; skin-friendliness; weight; finish | Warm off-white surface | Soft directional shadow | Shield, heart, feather, sparkle icons | Benefit packaging and material positioning | Why is this suitable for everyday wear? | High |
| `c2-s2` | `c2` | secondary | Ours/others comparison with product panels and five-row claim list | Medium-high | No | Product/graphic composite | Two-column comparison | Medium | Symmetric comparison cards with repeated rows | High | Yes | Comparison labels; five feature rows | Warm off-white | Soft graphic shadows | Product panels; comparison mark | Competitive differentiation and objection handling | What is better about this option? | High |
| `c2-s3` | `c2` | secondary | Three nostril close-ups for clean, sparkle, and layered looks | High | Partial face/nose close-up | Macro close-up | Three equal vertical panels | Medium-large | Triptych with one look per panel and short descriptors | Medium | Yes | Three look names; one-line descriptions; closing statement | Warm neutral skin/background | Soft beauty light | None | Style self-projection | How will the set look in different styling modes? | High |
| `c2-s4` | `c2` | secondary/storefront | Three model portraits for clean, sparkle, and bold styling | Medium | Full-face/half-body lifestyle | Medium to medium-wide | Two small top panels and one wide bottom panel | Small-medium | 2+1 editorial grid with labels over image | Medium | Yes | Three style labels; supporting sentence | Home/urban lifestyle interiors | Natural window light; darker ambient scene in bold panel | Clothing; hand/pose | Lifestyle aspiration and context | Can I wear this across occasions and aesthetics? | High |
| `c2-s5` | `c2` | secondary | Four product macro/detail panels: closure, rounded edge, double hoop, stone detail | Very high | No | Macro close-up | Equal 2x2 detail grid | Large | Four evidence cells with numbered captions | High | Yes | Four numbered features; short explanations | Warm neutral studio surface | Soft directional macro light | None | Construction and comfort proof | What physical details support comfort and use? | High |

## Cross-Set Findings

### Main image

- `competitor_visual_fact`: Both `c1-m1` and `c2-m1` use a clean white field, three separated product presentations, and a small worn-product inset.
- `inference`: The primary scan task is product-family recognition plus a minimal reality cue. The worn inset is secondary evidence, not the identity source.
- `existing_strategy_requirement`: The final main-image arrangement uses `asset_p1_gold_3pcs` and the approved three-style set registered in `data/first_party_catalog.json`.

### Secondary-image sequence

- `competitor_visual_fact`: Both sets repeat a sequence of product/benefit proof, size or style selection, construction detail, and model context.
- `inference`: A reusable system should organize images around consumer questions rather than around a fixed `1 + 5` count.
- `inference`: Size and product-proof images belong early because they answer a selection question with direct visual evidence. Lifestyle images can be later because they support projection after identity and fit are understood.
- `existing_strategy_requirement`: P0/P1/P2 ordering is reconciled against the registered sizes, claims, evidence notes, and G23Studio visual strategy.

### Information density

- `competitor_visual_fact`: The main images are low-density and text-free; secondary images range from a three-panel style grid to document-heavy proof and five-row comparisons.
- `inference`: Text is useful when it organizes a decision, but should be programmatically typeset for exactness. Image generation should not author measurements, test results, material grades, or competitive claims.

### Model/product relationship

- `competitor_visual_fact`: Model imagery appears at three scales: nose/ear macro proof (`c1-s2`, `c2-s3`), face-led style (`c1-s5`, `c2-s4`), and a wider lifestyle backdrop (`c1-s4`, `c2-s4`).
- `inference`: “Model image” is a layer policy selected by task, not a standalone image type.
- `inference`: Product-proof model images should prioritize product edge, closure, and size readability over facial expression.

### Risky elements to exclude by default

- `competitor_visual_fact`: Competitor images include competitor names, logos, “ours/others” claims, specific material grades, test documents, and exact size/placement statements.
- `inference`: These elements can be reused only as abstract information patterns. They must be deleted or replaced with approved first-party data.
- `existing_strategy_requirement`: Any comparison, test result, skin-safety statement, or material label requires a source record from the first-party strategy/product evidence set.

## Reference Conversion Matrix

| competitor image(s) | direct reference? | extract | converted artifact | remove/replace |
|---|---|---|---|---|
| `c1-m1`, `c2-m1` | No as a product reference; yes as a layout cue | Product grouping, white field, small worn-proof inset, diagonal spacing | `PRODUCT_IDENTITY_MAIN` layout blueprint; optional `STYLE_REFERENCE` for neutral studio light | All competitor products, logo/brand, exact color/shape, inset anatomy if not approved |
| `c1-s1`, `c2-s1` | No as product or claim reference; limited layout/style reference | Hand/surface as scale context; header-to-product-to-benefit hierarchy; soft warm studio light | `CONTENTS_SET` or `VALUE_PACKAGING` information/layout blueprint | Material grade, “hypoallergenic” or skin claims, icons, competitor typography |
| `c1-s2`, `c2-s3` | No as product reference; yes as layout and subject-relationship reference | Repeated equal panels, macro crop, one-size/one-look per cell | `SIZE_CHOICE_PROOF` or `WEAR_STYLE_TRIPTYCH` template reference | Competitor nose, tattoos, exact sizes/labels, product geometry |
| `c1-s3`, `c2-s5` | No as product reference; yes as information/layout reference | Evidence-first document overlay; 2x2 detail grid; numbered captions | `MATERIAL_EVIDENCE` and `STRUCTURE_USE` blueprints | Test report identity, unverified result, competitor product details, decorative claims |
| `c1-s4`, `c2-s2` | No as product or comparison truth; limited layout reference | Backdrop plus panel, comparison rows, centered evidence region | `STRUCTURE_USE` or `VALUE_PACKAGING` blueprint | “Ours/others” identity, negative competitor claims, competitor model, logo |
| `c1-s5`, `c2-s4` | No as product/model identity; limited style reference | Anatomy labels, 2+1 lifestyle grid, look labels, natural-light portrait language | `LIFESTYLE_MOMENTS` and `WEAR_STYLE_MODEL` blueprints | Competitor face/body, exact styling, brand text, unapproved placement claims |

## Decision

The usable transformation is:

`competitor image -> abstract layout/style/information/relationship evidence -> first-party template blueprint -> renderer-specific asset composition`

No competitor image is registered as `CANONICAL_PRODUCT`. Canonical identity is now supplied by `asset_p1_gold_3pcs`; the asset remains limited to the Gold-3PCS horizontal composite and does not prove worn scale or certification.
