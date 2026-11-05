"""Chat session & message schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    title: str | None = None
    preferred_language: str | None = None


class ChatSessionRead(BaseModel):
    id: str
    title: str | None = None
    language: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatTurnCreate(BaseModel):
    """A new user message in an existing session."""

    content: str = Field(min_length=1, max_length=8000)
    language: str | None = None


class ChatTurnResponse(BaseModel):
    """The assistant's reply plus a compact view of resolved agent state."""

    message_id: str
    role: str = "assistant"
    content: str
    language: str | None = None
    detected_language: str | None = None
    intent: str | None = None
    selected_scheme: str | None = None
    eligibility_outcome: str | None = None
    missing_requirements: list[str] = Field(default_factory=list)
    official_sources: list[dict] = Field(default_factory=list)
    request_id: str | None = None


class ChatMessageRead(BaseModel):
    id: str
    role: str
    content: str
    language: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LanguagePreferenceUpdate(BaseModel):
    preferred_language: str
