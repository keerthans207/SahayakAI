"""Health & readiness endpoints.

``/health`` always works without authentication or Azure credentials.
``/ready`` reports the state of optional integrations (DB, providers).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import _deps
from app.config import get_settings
from app.schemas.common import HealthResponse, ReadyResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    # Never requires credentials — pure liveness check.
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
async def ready(db: AsyncSession = Depends(_deps.get_db)):
    settings = get_settings()
    db_ok = False
    detail = {}
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # noqa: BLE001
        detail["database"] = str(exc)
    return ReadyResponse(
        status="ready" if db_ok else "not_ready",
        database=db_ok,
        llm_provider=settings.llm_provider,
        vector_store=settings.vector_store,
        search_provider=settings.search_provider,
        speech_provider=settings.speech_provider,
        details=detail,
    )
