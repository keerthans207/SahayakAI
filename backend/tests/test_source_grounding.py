"""Test source grounding and response quality for scheme discovery.

Ensures the system never invents eligibility criteria, benefit amounts,
or presents generic homepages as scheme-specific sources.
"""

import json
import pytest

from app.agents.graph import discover_node
from app.agents.prompts import response_prompt, SYSTEM_PROMPT
from app.services.scheme_service import SchemeService
from langchain_core.messages import HumanMessage


class TestSourceGrounding:
    """Test that responses are strictly grounded in registry data."""

    def test_system_prompt_has_strong_grounding_rules(self):
        """Verify system prompt contains explicit source-grounding instructions."""
        prompt = SYSTEM_PROMPT
        
        # Check for key grounding phrases
        assert "Never invent" in prompt, "Missing 'Never invent' rule"
        assert "only state" in prompt.lower() or "only explain" in prompt.lower()
        assert "cite" in prompt.lower() or "source" in prompt.lower()
        
        # Check for distinction markers
        assert "VERIFIED" in prompt or "OFFICIAL FACT" in prompt
        assert "UNVERIFIED" in prompt or "needs verification" in prompt
        assert "AI INTERPRETATION" in prompt or "explanation" in prompt
        
        # Check for generic homepage warning
        assert "generic" in prompt.lower() or "homepage" in prompt.lower()
        
    def test_discover_node_includes_confidence_status(self):
        """Verify confidence_status is passed to LLM context."""
        state = {
            "messages": [HumanMessage(content="Karnataka scholarships")],
            "current_intent": "scheme_discovery",
            "user_profile": {"state": "Karnataka"},
        }
        
        result = discover_node(state)
        content = result["retrieved_documents"][0]["content"]
        schemes = json.loads(content)
        
        for scheme in schemes:
            assert "confidence_status" in scheme, \
                f"Missing confidence_status for {scheme['scheme_id']}"
            # Should be a valid status
            assert scheme["confidence_status"] in ["verified", "needs_verification", "unverified"]
            
    def test_schemes_with_generic_homepage_urls(self):
        """Identify schemes that only have generic government homepage URLs."""
        svc = SchemeService()
        
        generic_urls = [
            "https://karnataka.gov.in",
            "http://karnataka.gov.in",
            "https://scholarships.gov.in",
            "http://scholarships.gov.in",
            "https://india.gov.in",
            "https://depwd.gov.in",
            "http://depwd.gov.in",
        ]
        
        schemes_with_generic_urls = []
        
        for scheme in svc.schemes:
            sources = scheme.get("sources", [])
            if sources:
                for src in sources:
                    url = src.get("url", "")
                    if url in generic_urls:
                        schemes_with_generic_urls.append({
                            "scheme_id": scheme["scheme_id"],
                            "url": url,
                            "has_specific_url": any(
                                s.get("url", "") not in generic_urls 
                                for s in sources
                            )
                        })
        
        # Document which schemes have generic URLs
        print(f"\nSchemes with generic homepage URLs: {len(schemes_with_generic_urls)}")
        for item in schemes_with_generic_urls[:5]:
            status = "✓ (also has specific URL)" if item["has_specific_url"] else "⚠ (ONLY generic URL)"
            print(f"  - {item['scheme_id']}: {item['url']} {status}")
            
    def test_benefit_amounts_not_invented(self):
        """Verify benefit amounts are either specific or explicitly marked as needing verification."""
        svc = SchemeService()
        
        for scheme in svc.schemes:
            benefit_amt = scheme.get("benefit_amount", "")
            
            # If benefit amount exists, it should either be:
            # 1. A specific amount/range
            # 2. Explicitly state "needs verification" or "not available"
            if benefit_amt:
                # Should not be vague phrases like "varies" or "as applicable"
                vague_phrases = ["varies", "as applicable", "to be determined"]
                for phrase in vague_phrases:
                    assert phrase.lower() not in benefit_amt.lower(), \
                        f"{scheme['scheme_id']}: Vague benefit amount '{benefit_amt}'"
                        
                # If it says "needs verification", that's acceptable
                if "needs verification" in benefit_amt.lower():
                    # This is fine - explicitly stating uncertainty
                    pass
                elif "not available" in benefit_amt.lower() or "not specified" in benefit_amt.lower():
                    # Also fine - explicit about missing data
                    pass
                elif "n/a" in benefit_amt.lower() or "not applicable" in benefit_amt.lower():
                    # N/A is acceptable for non-monetary benefits like reservations
                    pass
                else:
                    # Should contain either numbers or "as per" with rates
                    has_numbers = any(char.isdigit() for char in benefit_amt)
                    has_rate_ref = "as per" in benefit_amt.lower() and "rate" in benefit_amt.lower()
                    
                    assert has_numbers or has_rate_ref, \
                        f"{scheme['scheme_id']}: Benefit amount should be specific or marked unverified: '{benefit_amt}'"
                        
    def test_eligibility_rules_completeness(self):
        """Verify eligibility rules don't have invented criteria."""
        svc = SchemeService()
        
        valid_rule_types = [
            "age", "disability", "income", "state", "district",
            "education", "employment", "gender", "caste",
            "documents", "prerequisites", "residency"
        ]
        
        for scheme in svc.schemes:
            rules = scheme.get("rules", [])
            for rule in rules:
                rule_type = rule.get("rule_type")
                assert rule_type in valid_rule_types, \
                    f"{scheme['scheme_id']}: Unknown rule_type '{rule_type}'"
                
                # Each rule should have a rule dict
                assert "rule" in rule, \
                    f"{scheme['scheme_id']}: Rule missing 'rule' dict"
                
                # Rule dict should not be empty
                assert rule["rule"], \
                    f"{scheme['scheme_id']}: Empty rule dict for {rule_type}"
                    
    def test_required_documents_are_listed(self):
        """Verify required documents are explicit, not generic."""
        svc = SchemeService()
        
        for scheme in svc.schemes:
            docs = scheme.get("required_documents", [])
            
            # If scheme has documents, they should be specific
            for doc in docs:
                # Should not be overly generic
                assert doc.lower() not in ["documents", "papers", "forms"], \
                    f"{scheme['scheme_id']}: Document too generic: '{doc}'"
                
                # Should be a non-empty string
                assert isinstance(doc, str) and len(doc) > 2, \
                    f"{scheme['scheme_id']}: Invalid document: '{doc}'"
                    
    def test_response_prompt_includes_confidence_status(self):
        """Verify response_prompt passes confidence_status to LLM."""
        state = {
            "current_intent": "scheme_discovery",
            "detected_language": "en",
            "response_language": "en",
            "selected_scheme": "karnataka_pwd_scholarship",
            "retrieved_documents": [{
                "content": json.dumps([{
                    "scheme_id": "karnataka_pwd_scholarship",
                    "confidence_status": "needs_verification",
                    "benefit_amount": "As per state rates (needs verification)",
                }], ensure_ascii=False),
                "citation": {}
            }],
        }
        
        prompt = response_prompt(state)
        
        # Confidence status should be in the context
        assert "needs_verification" in prompt
        
    def test_no_specific_amounts_when_registry_says_needs_verification(self):
        """Verify schemes with 'needs verification' don't invent specific amounts."""
        svc = SchemeService()
        
        for scheme in svc.schemes:
            confidence = scheme.get("confidence_status", "")
            benefit_amt = scheme.get("benefit_amount", "")
            
            if confidence == "needs_verification" and benefit_amt:
                # Should explicitly state uncertainty
                uncertain_markers = [
                    "needs verification",
                    "to be verified", 
                    "not specified",
                    "not available",
                    "verify"
                ]
                
                has_uncertain_marker = any(
                    marker in benefit_amt.lower() 
                    for marker in uncertain_markers
                )
                
                # If no uncertain marker, should at least say "as per" or "N/A" (not specific number)
                if not has_uncertain_marker:
                    is_na = "n/a" in benefit_amt.lower() or "not applicable" in benefit_amt.lower()
                    has_as_per = "as per" in benefit_amt.lower()
                    
                    assert is_na or has_as_per, \
                        f"{scheme['scheme_id']}: Unverified scheme has specific-looking amount: '{benefit_amt}'"
                        
    def test_missing_fields_are_explicit(self):
        """Verify missing optional fields are None or empty, not invented."""
        svc = SchemeService()
        
        optional_fields = [
            "application_start_date",
            "application_deadline", 
            "benefit_frequency",
            "applicable_district",
        ]
        
        for scheme in svc.schemes:
            for field in optional_fields:
                value = scheme.get(field)
                
                # If field is present, should not be placeholder text
                if value:
                    placeholder_text = [
                        "to be announced",
                        "check portal",
                        "varies",
                        "not applicable"
                    ]
                    for placeholder in placeholder_text:
                        if isinstance(value, str):
                            assert placeholder not in value.lower(), \
                                f"{scheme['scheme_id']}: Placeholder in {field}: '{value}'"
                                
    def test_all_five_scholarship_schemes_have_complete_data(self):
        """Verify the five main scholarship schemes have required fields."""
        svc = SchemeService()
        
        scholarship_ids = [
            "karnataka_pwd_scholarship",
            "pm_pre_matric_pwd",
            "pm_post_matric_pwd",
            "pm_top_class_pwd",
            "national_fellowship_pwd",
        ]
        
        required_fields = [
            "official_name",
            "description",
            "category",
            "government_level",
            "rules",
            "sources",
            "required_documents",
        ]
        
        for scheme_id in scholarship_ids:
            scheme = svc.get_scheme(scheme_id)
            assert scheme is not None, f"Scholarship {scheme_id} not found"
            
            for field in required_fields:
                assert field in scheme, f"{scheme_id}: Missing {field}"
                value = scheme[field]
                
                # Check not empty
                if isinstance(value, str):
                    assert len(value) >= 4, f"{scheme_id}: {field} too short: '{value}'"
                elif isinstance(value, list):
                    assert len(value) > 0, f"{scheme_id}: {field} is empty list"
                    
    def test_sources_have_required_fields(self):
        """Verify all sources have title and URL."""
        svc = SchemeService()
        
        for scheme in svc.schemes:
            sources = scheme.get("sources", [])
            for i, src in enumerate(sources):
                assert "url" in src, \
                    f"{scheme['scheme_id']}: Source {i} missing URL"
                assert "title" in src or "publisher" in src, \
                    f"{scheme['scheme_id']}: Source {i} missing title/publisher"
                
                # URL should be valid-looking
                url = src["url"]
                assert url.startswith("http://") or url.startswith("https://"), \
                    f"{scheme['scheme_id']}: Invalid URL: {url}"


class TestResponseQuality:
    """Test that generated responses follow grounding rules."""
    
    def test_prompt_warns_against_generic_urls(self):
        """Verify system prompt explicitly warns about generic homepage URLs."""
        prompt = SYSTEM_PROMPT
        
        # Should mention generic homepages
        assert "generic" in prompt.lower() or "homepage" in prompt.lower()
        
        # Should mention specific examples
        assert "karnataka.gov.in" in prompt or "scholarships.gov.in" in prompt
        
    def test_prompt_requires_profile_info_based_on_rules(self):
        """Verify system prompt says to ask only for info needed by stored rules."""
        prompt = SYSTEM_PROMPT
        
        # Should instruct to check stored rules
        assert "stored rules" in prompt.lower() or "eligibility rules" in prompt.lower()
        
        # Should say don't ask for info not in rules
        assert "only" in prompt.lower() and ("ask" in prompt.lower() or "request" in prompt.lower())
