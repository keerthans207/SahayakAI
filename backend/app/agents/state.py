"""LangGraph agent state.

A TypedDict (with the ``add_messages`` reducer for the conversation history) is
the most stable way to define LangGraph state. Pydantic models are used for
the structured data carried within state (eligibility, application, profile).
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages

# Canonical intent labels routed by the graph.
Intent = str  # see prompts.py / intent.py for the fixed set of values

SUPPORTED_INTENTS = {
    "scheme_discovery",
    "eligibility_evaluation",
    "document_assistance",
    "application_guidance",
    "udid_otr_assistance",
    "employment_benefits",
    "assistive_device_benefits",
    "general_government_assistance",
}


class SahayakState(TypedDict, total=False):
    """State passed through every node of the Sahayak graph."""

    # Conversation history (reducer appends messages).
    messages: Annotated[list, add_messages]
    # Identity / session.
    user_id: str
    session_id: str
    # Language.
    preferred_language: str
    detected_language: str
    response_language: str
    # Profile snapshot used for routing & eligibility.
    user_profile: dict[str, Any]
    # Intent & scheme selection.
    current_intent: Intent
    selected_scheme: str
    discovered_scheme_ids: list[str]
    scheme_evaluations: list[dict[str, Any]]
    # Retrieved evidence.
    retrieved_documents: list[dict[str, Any]]
    official_sources: list[dict[str, Any]]
    # Eligibility & application.
    eligibility_result: dict[str, Any]
    missing_requirements: list[str]
    application_state: dict[str, Any]
    # Final response.
    response: str
    # Diagnostics.
    tool_calls: list[str]
    validation_flags: list[str]
