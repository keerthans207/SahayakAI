"""Common API schemas: health, pagination, error envelope."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "Sahayak AI"
    version: str = "0.1.0"


class ReadyResponse(BaseModel):
    status: str  # "ready" | "not_ready"
    database: bool = False
    llm_provider: str = ""
    vector_store: str = ""
    search_provider: str = ""
    speech_provider: str = ""
    details: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    request_id: str | None = None


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Generic paginated list response."""

    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20
