"""Test scheme registry → AI context integration.

Verifies that scheme details, rules, benefits, and sources are retrieved
and passed to the LLM context when a user queries for schemes.
"""

import json
import pytest

from app.agents.graph import discover_node
from app.services.scheme_service import SchemeService


class TestSchemeIntegration:
    """Test that scheme registry data flows through to AI context."""

    def test_karnataka_pwd_scholarship_exists_in_registry(self):
        """Verify karnataka_pwd_scholarship is loaded from data files."""
        svc = SchemeService()
        scheme = svc.get_scheme("karnataka_pwd_scholarship")

        assert scheme is not None, "karnataka_pwd_scholarship not found in registry"
        assert scheme["official_name"] == "Karnataka Scholarships for Differently Abled Students"
        assert scheme["category"] == "education"
        assert scheme["government_level"] == "state"
        assert scheme["applicable_state"] == "Karnataka"

    def test_karnataka_pwd_scholarship_has_complete_data(self):
        """Verify the scheme has description, rules, benefits, and sources."""
        svc = SchemeService()
        scheme = svc.get_scheme("karnataka_pwd_scholarship")

        assert scheme is not None

        # Description
        assert "description" in scheme
        assert len(scheme["description"]) > 50, "Description too short or missing"

        # Benefit details
        assert "benefit_description" in scheme
        assert "benefit_amount" in scheme

        # Rules
        assert "rules" in scheme
        assert len(scheme["rules"]) > 0, "No eligibility rules defined"

        # At least one rule should be for disability
        rule_types = [r["rule_type"] for r in scheme["rules"]]
        assert "disability" in rule_types, "Missing disability rule"

        # Sources
        assert "sources" in scheme
        assert len(scheme["sources"]) > 0, "No official sources defined"
        assert any("karnataka.gov.in" in src.get("url", "") for src in scheme["sources"])

        # Required documents
        assert "required_documents" in scheme
        assert len(scheme["required_documents"]) > 0

    def test_discover_node_includes_scheme_details_in_context(self):
        """Test that discover_node retrieves full scheme details for LLM context."""
        # Simulate a state where user asks about Karnataka scholarships
        state = {
            "messages": [],
            "current_intent": "scheme_discovery",
            "user_profile": {"state": "Karnataka"},
        }

        # Mock a user message about Karnataka scholarships
        from langchain_core.messages import HumanMessage
        state["messages"] = [
            HumanMessage(content="Find scholarships for students with disabilities in Karnataka")
        ]

        result = discover_node(state)

        # Check that schemes were found
        assert "retrieved_documents" in result
        assert len(result["retrieved_documents"]) > 0

        # Check that karnataka_pwd_scholarship is included
        import json
        content = result["retrieved_documents"][0]["content"]
        schemes = json.loads(content)

        scheme_ids = [s["scheme_id"] for s in schemes]
        assert "karnataka_pwd_scholarship" in scheme_ids, \
            "karnataka_pwd_scholarship not found in discover results"

    def test_discover_node_scheme_context_has_required_fields(self):
        """Test that discovered schemes include description, rules, and sources."""
        state = {
            "messages": [],
            "current_intent": "scheme_discovery",
            "user_profile": {"state": "Karnataka"},
        }

        from langchain_core.messages import HumanMessage
        state["messages"] = [
            HumanMessage(content="Karnataka scholarships for students with disabilities")
        ]

        result = discover_node(state)

        import json
        content = result["retrieved_documents"][0]["content"]
        schemes = json.loads(content)

        # Find karnataka_pwd_scholarship
        target_scheme = None
        for s in schemes:
            if s["scheme_id"] == "karnataka_pwd_scholarship":
                target_scheme = s
                break

        assert target_scheme is not None, "karnataka_pwd_scholarship not found in context"

        # Verify critical fields are included for LLM to have complete context
        assert "official_name" in target_scheme
        assert "scheme_id" in target_scheme

        # These fields are REQUIRED for proper AI context
        assert "description" in target_scheme, "Description not in context"
        assert len(target_scheme["description"]) > 50, "Description too short"

        assert "benefit_description" in target_scheme, "Benefit description not in context"
        assert target_scheme["benefit_description"], "Benefit description empty"

        assert "rules" in target_scheme, "Rules not in context"
        assert len(target_scheme["rules"]) > 0, "No rules in context"

        assert "sources" in target_scheme, "Sources not in context (for citations)"
        assert len(target_scheme["sources"]) > 0, "No sources in context"

        assert "required_documents" in target_scheme, "Required documents not in context"
        assert len(target_scheme["required_documents"]) > 0, "No documents in context"

        # Verify rule structure
        for rule in target_scheme["rules"]:
            assert "rule_type" in rule, "Rule missing rule_type"
            assert "rule" in rule, "Rule missing rule dict"

        # Verify source structure
        for src in target_scheme["sources"]:
            assert "url" in src, "Source missing URL"

    def test_search_finds_karnataka_pwd_scholarship(self):
        """Test that scheme search correctly finds the Karnataka scholarship."""
        svc = SchemeService()

        # Test various search terms
        test_queries = [
            "Karnataka scholarship",
            "disability scholarship Karnataka",
            "karnataka pwd scholarship",
            "students disabilities Karnataka",
        ]

        for query in test_queries:
            items, total = svc.search(
                query,
                category="education",
                state="Karnataka",
                page=1,
                page_size=10
            )

            scheme_ids = [s["scheme_id"] for s in items]
            assert "karnataka_pwd_scholarship" in scheme_ids, \
                f"Search query '{query}' did not find karnataka_pwd_scholarship"

    def test_scheme_rules_retrievable(self):
        """Test that scheme rules can be retrieved for eligibility evaluation."""
        svc = SchemeService()
        rules = svc.get_rules("karnataka_pwd_scholarship")

        assert len(rules) > 0, "No rules found for karnataka_pwd_scholarship"

        # Verify rule structure
        for rule in rules:
            assert "rule_type" in rule
            assert "rule" in rule

        # Check for expected rule types
        rule_types = [r["rule_type"] for r in rules]
        expected_types = ["disability", "state", "education", "documents"]
        for expected in expected_types:
            assert expected in rule_types, f"Missing {expected} rule"

    def test_scheme_sources_retrievable(self):
        """Test that official sources can be retrieved for citation."""
        svc = SchemeService()
        sources = svc.get_sources("karnataka_pwd_scholarship")

        assert len(sources) > 0, "No sources found for karnataka_pwd_scholarship"

        # Verify source structure
        for src in sources:
            assert "url" in src
            assert "title" in src or "publisher" in src

    def test_response_prompt_includes_scheme_rules_and_sources(self):
        """Test that response_prompt includes scheme details in SAHAYAK_CONTEXT."""
        from app.agents.prompts import response_prompt

        # Simulate state after discover_node with karnataka_pwd_scholarship
        state = {
            "current_intent": "scheme_discovery",
            "detected_language": "en",
            "response_language": "en",
            "selected_scheme": "karnataka_pwd_scholarship",
            "retrieved_documents": [{
                "content": json.dumps([{
                    "scheme_id": "karnataka_pwd_scholarship",
                    "official_name": "Karnataka Scholarships for Differently Abled Students",
                    "description": "State scholarships for students with disabilities...",
                    "rules": [
                        {"rule_type": "disability", "rule": {"min_percentage": 40}},
                        {"rule_type": "state", "rule": {"eq": "Karnataka"}},
                    ],
                    "sources": [
                        {"title": "Government of Karnataka", "url": "https://karnataka.gov.in"}
                    ],
                    "required_documents": ["disability_certificate", "income_certificate"],
                }], ensure_ascii=False),
                "citation": {}
            }],
            "official_sources": [
                {"title": "Government of Karnataka", "url": "https://karnataka.gov.in"}
            ],
        }

        prompt = response_prompt(state)

        # Verify the prompt includes SAHAYAK_CONTEXT marker
        assert "[SAHAYAK_CONTEXT]" in prompt, "Missing context marker"

        # Verify critical scheme details are in the prompt
        assert "karnataka_pwd_scholarship" in prompt
        assert "Karnataka Scholarships for Differently Abled Students" in prompt
        assert "disability" in prompt  # rule type should be present
        assert "karnataka.gov.in" in prompt  # source URL should be present

        # Verify the grounding rules are in the prompt
        assert "Never invent" in prompt or "Only state scheme details" in prompt
        assert "official source" in prompt.lower() or "cite" in prompt.lower()
