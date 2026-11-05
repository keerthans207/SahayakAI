"""Retrieval service — searches the vector store and produces cited results.

Results preserve source URL, title, publisher, page number, retrieval timestamp
and a freshness flag. Only official-domain sources are reported as authoritative.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.retrieval.metadata import is_stale
from app.retrieval.vector_store import get_vector_store
from app.services.scheme_service import is_official_domain


class RetrievedEvidence:
    def __init__(
        self,
        text: str,
        score: float,
        metadata: dict[str, Any],
        *,
        official: bool | None = None,
        stale: bool | None = None,
    ) -> None:
        self.text = text
        self.score = score
        self.metadata = metadata
        self.official = official if official is not None else _is_official(metadata)
        self.stale = stale if stale is not None else _is_stale(metadata)

    def citation(self) -> dict[str, Any]:
        return {
            "title": self.metadata.get("document_name"),
            "url": self.metadata.get("official_source_url"),
            "publisher": self.metadata.get("department"),
            "page_number": self.metadata.get("page_number"),
            "retrieved_at": self.metadata.get("retrieved_at"),
            "source_status": "official" if self.official else "unverified",
            "is_stale": self.stale,
            "score": round(self.score, 4),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.text,
            "score": round(self.score, 4),
            "citation": self.citation(),
        }


def _is_official(metadata: dict[str, Any]) -> bool:
    url = metadata.get("official_source_url") or ""
    return is_official_domain(url)


def _is_stale(metadata: dict[str, Any]) -> bool:
    pub = metadata.get("publication_date")
    if not pub:
        return True
    try:
        return is_stale(date.fromisoformat(pub))
    except (ValueError, TypeError):
        return True


class RetrievalService:
    """Thin wrapper over the vector store that enriches results with citations."""

    def __init__(self, store: Any | None = None) -> None:
        self.store = store or get_vector_store()

    def retrieve(
        self,
        query: str,
        *,
        k: int = 4,
        filter: dict[str, Any] | None = None,
    ) -> list[RetrievedEvidence]:
        results = self.store.search(query, k=k, filter=filter)
        return [RetrievedEvidence(text, score, meta) for text, score, meta in results]

    def retrieve_for_scheme(self, query: str, scheme_id: str, *, k: int = 4) -> list[RetrievedEvidence]:
        return self.retrieve(query, k=k, filter={"scheme_id": scheme_id})

    def is_available(self) -> bool:
        """True if the store has any indexed documents."""
        count = getattr(self.store, "count", None)
        if callable(count):
            try:
                return count() > 0
            except TypeError:
                return False
        return False


def retrieval_service() -> RetrievalService:
    return RetrievalService()
