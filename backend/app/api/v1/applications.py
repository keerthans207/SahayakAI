"""Application management endpoints — user-scoped."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1._deps import get_current_user_id
from app.schemas.applications import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationReadiness,
    ApplicationUpdate,
)
from app.services.application_service import ApplicationService

router = APIRouter()


def _to_read(record: dict) -> ApplicationRead:
    return ApplicationRead(**record)


@router.post("", response_model=ApplicationRead, status_code=201)
async def create_application(
    body: ApplicationCreate,
    user_id: str = Depends(get_current_user_id),
):
    svc = ApplicationService()
    try:
        record = svc.create_application(
            user_id, body.scheme_id,
            required_documents=body.required_documents,
            prerequisites=body.prerequisites,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return _to_read(record)


@router.get("", response_model=list[ApplicationRead])
async def list_applications(user_id: str = Depends(get_current_user_id)):
    svc = ApplicationService()
    return [_to_read(r) for r in svc.list_applications(user_id)]


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(application_id: str, user_id: str = Depends(get_current_user_id)):
    svc = ApplicationService()
    try:
        record = svc.get_application(application_id, user_id)
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the application owner")
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
    return _to_read(record)


@router.patch("/{application_id}", response_model=ApplicationRead)
async def update_application(
    application_id: str,
    body: ApplicationUpdate,
    user_id: str = Depends(get_current_user_id),
):
    svc = ApplicationService()
    try:
        record = svc.update_application(
            application_id, user_id,
            status=body.status,
            completed_fields=body.completed_fields,
            notes=body.notes,
        )
    except (KeyError, PermissionError, ValueError) as exc:
        if isinstance(exc, PermissionError):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the application owner")
        if isinstance(exc, KeyError):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Application not found")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return _to_read(record)


@router.get("/{application_id}/readiness", response_model=ApplicationReadiness)
async def readiness(application_id: str, user_id: str = Depends(get_current_user_id)):
    svc = ApplicationService()
    try:
        report = svc.readiness_report(application_id, user_id)
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the application owner")
    if "error" in report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, report["error"])
    return ApplicationReadiness(**report)
