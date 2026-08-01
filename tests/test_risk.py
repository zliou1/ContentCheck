from gateway.models import CategorySignal, ScanResult
from gateway.risk import decide, severity_to_risk_score


POLICY = {
    "policy_id": "test",
    "version": "0.1.0",
    "hard_block_categories": [],
    "review_categories": ["hate", "sexual"],
    "review_severity": 4,
    "block_severity": 6,
}


def result(*signals: CategorySignal) -> ScanResult:
    return ScanResult("text", signals, {"azure_ai_content_safety": {}})


def test_severity_is_normalized_to_product_score():
    assert severity_to_risk_score(0) == 0
    assert severity_to_risk_score(4) == 67
    assert severity_to_risk_score(6) == 100


def test_low_signal_is_allowed():
    decision = decide(result(CategorySignal("hate_or_harassment", 2)), POLICY, "trace-1")
    assert decision.decision == "allow"
    assert decision.risk_score == 33


def test_review_signal_is_reviewed():
    decision = decide(result(CategorySignal("hate_or_harassment", 4)), POLICY, "trace-2")
    assert decision.decision == "review"
    assert decision.categories == ["hate_or_harassment"]


def test_maximum_signal_is_blocked():
    decision = decide(result(CategorySignal("Violence", 6)), POLICY, "trace-3")
    assert decision.decision == "block"
    assert decision.risk_score == 100
