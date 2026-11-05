"""Document schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentUploadAck(BaseModel):
    document_id: str
    document_type: str
    original_filename: str
    size_bytes: int


class DocumentAssessment(BaseModel):
    document_type: str | None = None
    extracted_fields: dict = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    dates_to_check: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    is_genuine: bool | None = Field(
        default=None,
        description="Always None — we never authenticate documents.",
    )
    redacted: bool = False


class DocumentRead(BaseModel):
    id: str
    user_id: str
    document_type: str
    original_filename: str
    mime_type: str | None = None
    size_bytes: int
    created_at: datetime
    assessment: dict = Field(default_factory=dict)

    model_config = {"from_attributes": True}
