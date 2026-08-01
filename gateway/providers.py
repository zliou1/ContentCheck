from __future__ import annotations

import os
from base64 import b64decode
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # Keeps the credential-free CLI demo runnable.
    def load_dotenv(*_args, **_kwargs):
        return False

from .models import CategorySignal, ScanResult

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)


class DemoContentSafetyProvider:
    """Deterministic local simulator for demonstrations only.

    It proves gateway composition and policy decisions without calling Azure.
    It must never be enabled in a production environment.
    """

    TEXT_TRIGGERS = {
        "violent attack": ("violence", 6),
        "kill them": ("violence", 6),
        "explicit sexual content": ("sexual_content", 6),
        "i hate all": ("hate_or_harassment", 4),
        "hurt myself": ("self_harm", 6),
    }

    def analyze_text(self, text: str, blocklist_names: list[str] | None = None) -> ScanResult:
        lowered = text.casefold()
        signals = tuple(
            CategorySignal(category, severity, "demo_content_safety")
            for phrase, (category, severity) in self.TEXT_TRIGGERS.items()
            if phrase in lowered
        )
        return ScanResult("text", signals, {"demo_content_safety": {"mode": "local_simulation", "categories": [s.__dict__ for s in signals]}})

    def analyze_image_categories(self, categories: list[str]) -> ScanResult:
        valid = {"hate_or_harassment", "self_harm", "sexual_content", "violence"}
        signals = tuple(CategorySignal(category, 6, "demo_content_safety") for category in categories if category in valid)
        return ScanResult("image", signals, {"demo_content_safety": {"mode": "local_simulation", "categories": [s.__dict__ for s in signals]}})


class ContentSafetyProvider:
    """Azure AI Content Safety adapter.

    Imports happen only after credentials are supplied, so local tests and API
    schema inspection do not require the Azure SDK to be installed.
    """

    def __init__(self, endpoint: str | None = None, key: str | None = None):
        self.endpoint = endpoint or os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")
        self.key = key or os.getenv("AZURE_CONTENT_SAFETY_KEY")

    def _client(self):
        if not self.endpoint or not self.key:
            raise RuntimeError("Azure AI Content Safety is not configured. Add endpoint and key values to the project's .env file.")
        if not self.endpoint.startswith("https://"):
            raise RuntimeError("AZURE_CONTENT_SAFETY_ENDPOINT must start with https://.")
        from azure.ai.contentsafety import ContentSafetyClient
        from azure.core.credentials import AzureKeyCredential

        return ContentSafetyClient(self.endpoint, AzureKeyCredential(self.key))

    @staticmethod
    def _signals(analysis: object) -> tuple[CategorySignal, ...]:
        categories = getattr(analysis, "categories_analysis", []) or []
        category_map = {
            "hate": "hate_or_harassment",
            "selfharm": "self_harm",
            "sexual": "sexual_content",
            "violence": "violence",
        }

        def normalized_category(category: object) -> str:
            # SDK versions may expose a plain string or an enum value.
            raw = str(getattr(category, "value", category)).lower().replace("_", "")
            return category_map.get(raw, raw)

        return tuple(
            CategorySignal(category=normalized_category(item.category), severity=int(item.severity))
            for item in categories
        )

    def analyze_text(self, text: str, blocklist_names: list[str] | None = None) -> ScanResult:
        from azure.ai.contentsafety.models import AnalyzeTextOptions
        from azure.core.exceptions import HttpResponseError

        try:
            result = self._client().analyze_text(
                AnalyzeTextOptions(text=text, blocklist_names=blocklist_names or [], halt_on_blocklist_hit=False)
            )
        except HttpResponseError as error:
            raise RuntimeError(f"Azure AI Content Safety text analysis failed ({error.status_code}). Check the resource, key, network access, and quota.") from error
        signals = self._signals(result)
        blocklist_matches = getattr(result, "blocklists_match", []) or []
        if blocklist_matches:
            signals += (CategorySignal("regional_blocklist_match", 6, "azure_ai_content_safety"),)
        return ScanResult(
            content_type="text",
            signals=signals,
            provider_results={"azure_ai_content_safety": {"categories": [signal.__dict__ for signal in signals], "blocklist_match_count": len(blocklist_matches)}},
        )

    def analyze_image_base64(self, image_base64: str) -> ScanResult:
        from azure.ai.contentsafety.models import AnalyzeImageOptions, ImageData
        from azure.core.exceptions import HttpResponseError

        try:
            image_bytes = b64decode(image_base64, validate=True)
        except ValueError as error:
            raise ValueError("image_base64 must be valid base64 data.") from error
        if not image_bytes:
            raise ValueError("image_base64 must not be empty.")

        try:
            result = self._client().analyze_image(AnalyzeImageOptions(image=ImageData(content=image_bytes)))
        except HttpResponseError as error:
            raise RuntimeError(f"Azure AI Content Safety image analysis failed ({error.status_code}). Check the resource, key, network access, and quota.") from error
        signals = self._signals(result)
        return ScanResult(
            content_type="image",
            signals=signals,
            provider_results={"azure_ai_content_safety": {"categories": [signal.__dict__ for signal in signals]}},
        )
