"""Application guidance tools — checklist generation & readiness report."""

from __future__ import annotations

from langchain_core.tools import tool

from app.services.application_service import ApplicationService


@tool
def application_checklist_tool(scheme_id: str, user_id: str = "dev-user") -> dict:
    """Generate a scheme-specific application checklist (required documents + prerequisites).

    Args:
        scheme_id: the registered scheme id.
        user_id: the applicant id.
    """
    svc = ApplicationService()
    return svc.build_checklist(scheme_id, user_id)


@tool
def application_readiness_tool(application_id: str, user_id: str = "dev-user") -> dict:
    """Produce an application-readiness report for an existing application.

    Args:
        application_id: the application id.
        user_id: the applicant id (must own the application).
    """
    svc = ApplicationService()
    return svc.readiness_report(application_id, user_id)
