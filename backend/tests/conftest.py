"""Test configuration.

Sets the offline/mock configuration BEFORE any app module is imported, and
provides an isolated async test database + an HTTPX ASGI client. No test needs
Azure credentials, a network connection, Chroma, or an LLM service.
"""

from __future__ import annotations

import os

# Must run before importing anything from `app`.
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("EMBEDDING_PROVIDER", "mock")
os.environ.setdefault("VECTOR_STORE", "memory")
os.environ.setdefault("SEARCH_PROVIDER", "none")
os.environ.setdefault("SPEECH_PROVIDER", "none")
os.environ.setdefault("AUTH_PROVIDER", "none")
os.environ.setdefault("DEV_USER_ID", "dev-user")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_runtime.db")
os.environ.setdefault("UPLOAD_DIR", "./data/test_uploads")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.db import Base


@pytest_asyncio.fixture
async def test_db(tmp_path):
    """Fresh isolated async SQLite database per test."""
    db_path = tmp_path / "test.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    """HTTPX ASGI client with the DB dependency overridden to the test DB."""
    from app.api.v1._deps import get_db
    from app.main import app

    async def override_get_db():
        async with test_db() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def fresh_vector_store():
    """Reset the cached vector store so each retrieval test starts clean."""
    from app.retrieval import vector_store as vs

    vs.reset_vector_store()
    yield vs
    vs.reset_vector_store()


@pytest.fixture
def as_user(client):
    """Return a client that authenticates as a specific user id (dev mode)."""
    def _make(user_id: str) -> AsyncClient:
        from app.api.v1._deps import get_current_user_id
        from app.main import app

        app.dependency_overrides[get_current_user_id] = lambda: user_id
        return client

    return _make
