"""Scheme registry / discovery tests."""

from __future__ import annotations

from app.services.scheme_service import SchemeService, is_official_domain


def test_registry_loaded():
    svc = SchemeService()
    assert len(svc.schemes) >= 10
    ids = {s["scheme_id"] for s in svc.schemes}
    assert "pm_post_matric_pwd" in ids
    assert "karnataka_pwd_scholarship" in ids


def test_get_scheme():
    svc = SchemeService()
    s = svc.get_scheme("adip_scheme")
    assert s is not None
    assert s["category"] == "assistive_technology"


def test_get_scheme_unknown():
    assert SchemeService().get_scheme("nope") is None


def test_categories():
    cats = SchemeService().get_categories()
    names = [c["category"] for c in cats]
    assert "education" in names
    assert "financial_support" in names
    assert all(c["count"] >= 1 for c in cats)


def test_search_scholarship():
    items, total = SchemeService().search("scholarship")
    assert total >= 3
    assert any(s["scheme_id"] == "pm_post_matric_pwd" for s in items)


def test_filter_by_government_level():
    items, total = SchemeService().list_schemes(government_level="state")
    assert all(s["government_level"] == "state" for s in items)
    assert total >= 4  # karnataka schemes


def test_filter_by_category():
    items, total = SchemeService().list_schemes(category="assistive_technology")
    assert all(s["category"] == "assistive_technology" for s in items)
    assert total == 1


def test_filter_by_state():
    items, total = SchemeService().list_schemes(state="Karnataka")
    # Central schemes (no applicable_state) are always included.
    # Karnataka-specific schemes are also included.
    # No scheme with a different state (e.g. "Tamil Nadu") should appear.
    for s in items:
        sv = (s.get("applicable_state") or "").lower()
        assert sv in ("", "karnataka"), f"Unexpected state: {sv}"
    assert total >= 4
    assert any((s.get("applicable_state") or "").lower() == "karnataka" for s in items)


def test_discover_for_profile():
    items = SchemeService().discover_for_profile({"state": "Karnataka"})
    assert items
    # Karnataka schemes should rank high for a Karnataka profile.
    assert items[0].get("applicable_state") == "Karnataka"


def test_scheme_has_rules_and_sources():
    s = SchemeService().get_scheme("pm_post_matric_pwd")
    assert s["rules"]
    assert s["sources"]
    for src in s["sources"]:
        assert src["url"].startswith("http")


def test_is_official_domain():
    assert is_official_domain("https://depwd.gov.in/page") is True
    assert is_official_domain("https://scholarships.gov.in") is True
    assert is_official_domain("https://example.com") is False
    assert is_official_domain("https://blog.example.org/post") is False


def test_no_fabricated_fields():
    # No scheme should claim a fabricated "verified" status in seed data.
    for s in SchemeService().schemes:
        assert s["confidence_status"] == "needs_verification"
