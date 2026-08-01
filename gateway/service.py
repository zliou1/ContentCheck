from __future__ import annotations

from .context import LocalContextEngine
from .models import ScanResult
from .providers import ContentSafetyProvider, DemoContentSafetyProvider
from .risk import decide


def merge_results(*results: ScanResult) -> ScanResult:
    """Merge independent scanner outputs without discarding provider evidence."""
    return ScanResult(
        content_type=results[0].content_type,
        signals=tuple(signal for result in results for signal in result.signals),
        provider_results={key: value for result in results for key, value in result.provider_results.items()},
    )


class RiskGatewayService:
    def __init__(self, demo_mode: bool = False):
        self.content_safety = DemoContentSafetyProvider() if demo_mode else ContentSafetyProvider()
        self.context = LocalContextEngine()

    def scan_text(self, text: str, policy: dict, trace_id: str) -> dict:
        safety = self.content_safety.analyze_text(text, policy.get("azure_blocklists", []))
        context = self.context.analyze_text(text, policy)
        return decide(merge_results(safety, context), policy, trace_id).as_dict()

    def scan_image_base64(self, image_base64: str, policy: dict, trace_id: str) -> dict:
        scan = self.content_safety.analyze_image_base64(image_base64)
        return decide(scan, policy, trace_id).as_dict()

    def scan_demo_image(self, categories: list[str], policy: dict, trace_id: str) -> dict:
        scan = DemoContentSafetyProvider().analyze_image_categories(categories)
        return decide(scan, policy, trace_id).as_dict()
