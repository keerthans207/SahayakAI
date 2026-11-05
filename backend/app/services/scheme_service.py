"""Scheme discovery service.

Loads the scheme registry from the seeded JSON files under ``data/`` and offers
filtering, search and category aggregation. Schemes can optionally be persisted
to the database via :meth:`SchemeService.sync_to_db` (used by ``seed_schemes.py``).

The service works without a database so discovery remains testable offline.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings

# Category display names for the API category endpoint.
CATEGORY_LABELS = {
    "education": "Education & Scholarships",
    "employment": "Employment & Skill Development",
    "financial_support": "Financial Support & Pension",
    "assistive_technology": "Assistive Technology & Devices",
    "rehabilitation": "Rehabilitation Services",
    "travel": "Accessibility & Travel Concessions",
    "housing": "Housing & Social Welfare",
    "identity": "Identity & Certification (UDID / OTR)",
    "general": "General Government Assistance",
}


def _data_root() -> Path:
    settings = get_settings()
    # data/ lives at the project root (parent of backend/).
    root = Path(settings.chroma_persist_directory).resolve().parent.parent
    # Fallback to a workspace-relative path if the above looks unusual.
    here = Path(__file__).resolve()
    candidate = here.parents[3] / "data"
    return candidate if candidate.exists() else root


def _load_registry() -> list[dict[str, Any]]:
    """Load every schemes.json under data/<level>/ into a flat list."""
    root = _data_root()
    schemes: list[dict[str, Any]] = []
    if not root.exists():
        return schemes
    for json_path in sorted(root.glob("*/schemes.json")):
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for s in payload.get("schemes", []):
            schemes.append(s)
    return schemes


@lru_cache(maxsize=1)
def get_registry() -> list[dict[str, Any]]:
    return _load_registry()


class SchemeService:
    """In-memory scheme registry with filtering and search."""

    def __init__(self, registry: list[dict[str, Any]] | None = None) -> None:
        self._registry = registry if registry is not None else get_registry()

    @property
    def schemes(self) -> list[dict[str, Any]]:
        return self._registry

    def list_schemes(
        self,
        *,
        category: str | None = None,
        government_level: str | None = None,
        state: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        items = self._filter(category, government_level, state, status)
        total = len(items)
        start = (page - 1) * page_size
        return items[start : start + page_size], total

    def get_scheme(self, scheme_id: str) -> dict[str, Any] | None:
        for s in self._registry:
            if s.get("scheme_id") == scheme_id:
                return s
        return None

    def get_categories(self) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for s in self._registry:
            cat = s.get("category", "general")
            counts[cat] = counts.get(cat, 0) + 1
        result = []
        for cat, count in sorted(counts.items()):
            result.append(
                {
                    "category": cat,
                    "label": CATEGORY_LABELS.get(cat, cat.replace("_", " ").title()),
                    "count": count,
                }
            )
        return result

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        government_level: str | None = None,
        state: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        q = query.lower().strip() if query else ""
        filtered = self._filter(category, government_level, state, status)
        if not q:
            return self._paginate(filtered, page, page_size)
        scored: list[tuple[float, dict[str, Any]]] = []
        for s in filtered:
            haystack = " ".join(
                str(s.get(k, ""))
                for k in ("official_name", "description", "category", "department", "benefit_description")
            ).lower()
            score = sum(1.0 for term in q.split() if term in haystack)
            # Boost exact scheme_id / category matches.
            if s.get("scheme_id", "").lower().startswith(q):
                score += 5
            if s.get("category", "").lower() == q:
                score += 3
            if score > 0:
                scored.append((score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        return self._paginate([s for _, s in scored], page, page_size)

    def discover_for_profile(self, profile: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
        """Return schemes likely relevant to a profile (state + category hints)."""
        scored: list[tuple[int, dict[str, Any]]] = []
        p_state = (profile.get("state") or "").lower()
        for s in self._registry:
            score = 0
            s_state = (s.get("applicable_state") or "").lower()
            if not s_state:  # central schemes apply broadly
                score += 1
            if s_state == p_state:
                score += 3
            scored.append((score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:limit]]

    def get_rules(self, scheme_id: str) -> list[dict[str, Any]]:
        scheme = self.get_scheme(scheme_id)
        return scheme.get("rules", []) if scheme else []

    def get_sources(self, scheme_id: str) -> list[dict[str, Any]]:
        scheme = self.get_scheme(scheme_id)
        return scheme.get("sources", []) if scheme else []

    # ---- helpers ----------------------------------------------------------- #
    def _filter(self, category, government_level, state, status) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for s in self._registry:
            if category and s.get("category") != category:
                continue
            if government_level and s.get("government_level") != government_level:
                continue
            if state:
                s_state = (s.get("applicable_state") or "").lower()
                if s_state and s_state != state.lower():
                    continue
            if status and s.get("scheme_status") != status:
                continue
            items.append(s)
        return items

    @staticmethod
    def _paginate(items: list, page: int, page_size: int) -> tuple[list, int]:
        total = len(items)
        start = (page - 1) * page_size
        return items[start : start + page_size], total


# Module-level singleton for convenience.
def scheme_service() -> SchemeService:
    return SchemeService()


# --------------------------------------------------------------------------- #
# Source registry
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def get_source_registry() -> dict[str, Any]:
    root = _data_root()
    path = root / "source_registry" / "sources.json"
    if not path.exists():
        return {"official_domains": [], "sources": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"official_domains": [], "sources": []}


def is_official_domain(url: str) -> bool:
    """Return True if the URL host is on the official allowlist."""
    if not url:
        return False
    host = re.sub(r"^https?://", "", url).split("/")[0].lower()
    domains = get_source_registry().get("official_domains", [])
    return any(host == d or host.endswith("." + d) for d in domains)
