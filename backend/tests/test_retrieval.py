"""RAG ingestion & retrieval tests (offline, in-memory store)."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from app.retrieval.chunking import chunk_text, content_hash
from app.retrieval.embeddings import MockEmbeddings
from app.retrieval.ingestion import ingest_document
from app.retrieval.metadata import is_stale
from app.retrieval.vector_store import InMemoryVectorStore
from app.services.retrieval_service import RetrievalService


def _make_pdf(path: Path, pages: list[str]) -> None:
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path))
    for text in pages:
        c.drawString(72, 800, text)
        c.showPage()
    c.save()


def test_chunk_text_basic():
    text = "word " * 600
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=40)
    assert len(chunks) > 1
    assert all(c.content_hash for c in chunks)


def test_content_hash_dedup():
    text = "The ADIP scheme provides assistive devices to persons with disabilities."
    h1 = content_hash(text)
    h2 = content_hash(text)
    assert h1 == h2
    assert content_hash("different text") != h1


def test_ingest_txt_and_retrieve(tmp_path, fresh_vector_store):
    f = tmp_path / "scheme.txt"
    f.write_text(
        "The Post Matric Scholarship for Students with Disabilities supports higher education. "
        "Applicants need a disability certificate, income certificate and marksheets.",
        encoding="utf-8",
    )
    result = ingest_document(f, official_source_url="https://scholarships.gov.in")
    assert result.duplicate is False
    assert result.chunk_count >= 1

    rs = RetrievalService()
    ev = rs.retrieve("scholarship for disabled students", k=2)
    assert ev
    top = ev[0]
    assert "scholarship" in top.text.lower()
    # Citation preserves source url + official flag.
    assert top.citation()["source_status"] == "official"
    assert top.metadata["official_source_url"] == "https://scholarships.gov.in"


def test_pdf_ingestion_page_attribution(tmp_path, fresh_vector_store):
    pdf = tmp_path / "doc.pdf"
    _make_pdf(pdf, [
        "Page one is about the ADIP assistive device scheme run by DEPwD.",
        "Page two explains the eligibility income criteria for disability pension.",
    ])
    result = ingest_document(pdf, official_source_url="https://depwd.gov.in")
    assert result.page_count == 2
    rs = RetrievalService()
    ev = rs.retrieve("income criteria for disability pension", k=4)
    assert ev
    # At least one retrieved chunk should carry a page number from the PDF.
    paged = [e for e in ev if e.metadata.get("page_number") is not None]
    assert paged, "expected page-number metadata from PDF ingestion"
    assert paged[0].citation()["source_status"] == "official"


def test_duplicate_document_detection(tmp_path, fresh_vector_store):
    f = tmp_path / "dup.txt"
    f.write_text("Identical content for dedup test. " * 20, encoding="utf-8")
    known = set()
    first = ingest_document(f, known_hashes=known)
    assert first.duplicate is False
    second = ingest_document(f, known_hashes=known)
    assert second.duplicate is True
    assert second.chunk_count == 0


def test_stale_document_warning():
    old = date.today() - timedelta(days=400)
    assert is_stale(old) is True
    recent = date.today() - timedelta(days=10)
    assert is_stale(recent) is False
    assert is_stale(None) is True  # unknown age treated as stale


def test_unofficial_source_marked_unverified(tmp_path, fresh_vector_store):
    f = tmp_path / "blog.txt"
    f.write_text("Some unofficial summary of a disability scheme.", encoding="utf-8")
    ingest_document(f, official_source_url="https://blog.example.org/post")
    rs = RetrievalService()
    ev = rs.retrieve("disability scheme", k=2)
    assert ev
    # Non-official domain should be flagged unverified and filtered from evidence.
    assert all(e.official is False for e in ev)
    assert ev[0].citation()["source_status"] == "unverified"


def test_empty_store_returns_nothing():
    rs = RetrievalService(store=InMemoryVectorStore(MockEmbeddings()))
    assert rs.retrieve("anything") == []
    assert rs.is_available() is False
