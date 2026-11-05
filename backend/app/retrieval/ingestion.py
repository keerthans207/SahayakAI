"""Document ingestion: extract -> clean -> chunk -> embed -> store.

Supports PDF, DOCX, TXT and HTML. Each loader is imported lazily so the app runs
without every parser installed; only the loader for the requested file type is
needed.

Duplicate documents are detected via the content hash of the full extracted
text — the same file (or an identical re-upload) is not re-ingested.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.retrieval.chunking import Chunk, chunk_text, content_hash
from app.retrieval.embeddings import get_embeddings
from app.retrieval.metadata import build_metadata
from app.retrieval.vector_store import InMemoryVectorStore, get_vector_store


@dataclass
class IngestionResult:
    document_id: str
    document_name: str
    document_type: str
    page_count: int
    chunk_count: int
    content_hash: str
    duplicate: bool


def extract_text(path: str | Path) -> tuple[str, list[str]]:
    """Return (full_text, pages) where pages[i] is the text of page i+1.

    For formats without pages (txt/docx/html) a single "page" is returned.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _load_pdf(path)
    if suffix == ".docx":
        return _load_docx(path)
    if suffix in (".txt", ".md"):
        return _load_text(path)
    if suffix in (".html", ".htm"):
        return _load_html(path)
    raise ValueError(f"Unsupported document type: {suffix}")


def _load_pdf(path: Path) -> tuple[str, list[str]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("PDF ingestion requires 'pypdf'. Install it with: pip install pypdf") from exc
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages), pages


def _load_docx(path: Path) -> tuple[str, list[str]]:
    try:
        import docx
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("DOCX ingestion requires 'python-docx'.") from exc
    doc = docx.Document(str(path))
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return text, [text]


def _load_text(path: Path) -> tuple[str, list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return text, [text]


def _load_html(path: Path) -> tuple[str, list[str]]:
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("HTML ingestion requires 'beautifulsoup4'.") from exc
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    text = "\n".join(lines)
    return text, [text]


def ingest_document(
    path: str | Path,
    *,
    document_id: str | None = None,
    document_name: str | None = None,
    scheme_id: str | None = None,
    department: str | None = None,
    government_level: str | None = None,
    applicable_state: str | None = None,
    language: str | None = None,
    official_source_url: str | None = None,
    store: Any | None = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    known_hashes: set[str] | None = None,
) -> IngestionResult:
    """Ingest a single document into the vector store.

    ``known_hashes`` lets callers skip documents already ingested (dedup).
    """
    path = Path(path)
    store = store or get_vector_store()
    full_text, pages = extract_text(path)
    doc_hash = content_hash(full_text)
    document_id = document_id or f"doc-{doc_hash[:12]}"
    document_name = document_name or path.name
    document_type = path.suffix.lower().lstrip(".")

    if known_hashes is not None and doc_hash in known_hashes:
        return IngestionResult(
            document_id=document_id,
            document_name=document_name,
            document_type=document_type,
            page_count=len(pages),
            chunk_count=0,
            content_hash=doc_hash,
            duplicate=True,
        )

    # Chunk per page so page numbers are attributed correctly.
    all_chunks: list[Chunk] = []
    for page_idx, page_text in enumerate(pages, start=1):
        chunks = chunk_text(
            page_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            page_number=page_idx if len(pages) > 1 else None,
        )
        all_chunks.extend(chunks)

    texts = [c.text for c in all_chunks]
    metadatas = [
        build_metadata(
            document_id=document_id,
            document_name=document_name,
            document_type=document_type,
            scheme_id=scheme_id,
            department=department,
            government_level=government_level,
            applicable_state=applicable_state,
            language=language,
            official_source_url=official_source_url,
            page_number=c.page_number,
            content_hash=c.content_hash,
        )
        for c in all_chunks
    ]
    ids = [f"{document_id}-c{c.index}-p{c.page_number or 0}" for c in all_chunks]
    if texts:
        store.add(texts, metadatas, ids=ids)

    if known_hashes is not None:
        known_hashes.add(doc_hash)

    return IngestionResult(
        document_id=document_id,
        document_name=document_name,
        document_type=document_type,
        page_count=len(pages),
        chunk_count=len(all_chunks),
        content_hash=doc_hash,
        duplicate=False,
    )


def ingest_directory(
    directory: str | Path,
    *,
    store: Any | None = None,
    **kwargs: Any,
) -> list[IngestionResult]:
    """Ingest every supported document in a directory (recursively)."""
    directory = Path(directory)
    store = store or get_vector_store()
    known_hashes: set[str] = set()
    results: list[IngestionResult] = []
    for path in sorted(directory.rglob("*")):
        if path.suffix.lower() not in (".pdf", ".docx", ".txt", ".md", ".html", ".htm"):
            continue
        try:
            results.append(ingest_document(path, store=store, known_hashes=known_hashes, **kwargs))
        except Exception:  # noqa: BLE001 - keep ingesting other files
            continue
    return results
