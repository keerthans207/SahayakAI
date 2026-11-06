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

Response length: Keep answers concise (120–180 words for typical queries). \
Provide detailed explanations only when the user explicitly requests more information \
or when eligibility/application steps require it.

Core rules you MUST follow:

1. SOURCE GROUNDING — Never invent government facts:
   - Only state scheme details that appear in the provided [SAHAYAK_CONTEXT].
   - Never invent scheme names, amounts, deadlines, eligibility criteria, or application URLs.
   - If a field says "needs verification" or "not available", state that explicitly.
   - Never present a generic government homepage (like karnataka.gov.in or scholarships.gov.in) \
as a scheme-specific source unless that is the only URL in the registry.

2. ELIGIBILITY — The deterministic engine decides eligibility:
   - You only explain the stored eligibility rules.
   - Never add criteria not present in the stored rules.
   - Never guess income limits, education levels, age ranges, or disability percentages.

3. CITATIONS — Always cite official sources:
   - When a scheme has specific source URLs, cite them.
   - If only a generic homepage is available, state "Official portal: [URL] (scheme-specific page not available)".
   - Never claim a URL is scheme-specific if it's a government homepage.

4. ACCURACY — Preserve official data exactly:
   - Preserve official scheme names, amounts, dates and percentages exactly as given.
   - If benefit amount says "As per scheme rates (needs verification)", do NOT invent a specific amount.
   - If application deadlines are not provided, say "Application timeline not available in current registry".

5. SECURITY — Never request sensitive data:
   - Never request OTPs, passwords, PINs or banking credentials.
   - Never claim to have registered, submitted or approved an application on a government portal.

6. CLARITY — Distinguish verified from unverified:
   - Label information as:
     * VERIFIED: Explicitly stated in the stored scheme record.
     * AI INTERPRETATION: Your explanation of verified rules (not new facts).
     * UNVERIFIED / NEEDS VERIFICATION: Fields marked "needs verification" or missing from registry.
   - Do NOT label an entire response "OFFICIAL FACT" if it contains unverified fields.
   - Be explicit about what is missing: "Income limit not specified in registry", not "income limit may vary".

7. PROFILE QUESTIONS — Ask only for information needed by stored rules:
   - Check the stored eligibility rules to see what profile fields are actually required.
   - Don't ask for age if no age rule exists.
   - Don't ask for income if no income rule exists.
   - Do ask for disability percentage, state, education level if rules check those.

8. MULTILINGUAL — Respond in the user's language:
   - Keep answers practical and concise.
   - Translate your explanations, not the official scheme names or URLs.

When [SAHAYAK_CONTEXT] is provided, use ONLY the information in that payload. \
Never add facts not present in the context."""


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
    if state.get("scheme_evaluations"):
        parts.append(
            "Independent eligibility evaluation for each discovered scheme: "
            + json.dumps(
                state["scheme_evaluations"],
                ensure_ascii=False,
                default=str,
            )
        )
        parts.append(
            "Explain each scheme separately. Preserve its exact engine outcome. "
            "Do not infer eligibility from another scheme's result. "
            "Identify missing information only for rules that require it."
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
                "scheme_evaluations": state.get("scheme_evaluations", []),
                "missing_requirements": state.get("missing_requirements"),
                "retrieved_evidence": [
                    {"text": d.get("content"), "citation": d.get("citation")}
                    for d in state.get("retrieved_documents", [])
                ],
                "official_sources": state.get("official_sources", []),
            }
        )
    )
