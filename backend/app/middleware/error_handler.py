"""Global error handling & security headers."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import ConfigurationError, get_settings
from app.middleware.request_id import get_request_id
from app.security.auth import sanitise_for_log


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        return response


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ConfigurationError)
    async def _config_error(_: Request, exc: ConfigurationError):
        return JSONResponse(
            status_code=503,
            content={
                "error": "configuration_error",
                "detail": sanitise_for_log(str(exc)),
                "request_id": get_request_id(),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "detail": exc.errors(),
                "request_id": get_request_id(),
            },
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        # Never leak internals; the message is sanitised of PII/secret markers.
        settings = get_settings()
        detail = sanitise_for_log(str(exc)) if settings.is_dev else "Internal server error"
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "detail": detail,
                "request_id": get_request_id(),
            },
        )
