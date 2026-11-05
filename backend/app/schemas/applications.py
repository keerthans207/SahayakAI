"""Application schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ApplicationStatus = Literal[
    "discovered",
    "eligibility_pending",
    "eligible_pending_documents",
    "documents_incomplete",
    "ready_for_review",
    "ready_for_user_submission",
    "submitted_by_user",
    "under_verification",
    "approved",
    "rejected",
    "closed",
]


class ApplicationCreate(BaseModel):
    scheme_id: str
    required_documents: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    completed_fields: dict | None = None
    notes: str | None = None


class ApplicationRead(BaseModel):
    id: str
    user_id: str
    scheme_id: str
    status: ApplicationStatus
    required_documents: list[str] = Field(default_factory=list)
    completed_fields: dict = Field(default_factory=dict)
    prerequisites: list[str] = Field(default_factory=list)
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationReadiness(BaseModel):
    application_id: str
    scheme_id: str
    status: ApplicationStatus
    required_documents: list[str] = Field(default_factory=list)
    uploaded_documents: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    completed_fields: dict = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    prerequisites_met: bool = False
    prerequisites: list[str] = Field(default_factory=list)
    ready: bool
    report: str
