"""Sahayak LangGraph workflow.

Explicit graph implementing the required pipeline:

START -> detect_language -> classify_intent -> load_profile -> route_request
  -> (scheme_discovery | eligibility | documents | application | udid_otr |
      employment | assistive_device | general)
  -> retrieve_evidence -> validate_information -> generate_response -> END

Tool selection is deterministic Python routing (not LLM tool-calling), so the
workflow is fully reproducible with the MOCK model and never makes unnecessary
tool calls. The LLM only explains results; it never alters eligibility.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.agents.intent import category_for_intent, classify_intent
from app.agents.model_factory import get_chat_model
from app.agents.prompts import SYSTEM_PROMPT, response_prompt
from app.agents.state import SahayakState
from app.services.eligibility_engine import EligibilityRule, ProfileSnapshot, SchemeMeta, evaluate
from app.services.retrieval_service import RetrievalService
from app.services.scheme_service import SchemeService
from app.services.search_service import get_search_provider
from app.services.language_service import detect_language, resolve_response_language
from app.utils.content_normalizer import normalize_content


# --------------------------------------------------------------------------- #
# Nodes
# --------------------------------------------------------------------------- #
def detect_language_node(state: SahayakState) -> dict[str, Any]:
    last = _last_user_text(state)
    preferred = state.get("preferred_language")
    detected = detect_language(last, preferred)
    response_lang = resolve_response_language(
        detected.language, preferred, requested=None
    )
    return {
        "detected_language": detected.language,
        "response_language": response_lang,
        "validation_flags": [],
        "tool_calls": [],
    }


def classify_intent_node(state: SahayakState) -> dict[str, Any]:
    last = _last_user_text(state)
    intent = classify_intent(last)
    return {"current_intent": intent}


def load_profile_node(state: SahayakState) -> dict[str, Any]:
    # Profile is injected by the caller (from DB / request). Ensure it exists.
    profile = state.get("user_profile") or {}
    return {"user_profile": profile}


def route_request(state: SahayakState) -> str:
    """Conditional-edge router returning the node name for the current intent."""
    intent = state.get("current_intent", "general_government_assistance")
    mapping = {
        "scheme_discovery": "discover",
        "eligibility_evaluation": "evaluate",
        "document_assistance": "documents",
        "application_guidance": "application",
        "udid_otr_assistance": "udid_otr",
        "employment_benefits": "discover",
        "assistive_device_benefits": "discover",
        "general_government_assistance": "general",
    }
    return mapping.get(intent, "general")


# ---- intent handler nodes -------------------------------------------------- #
def discover_node(state: SahayakState) -> dict[str, Any]:
    last = _last_user_text(state)
    category = category_for_intent(state.get("current_intent", ""))
    profile = state.get("user_profile") or {}
    svc = SchemeService()
    # Prefer state filter from profile when present.
    state_filter = profile.get("state")
    items, total = svc.search(last or "", category=category, state=state_filter, page=1, page_size=10)
    
    # Include complete scheme details for LLM context: description, benefits, rules, sources
    schemes = [
        {
            "scheme_id": s["scheme_id"],
            "official_name": s["official_name"],
            "description": s.get("description", ""),
            "category": s["category"],
            "department": s.get("department"),
            "government_level": s["government_level"],
            "applicable_state": s.get("applicable_state"),
            "benefit_description": s.get("benefit_description"),
            "benefit_amount": s.get("benefit_amount"),
            "benefit_frequency": s.get("benefit_frequency"),
            "required_documents": s.get("required_documents", []),
            "prerequisite_services": s.get("prerequisite_services", []),
            "application_url": s.get("application_url"),
            "scheme_status": s.get("scheme_status"),
            "confidence_status": s.get("confidence_status"),
            "rules": s.get("rules", []),
            "sources": s.get("sources", []),
        }
        for s in items
    ]
    
    sources: list[dict[str, Any]] = []
    for s in items:
        for src in s.get("sources", []):
            sources.append({"title": src.get("title"), "url": src.get("url"), "publisher": src.get("publisher")})
    return {
        "retrieved_documents": [{"content": json.dumps(schemes, ensure_ascii=False), "citation": {}}],
        "official_sources": _dedupe_sources(sources),
        "selected_scheme": schemes[0]["scheme_id"] if schemes else "",
        "tool_calls": ["scheme_search"],
    }


def evaluate_node(state: SahayakState) -> dict[str, Any]:
    profile = state.get("user_profile") or {}
    scheme_id = state.get("selected_scheme")
    if not scheme_id:
        # Try to infer a scheme from the last message (scheme id mention).
        last = _last_user_text(state).lower()
        svc = SchemeService()
        for s in svc.schemes:
            if s["scheme_id"] in last:
                scheme_id = s["scheme_id"]
                break
    if not scheme_id:
        return {
            "eligibility_result": {"outcome": "insufficient_information"},
            "missing_requirements": ["scheme_id or sufficient profile to evaluate"],
            "tool_calls": ["eligibility"],
            "validation_flags": ["no_scheme_selected"],
        }
    svc = SchemeService()
    scheme = svc.get_scheme(scheme_id)
    if not scheme:
        return {"eligibility_result": {"outcome": "not_eligible", "error": f"unknown scheme {scheme_id}"}}
    rules = [EligibilityRule(**r) for r in scheme.get("rules", [])]
    snap = ProfileSnapshot(**{k: v for k, v in profile.items() if k in ProfileSnapshot.model_fields})
    meta = SchemeMeta(
        scheme_id=scheme["scheme_id"],
        official_name=scheme["official_name"],
        scheme_status=scheme.get("scheme_status", "active"),
        confidence_status=scheme.get("confidence_status", "needs_verification"),
    )
    result = evaluate(rules, snap, meta)
    sources = scheme.get("sources", [])
    return {
        "selected_scheme": scheme_id,
        "eligibility_result": result.to_dict(),
        "missing_requirements": result.missing_documents + result.missing_prerequisites + result.missing_information,
        "official_sources": _dedupe_sources(sources),
        "tool_calls": ["eligibility"],
    }


def documents_node(state: SahayakState) -> dict[str, Any]:
    scheme_id = state.get("selected_scheme") or _infer_scheme(state)
    if not scheme_id:
        return {
            "missing_requirements": ["Select a scheme first to see its document checklist."],
            "tool_calls": ["document_checklist"],
        }
    svc = SchemeService()
    scheme = svc.get_scheme(scheme_id)
    if not scheme:
        return {"missing_requirements": [f"Unknown scheme: {scheme_id}"]}
    available = (state.get("user_profile") or {}).get("available_documents", [])
    required = scheme.get("required_documents", [])
    available_lower = {d.lower() for d in available}
    missing = [d for d in required if d.lower() not in available_lower]
    return {
        "selected_scheme": scheme_id,
        "missing_requirements": missing,
        "retrieved_documents": [
            {
                "content": f"Required documents for {scheme['official_name']}: " + ", ".join(required),
                "citation": {"title": scheme["official_name"], "url": scheme.get("application_url")},
            }
        ],
        "official_sources": _dedupe_sources(scheme.get("sources", [])),
        "tool_calls": ["document_checklist", "missing_documents"],
    }


def application_node(state: SahayakState) -> dict[str, Any]:
    from app.services.application_service import ApplicationService

    scheme_id = state.get("selected_scheme") or _infer_scheme(state)
    if not scheme_id:
        return {"application_state": {"step": "select_scheme"}, "tool_calls": ["application_checklist"]}
    svc = ApplicationService()
    checklist = svc.build_checklist(scheme_id, state.get("user_id", "dev-user"))
    return {
        "selected_scheme": scheme_id,
        "application_state": {
            "checklist": checklist,
            "stage": "discovered",
            "application_url": checklist.get("application_url"),
        },
        "official_sources": _dedupe_sources(
            SchemeService().get_scheme(scheme_id).get("sources", []) if SchemeService().get_scheme(scheme_id) else []
        ),
        "tool_calls": ["application_checklist"],
    }


def udid_otr_node(state: SahayakState) -> dict[str, Any]:
    last = _last_user_text(state).lower()
    profile = state.get("user_profile") or {}
    guidance: list[str] = []
    if "otr" in last or "ot r" in last:
        guidance.append(
            "NSP One-Time Registration (OTR) is a prerequisite for National Scholarship "
            "Portal (NSP) scholarships. You create it once on scholarships.gov.in using "
            "your Aadhaar and mobile number. Forgotten OTR can be recovered on the portal."
        )
        if (profile.get("otr_status") or "").lower() in ("no_otr", "unknown", "", None):
            guidance.append("Your OTR status is not yet confirmed — register on the official NSP portal.")
    if "udid" in last or "disability certificate" in last:
        guidance.append(
            "UDID (Unique Disability ID) is issued via swavlambancard.gov.in after medical "
            "assessment. It is not mandatory for every scheme, but many require a disability "
            "certificate at minimum."
        )
        if (profile.get("udid_status") or "").lower() in ("no_udid", "unknown", "", None):
            guidance.append("Your UDID status is not yet confirmed — apply on the official UDID portal.")
    if not guidance:
        guidance.append(
            "I can guide you on UDID registration and NSP OTR. I will never request OTPs and "
            "never register on your behalf — authentication must happen on the official portal."
        )
    return {
        "retrieved_documents": [
            {
                "content": "\n".join(guidance),
                "citation": {"title": "UDID / OTR guidance", "url": "https://swavlambancard.gov.in"},
            }
        ],
        "official_sources": [
            {"title": "UDID portal", "url": "https://swavlambancard.gov.in", "publisher": "DEPwD"},
            {"title": "National Scholarship Portal", "url": "https://scholarships.gov.in", "publisher": "Government of India"},
        ],
        "tool_calls": ["udid_otr_guidance"],
    }


def general_node(state: SahayakState) -> dict[str, Any]:
    last = _last_user_text(state)
    provider = get_search_provider()
    if not provider.is_available():
        return {
            "retrieved_documents": [],
            "official_sources": [],
            "validation_flags": ["live_search_unavailable"],
            "tool_calls": ["government_search"],
        }
    results = provider.search(last, max_results=3)
    return {
        "retrieved_documents": [
            {"content": r.get("excerpt"), "citation": {"title": r.get("title"), "url": r.get("url")}}
            for r in results
        ],
        "official_sources": [
            {"title": r.get("title"), "url": r.get("url"), "publisher": r.get("publisher")}
            for r in results
            if r.get("official")
        ],
        "tool_calls": ["government_search"],
    }


# ---- evidence + validation + response ------------------------------------- #
def retrieve_evidence_node(state: SahayakState) -> dict[str, Any]:
    try:
        rs = RetrievalService()
    except Exception:  # noqa: BLE001 - store unavailable
        return {}
    if not rs.is_available():
        return {}
    query = _last_user_text(state)
    scheme_id = state.get("selected_scheme")
    evidence = rs.retrieve(query, k=3) if not scheme_id else rs.retrieve_for_scheme(query, scheme_id, k=3)
    docs = [
        {"content": e.text, "citation": e.citation()}
        for e in evidence
        if e.official  # only cite official sources as evidence
    ]
    existing = list(state.get("retrieved_documents", []))
    existing.extend(docs)
    return {"retrieved_documents": existing}


def validate_information_node(state: SahayakState) -> dict[str, Any]:
    flags = list(state.get("validation_flags", []))
    # Flag confidence on any scheme advice surfaced.
    if state.get("selected_scheme"):
        svc = SchemeService()
        scheme = svc.get_scheme(state["selected_scheme"])
        if scheme and scheme.get("confidence_status") == "needs_verification":
            flags.append("scheme_details_need_verification")
    if not state.get("retrieved_documents") and state.get("current_intent") in ("scheme_discovery",):
        flags.append("advising_from_registry_only")
    return {"validation_flags": flags}


async def generate_response_node(state: SahayakState) -> dict[str, Any]:
    model = get_chat_model()
    prompt = response_prompt(state)
    messages: list = [SystemMessage(content=prompt)]
    # Include a trimmed history for context (last 6 messages).
    history = list(state.get("messages", []))[-6:]
    messages.extend(history)
    if not messages or not any(isinstance(m, HumanMessage) for m in messages[-3:]):
        # Ensure there is at least one human turn for models that expect it.
        messages.append(HumanMessage(content=_last_user_text(state) or "Hello"))
    chunks: list[str] = []
    try:
        # Stream actual model chunks so LangGraph emits
        # on_chat_model_stream events to the agent stream.
        async for ai_chunk in model.astream(messages):
            chunk_text = normalize_content(
                getattr(ai_chunk, "content", "")
            )
            if chunk_text:
                chunks.append(chunk_text)

        content = "".join(chunks) if chunks else _fallback_response(state)

    except Exception:  # noqa: BLE001
        # Do not silently replace a partially streamed answer.
        if chunks:
            raise
        content = _fallback_response(state)
    return {"response": content, "messages": [AIMessage(content=content)]}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _last_user_text(state: SahayakState) -> str:
    for m in reversed(state.get("messages", [])):
        if getattr(m, "type", "") == "human":
            return m.content if isinstance(m.content, str) else str(m.content)
    return ""


def _infer_scheme(state: SahayakState) -> str | None:
    last = _last_user_text(state).lower()
    svc = SchemeService()
    for s in svc.schemes:
        if s["scheme_id"] in last or s["official_name"].lower() in last:
            return s["scheme_id"]
    return None


def _dedupe_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for s in sources:
        url = (s or {}).get("url") or ""
        if url in seen:
            continue
        seen.add(url)
        out.append(s)
    return out


def _fallback_response(state: SahayakState) -> str:
    intent = state.get("current_intent", "general_government_assistance")
    docs = state.get("retrieved_documents", [])
    if docs:
        first = docs[0]
        return first.get("content") or "I could not generate a model response."
    if state.get("eligibility_result"):
        return (
            f"Eligibility outcome: {state['eligibility_result'].get('outcome', 'unknown')}. "
            "See the eligibility breakdown for details."
        )
    return f"I can help with {intent.replace('_', ' ')}. Please share more details or pick a scheme."


# --------------------------------------------------------------------------- #
# Graph builder
# --------------------------------------------------------------------------- #
def build_graph():
    """Compile and return the Sahayak LangGraph workflow."""
    builder = StateGraph(SahayakState)
    builder.add_node("detect_language", detect_language_node)
    builder.add_node("classify_intent", classify_intent_node)
    builder.add_node("load_profile", load_profile_node)
    builder.add_node("discover", discover_node)
    builder.add_node("evaluate", evaluate_node)
    builder.add_node("documents", documents_node)
    builder.add_node("application", application_node)
    builder.add_node("udid_otr", udid_otr_node)
    builder.add_node("general", general_node)
    builder.add_node("retrieve_evidence", retrieve_evidence_node)
    builder.add_node("validate_information", validate_information_node)
    builder.add_node("generate_response", generate_response_node)

    builder.add_edge(START, "detect_language")
    builder.add_edge("detect_language", "classify_intent")
    builder.add_edge("classify_intent", "load_profile")
    builder.add_conditional_edges(
        "load_profile",
        route_request,
        {
            "discover": "discover",
            "evaluate": "evaluate",
            "documents": "documents",
            "application": "application",
            "udid_otr": "udid_otr",
            "general": "general",
        },
    )
    # All intent handlers converge to retrieval -> validation -> response.
    for n in ("discover", "evaluate", "documents", "application", "udid_otr", "general"):
        builder.add_edge(n, "retrieve_evidence")
    builder.add_edge("retrieve_evidence", "validate_information")
    builder.add_edge("validate_information", "generate_response")
    builder.add_edge("generate_response", END)
    return builder.compile()


# Module-level compiled graph (lazily built).
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
