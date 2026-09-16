# Image Planning Usage

Build both the six-image plan and resolved template records from the repository inputs:

```bash
python3 -m image_planning image-plan \
  --catalog data/first_party_catalog.json \
  --competitor-analysis docs/competitor-visual-analysis.md \
  --registry templates/registry.json \
  --output image_plan.json \
  --resolved-output resolved_templates.json
```

`image_plan.json` is the strategy-facing artifact. Every item contains a decision question, customer need, strategy reason, catalog-backed facts, catalog claim IDs, visual evidence, structured competitor gap, selected template, and forbidden elements.

`resolved_templates.json` is the visual-structure artifact. It contains the registry-derived canvas, composition, hierarchy, required elements, allowed style elements, and forbidden elements. It is not a Wan prompt.

