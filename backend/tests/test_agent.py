"""Agent / LangGraph workflow tests."""

from __future__ import annotations

import pytest

from app.agents.factory import SahayakAgent, reset_agent
from app.agents.intent import classify_intent


def test_intent_classification():
    assert classify_intent("find scholarships for me") == "scheme_discovery"
    assert classify_intent("am I eligible for the pension?") == "eligibility_evaluation"
    assert classify_intent("what documents do I need?") == "document_assistance"
    assert classify_intent("how do I apply?") == "application_guidance"
    assert classify_intent("I need help with UDID") == "udid_otr_assistance"
    assert classify_intent("find government jobs for PwD") == "employment_benefits"
    assert classify_intent("I need a wheelchair") == "assistive_device_benefits"
    assert classify_intent("hello") == "general_government_assistance"


@pytest.fixture
def agent():
    reset_agent()
    return SahayakAgent()


async def test_agent_scheme_discovery(agent):
    res = await agent.run(
        user_message="I am a B.Tech student from Karnataka with 60% disability. Find scholarships.",
        user_profile={"state": "Karnataka", "disability_percentage": 60, "education_level": "undergraduate"},
    )
    assert res["current_intent"] == "scheme_discovery"
    assert res["selected_scheme"]  # a scheme was selected
    assert res["response"]
    assert "scheme_search" in res["tool_calls"]


async def test_agent_eligibility_evaluation(agent):
    res = await agent.run(
        user_message="Am I eligible for pm_post_matric_pwd? I have 60% disability.",
        user_profile={"disability_percentage": 60, "scheme_id": "pm_post_matric_pwd"},
    )
    assert res["current_intent"] == "eligibility_evaluation"
    assert res["selected_scheme"] == "pm_post_matric_pwd"
    assert res["eligibility_result"]["outcome"] in (
        "likely_eligible", "potentially_eligible", "insufficient_information", "not_eligible",
    )


async def test_agent_document_assistance(agent):
    res = await agent.run(
        user_message="What documents do I need for pm_post_matric_pwd?",
        user_profile={"selected_scheme": "pm_post_matric_pwd"},
    )
    assert res["current_intent"] == "document_assistance"
    assert "document_checklist" in res["tool_calls"]
    assert res["missing_requirements"] is not None


async def test_agent_udid_otr_guidance(agent):
    res = await agent.run(
        user_message="I have UDID but no NSP OTR, help me",
        user_profile={"udid_status": "has_udid", "otr_status": "no_otr"},
    )
    assert res["current_intent"] == "udid_otr_assistance"
    assert any("scholarships.gov.in" in s.get("url", "") for s in res["official_sources"])


async def test_agent_employment_benefits(agent):
    res = await agent.run(
        user_message="Find government employment opportunities for PwD applicants",
        user_profile={"state": "Karnataka"},
    )
    assert res["current_intent"] == "employment_benefits"
    # Employment routes into the discover node with employment category.
    assert "scheme_search" in res["tool_calls"]


async def test_agent_assistive_device(agent):
    res = await agent.run(
        user_message="Which assistive device schemes are available to me?",
        user_profile={},
    )
    assert res["current_intent"] == "assistive_device_benefits"
    assert "scheme_search" in res["tool_calls"]


async def test_agent_language_retained(agent):
    res = await agent.run(
        user_message="ನನಗೆ ವಿದ್ಯಾರ್ಥಿವೇತನ ಬೇಕು",
        user_profile={},
    )
    assert res["detected_language"] == "kn"
    assert res["response_language"] == "kn"


async def test_agent_conversation_context_preserved(agent):
    history = [
        {"role": "user", "content": "I am from Karnataka"},
        {"role": "assistant", "content": "Noted, you are from Karnataka."},
    ]
    res = await agent.run(
        user_message="Find scholarships",
        user_profile={"state": "Karnataka"},
        history=history,
    )
    # History is carried; messages should include the prior turns.
    assert len(res["messages"]) >= 3


async def test_agent_no_unnecessary_tool_calls_general(agent):
    res = await agent.run(user_message="hello there", user_profile={})
    # General greeting should not fabricate scheme details.
    assert res["current_intent"] == "general_government_assistance"
    # When live search is off, no official documents are returned for a bare greeting.
    assert res.get("selected_scheme") in ("", None) or not res.get("retrieved_documents")


async def test_agent_no_hallucinated_scheme_ids(agent):
    res = await agent.run(user_message="find schemes", user_profile={})
    # Any scheme referenced must exist in the registry.
    from app.services.scheme_service import SchemeService

    registry_ids = {s["scheme_id"] for s in SchemeService().schemes}
    selected = res.get("selected_scheme")
    if selected:
        assert selected in registry_ids


async def test_agent_tool_error_handled(agent):
    # Unknown scheme id in eligibility path should not crash the graph.
    res = await agent.run(
        user_message="am I eligible for unknown_scheme_xyz?",
        user_profile={"disability_percentage": 50},
    )
    assert res["current_intent"] == "eligibility_evaluation"
    # Graph must still produce a response.
    assert res["response"]


async def test_agent_e2e_case_no_income_certificate(agent):
    res = await agent.run(
        user_message="I don't have an income certificate, what do I do?",
        user_profile={"selected_scheme": "pm_post_matric_pwd"},
    )
    assert res["current_intent"] in ("document_assistance", "general_government_assistance")
    assert res["response"]
