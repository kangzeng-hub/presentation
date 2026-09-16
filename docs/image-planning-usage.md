# Image Planning Usage

Build both the six-image plan and resolved template records from the repository inputs:

```bash
python3 -m image_planning image-plan \
  --catalog examples/demo_sku/catalog.json \
  --competitor-analysis examples/demo_sku/competitor-analysis.md \
  --registry templates/registry.json \
  --output output/image_plan.json \
  --resolved-output output/resolved_templates.json
```

The checked-in public demo plan is `examples/demo_sku/generated-fixtures/image_plan.json` and the command output above is a local runtime artifact. Every item contains a decision question, customer need, strategy reason, catalog-backed facts, catalog claim IDs, visual evidence, structured competitor gap, selected template, and forbidden elements.

`examples/demo_sku/generated-fixtures/resolved_templates.json` is the checked-in visual-structure artifact. It contains the registry-derived canvas, composition, hierarchy, required elements, allowed style elements, and forbidden elements. It is not a Wan prompt.
