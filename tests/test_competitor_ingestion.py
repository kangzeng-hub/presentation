import json
import tempfile
import unittest
from pathlib import Path

from competitor_ingestion.cli import run_ingestion
from competitor_ingestion.models import CompetitorReview
from competitor_ingestion.normalize import detect_marketplace, extract_asin, normalize_product, normalize_reviews
from competitor_ingestion.provider import AmazonScraperProvider


class FakeProvider(AmazonScraperProvider):
    def get_product(self, amazon_url):
        return {
            "asin": "B0ABC12345", "title": "Demo product", "brand": "Demo",
            "price": "$19.99", "rating": "4.3", "reviewCount": "123",
            "bulletPoints": ["One", "Two"], "description": "Details",
            "images": [{"url": "https://images.example/a.jpg"}],
        }

    def get_reviews(self, amazon_url):
        return [
            {"rating": 1, "reviewTitle": "Bad", "reviewBody": "No", "verifiedPurchase": True},
            {"rating": 2, "title": "Two", "text": "Meh"},
            {"rating": 3, "title": "Three", "text": "Okay"},
            {"rating": 4, "title": "Good", "text": "Fine"},
        ]


class CompetitorIngestionTests(unittest.TestCase):
    def test_url_marketplace_parsing(self):
        url = "https://www.amazon.com/dp/B0ABC12345?tag=x"
        self.assertEqual(detect_marketplace(url), "amazon.com")

    def test_asin_extraction(self):
        url = "https://www.amazon.com/dp/B0ABC12345?tag=x"
        self.assertEqual(extract_asin(url), "B0ABC12345")
        self.assertEqual(extract_asin("https://amazon.co.uk/gp/product/B0ABC12345"), "B0ABC12345")

    def test_invalid_url(self):
        with self.assertRaises(ValueError):
            extract_asin("https://example.com/dp/B0ABC12345")

    def test_product_normalize(self):
        product = normalize_product({"title": "T", "price": "$12.50", "bulletPoints": "A\nB", "images": ["https://x"]}, asin="B0ABC12345", marketplace="amazon.com", captured_at="2026-01-01T00:00:00Z", provider="fake")
        self.assertEqual(product.price, 12.5)
        self.assertEqual(product.bullet_points, ["A", "B"])
        self.assertEqual(product.images, ["https://x"])

    def test_review_normalize_and_filter(self):
        reviews = normalize_reviews([{"rating": 1, "title": "a"}, {"rating": 3.0, "text": "c"}, {"rating": 5, "text": "ignore"}, {"rating": "bad"}])
        self.assertEqual([review.rating for review in reviews], [1, 3])
        self.assertTrue(all(isinstance(review, CompetitorReview) for review in reviews))

    def test_complete_smoke_and_files(self):
        with tempfile.TemporaryDirectory() as temp:
            product, directory, raw_product, raw_reviews = run_ingestion("https://www.amazon.com/dp/B0ABC12345", provider=FakeProvider(), output_root=temp, captured_at="2026-01-01T00:00:00Z")
            self.assertEqual(len(product.reviews), 3)
            self.assertEqual({review.rating for review in product.reviews}, {1, 2, 3})
            self.assertEqual(directory.name, "competitor_B0ABC12345")
            for name in ("raw_product.json", "raw_reviews.json", "competitor.json"):
                self.assertTrue((directory / name).exists())
            raw_saved = json.loads((directory / "raw_product.json").read_text())
            self.assertEqual(raw_saved["asin"], "B0ABC12345")
            self.assertEqual(raw_saved["_ingestion"]["provider"], "FakeProvider")
            saved = json.loads((directory / "competitor.json").read_text())
            self.assertEqual(saved["provider"], "FakeProvider")
            self.assertEqual(saved["asin"], "B0ABC12345")


if __name__ == "__main__":
    unittest.main()
