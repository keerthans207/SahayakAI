"""Language detection & resolution tests."""

from __future__ import annotations

from app.services.language_service import (
    SUPPORTED_LANGUAGES,
    detect_language,
    language_name,
    preserve_tokens,
    resolve_response_language,
)


def test_detect_english():
    r = detect_language("Find scholarships for engineering students")
    assert r.language == "en"


def test_detect_kannada_script():
    r = detect_language("ನಮಸ್ಕಾರ, ನನಗೆ ವಿದ್ಯಾರ್ಥಿವೇತನ ಬೇಕು")
    assert r.language == "kn"


def test_detect_hindi_script():
    r = detect_language("नमस्ते, मुझे छात्रवृत्ति चाहिए")
    assert r.language == "hi"


def test_detect_tamil_script():
    r = detect_language("வணக்கம், எனக்கு உதவை தேவை")
    assert r.language == "ta"


def test_romanised_kannada():
    # "namaskara" + "beku" are both Kannada cues.
    r = detect_language("namaskara, nanage scholarship beku")
    assert r.language == "kn"


def test_mixed_kannada_english():
    r = detect_language("I need scholarship, ನನಗೆ ಸಹಾಯ ಬೇಕು")
    assert r.language == "kn"


def test_preferred_language_respected_for_short_text():
    r = detect_language("ok", preferred="hi")
    assert r.language == "hi"


def test_resolve_response_language_priority():
    # signature: (detected, preferred, requested)
    # explicit requested always wins
    assert resolve_response_language("hi", "en", "kn") == "kn"
    # no requested → detected wins
    assert resolve_response_language("kn", None, None) == "kn"
    # no requested → detected wins over preferred
    assert resolve_response_language("en", "hi", None) == "en"
    # nothing set → fallback english
    assert resolve_response_language(None, None, None) == "en"
    # preferred wins when detected is None
    assert resolve_response_language(None, "hi", None) == "hi"


def test_preserve_tokens():
    toks = preserve_tokens("The pension is ₹1,500 per month and 40% disability.")
    assert any("₹" in t or "1,500" in t for t in toks)
    assert any("40%" in t for t in toks)


def test_all_supported_languages_present():
    for code in ["en", "kn", "hi", "ta", "te", "ml", "mr", "bn", "gu", "pa", "or", "as", "ur"]:
        assert code in SUPPORTED_LANGUAGES


def test_language_name():
    assert language_name("kn") == "Kannada"
    assert language_name("en") == "English"
