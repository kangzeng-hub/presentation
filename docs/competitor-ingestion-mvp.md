# Amazon Competitor Data Ingestion MVP

Configure `APIFY_API_TOKEN` in `.env` (or the shell), then run:

```bash
python app.py "https://www.amazon.com/dp/B0XXXXXXXX"
```

The command calls the configurable Apify product and review Actors, keeps only
1–3 star reviews, and writes:

```text
output/competitor_<ASIN>/
├── raw_product.json
├── raw_reviews.json
└── competitor.json
```

`competitor.json` is provider-independent and includes `asin`, `marketplace`,
`captured_at`, `provider`, the requested listing fields, and normalized reviews.
The raw files retain the provider response plus an `_ingestion` provenance
object. Override Actors with `APIFY_PRODUCT_ACTOR` and
`APIFY_REVIEWS_ACTOR` when needed.
