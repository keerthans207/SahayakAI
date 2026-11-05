"""Eligibility schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

EligibilityOutcome = Literal[
    "likely_eligible",
    "potentially_eligible",
    "not_eligible",
    "insufficient_information",
    "requires_official_verification",
]


class RequirementResult(BaseModel):
    rule_type: str
    description: str | None = None
    status: Literal["satisfied", "not_satisfied", "unknown"]
    detail: str | None = None


class EligibilityEvaluationRequest(BaseModel):
    """Evaluate eligibility for one scheme against a profile snapshot."""

    scheme_id: str
    user_id: str | None = None
    profile: dict = Field(
        default_factory=dict,
        description="Snapshot of profile attributes used by the rules engine.",
    )


class EligibilityRead(BaseModel):
    id: str
    user_id: str | None = None
    scheme_id: str
    outcome: EligibilityOutcome
    requirements_satisfied: list[RequirementResult] = Field(default_factory=list)
    requirements_not_satisfied: list[RequirementResult] = Field(default_factory=list)
    unknown_requirements: list[RequirementResult] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}
