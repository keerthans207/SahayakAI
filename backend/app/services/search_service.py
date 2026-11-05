"""Government web search abstraction.

Providers:
- tavily : Tavily API (lazy import of ``tavily-python`` / ``langchain-community``).
- none   : live search unavailable — returns an explicit "unavailable" result.

Search is restricted to the official-domain allowlist from the source registry.
Results preserve URL, title, publisher, publication date (where available),
retrieval timestamp, source domain and a relevant excerpt.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from app.config import ConfigurationError, get_settings
from app.services.scheme_service import get_source_registry, is_official_domain


class SearchProvider(Protocol):
    def is_available(self) -> bool: ...
    def search(self, query: str, *, max_results: int = 5) -> list[dict[str, Any]]: ...


class NoneSearchProvider:
    """Used when no search provider is configured — never fabricates results."""

    def is_available(self) -> bool:
        return False

    def search(self, query: str, *, max_results: int = 5) -> list[dict[str, Any]]:
        return [
            {
                "title": "Live search unavailable",
                "url": "",
                "domain": "",
                "publisher": "",
                "excerpt": (
                    "Live government web search is not configured. Results shown are "
                    "from the local knowledge base only."
                ),
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "official": False,
            }
        ]


class TavilySearchProvider:
    """Tavily search restricted to the official-domain allowlist."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.tavily_api_key:
            raise ConfigurationError("SEARCH_PROVIDER='tavily' requires TAVILY_API_KEY.")
        self._api_key = settings.tavily_api_key
        self._domains = get_source_registry().get("official_domains", [])

    def is_available(self) -> bool:
        return True

    def search(self, query: str, *, max_results: int = 5) -> list[dict[str, Any]]:
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults
        except ImportError:
            return self._fallback_unavailable(
                "Tavily search requires 'langchain-community' and 'tavily-python'."
            )
        try:
            tool = TavilySearchResults(
                max_results=max_results,
                api_key=self._api_key,
                include_domains=self._domains or None,
            )
            raw = tool.invoke({"query": query})
        except Exception:  # noqa: BLE001 - network/credential errors
            return self._fallback_unavailable("Live search call failed.")
        return [self._normalise(item) for item in raw if isinstance(item, dict)]

    @staticmethod
    def _fallback_unavailable(message: str) -> list[dict[str, Any]]:
        return [
            {
                "title": "Live search unavailable",
                "url": "",
                "domain": "",
                "publisher": "",
                "excerpt": message,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "official": False,
            }
        ]

    @staticmethod
    def _normalise(item: dict[str, Any]) -> dict[str, Any]:
        url = item.get("url") or ""
        return {
            "title": item.get("title") or "",
            "url": url,
            "domain": _domain_of(url),
            "publisher": "",
            "publication_date": item.get("published_date"),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "excerpt": item.get("content") or item.get("raw_content") or "",
            "official": is_official_domain(url),
        }


def _domain_of(url: str) -> str:
    if not url:
        return ""
    return url.split("/")[2] if url.startswith("http") else url.split("/")[0]


_provider: SearchProvider | None = None


def get_search_provider() -> SearchProvider:
    global _provider
    if _provider is not None:
        return _provider
    settings = get_settings()
    if settings.search_provider == "tavily":
        try:
            _provider = TavilySearchProvider()
        except ConfigurationError:
            _provider = NoneSearchProvider()
    else:
        _provider = NoneSearchProvider()
    return _provider


def reset_search_provider() -> None:
    global _provider
    _provider = None
