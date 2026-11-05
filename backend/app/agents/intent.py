"""Deterministic intent classification.

Keyword + rule based so behaviour is reproducible and testable without an LLM.
The LLM may refine intent in the future, but the default classifier never
depends on a network call. Returns one of the canonical intents in
``state.SUPPORTED_INTENTS``.
"""

from __future__ import annotations

from app.agents.state import SUPPORTED_INTENTS

# Ordered by specificity — earlier rules win on overlap.
_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "udid_otr_assistance",
        ("udid", "otr", "one time registration", "disability certificate", "swavlamban"),
    ),
    ("eligibility_evaluation", ("eligib", "qualify", "am i eligible", "can i get", "do i qualify")),
    ("document_assistance", ("document", "certificate", "what do i need", "papers", "proof")),
    (
        "assistive_device_benefits",
        ("wheelchair", "hearing aid", "prosthetic", "orthotic", "assistive", "mobility", "device"),
    ),
    (
        "employment_benefits",
        ("job", "employment", "recruitment", "vacancy", "skill development", "vocational", "apprentice", "reservation"),
    ),
    ("application_guidance", ("apply", "application", "how to register", "process", "form", "submit")),
    (
        "scheme_discovery",
        ("scholarship", "scheme", "benefit", "pension", "concession", "find", "available", "schemes for", "keli financial help"),
    ),
    ("general_government_assistance", ("government", "sarkari", "office", "department", "how to")),
]


def classify_intent(text: str) -> str:
    """Return the most specific intent matching ``text``."""
    if not text:
        return "general_government_assistance"
    lower = text.lower()
    for intent, keywords in _RULES:
        if any(kw in lower for kw in keywords):
            return intent if intent in SUPPORTED_INTENTS else "general_government_assistance"
    return "general_government_assistance"


# Map intents to scheme categories for discovery routing.
INTENT_CATEGORY_MAP = {
    "scheme_discovery": None,  # broad
    "employment_benefits": "employment",
    "assistive_device_benefits": "assistive_technology",
}


def category_for_intent(intent: str) -> str | None:
    return INTENT_CATEGORY_MAP.get(intent)
