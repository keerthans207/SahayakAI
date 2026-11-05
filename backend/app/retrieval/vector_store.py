"""Vector store abstraction.

- ``InMemoryVectorStore``: pure-Python cosine-similarity store; no external
  dependency. Default for tests and dev without Chroma.
- ``ChromaVectorStore``: persistent Chroma store via ``langchain-chroma``;
  imported lazily so the app runs without Chroma installed.

Both implement the same interface (``add`` / ``search`` / ``delete``).
"""

from __future__ import annotations

import math
from typing import Any, Protocol

from app.config import ConfigurationError, get_settings
from app.retrieval.embeddings import MockEmbeddings, get_embeddings


class VectorRecord:
    __slots__ = ("id", "text", "vector", "metadata")

    def __init__(self, id: str, text: str, vector: list[float], metadata: dict[str, Any]):
        self.id = id
        self.text = text
        self.vector = vector
        self.metadata = metadata


class VectorStore(Protocol):
    def add(
        self, texts: list[str], metadatas: list[dict[str, Any]], ids: list[str] | None = None
    ) -> list[str]: ...

    def search(
        self, query: str, k: int = 4, filter: dict[str, Any] | None = None
    ) -> list[tuple[str, float, dict[str, Any]]]: ...

    def delete(self, ids: list[str]) -> None: ...


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def _matches_filter(metadata: dict[str, Any], filter: dict[str, Any] | None) -> bool:
    if not filter:
        return True
    for key, value in filter.items():
        if metadata.get(key) != value:
            return False
    return True


class InMemoryVectorStore:
    """Deterministic in-memory cosine vector store (offline)."""

    def __init__(self, embeddings=None) -> None:
        self.embeddings = embeddings or get_embeddings()
        self._records: list[VectorRecord] = []
        self._ids: set[str] = set()

    def add(
        self, texts: list[str], metadatas: list[dict[str, Any]], ids: list[str] | None = None
    ) -> list[str]:
        if ids is None:
            ids = [f"rec-{len(self._records) + i}" for i in range(len(texts))]
        vectors = self.embeddings.embed_documents(texts)
        for text, vector, meta, rid in zip(texts, vectors, metadatas, ids):
            if rid in self._ids:
                # Replace existing record (dedup by id).
                self._records = [r for r in self._records if r.id != rid]
            self._records.append(VectorRecord(rid, text, vector, meta))
            self._ids.add(rid)
        return ids

    def search(
        self, query: str, k: int = 4, filter: dict[str, Any] | None = None
    ) -> list[tuple[str, float, dict[str, Any]]]:
        if not self._records:
            return []
        qv = self.embeddings.embed_query(query)
        scored = [
            (rec.text, _cosine(qv, rec.vector), rec.metadata)
            for rec in self._records
            if _matches_filter(rec.metadata, filter)
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def delete(self, ids: list[str]) -> None:
        idset = set(ids)
        self._records = [r for r in self._records if r.id not in idset]
        self._ids -= idset

    @property
    def count(self) -> int:
        return len(self._records)


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is not None:
        return _store
    settings = get_settings()
    if settings.vector_store == "chroma":
        _store = _build_chroma(settings)
    else:
        _store = InMemoryVectorStore()
    return _store


def reset_vector_store() -> None:
    """Reset the cached store (used by tests)."""
    global _store
    _store = None


def _build_chroma(settings) -> VectorStore:
    try:
        import chromadb
        from langchain_chroma import Chroma
    except ImportError as exc:  # pragma: no cover
        # Fall back gracefully with a clear signal rather than crashing startup.
        import logging

        logging.getLogger(__name__).warning(
            "Chroma requested but not installed; falling back to in-memory store. "
            "Install with: pip install langchain-chroma chromadb"
        )
        return InMemoryVectorStore()
    import os

    os.makedirs(settings.chroma_persist_directory, exist_ok=True)
    client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
    embeddings = get_embeddings()
    # langchain-chroma accepts a custom embedding function.
    return Chroma(  # pragma: no cover - needs Chroma installed
        client=client,
        collection_name="sahayak_knowledge",
        embedding_function=embeddings,
    )
