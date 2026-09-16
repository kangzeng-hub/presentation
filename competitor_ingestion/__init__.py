"""Minimal Amazon competitor data ingestion package."""

from .normalize import extract_asin, detect_marketplace, normalize_product, normalize_reviews
from .provider import AmazonScraperProvider, ApifyAmazonProvider

__all__ = [
    "AmazonScraperProvider",
    "ApifyAmazonProvider",
    "detect_marketplace",
    "extract_asin",
    "normalize_product",
    "normalize_reviews",
]
