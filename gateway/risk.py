from __future__ import annotations

from .models import RiskDecision, ScanResult

# Azure AI Content Safety's standard categories are scored on a 0, 2, 4, 6 scale.
# We preserve that scale in provider_results and expose this product-level 0-100 score.
AZURE_MAX_SEVERITY = 6


def severity_to_risk_score(severity: int) -> int:
    """Convert a provider severity to the gateway's inclusive 0-100 scale."""
    bounded = max(0, min(AZURE_MAX_SEVERITY, severity))
    return round((bounded / AZURE_MAX_SEVERITY) * 100)


def decide(scan: ScanResult, policy: dict, trace_id: str) -> RiskDecision:
    """Apply one versioned policy to provider signals.

    The overall score is the highest normalized category severity. It represents
    risk intensity, while the policy determines whether that risk is allowed,
    reviewed, or blocked.
    """
    active_signals = [signal for signal in scan.signals if signal.severity > 0]
    highest_severity = max((signal.severity for signal in active_signals), default=0)
    score = severity_to_risk_score(highest_severity)
    categories = sorted({signal.category.lower() for signal in active_signals})

    hard_block_categories = {item.lower() for item in policy.get("hard_block_categories", [])}
    review_categories = {item.lower() for item in policy.get("review_categories", [])}
    block_threshold = int(policy.get("block_severity", AZURE_MAX_SEVERITY))
    review_threshold = int(policy.get("review_severity", 4))

    blocked = [signal for signal in active_signals if signal.category.lower() in hard_block_categories]
    threshold_blocked = [signal for signal in active_signals if signal.severity >= block_threshold]
    review = [signal for signal in active_signals if signal.category.lower() in review_categories]

    if blocked or threshold_blocked:
        decision = "block"
        reasons = list(dict.fromkeys(f"{signal.category} reached the block threshold." for signal in (blocked or threshold_blocked)))
    elif review or highest_severity >= review_threshold:
        decision = "review"
        reasons = list(dict.fromkeys(f"{signal.category} requires policy review." for signal in review)) or ["Severity reached the review threshold."]
    else:
        decision = "allow"
        reasons = ["No policy threshold was triggered."]

    return RiskDecision(
        trace_id=trace_id,
        decision=decision,
        risk_score=score,
        policy={"id": policy["policy_id"], "version": str(policy["version"])},
        categories=categories,
        reasons=reasons[:5],
        provider_results=scan.provider_results,
    )
