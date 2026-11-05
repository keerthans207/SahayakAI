"""Document upload, retrieval and deletion — per-user isolation."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.v1._deps import get_current_user_id
from app.config import get_settings
from app.middleware.request_id import get_request_id
from app.schemas.documents import DocumentAssessment, DocumentRead, DocumentUploadAck
from app.services.document_service import DocumentService

router = APIRouter()

# In-process metadata store (durable DB persistence is the production path).
_DOCS: dict[str, dict] = {}


@router.post("/upload", response_model=DocumentUploadAck, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    scheme_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    svc = DocumentService()
    content = await file.read()
    size = len(content)
    problems = svc.validate_upload(file.filename or "", file.content_type, size)
    if problems:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "; ".join(problems))

    text = svc.extract_text(content, file.content_type, file.filename or "upload")
    doc_type = svc.identify_type(text, file.filename or "")
    assessment = svc.assess(text, doc_type, scheme_id=scheme_id)
    # Redact PII before storing any extracted text.
    from app.security.auth import mask_pii

    doc_id = str(uuid.uuid4())
    upload_dir = Path(get_settings().upload_dir) / user_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"{doc_id}_{file.filename}"
    stored_path.write_bytes(content)

    record = {
        "id": doc_id,
        "user_id": user_id,
        "document_type": doc_type,
        "original_filename": file.filename,
        "stored_path": str(stored_path),
        "mime_type": file.content_type,
        "size_bytes": size,
        "extracted_text": mask_pii(text),
        "assessment": assessment,
        "request_id": get_request_id(),
    }
    _DOCS[doc_id] = record
    return DocumentUploadAck(
        document_id=doc_id, document_type=doc_type,
        original_filename=file.filename or "", size_bytes=size,
    )


@router.get("/{document_id}")
async def get_document(document_id: str, user_id: str = Depends(get_current_user_id)):
    record = _DOCS.get(document_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if record["user_id"] != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the document owner")
    # Do not return extracted_text to avoid leaking stored PII.
    return DocumentRead(
        id=record["id"], user_id=record["user_id"], document_type=record["document_type"],
        original_filename=record["original_filename"], mime_type=record["mime_type"],
        size_bytes=record["size_bytes"], created_at=record.get("created_at") or _now(),
        assessment=record["assessment"],
    )


@router.get("/{document_id}/assessment", response_model=DocumentAssessment)
async def get_assessment(document_id: str, user_id: str = Depends(get_current_user_id)):
    record = _DOCS.get(document_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if record["user_id"] != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the document owner")
    return DocumentAssessment(**record["assessment"])


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: str, user_id: str = Depends(get_current_user_id)):
    record = _DOCS.get(document_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if record["user_id"] != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not the document owner")
    try:
        os.remove(record["stored_path"])
    except OSError:
        pass
    _DOCS.pop(document_id, None)
    return None


def _now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)
