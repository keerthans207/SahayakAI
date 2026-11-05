"""Speech service — STT / TTS abstraction with an optional Azure AI Speech impl.

Voice is a separate integration layer. Missing speech credentials never block
application startup: when no provider is configured, the service reports
``available=False`` and the endpoints return a clear message.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.config import get_settings


class SpeechToTextProvider(Protocol):
    def is_available(self) -> bool: ...
    async def transcribe(self, audio_bytes: bytes, language: str | None = None) -> str: ...


class TextToSpeechProvider(Protocol):
    def is_available(self) -> bool: ...
    async def synthesize(self, text: str, language: str | None = None, voice: str | None = None) -> bytes: ...


class LanguageDetectionProvider(Protocol):
    def detect(self, text: str) -> str: ...


class NoSpeechProvider:
    """Default when no speech provider is configured."""

    def is_available(self) -> bool:
        return False

    async def transcribe(self, audio_bytes: bytes, language: str | None = None) -> str:
        return ""

    async def synthesize(self, text: str, language: str | None = None, voice: str | None = None) -> bytes:
        return b""


class AzureSpeechProvider:
    """Azure AI Speech implementation (lazy import of azure-cognitiveservices-speech)."""

    def __init__(self) -> None:
        settings = get_settings()
        if not (settings.azure_speech_key and settings.azure_speech_region):
            raise RuntimeError("Azure Speech requires AZURE_SPEECH_KEY and AZURE_SPEECH_REGION.")
        self._key = settings.azure_speech_key
        self._region = settings.azure_speech_region

    def is_available(self) -> bool:
        return True

    async def transcribe(self, audio_bytes: bytes, language: str | None = None) -> str:  # pragma: no cover
        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError as exc:
            raise RuntimeError("Azure Speech requires 'azure-cognitiveservices-speech'.") from exc
        # NOTE: real implementation wires PushAudioInputStream + SpeechRecognizer.
        raise RuntimeError("Azure Speech transcribe not wired in this build.")

    async def synthesize(self, text: str, language: str | None = None, voice: str | None = None) -> bytes:  # pragma: no cover
        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError as exc:
            raise RuntimeError("Azure Speech requires 'azure-cognitiveservices-speech'.") from exc
        raise RuntimeError("Azure Speech synthesize not wired in this build.")


_stt: SpeechToTextProvider | None = None
_tts: TextToSpeechProvider | None = None


def get_stt_provider() -> SpeechToTextProvider:
    global _stt
    if _stt is not None:
        return _stt
    settings = get_settings()
    if settings.speech_provider == "azure_speech":
        try:
            _stt = AzureSpeechProvider()
        except RuntimeError:
            _stt = NoSpeechProvider()
    else:
        _stt = NoSpeechProvider()
    return _stt


def get_tts_provider() -> TextToSpeechProvider:
    global _tts
    if _tts is not None:
        return _tts
    settings = get_settings()
    if settings.speech_provider == "azure_speech":
        try:
            _tts = AzureSpeechProvider()
        except RuntimeError:
            _tts = NoSpeechProvider()
    else:
        _tts = NoSpeechProvider()
    return _tts


def reset_speech_providers() -> None:
    global _stt, _tts
    _stt = None
    _tts = None
