"""Scheme schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class SchemeSummary(BaseModel):
    scheme_id: str
    official_name: str
    category: str
    government_level: str
    applicable_state: str | None = None
    benefit_amount: str | None = None
    scheme_status: str
    confidence_status: str

    model_config = {"from_attributes": True}


class SchemeRead(BaseModel):
    scheme_id: str
    official_name: str
    description: str
    category: str
    department: str | None = None
    government_level: str
    applicable_state: str | None = None
    applicable_district: str | None = None
    target_beneficiaries: list[str] = Field(default_factory=list)
    benefit_description: str | None = None
    benefit_amount: str | None = None
    benefit_frequency: str | None = None
    required_documents: list[str] = Field(default_factory=list)
    prerequisite_services: list[str] = Field(default_factory=list)
    application_start_date: date | None = None
    application_deadline: date | None = None
    application_url: str | None = None
    official_contact: str | None = None
    scheme_status: str
    confidence_status: str
    source_publication_date: date | None = None
    last_verified_at: object | None = None

    model_config = {"from_attributes": True}


class SchemeSearchRequest(BaseModel):
    q: str | None = None
    category: str | None = None
    government_level: str | None = None
    state: str | None = None
    status: str | None = None
    page: int = 1
    page_size: int = 20


class SchemeCategoryRead(BaseModel):
    category: str
    count: int
