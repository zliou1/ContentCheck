from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CategorySignal:
    """A normalized harmful-content signal returned by a provider."""

    category: str
    severity: int
    source: str = "azure_ai_content_safety"


@dataclass(frozen=True)
class ScanResult:
    content_type: str
    signals: tuple[CategorySignal, ...]
    provider_results: dict[str, Any]


@dataclass(frozen=True)
class RiskDecision:
    trace_id: str
    decision: str
    risk_score: int
    policy: dict[str, str]
    categories: list[str]
    reasons: list[str]
    provider_results: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
