"""API integration tests — health, chat, schemes, eligibility, applications."""

from __future__ import annotations

import pytest


# ---- health --------------------------------------------------------------- #
async def test_health(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_ready(client):
    r = await client.get("/api/v1/ready")
    assert r.status_code == 200
    data = r.json()
    assert data["llm_provider"] == "mock"
    assert data["database"] is True  # SQLite always ready in test


# ---- schemes -------------------------------------------------------------- #
async def test_list_schemes(client):
    r = await client.get("/api/v1/schemes")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 10
    assert len(data["items"]) >= 1


async def test_get_scheme(client):
    r = await client.get("/api/v1/schemes/adip_scheme")
    assert r.status_code == 200
    assert r.json()["scheme_id"] == "adip_scheme"
    assert r.json()["category"] == "assistive_technology"


async def test_scheme_not_found(client):
    r = await client.get("/api/v1/schemes/does_not_exist")
    assert r.status_code == 404


async def test_scheme_categories(client):
    r = await client.get("/api/v1/schemes/categories")
    assert r.status_code == 200
    cats = r.json()
    names = [c["category"] for c in cats]
    assert "education" in names
    assert "assistive_technology" in names


async def test_scheme_search(client):
    r = await client.get("/api/v1/schemes/search?q=scholarship")
    assert r.status_code == 200
    assert r.json()["total"] >= 3


async def test_scheme_filter_state(client):
    r = await client.get("/api/v1/schemes?state=Karnataka")
    items = r.json()["items"]
    assert items
    # Central schemes (applicable_state=null) also appear because they apply nationwide.
    # No item should have a non-Karnataka state value.
    for item in items:
        s = item["applicable_state"]
        assert s is None or s == "Karnataka", f"Unexpected state: {s}"
    # At least some Karnataka-specific schemes must be included.
    assert any(item["applicable_state"] == "Karnataka" for item in items)


# ---- eligibility ---------------------------------------------------------- #
async def test_evaluate_eligibility_likely(client):
    r = await client.post(
        "/api/v1/eligibility/evaluate",
        json={
            "scheme_id": "adip_scheme",
            "profile": {
                "disability_percentage": 60,
                "income_amount": 100000,
                "available_documents": ["disability_certificate_or_udid", "income_certificate"],
                "udid_status": "has_udid",
            },
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["outcome"] in ("likely_eligible", "potentially_eligible")
    assert data["next_steps"]


async def test_evaluate_eligibility_not_eligible(client):
    r = await client.post(
        "/api/v1/eligibility/evaluate",
        json={
            "scheme_id": "adip_scheme",
            "profile": {"disability_percentage": 10},
        },
    )
    assert r.status_code == 200
    assert r.json()["outcome"] == "not_eligible"


async def test_evaluate_eligibility_missing_info(client):
    r = await client.post(
        "/api/v1/eligibility/evaluate",
        json={"scheme_id": "adip_scheme", "profile": {}},
    )
    assert r.status_code == 200
    assert r.json()["outcome"] == "insufficient_information"


async def test_evaluate_unknown_scheme(client):
    r = await client.post(
        "/api/v1/eligibility/evaluate",
        json={"scheme_id": "no_such_scheme", "profile": {}},
    )
    assert r.status_code == 404


async def test_get_assessment_by_id(client):
    post_r = await client.post(
        "/api/v1/eligibility/evaluate",
        json={"scheme_id": "adip_scheme", "profile": {"disability_percentage": 50}},
    )
    assessment_id = post_r.json()["id"]
    get_r = await client.get(f"/api/v1/eligibility/{assessment_id}")
    assert get_r.status_code == 200
    assert get_r.json()["id"] == assessment_id


# ---- chat ----------------------------------------------------------------- #
async def test_create_chat_session(client):
    r = await client.post("/api/v1/chat/sessions", json={"title": "Test session"})
    assert r.status_code == 201
    assert r.json()["id"]


async def test_get_chat_session(client):
    cr = await client.post("/api/v1/chat/sessions", json={})
    sid = cr.json()["id"]
    r = await client.get(f"/api/v1/chat/sessions/{sid}")
    assert r.status_code == 200
    assert r.json()["session"]["id"] == sid
    assert r.json()["messages"] == []


async def test_send_message_and_get_response(client):
    cr = await client.post("/api/v1/chat/sessions", json={"preferred_language": "en"})
    sid = cr.json()["id"]
    r = await client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        json={"content": "Find scholarship schemes for persons with disabilities in Karnataka"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["role"] == "assistant"
    assert data["content"]
    assert data["intent"] == "scheme_discovery"


async def test_conversation_history_preserved(client):
    cr = await client.post("/api/v1/chat/sessions", json={})
    sid = cr.json()["id"]
    await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": "I am from Karnataka"})
    await client.post(f"/api/v1/chat/sessions/{sid}/messages", json={"content": "Find schemes"})
    get_r = await client.get(f"/api/v1/chat/sessions/{sid}")
    msgs = get_r.json()["messages"]
    assert len(msgs) == 4  # 2 user + 2 assistant


async def test_delete_chat_session(client):
    cr = await client.post("/api/v1/chat/sessions", json={})
    sid = cr.json()["id"]
    dr = await client.delete(f"/api/v1/chat/sessions/{sid}")
    assert dr.status_code == 204
    gr = await client.get(f"/api/v1/chat/sessions/{sid}")
    assert gr.status_code == 404


async def test_chat_session_not_found(client):
    r = await client.get("/api/v1/chat/sessions/nonexistent-id")
    assert r.status_code == 404


async def test_stream_endpoint_returns_events(client):
    cr = await client.post("/api/v1/chat/sessions", json={})
    sid = cr.json()["id"]
    r = await client.post(
        f"/api/v1/chat/sessions/{sid}/stream",
        json={"content": "hello"},
    )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    body = r.text
    assert "data:" in body


# ---- applications --------------------------------------------------------- #
async def test_create_application(client):
    r = await client.post("/api/v1/applications", json={"scheme_id": "adip_scheme"})
    assert r.status_code == 201
    data = r.json()
    assert data["scheme_id"] == "adip_scheme"
    assert data["status"] == "discovered"


async def test_list_applications(client):
    await client.post("/api/v1/applications", json={"scheme_id": "adip_scheme"})
    r = await client.get("/api/v1/applications")
    assert r.status_code == 200
    assert len(r.json()) >= 1


async def test_get_application(client):
    cr = await client.post("/api/v1/applications", json={"scheme_id": "adip_scheme"})
    app_id = cr.json()["id"]
    r = await client.get(f"/api/v1/applications/{app_id}")
    assert r.status_code == 200
    assert r.json()["id"] == app_id


async def test_update_application_status(client):
    cr = await client.post("/api/v1/applications", json={"scheme_id": "adip_scheme"})
    app_id = cr.json()["id"]
    r = await client.patch(
        f"/api/v1/applications/{app_id}",
        json={"status": "eligibility_pending"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "eligibility_pending"


async def test_application_readiness(client):
    cr = await client.post("/api/v1/applications", json={"scheme_id": "adip_scheme"})
    app_id = cr.json()["id"]
    r = await client.get(f"/api/v1/applications/{app_id}/readiness")
    assert r.status_code == 200
    data = r.json()
    assert "ready" in data
    assert "missing_documents" in data
    assert "report" in data


async def test_application_unknown_scheme_rejected(client):
    r = await client.post("/api/v1/applications", json={"scheme_id": "no_such_scheme"})
    assert r.status_code == 400


# ---- pagination & validation ---------------------------------------------- #
async def test_page_size_respected(client):
    r = await client.get("/api/v1/schemes?page=1&page_size=3")
    assert r.status_code == 200
    assert len(r.json()["items"]) <= 3


async def test_invalid_message_content_rejected(client):
    cr = await client.post("/api/v1/chat/sessions", json={})
    sid = cr.json()["id"]
    r = await client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        json={"content": ""},
    )
    assert r.status_code == 422
