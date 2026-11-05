#!/usr/bin/env python
"""Ingest government documents into the Sahayak knowledge base.

Usage (from project root):
    python scripts/ingest_documents.py --dir data/central
    python scripts/ingest_documents.py --file path/to/doc.pdf --scheme-id pm_post_matric_pwd

Ingests PDF, DOCX, TXT and HTML files. Deduplicates by content hash so
repeated ingestion is idempotent.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import get_settings
from app.retrieval.ingestion import ingest_directory, ingest_document
from app.retrieval.vector_store import get_vector_store


def parse_args():
    p = argparse.ArgumentParser(description="Ingest government documents")
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--dir", help="Directory of documents to ingest recursively")
    grp.add_argument("--file", help="Single file to ingest")
    p.add_argument("--scheme-id", default=None, help="Associate all documents with a scheme id")
    p.add_argument("--state", default=None, help="Applicable state")
    p.add_argument("--level", default=None, help="government_level (central|state|district)")
    p.add_argument("--url", default=None, help="Official source URL for the documents")
    return p.parse_args()


async def main() -> None:
    args = parse_args()
    settings = get_settings()
    print(f"Vector store: {settings.vector_store}")
    print(f"Embedding provider: {settings.embedding_provider}")
    store = get_vector_store()

    kwargs = {
        "scheme_id": args.scheme_id,
        "applicable_state": args.state,
        "government_level": args.level,
        "official_source_url": args.url,
        "store": store,
    }

    if args.file:
        result = ingest_document(args.file, **kwargs)
        print(f"File: {result.document_name}")
        print(f"  Duplicate: {result.duplicate}")
        print(f"  Chunks: {result.chunk_count}")
        print(f"  Pages: {result.page_count}")
        print(f"  Hash: {result.content_hash[:12]}...")
    else:
        results = ingest_directory(args.dir, **kwargs)
        ingested = sum(1 for r in results if not r.duplicate)
        dupes = sum(1 for r in results if r.duplicate)
        total_chunks = sum(r.chunk_count for r in results)
        print(f"Ingested {ingested} documents, {dupes} duplicates, {total_chunks} chunks total.")


if __name__ == "__main__":
    asyncio.run(main())
