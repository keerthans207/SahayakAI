"""Retrieval metadata envelope.

Every chunk carries this metadata so retrieval results can be cited with their
source, publisher, page and freshness status.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any


def build_metadata(
    *,
    document_id: str,
    document_name: str,
    document_type: str,
    scheme_id: str | None = None,
    department: str | None = None,
    government_level: str | None = None,
    applicable_state: str | None = None,
    language: str | None = None,
    publication_date: date | None = None,
    official_source_url: str | None = None,
    page_number: int | None = None,
    source_status: str = "official",
    content_hash: str | None = None,
    retrieved_at: datetime | None = None,
) -> dict[str, Any]:
    return {
        "document_id": document_id,
        "document_name": document_name,
        "document_type": document_type,
        "scheme_id": scheme_id,
        "department": department,
        "government_level": government_level,
        "applicable_state": applicable_state,
        "language": language,
        "publication_date": publication_date.isoformat() if publication_date else None,
        "official_source_url": official_source_url,
        "page_number": page_number,
        "source_status": source_status,
        "content_hash": content_hash,
        "retrieved_at": (retrieved_at or datetime.now(timezone.utc)).isoformat(),
    }


def is_stale(publication_date: date | None, max_age_days: int = 365) -> bool:
    """Return True if a document's publication date is older than max_age_days."""
    if publication_date is None:
        return True  # unknown age — treat as potentially stale
    age = (date.today() - publication_date).days
    return age > max_age_days
