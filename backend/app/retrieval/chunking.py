"""Text chunking with configurable size/overlap and content hashing."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class Chunk:
    text: str
    index: int
    page_number: int | None
    content_hash: str


def make_splitter(chunk_size: int = 1000, chunk_overlap: int = 200) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )


def chunk_text(
    text: str,
    *,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    page_number: int | None = None,
) -> list[Chunk]:
    """Split ``text`` into overlapping chunks with per-chunk content hashes."""
    if not text or not text.strip():
        return []
    splitter = make_splitter(chunk_size, chunk_overlap)
    pieces = splitter.split_text(text)
    chunks: list[Chunk] = []
    for i, piece in enumerate(pieces):
        chunks.append(
            Chunk(
                text=piece,
                index=i,
                page_number=page_number,
                content_hash=content_hash(piece),
            )
        )
    return chunks
