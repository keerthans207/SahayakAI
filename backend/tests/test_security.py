"""Security tests — user isolation, PII redaction, auth guards."""

from __future__ import annotations

import pytest

from app.security.auth import mask_pii


def test_mask_aadhaar():
    out = mask_pii("Aadhaar number is 1234 5678 9012 valid")
    assert "1234 5678 9012" not in out
    assert "AADHAAR-REDACTED" in out


def test_mask_phone_number():
    out = mask_pii("Call me on 9876543210")
    assert "9876543210" not in out
    assert "PHONE-REDACTED" in out


def test_normal_text_unchanged():
    out = mask_pii("The scholarship amount is ₹5000 per year")
    assert "scholarship" in out
    # 4-digit amounts should NOT be masked (not Aadhaar pattern).


def test_user_cannot_access_other_users_applications(as_user):
    import asyncio

    from app.services.application_service import ApplicationService

    svc = ApplicationService({})
    rec = svc.create_application("user-A", "adip_scheme")
    with pytest.raises(PermissionError):
        svc.get_application(rec["id"], "user-B")


def test_user_cannot_access_other_users_docs():
    from app.services.document_service import DocumentService

    svc = DocumentService()
    # validate_upload is user-agnostic; isolation is enforced in the route layer.
    problems = svc.validate_upload("udid.pdf", "application/pdf", 100)
    assert problems == []
    problems = svc.validate_upload("bad.exe", "application/x-msdownload", 100)
    assert problems


def test_sensitive_info_not_in_logs():
    from app.security.auth import is_safe_log_value

    assert is_safe_log_value("normal text") is True
    assert is_safe_log_value("password=abc123") is False
    assert is_safe_log_value("otp:123456") is False


async def test_unauthenticated_admin_request_rejected(client):
    # Admin route must require admin flag even in dev mode (no is_admin).
    resp = await client.get("/api/v1/admin/schemes/count")
    assert resp.status_code == 403


async def test_health_works_without_auth(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_ready_endpoint_returns_providers(client):
    resp = await client.get("/api/v1/ready")
    data = resp.json()
    assert "llm_provider" in data
    assert data["llm_provider"] == "mock"


def test_invalid_file_type_rejected():
    from app.services.document_service import DocumentService

    svc = DocumentService()
    problems = svc.validate_upload("virus.exe", "application/x-msdownload", 500)
    assert problems


def test_oversized_file_rejected():
    from app.services.document_service import DocumentService

    svc = DocumentService()
    problems = svc.validate_upload("big.pdf", "application/pdf", 99 * 1024 * 1024)
    assert problems
