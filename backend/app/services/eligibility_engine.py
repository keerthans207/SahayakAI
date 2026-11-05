"""Deterministic eligibility engine.

The LLM never decides eligibility. Rules are expressed as typed Pydantic
predicates and evaluated in Python. Each rule produces a status of
``satisfied`` / ``not_satisfied`` / ``unknown``; the overall outcome is derived
from those statuses, never guessed.

Outcomes:
    likely_eligible            every substantive rule satisfied
    potentially_eligible       no hard failure, but scheme confidence is limited
    not_eligible                at least one substantive rule not satisfied
    insufficient_information    at least one unknown rule (no hard failure)
    requires_official_verification  scheme status/currency cannot be confirmed

Documents and prerequisites are reported as *missing requirements* (they do
not by themselves make someone ineligible — an applicant can obtain them).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

RuleStatus = Literal["satisfied", "not_satisfied", "unknown"]
Outcome = Literal[
    "likely_eligible",
    "potentially_eligible",
    "not_eligible",
    "insufficient_information",
    "requires_official_verification",
]

# Ordered education ladder (lower index = lower level).
EDUCATION_ORDER: dict[str, int] = {
    "none": 0,
    "below_10th": 1,
    "8th": 2,
    "10th": 3,
    "matric": 3,
    "12th": 4,
    "intermediate": 4,
    "diploma": 4,
    "undergraduate": 5,
    "graduate": 5,
    "b.tech": 5,
    "bachelor": 5,
    "postgraduate": 6,
    "post_graduate": 6,
    "masters": 6,
    "doctoral": 7,
    "phd": 7,
    "other": 8,
}


def _education_rank(level: str | None) -> int | None:
    if level is None:
        return None
    return EDUCATION_ORDER.get(level.strip().lower())


def _norm(s: str | None) -> str:
    return (s or "").strip().lower().replace(" ", "_")


# --------------------------------------------------------------------------- #
# Typed rule predicates
# --------------------------------------------------------------------------- #
class EligibilityRule(BaseModel):
    rule_type: str
    rule: dict[str, Any]
    description: str | None = None


class ProfileSnapshot(BaseModel):
    """A minimal, PII-safe snapshot the engine evaluates against."""

    age: int | None = None
    disability_percentage: float | None = None
    disability_category: str | None = None
    income_amount: float | None = None
    income_range: str | None = None  # below_limit | above_limit | unknown
    education_level: str | None = None
    course: str | None = None
    institution_type: str | None = None
    state: str | None = None
    district: str | None = None
    social_category: str | None = None
    employment_status: str | None = None
    udid_status: str | None = None
    otr_status: str | None = None
    has_aadhaar: bool | None = None
    available_documents: list[str] = Field(default_factory=list)


class SchemeMeta(BaseModel):
    scheme_id: str
    official_name: str
    scheme_status: str = "active"
    confidence_status: str = "needs_verification"


@dataclass
class RuleResult:
    rule_type: str
    status: RuleStatus
    description: str | None = None
    detail: str | None = None


@dataclass
class EligibilityResult:
    scheme_id: str
    outcome: Outcome = "insufficient_information"
    requirements_satisfied: list[RuleResult] = field(default_factory=list)
    requirements_not_satisfied: list[RuleResult] = field(default_factory=list)
    unknown_requirements: list[RuleResult] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    supporting_evidence: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    required_documents: list[str] = field(default_factory=list)
    missing_documents: list[str] = field(default_factory=list)
    missing_prerequisites: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        def _rs(r: RuleResult) -> dict:
            return {
                "rule_type": r.rule_type,
                "status": r.status,
                "description": r.description,
                "detail": r.detail,
            }

        return {
            "scheme_id": self.scheme_id,
            "outcome": self.outcome,
            "requirements_satisfied": [_rs(r) for r in self.requirements_satisfied],
            "requirements_not_satisfied": [_rs(r) for r in self.requirements_not_satisfied],
            "unknown_requirements": [_rs(r) for r in self.unknown_requirements],
            "missing_information": self.missing_information,
            "supporting_evidence": self.supporting_evidence,
            "next_steps": self.next_steps,
            "required_documents": self.required_documents,
            "missing_documents": self.missing_documents,
            "missing_prerequisites": self.missing_prerequisites,
        }


# --------------------------------------------------------------------------- #
# Per-rule evaluators
# --------------------------------------------------------------------------- #
def _eval_age(rule: dict, p: ProfileSnapshot) -> RuleResult:
    age = p.age
    lo = rule.get("min")
    hi = rule.get("max")
    if age is None:
        return RuleResult("age", "unknown", detail="Applicant age not provided")
    if lo is not None and age < lo:
        return RuleResult("age", "not_satisfied", detail=f"Minimum age is {lo}; applicant is {age}")
    if hi is not None and age > hi:
        return RuleResult("age", "not_satisfied", detail=f"Maximum age is {hi}; applicant is {age}")
    return RuleResult("age", "satisfied", detail=f"Age {age} within range")


def _eval_disability(rule: dict, p: ProfileSnapshot) -> RuleResult:
    min_pct = rule.get("min_percentage")
    cats = rule.get("categories")
    ok = True
    if min_pct is not None:
        if p.disability_percentage is None:
            return RuleResult("disability", "unknown", detail="Disability percentage not provided")
        if p.disability_percentage < min_pct:
            return RuleResult(
                "disability",
                "not_satisfied",
                detail=f"Minimum {min_pct}% disability required; applicant has {p.disability_percentage}%",
            )
    if cats:
        if p.disability_category is None:
            return RuleResult("disability", "unknown", detail="Disability category not provided")
        if _norm(p.disability_category) not in {_norm(c) for c in cats}:
            return RuleResult(
                "disability",
                "not_satisfied",
                detail=f"Category must be one of {cats}; applicant is {p.disability_category}",
            )
    if ok:
        return RuleResult("disability", "satisfied", detail="Disability criteria met")


def _eval_income(rule: dict, p: ProfileSnapshot) -> RuleResult:
    max_income = rule.get("max_income")
    if max_income is None:
        return RuleResult("income", "satisfied", detail="No income limit")
    # Prefer an explicit income_range signal if present.
    if p.income_range:
        if _norm(p.income_range) == "below_limit":
            return RuleResult("income", "satisfied", detail="Income declared within limit")
        if _norm(p.income_range) == "above_limit":
            return RuleResult(
                "income", "not_satisfied", detail=f"Income exceeds the {max_income} limit"
            )
    if p.income_amount is None and not p.income_range:
        return RuleResult("income", "unknown", detail="Income not provided")
    if p.income_amount is not None and p.income_amount > max_income:
        return RuleResult(
            "income", "not_satisfied", detail=f"Income {p.income_amount} exceeds limit {max_income}"
        )
    return RuleResult("income", "satisfied", detail=f"Income within {max_income} limit")


def _eval_education(rule: dict, p: ProfileSnapshot) -> RuleResult:
    min_level = rule.get("min_level")
    if min_level is None:
        return RuleResult("education", "satisfied", detail="No education requirement")
    required = _education_rank(min_level)
    actual = _education_rank(p.education_level)
    if actual is None:
        return RuleResult("education", "unknown", detail="Education level not provided")
    if actual < required:
        return RuleResult(
            "education",
            "not_satisfied",
            detail=f"Requires {min_level}; applicant has {p.education_level}",
        )
    return RuleResult("education", "satisfied", detail=f"Education {p.education_level} meets {min_level}")


def _eval_membership(rule_type: str, rule: dict, value: str | None) -> RuleResult:
    allowed = rule.get("in") or ([rule["eq"]] if "eq" in rule else None)
    if not allowed:
        return RuleResult(rule_type, "satisfied", detail="No restriction")
    if value is None:
        return RuleResult(rule_type, "unknown", detail=f"{rule_type} not provided")
    if _norm(value) in {_norm(a) for a in allowed}:
        return RuleResult(rule_type, "satisfied", detail=f"{rule_type} '{value}' allowed")
    return RuleResult(
        rule_type, "not_satisfied", detail=f"{rule_type} must be one of {allowed}; got '{value}'"
    )


def _eval_other(rule: dict, p: ProfileSnapshot) -> RuleResult:
    # Free-form condition with an explicit field reference.
    field_name = rule.get("field")
    expected = rule.get("equals")
    if field_name is None:
        return RuleResult("other", "satisfied", detail="No extra condition")
    actual = getattr(p, field_name, None)
    if actual is None:
        return RuleResult("other", "unknown", detail=f"{field_name} not provided")
    if str(actual).lower() == str(expected).lower():
        return RuleResult("other", "satisfied", detail=f"{field_name} matches")
    return RuleResult(
        "other", "not_satisfied", detail=f"{field_name} must be '{expected}'"
    )


_SUBSTANTIVE = {
    "age": _eval_age,
    "disability": _eval_disability,
    "income": _eval_income,
    "education": _eval_education,
    "course": lambda r, p: _eval_membership("course", r, p.course),
    "institution_type": lambda r, p: _eval_membership("institution_type", r, p.institution_type),
    "state": lambda r, p: _eval_membership("state", r, p.state),
    "district": lambda r, p: _eval_membership("district", r, p.district),
    "category": lambda r, p: _eval_membership("category", r, p.social_category),
    "employment": lambda r, p: _eval_membership("employment", r, p.employment_status),
    "other": _eval_other,
}

# These are reported but never flip the outcome to not_eligible.
_INFORMATIONAL = {"documents", "prerequisites"}


def evaluate(
    rules: list[EligibilityRule | dict],
    profile: ProfileSnapshot | dict,
    scheme: SchemeMeta | dict,
) -> EligibilityResult:
    """Evaluate ``rules`` against ``profile`` for ``scheme`` deterministically."""
    if isinstance(profile, dict):
        profile = ProfileSnapshot(**{k: v for k, v in profile.items() if k in ProfileSnapshot.model_fields})
    if isinstance(scheme, dict):
        scheme = SchemeMeta(**{k: v for k, v in scheme.items() if k in SchemeMeta.model_fields})

    result = EligibilityResult(scheme_id=scheme.scheme_id)
    required_docs: list[str] = []

    for raw in rules:
        rule = raw if isinstance(raw, EligibilityRule) else EligibilityRule(**raw)
        rtype = rule.rule_type
        predicate = rule.rule

        if rtype == "documents":
            required = predicate.get("required", [])
            required_docs.extend(required)
            available = {d.lower() for d in profile.available_documents}
            missing = [d for d in required if d.lower() not in available]
            result.required_documents = list(dict.fromkeys(required_docs))
            result.missing_documents = list(dict.fromkeys(missing))
            for d in required:
                if d.lower() in available:
                    result.requirements_satisfied.append(
                        RuleResult("documents", "satisfied", detail=f"Has {d}")
                    )
                else:
                    result.missing_information.append(f"Document: {d}")
            continue

        if rtype == "prerequisites":
            required = predicate.get("required", [])
            for pre in required:
                key = f"{pre}_status"
                val = getattr(profile, key, None)
                met = _norm(val) in {"has_udid", "has_otr", "true", "yes"}
                if val is None:
                    result.unknown_requirements.append(
                        RuleResult("prerequisites", "unknown", detail=f"{pre} status unknown")
                    )
                    result.missing_information.append(f"Prerequisite: {pre}")
                elif met:
                    result.requirements_satisfied.append(
                        RuleResult("prerequisites", "satisfied", detail=f"{pre} available")
                    )
                else:
                    result.missing_prerequisites.append(pre)
                    result.missing_information.append(f"Prerequisite: {pre}")
            continue

        evaluator = _SUBSTANTIVE.get(rtype)
        if evaluator is None:
            result.unknown_requirements.append(
                RuleResult(rtype, "unknown", detail=f"Unsupported rule type '{rtype}'")
            )
            continue
        rr = evaluator(predicate, profile)
        rr.description = rule.description
        if rr.status == "satisfied":
            result.requirements_satisfied.append(rr)
        elif rr.status == "not_satisfied":
            result.requirements_not_satisfied.append(rr)
        else:
            result.unknown_requirements.append(rr)
            result.missing_information.append(f"{rtype}: {rr.detail or 'value missing'}")

    result.outcome = _derive_outcome(result, scheme)
    _fill_next_steps(result)
    return result


def _derive_outcome(result: EligibilityResult, scheme: SchemeMeta) -> Outcome:
    # Scheme-level currency first.
    if scheme.scheme_status in ("inactive", "closed"):
        return "not_eligible"
    if scheme.scheme_status in ("upcoming", "unknown"):
        return "requires_official_verification"

    if result.requirements_not_satisfied:
        return "not_eligible"
    if result.unknown_requirements:
        return "insufficient_information"
    # All substantive rules satisfied.
    if scheme.confidence_status == "needs_verification":
        return "potentially_eligible"
    return "likely_eligible"


def _fill_next_steps(result: EligibilityResult) -> None:
    steps: list[str] = []
    if result.missing_documents:
        steps.append("Obtain the missing documents: " + ", ".join(result.missing_documents))
    if result.missing_prerequisites:
        steps.append("Complete prerequisites: " + ", ".join(result.missing_prerequisites))
    if result.outcome == "insufficient_information":
        steps.append("Provide the missing profile information so eligibility can be finalised.")
    if result.outcome == "not_eligible":
        steps.append("Review the not-satisfied requirements; consider other applicable schemes.")
    if result.outcome in ("likely_eligible", "potentially_eligible"):
        steps.append("Proceed to gather documents and prepare the application.")
    if not steps:
        steps.append("Check the official portal for the current application window.")
    result.next_steps = steps
