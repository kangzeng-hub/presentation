"""URL parsing and tolerant normalization of scraper responses."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs, urlparse

from .models import CompetitorProduct, CompetitorReview

ASIN_RE = re.compile(r"\b([A-Z0-9]{10})\b", re.I)
AMAZON_HOST_RE = re.compile(r"(^|\.)amazon\.[a-z.]+$", re.I)


def detect_marketplace(amazon_url: str) -> str:
    parsed = urlparse(amazon_url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if not host or not AMAZON_HOST_RE.search(host):
        raise ValueError("URL must point to an Amazon marketplace")
    return host


def extract_asin(amazon_url: str) -> str:
    marketplace = detect_marketplace(amazon_url)
    parsed = urlparse(amazon_url)
    path = parsed.path
    patterns = (r"/(?:dp|gp/product|product)/([A-Z0-9]{10})(?:[/?]|$)", r"/ASIN/([A-Z0-9]{10})(?:[/?]|$)")
    for pattern in patterns:
        match = re.search(pattern, path, re.I)
        if match:
            return match.group(1).upper()
    for key in ("asin", "ASIN"):
        values = parse_qs(parsed.query).get(key, [])
        if values and ASIN_RE.fullmatch(values[0]):
            return values[0].upper()
    # Some scraper links contain a valid ASIN in a path segment.
    match = ASIN_RE.search(path)
    if match:
        return match.group(1).upper()
    raise ValueError(f"ASIN could not be extracted from Amazon URL ({marketplace})")


def captured_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _record(raw: Any) -> dict[str, Any]:
    if isinstance(raw, list):
        return next((item for item in raw if isinstance(item, dict)), {})
    return raw if isinstance(raw, dict) else {}


def _value(record: dict[str, Any], *names: str) -> Any:
    lowered = {str(key).lower(): value for key, value in record.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("text") or value.get("value") or value.get("name")
    text = str(value).strip()
    return text or None


def _number(value: Any, integer: bool = False) -> float | int | None:
    if value is None or isinstance(value, bool):
        return None
    match = re.search(r"[-+]?\d+(?:[.,]\d+)?", str(value).replace(",", ""))
    if not match:
        return None
    try:
        number = float(match.group(0))
        return int(number) if integer else number
    except ValueError:
        return None


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip(" -•\t") for line in re.split(r"\n+|\r+", value) if line.strip(" -•\t")]
    if isinstance(value, dict):
        value = value.get("text") or value.get("value") or value.get("items") or []
    if not isinstance(value, (list, tuple)):
        return [_text(value)] if _text(value) else []
    result = []
    for item in value:
        text = _text(item)
        if text:
            result.append(text)
    return result


def _images(value: Any) -> list[str]:
    values = value if isinstance(value, (list, tuple)) else [value]
    result = []
    for item in values:
        if isinstance(item, dict):
            item = item.get("url") or item.get("imageUrl") or item.get("src")
        if item and str(item).startswith(("http://", "https://")):
            result.append(str(item))
    return list(dict.fromkeys(result))


def normalize_product(raw: Any, *, asin: str, marketplace: str, captured_at: str, provider: str, reviews: list[CompetitorReview] | None = None) -> CompetitorProduct:
    record = _record(raw)
    nested = record.get("product") if isinstance(record.get("product"), dict) else {}
    merged = {**record, **nested}
    raw_asin = _text(_value(merged, "asin", "productAsin", "ASIN"))
    return CompetitorProduct(
        asin=(raw_asin or asin).upper(),
        marketplace=marketplace,
        captured_at=captured_at,
        provider=provider,
        title=_text(_value(merged, "title", "productTitle", "name")),
        brand=_text(_value(merged, "brand", "brandName")),
        price=_number(_value(merged, "price", "currentPrice", "priceValue", "priceAmount")),
        rating=_number(_value(merged, "rating", "stars", "averageRating")),
        review_count=_number(_value(merged, "reviewCount", "numberOfReviews", "reviewsCount", "totalReviews"), integer=True),
        bullet_points=_strings(_value(merged, "bulletPoints", "featureBullets", "bullets", "features")),
        description=_text(_value(merged, "productDescription", "description", "product_description")),
        images=_images(_value(merged, "imageUrls", "images", "productImages", "imageURLList", "imageUrlsList")),
        reviews=reviews or [],
    )


def _review_records(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        for key in ("reviews", "items", "data", "results"):
            if isinstance(raw.get(key), list):
                return [item for item in raw[key] if isinstance(item, dict)]
        return [raw]
    return []


def _bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    value = str(value).strip().lower()
    if value in {"true", "yes", "y", "verified", "1"}:
        return True
    if value in {"false", "no", "n", "unverified", "0"}:
        return False
    return None


def normalize_reviews(raw: Any) -> list[CompetitorReview]:
    result: list[CompetitorReview] = []
    for record in _review_records(raw):
        rating = _number(_value(record, "rating", "stars", "starRating", "reviewRating"), integer=True)
        if rating is None or not 1 <= rating <= 3:
            continue
        result.append(CompetitorReview(
            rating=rating,
            title=_text(_value(record, "title", "reviewTitle", "summary")),
            text=_text(_value(record, "text", "reviewBody", "body", "content")),
            date=_text(_value(record, "date", "reviewDate", "publishedAt")),
            verified=_bool(_value(record, "verified", "isVerifiedPurchase", "verifiedPurchase")),
        ))
    return result
