"""Speech endpoints — optional integration layer.

When no speech provider is configured, both endpoints return ``available=False``
with a clear message instead of failing. This keeps the core text app working.
"""

from __future__ import annotations

import base64

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.v1._deps import get_current_user_id
from app.schemas.speech import SynthesizeRequest, SynthesizeResponse, TranscribeResponse
from app.services.speech_service import get_stt_provider, get_tts_provider

router = APIRouter()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile = File(...),
    language: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    provider = get_stt_provider()
    if not provider.is_available():
        return TranscribeResponse(text="", detected_language=None)
    audio = await file.read()
    text = await provider.transcribe(audio, language=language)
    from app.services.language_service import detect_language

    detected = detect_language(text).language
    return TranscribeResponse(text=text, detected_language=detected)


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize(
    body: SynthesizeRequest,
    user_id: str = Depends(get_current_user_id),
):
    provider = get_tts_provider()
    if not provider.is_available():
        return SynthesizeResponse(
            available=False,
            message="Speech synthesis is not configured. Set SPEECH_PROVIDER=azure_speech "
            "and provide AZURE_SPEECH_KEY / AZURE_SPEECH_REGION.",
        )
    audio = await provider.synthesize(body.text, language=body.language, voice=body.voice)
    return SynthesizeResponse(
        available=True,
        audio_base64=base64.b64encode(audio).decode("ascii") if audio else None,
        content_type="audio/wav",
    )
