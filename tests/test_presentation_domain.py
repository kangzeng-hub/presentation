import unittest

from presentation_domain.models import (
    AsyncStatus, CompetitorInsight, CompetitorSnapshot, EvidenceRef,
    FactKind, HumanReview, ListingPlan, PresentationStrategy, ProductTruth,
    VideoPlan,
)


class DomainTests(unittest.TestCase):
    def truth(self):
        return ProductTruth("p1", "SKU-1", "Demo", "jewelry", {}, {}, [], ["set"], ["hinge"], [{"kind": "CLAIM", "text": "safe", "source": "catalog"}], ["p1.jpg"], ["catalog"], 1)

    def test_product_truth_independent_and_claim_source(self):
        truth = self.truth()
        self.assertIs(truth.validate(), truth)
        invalid = self.truth(); invalid.verified_claims = [{"kind": FactKind.CLAIM.value, "text": "x"}]
        with self.assertRaises(ValueError): invalid.validate()

    def test_snapshot_preserves_raw_and_status(self):
        snapshot = CompetitorSnapshot("c1", "https://amazon.com/dp/X", raw_source={"raw": 1})
        self.assertIs(snapshot.validate(), snapshot); self.assertEqual(snapshot.raw_source["raw"], 1)
        snapshot.crawl_status = "unknown"
        with self.assertRaises(ValueError): snapshot.validate()

    def test_insight_requires_traceable_evidence(self):
        insight = CompetitorInsight("p1", [], ["pain"], [], [], [], ["gap"], ["gap"], [EvidenceRef("c1", "reviews")], .8)
        self.assertIs(insight.validate(), insight)
        insight.evidence = []
        with self.assertRaises(ValueError): insight.validate()

    def test_strategy_reusable_by_listing_and_video(self):
        strategy = PresentationStrategy("p1", ["safety"], [], ["hinge"], ["claim"], ["evidence"], ["safety"], {}, {}, {}, 1)
        self.assertIs(strategy.validate(), strategy)
        listing = ListingPlan("p1", 1, 1, 1, "Title", [], "Desc", [], ["strategy:p1:v1"], generated_content={"title": "Title"})
        video = VideoPlan("p1", 1, "demo", "buyers", 15, "hook", ["hinge"], [{"shot": 1}], "clean", "say", [], "prompt", strategy_refs=["strategy:p1:v1"])
        listing.validate(); video.validate()
        listing.validate_references(self.truth(), CompetitorInsight("p1", [], [], [], [], [], [], [], [EvidenceRef("c1", "title")], .5), strategy)
        with self.assertRaises(ValueError): listing.validate_references(None, None, strategy)

    def test_invalid_versions_and_states(self):
        project_status = AsyncStatus.COMPLETED.value
        self.assertEqual(project_status, "completed")
        listing = ListingPlan("p1", 0, 1, 1, "T", [], "D", [], ["s"], status="bad")
        with self.assertRaises(ValueError): listing.validate()
        review = HumanReview("p1", "image_01", "approved", version=1)
        self.assertIs(review.validate(), review)


if __name__ == "__main__": unittest.main()
