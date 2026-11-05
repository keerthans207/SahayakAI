"""Shared API dependencies."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.security.auth import get_current_user_id

# Re-exported so route modules import a single dependency module.
async def db_dep() -> AsyncSession:  # pragma: no cover - thin alias
    async for s in get_db():
        yield s


__all__ = ["get_db", "get_current_user_id", "db_dep"]
