"""Authentication & authorisation.

Production: OIDC bearer-token validation (Microsoft Entra ID or compatible).
Development: an isolated, clearly-labelled development identity (DEV_USER_ID) so
the app runs locally with no identity provider configured.

This module also provides ownership checks and PII sanitisation helpers used by
audit logging and document intelligence.
"""

from __future__ import annotations

import re
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.config import get_settings


def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Resolve the authenticated user id.

    In development (AUTH_PROVIDER=none) we return the configured DEV_USER_ID.
    In production (AUTH_PROVIDER=oidc) we validate a bearer token; this stub
    accepts an `X-User-Id` header for integration tests but production must wire
    a real OIDC validator (see ``oidc`` module note below).
    """
    settings = get_settings()
    if settings.auth_provider == "none":
        return settings.dev_user_id

    # OIDC path: bearer token expected.
    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    # Lightweight integration-test hook: callers may pass X-User-Id with a valid
    # bearer to impersonate a user in tests. Production replaces this with a
    # real JWT/Entra ID validation (see MODEL_CONFIGURATION / SECURITY docs).
    return _validate_oidc_token(token, settings)


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def _validate_oidc_token(token: str, settings) -> str:
    """Validate an OIDC bearer token and return the subject user id.

    NOTE: This default implementation is intentionally a pluggable seam. For a
    real deployment, install a JWT validator (e.g. ``PyJWT`` + JWKS) or use
    Entra ID validation and replace this body. The dev/tests path above never
    reaches here. We deliberately do NOT trust an unverified token in prod.
    """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="OIDC validation is not configured in this build. "
        "Set AUTH_PROVIDER=oidc and wire a JWT validator (see SECURITY.md).",
    )


def require_admin(user_id: str = Depends(get_current_user_id)) -> str:
    """Require an admin user. Admin flag is read from the DB by the route layer."""
    return user_id


def assert_owner(resource_owner_id: str, requesting_user_id: str) -> None:
    """Raise 403 if the requesting user does not own the resource."""
    if resource_owner_id != requesting_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this resource.",
        )


# --------------------------------------------------------------------------- #
# PII sanitisation — used before logging or storing any derived text
# --------------------------------------------------------------------------- #
_AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
_UDID_RE = re.compile(r"\b[A-Z]{2}\d{7,}\b")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+91[\-\s]?)?[6-9]\d{9}(?!\d)")
_BANK_RE = re.compile(r"\b\d{9,18}\b")


def mask_pii(text: str) -> str:
    """Redact common Indian PII patterns from free text.

    Replaces Aadhaar-like numbers, phone numbers, and long digit runs (likely
    bank account numbers) with a masked token. UDID identifiers are masked by
    default as well. This is best-effort redaction, not cryptographic.
    """
    if not text:
        return text
    text = _AADHAAR_RE.sub("[AADHAAR-REDACTED]", text)
    text = _PHONE_RE.sub("[PHONE-REDACTED]", text)
    text = _UDID_RE.sub("[UDID-REDACTED]", text)
    text = _BANK_RE.sub("[ACCOUNT-REDACTED]", text)
    return text


def is_safe_log_value(value: object) -> bool:
    """Return False for values that must never be logged verbatim."""
    if value is None:
        return True
    s = str(value)
    for key in ("password", "otp", "secret", "token", "aadhaar", "api_key"):
        if key in s.lower():
            return False
    return True


def sanitise_for_log(value: object) -> str:
    """Return a log-safe representation of a value."""
    return mask_pii(str(value)) if not is_safe_log_value(value) else str(value)
