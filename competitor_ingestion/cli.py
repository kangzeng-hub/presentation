from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from .models import CompetitorProduct
from .normalize import captured_now, detect_marketplace, extract_asin, normalize_product, normalize_reviews
from .provider import AmazonScraperProvider, ApifyAmazonProvider
from .storage import save_json, save_run


class IngestionError(RuntimeError):
    pass


def _fetched_count(raw_reviews: Any) -> int:
    if isinstance(raw_reviews, list):
        return len(raw_reviews)
    if isinstance(raw_reviews, dict):
        for key in ("reviews", "items", "data", "results"):
            if isinstance(raw_reviews.get(key), list):
                return len(raw_reviews[key])
    return 0


def run_ingestion(amazon_url: str, *, provider: AmazonScraperProvider | None = None, output_root: str | Path = "output", captured_at: str | None = None) -> tuple[CompetitorProduct, Path, dict[str, Any], Any]:
    try:
        asin = extract_asin(amazon_url)
        marketplace = detect_marketplace(amazon_url)
    except ValueError as exc:
        raise IngestionError(str(exc)) from exc
    provider = provider or ApifyAmazonProvider()
    provider_name = provider.__class__.__name__
    captured_at = captured_at or captured_now()
    try:
        raw_product = provider.get_product(amazon_url)
    except Exception as exc:
        raise IngestionError(str(exc)) from exc
    if raw_product is None or raw_product == {} or raw_product == []:
        # Keep an audit artifact even when the product response is empty.
        directory = Path(output_root) / f"competitor_{asin}"
        save_json(directory / "raw_product.json", {
            "data": raw_product,
            "_ingestion": {
                "captured_at": captured_at,
                "provider": provider_name,
                "asin": asin,
                "marketplace": marketplace,
            },
        })
        raise IngestionError("Product data is empty")
    try:
        raw_reviews = provider.get_reviews(amazon_url)
    except Exception as exc:
        raise IngestionError(str(exc)) from exc
    reviews = normalize_reviews(raw_reviews)
    product = normalize_product(raw_product, asin=asin, marketplace=marketplace, captured_at=captured_at, provider=provider_name, reviews=reviews)
    directory = save_run(output_root, asin, raw_product, raw_reviews, product)
    return product, directory, raw_product, raw_reviews


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Amazon Competitor Data Ingestion MVP")
    parser.add_argument("url", help="Amazon product URL")
    parser.add_argument("--output", default="output", help="Output root directory (default: output)")
    args = parser.parse_args(argv)
    print("Amazon Competitor MVP\n---------------------\n")
    print(f"URL: {args.url}")
    try:
        asin = extract_asin(args.url)
        print(f"ASIN: {asin}\n")
        product, directory, _, raw_reviews = run_ingestion(args.url, output_root=args.output)
    except (IngestionError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    missing = [name for name in ("title", "brand", "price", "rating", "review_count", "description") if getattr(product, name) is None]
    print("Product: OK")
    print(f"Title: {'OK' if product.title else 'missing'}")
    print(f"Bullet Points: {len(product.bullet_points)}")
    print(f"Images: {len(product.images)}")
    fetched = _fetched_count(raw_reviews)
    print(f"Reviews fetched: {fetched}")
    print(f"Low-rating reviews kept: {len(product.reviews)}")
    if missing:
        print(f"[WARN] Fields unavailable: {', '.join(missing)}")
    if not product.reviews:
        print("[WARN] No 1-3 star reviews returned")
    print(f"\nOutput:\n{directory}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
