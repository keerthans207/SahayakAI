"""User profile schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    """Partial profile update. Collect only what the requested scheme needs."""

    preferred_language: str | None = None
    state: str | None = None
    district: str | None = None
    education_level: str | None = None
    course: str | None = None
    institution_type: str | None = None
    employment_status: str | None = None
    disability_category: str | None = None
    disability_percentage: float | None = Field(default=None, ge=0, le=100)
    udid_status: str | None = None  # has_udid | no_udid | unknown
    otr_status: str | None = None  # has_otr | no_otr | unknown
    income_range: str | None = None  # below_limit | above_limit | unknown
    income_amount: float | None = Field(default=None, ge=0)
    has_aadhaar: bool | None = None


class UserProfileRead(BaseModel):
    user_id: str
    preferred_language: str | None = None
    state: str | None = None
    district: str | None = None
    education_level: str | None = None
    course: str | None = None
    institution_type: str | None = None
    employment_status: str | None = None
    disability_category: str | None = None
    disability_percentage: float | None = None
    udid_status: str | None = None
    otr_status: str | None = None
    income_range: str | None = None
    income_amount: float | None = None
    has_aadhaar: bool | None = None

    model_config = {"from_attributes": True}
