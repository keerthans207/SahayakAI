"""Scheme discovery endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.common import Page
from app.schemas.scheme import (
    SchemeCategoryRead,
    SchemeRead,
    SchemeSearchRequest,
    SchemeSummary,
)
from app.services.scheme_service import SchemeService

router = APIRouter()


@router.get("", response_model=Page[SchemeSummary])
async def list_schemes(
    category: str | None = None,
    government_level: str | None = None,
    state: str | None = None,
    status_: str | None = Query(None, alias="status"),
    page: int = 1,
    page_size: int = 20,
):
    svc = SchemeService()
    items, total = svc.list_schemes(
        category=category,
        government_level=government_level,
        state=state,
        status=status_,
        page=page,
        page_size=page_size,
    )
    return Page[SchemeSummary](items=[SchemeSummary(**s) for s in items], total=total, page=page, page_size=page_size)


@router.get("/categories", response_model=list[SchemeCategoryRead])
async def categories():
    svc = SchemeService()
    return [SchemeCategoryRead(**c) for c in svc.get_categories()]


@router.get("/search", response_model=Page[SchemeSummary])
async def search_schemes(
    q: str = "",
    category: str | None = None,
    government_level: str | None = None,
    state: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    svc = SchemeService()
    items, total = svc.search(
        q, category=category, government_level=government_level,
        state=state, status=status, page=page, page_size=page_size,
    )
    return Page[SchemeSummary](items=[SchemeSummary(**s) for s in items], total=total, page=page, page_size=page_size)


@router.get("/{scheme_id}", response_model=SchemeRead)
async def get_scheme(scheme_id: str):
    svc = SchemeService()
    scheme = svc.get_scheme(scheme_id)
    if scheme is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scheme not found")
    return SchemeRead(**scheme)
