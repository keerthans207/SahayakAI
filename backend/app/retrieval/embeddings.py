"""Embedding provider abstraction.

Providers:
- mock         : deterministic hash-based embeddings (offline, no deps)
- azure_foundry : langchain_azure_ai AzureAIOpenAIApiEmbeddings (lazy)
- openai_compatible : langchain_openai OpenAIEmbeddings (lazy)

The mock embeddings never call a network service and are dimension-stable,
so the in-memory vector store can compute cosine similarity offline for tests.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

from langchain_core.embeddings import Embeddings

from app.config import ConfigurationError, get_settings

MOCK_DIM = 128


class MockEmbeddings(Embeddings):
    """Deterministic bag-of-token hashing embeddings.

    Each token is hashed to two buckets (one positive, one negative) within a
    fixed-dimension vector, then L2-normalised. Semantically similar texts
    therefore produce vectors with higher cosine similarity — enough for the
    in-memory store to retrieve relevant chunks deterministically in tests.
    """

    dimensions: int = MOCK_DIM

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        tokens = self._tokenize(text)
        for tok in tokens:
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimensions
            sign = 1.0 if (h >> 20) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [t for t in text.lower().split() if len(t) > 1]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)


def get_embeddings(provider: str | None = None) -> Embeddings:
    settings = get_settings()
    provider = provider or settings.embedding_provider

    if provider == "mock":
        return MockEmbeddings()

    if provider == "azure_foundry":
        return _build_azure_embeddings(settings)

    if provider == "openai_compatible":
        return _build_openai_embeddings(settings)

    raise ConfigurationError(f"Unknown EMBEDDING_PROVIDER '{provider}'.")


def _require_embedding_model(settings) -> str:
    if not settings.azure_ai_embedding_model:
        raise ConfigurationError(
            "EMBEDDING_PROVIDER='azure_foundry' requires AZURE_AI_EMBEDDING_MODEL."
        )
    return settings.azure_ai_embedding_model


def _build_azure_embeddings(settings) -> Embeddings:
    settings.validate_llm_provider()
    _require_embedding_model(settings)
    try:
        from azure.identity.aio import DefaultAzureCredential
        from langchain_azure_ai.embeddings import AzureAIOpenAIApiEmbeddings
    except ImportError as exc:  # pragma: no cover
        raise ConfigurationError(
            "azure_foundry embeddings require 'langchain-azure-ai'. "
            "Install it with: pip install langchain-azure-ai"
        ) from exc
    return AzureAIOpenAIApiEmbeddings(  # pragma: no cover - needs Azure creds
        project_endpoint=settings.foundry_project_endpoint,
        credential=DefaultAzureCredential(),
        model=settings.azure_ai_embedding_model,
    )


def _build_openai_embeddings(settings) -> Embeddings:
    if not settings.openai_api_key:
        raise ConfigurationError("openai_compatible embeddings require OPENAI_API_KEY.")
    try:
        from langchain_openai import OpenAIEmbeddings
    except ImportError as exc:  # pragma: no cover
        raise ConfigurationError(
            "openai_compatible embeddings require 'langchain-openai'."
        ) from exc
    return OpenAIEmbeddings(  # pragma: no cover - needs endpoint
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
        model=settings.azure_ai_embedding_model or "text-embedding-3-small",
    )
