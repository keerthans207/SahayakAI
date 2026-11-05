"""Speech schemas."""

from __future__ import annotations

from pydantic import BaseModel


class TranscribeResponse(BaseModel):
    text: str
    detected_language: str | None = None


class SynthesizeRequest(BaseModel):
    text: str
    language: str | None = None
    voice: str | None = None


class SynthesizeResponse(BaseModel):
    audio_base64: str | None = None
    content_type: str = "audio/wav"
    available: bool
    message: str | None = None
