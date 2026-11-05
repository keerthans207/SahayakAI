"""Pydantic request/response schemas for the Sahayak AI API."""

from app.schemas.applications import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationReadiness,
    ApplicationUpdate,
)
from app.schemas.chat import (
    ChatMessageRead,
    ChatSessionCreate,
    ChatSessionRead,
    ChatTurnCreate,
    ChatTurnResponse,
    LanguagePreferenceUpdate,
)
from app.schemas.common import ErrorResponse, HealthResponse, Page, ReadyResponse
from app.schemas.documents import DocumentAssessment, DocumentRead, DocumentUploadAck
from app.schemas.eligibility import (
    EligibilityEvaluationRequest,
    EligibilityOutcome,
    EligibilityRead,
    RequirementResult,
)
from app.schemas.scheme import (
    SchemeCategoryRead,
    SchemeRead,
    SchemeSearchRequest,
    SchemeSummary,
)
from app.schemas.speech import SynthesizeRequest, SynthesizeResponse, TranscribeResponse
from app.schemas.user import ProfileUpdate, UserProfileRead

__all__ = [
    "ApplicationCreate",
    "ApplicationRead",
    "ApplicationReadiness",
    "ApplicationUpdate",
    "ChatMessageRead",
    "ChatSessionCreate",
    "ChatSessionRead",
    "ChatTurnCreate",
    "ChatTurnResponse",
    "DocumentAssessment",
    "DocumentRead",
    "DocumentUploadAck",
    "EligibilityEvaluationRequest",
    "EligibilityOutcome",
    "EligibilityRead",
    "ErrorResponse",
    "HealthResponse",
    "LanguagePreferenceUpdate",
    "Page",
    "ProfileUpdate",
    "ReadyResponse",
    "RequirementResult",
    "SchemeCategoryRead",
    "SchemeRead",
    "SchemeSearchRequest",
    "SchemeSummary",
    "SynthesizeRequest",
    "SynthesizeResponse",
    "TranscribeResponse",
    "UserProfileRead",
]
