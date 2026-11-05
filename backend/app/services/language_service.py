"""Language detection, preference and switching.

Fully offline and deterministic — uses Unicode script ranges plus a Romanised
keyword lexicon. This avoids a hard dependency on ``langdetect`` (which ships a
model) and keeps behaviour reproducible for tests.

Supported languages: English, Kannada, Hindi, Tamil, Telugu, Malayalam, Marathi,
Bengali, Gujarati, Punjabi, Odia, Assamese, Urdu.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

SUPPORTED_LANGUAGES = {
    "en": "English",
    "kn": "Kannada",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
}

# Unicode block start ranges (start, end, code) for Indic scripts.
_SCRIPT_RANGES = [
    (0x0900, 0x097F, "hi"),  # Devanagari -> Hindi (also Marathi, but we refine below)
    (0x0980, 0x09FF, "bn"),  # Bengali/Assamese
    (0x0A00, 0x0A7F, "gu"),  # Gujarati
    (0x0A80, 0x0AFF, "pa"),  # Gurmukhi (Punjabi)
    (0x0B00, 0x0B7F, "or"),  # Oriya
    (0x0B80, 0x0BFF, "ta"),  # Tamil
    (0x0C00, 0x0C7F, "te"),  # Telugu
    (0x0C80, 0x0CFF, "kn"),  # Kannada
    (0x0D00, 0x0D7F, "ml"),  # Malayalam
    (0x0D80, 0x0DFF, "si"),  # Sinhala (not supported; ignore)
    (0x0600, 0x06FF, "ur"),  # Arabic block -> Urdu (romanised handling separate)
]

# Romanised (Latin) keyword cues for code-switched input.
_ROMANISED_CUES = {
    "kn": ["namaskara", "kannada", "yelli", "hesaru", "swalpa", "keli", "sahaya", "yava", "iski", "beku", "illi", "nanna"],
    "hi": ["namaste", "mera", "tumhara", "kya", "kaise", "madad", "sarkari", "vidyarthi"],
    "ta": ["vanakkam", "nanri", "vendum", "illai", "engal", "enna", "sollunga"],
    "te": ["namaste", "mithrama", "enti", "chesa", "cheyyali", "undhi"],
    "ml": ["namaskaram", "enthu", "aanu", "cheyyanam", "venda"],
    "mr": ["namaskar", "kasa", "aahe", "shikshan", "mahiti"],
    "bn": ["namaskar", "ki", "koro", "korte", "amader"],
    "gu": ["namaste", "kem", "cho", "tamari", "amne"],
    "pa": ["sat", "sri", "akal", "haal", "karda"],
    "or": ["namaskar", "kana", "heba", "achhi"],
    "as": ["namaskar", "kio", "hol", "dilek"],
    "ur": ["salam", "madad", "zaroorat", "chahiye"],
}


@dataclass
class DetectionResult:
    language: str  # ISO-639-1 code
    name: str
    script: str  # "indic" | "latin" | "mixed"
    confidence: float


def detect_language(text: str, preferred: str | None = None) -> DetectionResult:
    """Detect the dominant language of ``text``.

    A saved ``preferred`` language short-circuits detection when the input has
    no strong script signal (e.g. short English greetings). Official scheme
    names and numbers are preserved by the caller — detection only sets a tag.
    """
    if not text or not text.strip():
        lang = preferred or "en"
        return DetectionResult(lang, SUPPORTED_LANGUAGES.get(lang, "English"), "latin", 0.5)

    indic_counts: dict[str, int] = {}
    latin_count = 0
    for ch in text:
        cp = ord(ch)
        if 0x0041 <= cp <= 0x007A or ch in " ":
            if ch.isalpha():
                latin_count += 1
            continue
        for start, end, code in _SCRIPT_RANGES:
            if start <= cp <= end:
                indic_counts[code] = indic_counts.get(code, 0) + 1
                break

    total_alpha = latin_count + sum(indic_counts.values())
    if total_alpha == 0:
        return DetectionResult("en", "English", "latin", 0.4)

    dominant_indic = max(indic_counts, key=indic_counts.get) if indic_counts else None
    indic_share = (sum(indic_counts.values()) / total_alpha) if total_alpha else 0.0

    # Refine Devanagari: prefer Marathi when Latin cues point that way.
    if dominant_indic == "hi":
        lower = text.lower()
        if any(c in lower for c in _ROMANISED_CUES["mr"]) and "aahe" in lower:
            dominant_indic = "mr"

    if dominant_indic and indic_share >= 0.3:
        script = "mixed" if latin_count else "indic"
        conf = round(min(0.6 + indic_share * 0.4, 0.99), 2)
        return DetectionResult(
            dominant_indic,
            SUPPORTED_LANGUAGES.get(dominant_indic, "Unknown"),
            script,
            conf,
        )

    # Latin / romanised input — sniff the keyword cues.
    lower = text.lower()
    best, best_score = None, 0
    for code, cues in _ROMANISED_CUES.items():
        score = sum(1 for c in cues if c in lower)
        if score > best_score:
            best, best_score = code, score
    if best and best_score >= 2:
        return DetectionResult(best, SUPPORTED_LANGUAGES.get(best, "English"), "latin", 0.6)

    # Default: respect saved preference, else English.
    lang = preferred or "en"
    return DetectionResult(lang, SUPPORTED_LANGUAGES.get(lang, "English"), "latin", 0.5)


def resolve_response_language(
    detected: str, preferred: str | None, requested: str | None
) -> str:
    """Pick the language to respond in.

    Order: explicit user switch (requested) > detected > saved preference > en.
    """
    if requested and requested in SUPPORTED_LANGUAGES:
        return requested
    if detected and detected in SUPPORTED_LANGUAGES:
        return detected
    if preferred and preferred in SUPPORTED_LANGUAGES:
        return preferred
    return "en"


def is_supported(code: str | None) -> bool:
    return bool(code) and code in SUPPORTED_LANGUAGES


def language_name(code: str) -> str:
    return SUPPORTED_LANGUAGES.get(code or "en", "English")


# Patterns that must survive translation verbatim.
_PRESERVE_RE = re.compile(r"₹\s?\d[\d,]*|\d+\s?%|\b\d{2}/\d{2}/\d{4}\b")


def preserve_tokens(text: str) -> list[str]:
    """Return the amounts/dates/percentages that must not be translated."""
    return _PRESERVE_RE.findall(text)
