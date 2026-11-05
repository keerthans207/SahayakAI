"""LangChain tools used by the Sahayak graph nodes."""

from app.agents.tools.application_tool import (
    application_checklist_tool,
    application_readiness_tool,
)
from app.agents.tools.document_tool import (
    document_checklist_tool,
    missing_documents_tool,
)
from app.agents.tools.eligibility_tool import eligibility_tool
from app.agents.tools.government_search import government_search_tool
from app.agents.tools.scheme_search import scheme_search_tool

ALL_TOOLS = [
    scheme_search_tool,
    government_search_tool,
    eligibility_tool,
    document_checklist_tool,
    missing_documents_tool,
    application_checklist_tool,
    application_readiness_tool,
]

__all__ = [
    "ALL_TOOLS",
    "application_checklist_tool",
    "application_readiness_tool",
    "document_checklist_tool",
    "eligibility_tool",
    "government_search_tool",
    "missing_documents_tool",
    "scheme_search_tool",
]
