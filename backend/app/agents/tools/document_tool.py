"""Document assistance tools — required-document checklist & missing detection."""

from __future__ import annotations

from langchain_core.tools import tool

from app.services.scheme_service import SchemeService


def _required_documents(scheme_id: str) -> tuple[list[str], list[str]] | None:
    svc = SchemeService()
    scheme = svc.get_scheme(scheme_id)
    if not scheme:
        return None
    required = list(scheme.get("required_documents", []))
    prerequisites = list(scheme.get("prerequisite_services", []))
    return required, prerequisites


@tool
def document_checklist_tool(scheme_id: str) -> dict:
    """Return the official required-document checklist for a scheme.

    Args:
        scheme_id: the registered scheme id.
    """
    info = _required_documents(scheme_id)
    if info is None:
        return {"error": f"Unknown scheme: {scheme_id}"}
    required, prerequisites = info
    return {
        "scheme_id": scheme_id,
        "required_documents": required,
        "prerequisite_services": prerequisites,
    }


@tool
def missing_documents_tool(scheme_id: str, available_documents: list[str]) -> dict:
    """Compare a user's available documents against a scheme's requirements.

    Args:
        scheme_id: the registered scheme id.
        available_documents: list of document types the user already has.
    """
    info = _required_documents(scheme_id)
    if info is None:
        return {"error": f"Unknown scheme: {scheme_id}"}
    required, prerequisites = info
    available = {d.lower() for d in (available_documents or [])}
    missing = [d for d in required if d.lower() not in available]
    present = [d for d in required if d.lower() in available]
    return {
        "scheme_id": scheme_id,
        "required_documents": required,
        "present_documents": present,
        "missing_documents": missing,
        "prerequisite_services": prerequisites,
    }
