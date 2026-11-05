"""Eligibility evaluation endpoints — deterministic engine only."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._deps import get_current_user_id, get_db
from app.models.db import EligibilityAssessment, UserProfile, User
from app.schemas.eligibility import (
    EligibilityEvaluationRequest,
    EligibilityRead,
    RequirementResult,
)
from app.services.eligibility_engine import EligibilityRule, ProfileSnapshot, SchemeMeta, evaluate
from app.services.scheme_service import SchemeService

router = APIRouter()

# In-process store so GET /{assessment_id} works without DB wiring in dev.
_ASSESSMENTS: dict[str, dict[str, Any]] = {}


@router.post("/evaluate", response_model=EligibilityRead, status_code=200)
async def evaluate_eligibility(
    body: EligibilityEvaluationRequest,
    user_id: str = Depends(get_current_user_id),
):
    svc = SchemeService()
    scheme = svc.get_scheme(body.scheme_id)
    if scheme is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scheme not found")
    rules = [EligibilityRule(**r) for r in scheme.get("rules", [])]
    profile = body.profile or {}
    # Merge a stored profile if a user_id was supplied and we have one in DB.
    snap = ProfileSnapshot(**{k: v for k, v in profile.items() if k in ProfileSnapshot.model_fields})
    meta = SchemeMeta(
        scheme_id=scheme["scheme_id"],
        official_name=scheme["official_name"],
        scheme_status=scheme.get("scheme_status", "active"),
        confidence_status=scheme.get("confidence_status", "needs_verification"),
    )
    result = evaluate(rules, snap, meta)
    data = result.to_dict()
    assessment_id = str(uuid.uuid4())
    record = {
        "id": assessment_id,
        "user_id": user_id,
        "scheme_id": body.scheme_id,
        **data,
    }
    _ASSESSMENTS[assessment_id] = record
    return _to_read(record)


@router.get("/{assessment_id}", response_model=EligibilityRead)
async def get_assessment(assessment_id: str, user_id: str = Depends(get_current_user_id)):
    record = _ASSESSMENTS.get(assessment_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assessment not found")
    return _to_read(record)


def _to_read(record: dict[str, Any]) -> EligibilityRead:
    def _rr(items):
        return [RequirementResult(**r) if isinstance(r, dict) else RequirementResult(
            rule_type=r.rule_type, status=r.status, description=r.description, detail=r.detail
        ) for r in items]
    return EligibilityRead(
        id=record["id"],
        user_id=record.get("user_id"),
        scheme_id=record["scheme_id"],
        outcome=record["outcome"],
        requirements_satisfied=_rr(record.get("requirements_satisfied", [])),
        requirements_not_satisfied=_rr(record.get("requirements_not_satisfied", [])),
        unknown_requirements=_rr(record.get("unknown_requirements", [])),
        missing_information=record.get("missing_information", []),
        supporting_evidence=record.get("supporting_evidence", []),
        next_steps=record.get("next_steps", []),
    )
