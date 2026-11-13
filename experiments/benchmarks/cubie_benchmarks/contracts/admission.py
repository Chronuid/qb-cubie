"""Validate documented human approvals independently of executable checks."""

from cubie_benchmarks.contracts import _validation as v


def validate_admission(root, scenario, reference):
    """Require distinct, traceable approvals for independent admission."""
    reviews = reference.get("human_reviews")
    v.require(type(reviews) is list, "human_reviews", "expected a list")
    if reference["validation_status"] != "independently_checked":
        return
    identities = [_approval(root, scenario, review) for review in reviews]
    v.require(len(identities) >= 2 and len(set(identities)) == len(identities),
              "human_reviews", "two distinct independent approvals are required")


def _approval(root, scenario, review):
    """Bind an approval to an identity and private evidence within the scenario."""
    v.mapping(review, "human_reviews")
    identity = v.text(review.get("reviewer_id"), "human_reviews.reviewer_id").strip().casefold()
    v.choice(review.get("decision"), {"approve"}, "human_reviews.decision")
    evidence = v.contained(root, review.get("evidence"), "human_reviews.evidence")
    v.require(not evidence.is_relative_to((root / scenario["visible"]).resolve()),
              "human_reviews.evidence", "approval evidence must stay outside visible material")
    v.text(evidence.read_text(encoding="utf-8"), "human_reviews.evidence")
    return identity
