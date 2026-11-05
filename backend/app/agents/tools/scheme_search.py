"""Scheme discovery tool."""

from __future__ import annotations

from langchain_core.tools import tool

from app.services.scheme_service import SchemeService


@tool
def scheme_search_tool(query: str = "", category: str = "", state: str = "") -> dict:
    """Search the registered government scheme registry.

    Args:
        query: free-text query, e.g. "scholarship" or "pension".
        category: optional category filter (education, employment, financial_support,
            assistive_technology, rehabilitation, travel, housing, identity).
        state: optional state filter (e.g. "Karnataka").

    Returns a JSON object with matching scheme summaries and their official sources.
    Only schemes present in the registry are returned — never invented.
    """
    svc = SchemeService()
    items, total = svc.search(
        query=query or None,
        category=category or None,
        state=state or None,
        page=1,
        page_size=20,
    )
    summaries = [
        {
            "scheme_id": s["scheme_id"],
            "official_name": s["official_name"],
            "category": s["category"],
            "government_level": s["government_level"],
            "applicable_state": s.get("applicable_state"),
            "benefit_amount": s.get("benefit_amount"),
            "scheme_status": s.get("scheme_status"),
            "confidence_status": s.get("confidence_status"),
            "application_url": s.get("application_url"),
            "sources": s.get("sources", []),
        }
        for s in items
    ]
    return {"count": len(summaries), "total": total, "schemes": summaries}
