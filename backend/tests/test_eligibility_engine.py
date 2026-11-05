"""Deterministic eligibility engine tests."""

from __future__ import annotations

import pytest

from app.services.eligibility_engine import (
    EligibilityRule,
    ProfileSnapshot,
    SchemeMeta,
    evaluate,
)


SCHEME = {"scheme_id": "test", "official_name": "Test Scheme", "scheme_status": "active", "confidence_status": "verified"}


def _eval(rules, profile):
    return evaluate([EligibilityRule(**r) for r in rules], profile, SCHEME)


def test_disability_threshold_satisfied():
    r = _eval([{"rule_type": "disability", "rule": {"min_percentage": 40}}],
              {"disability_percentage": 60})
    assert r.outcome == "likely_eligible"


def test_disability_threshold_not_met():
    r = _eval([{"rule_type": "disability", "rule": {"min_percentage": 40}}],
              {"disability_percentage": 30})
    assert r.outcome == "not_eligible"
    assert any(rr.rule_type == "disability" for rr in r.requirements_not_satisfied)


def test_income_threshold_exceeded():
    r = _eval([{"rule_type": "income", "rule": {"max_income": 250000}}],
              {"income_amount": 300000})
    assert r.outcome == "not_eligible"


def test_income_threshold_within():
    r = _eval([{"rule_type": "income", "rule": {"max_income": 250000}}],
              {"income_amount": 100000})
    assert r.outcome == "likely_eligible"


def test_income_range_signal():
    r = _eval([{"rule_type": "income", "rule": {"max_income": 250000}}],
              {"income_range": "below_limit"})
    assert r.outcome == "likely_eligible"
    r2 = _eval([{"rule_type": "income", "rule": {"max_income": 250000}}],
               {"income_range": "above_limit"})
    assert r2.outcome == "not_eligible"


def test_age_threshold():
    young = _eval([{"rule_type": "age", "rule": {"min": 18, "max": 60}}], {"age": 15})
    assert young.outcome == "not_eligible"
    ok = _eval([{"rule_type": "age", "rule": {"min": 18, "max": 60}}], {"age": 30})
    assert ok.outcome == "likely_eligible"


def test_state_restriction():
    r = _eval([{"rule_type": "state", "rule": {"eq": "Karnataka"}}], {"state": "Karnataka"})
    assert r.outcome == "likely_eligible"
    r2 = _eval([{"rule_type": "state", "rule": {"eq": "Karnataka"}}], {"state": "Tamil Nadu"})
    assert r2.outcome == "not_eligible"


def test_education_requirement():
    ok = _eval([{"rule_type": "education", "rule": {"min_level": "undergraduate"}}],
               {"education_level": "postgraduate"})
    assert ok.outcome == "likely_eligible"
    no = _eval([{"rule_type": "education", "rule": {"min_level": "undergraduate"}}],
               {"education_level": "12th"})
    assert no.outcome == "not_eligible"


def test_missing_information():
    r = _eval([{"rule_type": "disability", "rule": {"min_percentage": 40}}], {})
    assert r.outcome == "insufficient_information"
    assert r.unknown_requirements


def test_ineligible_applicant_with_multiple_rules():
    rules = [
        {"rule_type": "disability", "rule": {"min_percentage": 40}},
        {"rule_type": "age", "rule": {"min": 18, "max": 60}},
    ]
    r = _eval(rules, {"disability_percentage": 60, "age": 70})
    assert r.outcome == "not_eligible"  # age fails even though disability passes


def test_documents_do_not_make_ineligible():
    rules = [
        {"rule_type": "disability", "rule": {"min_percentage": 40}},
        {"rule_type": "documents", "rule": {"required": ["udid", "income_certificate"]}},
    ]
    r = _eval(rules, {"disability_percentage": 60, "available_documents": ["udid"]})
    # Missing income_certificate but still likely eligible (docs are informational).
    assert r.outcome == "likely_eligible"
    assert "income_certificate" in r.missing_documents


def test_prerequisites_reported_as_missing():
    rules = [
        {"rule_type": "disability", "rule": {"min_percentage": 40}},
        {"rule_type": "prerequisites", "rule": {"required": ["udid"]}},
    ]
    r = _eval(rules, {"disability_percentage": 60, "udid_status": "no_udid"})
    assert "udid" in r.missing_prerequisites
    assert r.outcome == "likely_eligible"  # prerequisite is informational


def test_closed_scheme_requires_verification_not_personal_rejection():
    scheme = {"scheme_id": "x", "official_name": "X", "scheme_status": "closed", "confidence_status": "verified"}
    r = evaluate([EligibilityRule(rule_type="disability", rule={"min_percentage": 40})],
                 {"disability_percentage": 60}, scheme)
    assert r.outcome == "requires_official_verification"


def test_confirmed_personal_failure_still_means_not_eligible_when_scheme_closed():
    scheme = {"scheme_id": "x", "official_name": "X", "scheme_status": "closed", "confidence_status": "verified"}
    r = evaluate([EligibilityRule(rule_type="disability", rule={"min_percentage": 40})],
                 {"disability_percentage": 20}, scheme)
    assert r.outcome == "not_eligible"


def test_needs_verification_gives_potentially_eligible():
    scheme = {"scheme_id": "x", "official_name": "X", "scheme_status": "active", "confidence_status": "needs_verification"}
    r = evaluate([EligibilityRule(rule_type="disability", rule={"min_percentage": 40})],
                 {"disability_percentage": 60}, scheme)
    assert r.outcome == "potentially_eligible"


def test_category_membership():
    r = _eval([{"rule_type": "category", "rule": {"in": ["sc", "st"]}}], {"social_category": "sc"})
    assert r.outcome == "likely_eligible"
    r2 = _eval([{"rule_type": "category", "rule": {"in": ["sc", "st"]}}], {"social_category": "general"})
    assert r2.outcome == "not_eligible"


def test_result_serialisable():
    import json

    r = _eval([{"rule_type": "disability", "rule": {"min_percentage": 40}}], {"disability_percentage": 60})
    json.dumps(r.to_dict())  # must not raise


def test_unverified_bpl_rule_never_rejects_applicant():
    rules = [{
        "rule_type": "bpl",
        "rule": {"required": True, "verification_status": "needs_verification"},
    }]
    r = _eval(rules, {"bpl_status": "no"})
    assert r.outcome == "requires_official_verification"
    assert r.unknown_requirements


def test_verified_bpl_rule_accepts_confirmed_bpl_status():
    rules = [{
        "rule_type": "bpl",
        "rule": {"required": True, "verification_status": "verified"},
    }]
    r = _eval(rules, {"bpl_status": "yes"})
    assert r.outcome == "likely_eligible"


def test_verified_bpl_rule_rejects_confirmed_non_bpl_status():
    rules = [{
        "rule_type": "bpl",
        "rule": {"required": True, "verification_status": "verified"},
    }]
    r = _eval(rules, {"bpl_status": "no"})
    assert r.outcome == "not_eligible"


def test_verified_bpl_rule_reports_missing_status():
    rules = [{
        "rule_type": "bpl",
        "rule": {"required": True, "verification_status": "verified"},
    }]
    r = _eval(rules, {})
    assert r.outcome == "insufficient_information"


def test_udid_status_does_not_accept_otr_status_value():
    rules = [{
        "rule_type": "prerequisites",
        "rule": {"required": ["udid"]},
    }]
    r = _eval(rules, {"udid_status": "has_otr"})
    assert "udid" in r.missing_prerequisites
