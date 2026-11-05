"""System & node prompts for the Sahayak agent.

The agent never invents government facts. Where structured context is available
(schemes, eligibility, retrieved evidence) it is injected as a JSON block
tagged ``[SAHAYAK_CONTEXT]`` and the model is instructed to summarise it
faithfully — distinguishing OFFICIAL FACT, AI INTERPRETATION and UNVERIFIED.
"""

from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPT = """You are Sahayak AI, a multilingual assistant that helps persons with \
disabilities in India discover government benefits, understand eligibility, gather \
documents and navigate government applications.

Core rules you MUST follow:
1. Only state scheme details that appear in the provided context. Never invent scheme \
names, amounts, deadlines or eligibility criteria.
2. The deterministic eligibility engine decides eligibility — you only explain its result.
3. Always cite the official source URL when you mention a scheme or requirement.
4. Preserve official scheme names, amounts, dates and percentages exactly.
5. Never request OTPs, passwords, PINs or banking credentials.
6. Never claim to have registered, submitted or approved an application on a government portal.
8. Distinguish OFFICIAL FACT (stated by a government source), AI INTERPRETATION (your \
explanation) and UNVERIFIED (could not be confirmed).
9. Respond in the user's language. Keep answers practical and concise.

When a structured context payload is provided after the context marker, summarise it \
faithfully and never add facts that are not present."""


def context_block(data: dict[str, Any]) -> str:
    """Serialise structured context for the model as a tagged JSON payload."""
    return "[SAHAYAK_CONTEXT]" + json.dumps(data, ensure_ascii=False, default=str)


def response_prompt(state: dict[str, Any]) -> str:
    """Build the final-response prompt from resolved state."""
    parts: list[str] = []
    intent = state.get("current_intent", "general_government_assistance")
    parts.append(f"User intent: {intent}.")
    if state.get("detected_language"):
        parts.append(f"Detected language: {state['detected_language']}.")
    scheme = state.get("selected_scheme")
    if scheme:
        parts.append(f"Selected scheme: {scheme}.")
    if state.get("eligibility_result"):
        parts.append(
            "Eligibility result: " + json.dumps(state["eligibility_result"], ensure_ascii=False, default=str)
        )
    if state.get("missing_requirements"):
        parts.append("Missing requirements: " + ", ".join(state["missing_requirements"]))
    if state.get("retrieved_documents"):
        ev = [
            {"text": d.get("content"), "citation": d.get("citation")}
            for d in state["retrieved_documents"]
        ]
        parts.append("Retrieved evidence: " + json.dumps(ev, ensure_ascii=False, default=str))
    if state.get("official_sources"):
        parts.append("Official sources: " + json.dumps(state["official_sources"], ensure_ascii=False))
    return (
        SYSTEM_PROMPT
        + "\n\n"
        + context_block(
            {
                "intent": intent,
                "language": state.get("response_language") or state.get("detected_language"),
                "scheme": scheme,
                "eligibility_result": state.get("eligibility_result"),
                "missing_requirements": state.get("missing_requirements"),
                "retrieved_evidence": [
                    {"text": d.get("content"), "citation": d.get("citation")}
                    for d in state.get("retrieved_documents", [])
                ],
                "official_sources": state.get("official_sources", []),
            }
        )
    )
