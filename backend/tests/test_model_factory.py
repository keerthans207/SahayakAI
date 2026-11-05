"""Model provider factory tests (mock + provider construction)."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.model_factory import MockChatModel, get_chat_model
from app.config import ConfigurationError, get_settings


def test_mock_model_deterministic():
    m = get_chat_model("mock")
    assert isinstance(m, MockChatModel)
    r1 = m.invoke([HumanMessage(content="find scholarships")])
    r2 = m.invoke([HumanMessage(content="find scholarships")])
    assert r1.content == r2.content  # deterministic


def test_mock_model_streaming_yields_chunks():
    m = MockChatModel()
    chunks = list(m.stream([HumanMessage(content="hello")]))
    assert len(chunks) > 1
    # Strip whitespace-only tail chunks (word tokenisation may produce them).
    non_empty = [c for c in chunks if c.content.strip()]
    assert non_empty


def test_mock_model_bind_tools_noop():
    m = MockChatModel()
    bound = m.bind_tools(["some_tool"])
    assert bound is m


def test_mock_model_structured_output():
    m = MockChatModel()
    runnable = m.with_structured_output(None)
    out = runnable.invoke([HumanMessage(content="anything")])
    assert isinstance(out, dict)


def test_get_chat_model_unknown_raises():
    with pytest.raises(ConfigurationError):
        get_chat_model("does_not_exist")


def test_mock_context_summary():
    m = MockChatModel()
    sys = SystemMessage(
        content=(
            "You are Sahayak.\n\n[SAHAYAK_CONTEXT]"
            '{"schemes": [{"official_name": "ADIP", "department": "DEPwD", '
            '"scheme_status": "active"}], "official_sources": ['
            '{"title": "DEPwD", "url": "https://depwd.gov.in"}]}'
        )
    )
    out = m.invoke([sys, HumanMessage(content="find assistive device schemes")])
    assert "ADIP" in out.content
    assert "depwd.gov.in" in out.content


def test_azure_provider_missing_config_raises():
    # Even if the package is installed, missing config must raise ConfigurationError.
    get_settings.cache_clear()
    import app.config as cfg

    cfg.get_settings.cache_clear()
    with pytest.raises(ConfigurationError):
        get_chat_model("azure_foundry")
