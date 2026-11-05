"""Document intelligence for individual user documents.

Pipeline: validate file -> extract text safely -> identify document type ->
extract relevant fields -> compare against scheme requirements -> flag dates ->
return a descriptive assessment. This is never legal authentication of a
certificate and never claims genuineness.

Personal documents are kept isolated per user (the API stores under per-user
paths) and are never ingested into the shared government knowledge base.
"""

from __future__ import annotations

import io
import re
from datetime import date
from typing import Any

from app.config import ConfigurationError, get_settings
from app.security.auth import mask_pii
from app.services.scheme_service import SchemeService

# Field-extraction regexes (best-effort, never store full Aadhaar).
_UDID_NUM_RE = re.compile(r"UDID[\s:]*([A-Z0-9-]+)", re.I)
_DISABILITY_PCT_RE = re.compile(r"(\d{1,3})\s*%")
_DATE_RE = re.compile(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b")
_INCOME_RE = re.compile(r"(?:Rs\.?|INR|₹)\s*([\d,]+)")
_AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")


def allowed_mime(mime: str | None) -> bool:
    return mime in get_settings().allowed_upload_mimetypes


def max_upload_bytes() -> int:
    return get_settings().max_upload_mb * 1024 * 1024


class DocumentService:
    def __init__(self, schemes: SchemeService | None = None) -> None:
        self._schemes = schemes or SchemeService()

    # ---- validation ------------------------------------------------------- #
    def validate_upload(self, filename: str, mime_type: str | None, size: int) -> list[str]:
        problems: list[str] = []
        if not allowed_mime(mime_type):
            problems.append(f"Unsupported file type: {mime_type}")
        if size > max_upload_bytes():
            problems.append(
                f"File too large: {size} bytes (max {get_settings().max_upload_mb} MB)"
            )
        if not filename:
            problems.append("Missing filename")
        return problems

    # ---- extraction -------------------------------------------------------- #
    def extract_text(self, content: bytes, mime_type: str | None, filename: str) -> str:
        ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
        if ext == "pdf" or mime_type == "application/pdf":
            return self._extract_pdf(content)
        if ext == "docx" or "wordprocessingml" in (mime_type or ""):
            return self._extract_docx(content)
        if ext in ("txt",) or (mime_type or "").startswith("text/"):
            try:
                return content.decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                return ""
        if ext in ("html", "htm"):
            return self._extract_html(content)
        raise ConfigurationError(f"Cannot extract text from {filename} ({mime_type})")

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover
            raise ConfigurationError("PDF extraction requires 'pypdf'.") from exc
        reader = PdfReader(io.BytesIO(content))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)

    @staticmethod
    def _extract_docx(content: bytes) -> str:
        try:
            import docx
        except ImportError as exc:  # pragma: no cover
            raise ConfigurationError("DOCX extraction requires 'python-docx'.") from exc
        doc = docx.Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    @staticmethod
    def _extract_html(content: bytes) -> str:
        try:
            from bs4 import BeautifulSoup
        except ImportError as exc:  # pragma: no cover
            raise ConfigurationError("HTML extraction requires 'beautifulsoup4'.") from exc
        soup = BeautifulSoup(content.decode("utf-8", errors="replace"), "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator="\n")

    # ---- identification & field extraction --------------------------------- #
    def identify_type(self, text: str, filename: str) -> str:
        lower = (text or "").lower()
        name = (filename or "").lower()
        if "udid" in lower or "udid" in name:
            return "udid"
        if "disability certificate" in lower or "disability_certificate" in name:
            return "disability_certificate"
        if "income certificate" in lower or "income_certificate" in name:
            return "income_certificate"
        if "domicile" in lower:
            return "domicile_certificate"
        if "marksheet" in lower or "marksheet" in name or "transcript" in lower:
            return "marksheets"
        if "bonafide" in lower:
            return "bonafide_certificate"
        if "admission" in lower:
            return "admission_certificate"
        if "bank" in lower and ("passbook" in lower or "account" in lower):
            return "bank_account_proof"
        return "unknown"

    def extract_fields(self, text: str, document_type: str) -> dict[str, Any]:
        fields: dict[str, Any] = {}
        redacted = mask_pii(text or "")
        pct = _DISABILITY_PCT_RE.search(redacted)
        if pct:
            try:
                val = int(pct.group(1))
                if 0 <= val <= 100:
                    fields["disability_percentage"] = val
            except ValueError:
                pass
        udid = _UDID_NUM_RE.search(redacted)
        if udid:
            fields["udid_number"] = "[UDID-REDACTED]"  # never echo full value
            fields["has_udid"] = True
        dates = _DATE_RE.findall(redacted)
        if dates:
            fields["dates_found"] = dates
        income = _INCOME_RE.search(redacted)
        if income:
            fields["income_amount_raw"] = income.group(1)
        # Detect Aadhaar presence without storing the number.
        if _AADHAAR_RE.search(redacted):
            fields["has_aadhaar"] = True
        if "udid" in (document_type or "").lower():
            fields["document_type"] = "udid"
        return fields

    # ---- assessment -------------------------------------------------------- #
    def assess(
        self,
        text: str,
        document_type: str,
        scheme_id: str | None = None,
    ) -> dict[str, Any]:
        fields = self.extract_fields(text, document_type)
        notes: list[str] = []
        missing_fields: list[str] = []
        dates_to_check: list[str] = []

        if document_type == "udid" and not fields.get("has_udid"):
            missing_fields.append("udid_number")
        if document_type == "disability_certificate" and "disability_percentage" not in fields:
            missing_fields.append("disability_percentage")
        if document_type == "income_certificate" and "income_amount_raw" not in fields:
            missing_fields.append("income_amount")

        for d in fields.get("dates_found", []):
            dates_to_check.append(d)
            notes.append(f"Verify date {d} is current and valid for the application window.")

        scheme_required: list[str] = []
        if scheme_id:
            scheme = self._schemes.get_scheme(scheme_id)
            if scheme:
                scheme_required = list(scheme.get("required_documents", []))

        notes.append(
            "This assessment is descriptive only — it does not authenticate the document."
        )
        if fields.get("has_aadhaar"):
            notes.append("Aadhaar-like number detected and redacted from stored text.")

        return {
            "document_type": document_type,
            "extracted_fields": fields,
            "missing_fields": missing_fields,
            "dates_to_check": dates_to_check,
            "notes": notes,
            "required_for_scheme": scheme_required,
            "is_genuine": None,  # never claim authenticity
        }


def document_service() -> DocumentService:
    return DocumentService()
