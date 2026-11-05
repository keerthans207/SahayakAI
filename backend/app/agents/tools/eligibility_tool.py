"""Deterministic eligibility tool — delegates to the rules engine, never the LLM."""

from __future__ import annotations

from langchain_core.tools import tool

from app.services.eligibility_engine import EligibilityRule, ProfileSnapshot, SchemeMeta, evaluate
from app.services.scheme_service import SchemeService


def _build_inputs(scheme_id: str, profile: dict):
    svc = SchemeService()
    scheme = svc.get_scheme(scheme_id)
    if not scheme:
        return None, None, None
    rules = [EligibilityRule(**r) for r in scheme.get("rules", [])]
    snap = ProfileSnapshot(**{k: v for k, v in profile.items() if k in ProfileSnapshot.model_fields})
    meta = SchemeMeta(
        scheme_id=scheme["scheme_id"],
        official_name=scheme["official_name"],
        scheme_status=scheme.get("scheme_status", "active"),
        confidence_status=scheme.get("confidence_status", "needs_verification"),
    )
    return rules, snap, meta


@tool
def eligibility_tool(scheme_id: str, profile: dict) -> dict:
    """Evaluate preliminary eligibility for a scheme using deterministic Python rules.

    The LLM does not decide eligibility; this tool runs the rules engine and
    returns the outcome plus satisfied / not-satisfied / unknown requirements and
    missing information.

    Args:
        scheme_id: the registered scheme id.
        profile: profile snapshot with keys such as age, disability_percentage,
            disability_category, income_amount, education_level, state, etc.
    """
    rules, snap, meta = _build_inputs(scheme_id, profile or {})
    if meta is None:
        return {"error": f"Unknown scheme: {scheme_id}"}
    result = evaluate(rules, snap, meta)
    return result.to_dict()
