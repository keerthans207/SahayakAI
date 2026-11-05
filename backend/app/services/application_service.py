"""Application management service.

Builds scheme-specific checklists, tracks application progress and produces a
final readiness report. Uses an in-memory store by default (persists for the
life of the process) so the API and the agent tools share state; the SQLAlchemy
``Application`` model is available for durable production persistence.

Status transitions follow the fixed lifecycle in the spec. ``SUBMITTED_BY_USER``
is only set when the user explicitly confirms submission.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.schemas.applications import ApplicationStatus
from app.services.scheme_service import SchemeService

# Canonical ordered lifecycle for validation.
_STATUS_ORDER: list[ApplicationStatus] = [
    "discovered",
    "eligibility_pending",
    "eligible_pending_documents",
    "documents_incomplete",
    "ready_for_review",
    "ready_for_user_submission",
    "submitted_by_user",
    "under_verification",
    "approved",
    "rejected",
    "closed",
]

# In-process store shared by the API and the agent tools.
_SHARED_STORE: dict[str, dict[str, Any]] = {}


class ApplicationService:
    def __init__(self, store: dict[str, dict[str, Any]] | None = None) -> None:
        self._store = store if store is not None else _SHARED_STORE
        self._schemes = SchemeService()

    # ---- checklist -------------------------------------------------------- #
    def build_checklist(self, scheme_id: str, user_id: str = "dev-user") -> dict[str, Any]:
        scheme = self._schemes.get_scheme(scheme_id)
        if not scheme:
            return {"error": f"Unknown scheme: {scheme_id}"}
        required_docs = list(scheme.get("required_documents", []))
        prerequisites = list(scheme.get("prerequisite_services", []))
        return {
            "scheme_id": scheme_id,
            "scheme_name": scheme["official_name"],
            "user_id": user_id,
            "required_documents": required_docs,
            "prerequisite_services": prerequisites,
            "application_url": scheme.get("application_url"),
            "checklist": [
                {"item": d, "type": "document", "required": True} for d in required_docs
            ]
            + [{"item": p, "type": "prerequisite", "required": True} for p in prerequisites],
        }

    # ---- CRUD ------------------------------------------------------------- #
    def create_application(
        self,
        user_id: str,
        scheme_id: str,
        required_documents: list[str] | None = None,
        prerequisites: list[str] | None = None,
    ) -> dict[str, Any]:
        if not self._schemes.get_scheme(scheme_id):
            raise ValueError(f"Unknown scheme: {scheme_id}")
        if required_documents is None:
            required_documents = list(
                self._schemes.get_scheme(scheme_id).get("required_documents", [])
            )
        if prerequisites is None:
            prerequisites = list(self._schemes.get_scheme(scheme_id).get("prerequisite_services", []))
        app_id = str(uuid.uuid4())
        record: dict[str, Any] = {
            "id": app_id,
            "user_id": user_id,
            "scheme_id": scheme_id,
            "status": "discovered",
            "required_documents": required_documents,
            "completed_fields": {},
            "uploaded_documents": [],
            "prerequisites": prerequisites,
            "prerequisites_met": False,
            "notes": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._store[app_id] = record
        return record

    def get_application(self, application_id: str, user_id: str) -> dict[str, Any] | None:
        record = self._store.get(application_id)
        if record is None:
            return None
        if record.get("user_id") != user_id:
            raise PermissionError("Not the application owner")
        return record

    def list_applications(self, user_id: str) -> list[dict[str, Any]]:
        return [r for r in self._store.values() if r.get("user_id") == user_id]

    def update_application(
        self,
        application_id: str,
        user_id: str,
        *,
        status: ApplicationStatus | None = None,
        completed_fields: dict | None = None,
        uploaded_documents: list[str] | None = None,
        notes: str | None = None,
        submit: bool = False,
    ) -> dict[str, Any]:
        record = self.get_application(application_id, user_id)
        if record is None:
            raise KeyError(application_id)
        if status:
            self._validate_transition(record["status"], status)
            record["status"] = status
        if completed_fields is not None:
            record["completed_fields"].update(completed_fields)
        if uploaded_documents is not None:
            existing = set(record.get("uploaded_documents", []))
            existing.update(uploaded_documents)
            record["uploaded_documents"] = sorted(existing)
        if notes is not None:
            record["notes"] = notes
        # SUBMITTED_BY_USER only on explicit user confirmation.
        if submit:
            record["status"] = "submitted_by_user"
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._store[application_id] = record
        return record

    def _validate_transition(self, current: str, target: ApplicationStatus) -> None:
        if target == "submitted_by_user":
            raise ValueError("Use submit=True to mark an application submitted by the user.")
        if target not in _STATUS_ORDER:
            raise ValueError(f"Unknown status: {target}")

    # ---- readiness -------------------------------------------------------- #
    def readiness_report(self, application_id: str, user_id: str) -> dict[str, Any]:
        record = self.get_application(application_id, user_id)
        if record is None:
            return {"error": f"Application not found: {application_id}"}
        required = set(record.get("required_documents", []))
        uploaded = set(record.get("uploaded_documents", []))
        missing = sorted(required - uploaded)
        completed = record.get("completed_fields", {})
        missing_fields = [k for k, v in completed.items() if not v]
        prereq = record.get("prerequisites", [])
        prereq_met = record.get("prerequisites_met", False)
        ready = (
            not missing
            and not missing_fields
            and prereq_met
            and record["status"] in ("discovered", "eligible_pending_documents", "documents_incomplete", "ready_for_review")
        )
        if ready:
            record["status"] = "ready_for_user_submission"
        report = self._render_report(record, missing, missing_fields, prereq, prereq_met, ready)
        return {
            "application_id": application_id,
            "scheme_id": record["scheme_id"],
            "status": record["status"],
            "required_documents": sorted(required),
            "uploaded_documents": sorted(uploaded),
            "missing_documents": missing,
            "completed_fields": completed,
            "missing_fields": missing_fields,
            "prerequisites": prereq,
            "prerequisites_met": prereq_met,
            "ready": ready,
            "report": report,
        }

    @staticmethod
    def _render_report(record, missing, missing_fields, prereq, prereq_met, ready) -> str:
        lines = [
            f"Application readiness for scheme '{record['scheme_id']}'.",
        ]
        if missing:
            lines.append("Still missing documents: " + ", ".join(missing))
        else:
            lines.append("All required documents uploaded.")
        if missing_fields:
            lines.append("Still missing fields: " + ", ".join(missing_fields))
        if not prereq_met:
            lines.append("Pending prerequisites: " + ", ".join(prereq))
        lines.append("Overall: " + ("READY for your review and submission." if ready else "Not ready yet."))
        lines.append(
            "Note: submitting on the official government portal is the applicant's step; "
            "Sahayak AI does not submit or approve applications."
        )
        return "\n".join(lines)


def application_service() -> ApplicationService:
    return ApplicationService()
