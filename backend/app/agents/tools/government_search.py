"""Government web search tool (Tavily-backed, official-domain restricted)."""

from __future__ import annotations

from langchain_core.tools import tool

from app.services.search_service import get_search_provider


@tool
def government_search_tool(query: str, max_results: int = 5) -> dict:
    """Search official government websites for current scheme information.

    Only official-domain results are treated as authoritative. When live search
    is not configured, returns an explicit 'unavailable' marker — never fabricated
    current results.

    Args:
        query: the search query, e.g. "post matric scholarship PwD 2025".
        max_results: maximum number of results (default 5).
    """
    provider = get_search_provider()
    results = provider.search(query, max_results=max_results)
    return {
        "available": provider.is_available(),
        "results": results,
    }
