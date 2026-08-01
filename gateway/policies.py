from __future__ import annotations

from pathlib import Path

try:  # The runnable demo deliberately works without optional packages.
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised in dependency-free demo environments
    yaml = None


POLICY_DIRECTORY = Path(__file__).resolve().parent.parent / "policies"

BUILTIN_POLICIES = {
    "eu": {
        "policy_id": "eu", "version": "0.1.0", "review_severity": 4, "block_severity": 6,
        "hard_block_categories": ["child_sexual_content", "credible_violent_threat", "doxxing_or_personal_data_exposure", "regional_blocklist_match"],
        "azure_blocklists": [],
        "review_categories": ["hate_or_harassment", "sexual_content", "self_harm", "violence", "illegal_activity", "cultural_or_religious_sensitivity", "jailbreak_or_prompt_injection", "personal_data_exposure"],
        "cultural_review_terms": ["sacred site vandalism", "宗教场所破坏"],
    },
    "us-child-safety": {
        "policy_id": "us-child-safety", "version": "0.1.0", "review_severity": 4, "block_severity": 6,
        "hard_block_categories": ["child_sexual_content", "sexual_content_in_child_experience", "credible_violent_threat", "doxxing_or_personal_data_exposure", "regional_blocklist_match"],
        "azure_blocklists": [],
        "review_categories": ["hate_or_harassment", "self_harm", "violence", "illegal_activity", "jailbreak_or_prompt_injection", "personal_data_exposure"],
        "cultural_review_terms": ["sacred site vandalism"],
    },
    "conservative-market-baseline": {
        "policy_id": "conservative-market-baseline", "version": "0.1.0", "review_severity": 4, "block_severity": 6,
        "hard_block_categories": ["child_sexual_content", "credible_violent_threat", "doxxing_or_personal_data_exposure", "regional_blocklist_match"],
        "azure_blocklists": [],
        "review_categories": ["sexual_content", "hate_or_harassment", "self_harm", "violence", "illegal_activity", "cultural_or_religious_sensitivity", "jailbreak_or_prompt_injection", "personal_data_exposure"],
        "cultural_review_terms": ["sacred site vandalism", "public insult to religion"],
    },
}


def load_policy(policy_id: str) -> dict:
    """Load a trusted server-selected regional policy by its public identifier."""
    if yaml is not None:
        for policy_file in POLICY_DIRECTORY.glob("*.yaml"):
            policy = yaml.safe_load(policy_file.read_text(encoding="utf-8"))
            if policy.get("policy_id") == policy_id:
                return policy
    if policy_id in BUILTIN_POLICIES:
        return BUILTIN_POLICIES[policy_id]
    raise ValueError(f"Unknown policy: {policy_id}")
