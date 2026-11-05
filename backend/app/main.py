"""Sahayak AI FastAPI application entrypoint.

Run locally (from backend/):  uvicorn app.main:app --reload
The app starts with LLM_PROVIDER=mock by default — no Azure credentials needed.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config import get_settings
from app.database.session import dispose_engine, init_db
from app.middleware.error_handler import (
    SecurityHeadersMiddleware,
    register_exception_handlers,
)
from app.middleware.request_id import RequestIdMiddleware


def _configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_app() -> FastAPI:
    _configure_logging()
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Multilingual government benefits discovery and application assistance "
            "platform for Persons with Disabilities (PwDs) in India."
        ),
    )

    # ---- middleware (order: outer -> inner) ----
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- routes ----
    app.include_router(api_router, prefix="/api/v1")

    # ---- error handlers ----
    register_exception_handlers(app)

    @app.on_event("startup")
    async def _startup() -> None:  # pragma: no cover - lifecycle
        # Create tables for local dev / SQLite. Production uses Alembic.
        try:
            await init_db()
        except Exception as exc:  # noqa: BLE001
            logging.getLogger(__name__).warning("init_db skipped: %s", exc)
        # Validate the configured LLM provider only if it is not the mock.
        # Mock is allowed to run with zero external configuration.
        if settings.llm_provider != "mock":
            try:
                settings.validate_llm_provider()
            except Exception as exc:  # noqa: BLE001
                logging.getLogger(__name__).error("LLM config error: %s", exc)

    @app.on_event("shutdown")
    async def _shutdown() -> None:  # pragma: no cover - lifecycle
        await dispose_engine()

    return app


app = create_app()
