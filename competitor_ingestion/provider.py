"""Replaceable Amazon scraping provider; MVP implementation uses Apify."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Callable


class ProviderError(RuntimeError):
    pass


class AmazonScraperProvider(ABC):
    @abstractmethod
    def get_product(self, amazon_url: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def get_reviews(self, amazon_url: str) -> Any:
        raise NotImplementedError


class ApifyAmazonProvider(AmazonScraperProvider):
    """Run configurable Apify Actors and return their raw dataset JSON."""

    def __init__(self, token: str | None = None, *, product_actor: str | None = None, reviews_actor: str | None = None, timeout: int = 120, request_fn: Callable[..., Any] | None = None):
        env = _load_dotenv()
        self.token = token or os.getenv("APIFY_API_TOKEN") or env.get("APIFY_API_TOKEN")
        self.product_actor = product_actor or os.getenv("APIFY_PRODUCT_ACTOR") or env.get("APIFY_PRODUCT_ACTOR", "junglee/amazon-product-scraper")
        self.reviews_actor = reviews_actor or os.getenv("APIFY_REVIEWS_ACTOR") or env.get("APIFY_REVIEWS_ACTOR", "junglee/amazon-reviews-scraper")
        self.timeout = timeout
        self._request_fn = request_fn or urllib.request.urlopen

    def _run(self, actor: str, amazon_url: str) -> Any:
        if not self.token:
            raise ProviderError("APIFY_API_TOKEN is not configured")
        actor_path = urllib.parse.quote(actor, safe="")
        endpoint = f"https://api.apify.com/v2/acts/{actor_path}/run-sync-get-dataset-items?token={urllib.parse.quote(self.token)}"
        payload = {"startUrls": [{"url": amazon_url}], "productUrls": [amazon_url], "urls": [amazon_url]}
        request = urllib.request.Request(endpoint, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        try:
            response = self._request_fn(request, timeout=self.timeout)
            body = response.read() if hasattr(response, "read") else response
            if isinstance(body, bytes):
                body = body.decode("utf-8")
            if not body:
                return []
            return json.loads(body)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise ProviderError(f"Apify API request failed ({exc.code}): {detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ProviderError(f"Apify API request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ProviderError("Apify returned invalid JSON") from exc

    def get_product(self, amazon_url: str) -> Any:
        return self._run(self.product_actor, amazon_url)

    def get_reviews(self, amazon_url: str) -> Any:
        return self._run(self.reviews_actor, amazon_url)


def _load_dotenv() -> dict[str, str]:
    """Read a local .env without requiring python-dotenv as a runtime dependency."""
    values: dict[str, str] = {}
    for directory in (os.getcwd(), os.path.dirname(os.path.dirname(__file__))):
        path = os.path.join(directory, ".env")
        if not os.path.isfile(path):
            continue
        try:
            for line in open(path, encoding="utf-8"):
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values.setdefault(key.strip(), value.strip().strip("'\""))
        except OSError:
            pass
        break
    return values
