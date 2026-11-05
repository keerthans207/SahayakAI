"""Admin endpoints — must be explicitly protected.

No unrestricted admin routes are exposed by default. The single admin endpoint
here checks the ``is_admin`` flag on the user record (seeded via DB). In a
production build, gate this with a real Entra ID admin role check.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._deps import get_current_user_id, get_db
from app.models.db import User
from app.services.scheme_service import SchemeService

router = APIRouter()


async def _require_admin(db: AsyncSession, user_id: str) -> User:
    result = await db.execute(select(User).where(User.external_id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user


@router.get("/schemes/count")
async def admin_scheme_count(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    await _require_admin(db, user_id)
    return {"total": len(SchemeService().schemes)}
