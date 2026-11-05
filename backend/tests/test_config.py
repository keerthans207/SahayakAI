"""Configuration tests."""

from __future__ import annotations

import pytest

from app.config import ConfigurationError, Settings


def test_defaults_load_without_secrets():
    s = Settings()
    assert s.llm_provider == "mock"
    assert s.vector_store == "memory"
    assert s.search_provider == "none"
    assert s.app_env == "development"
    assert s.is_dev is True


def test_json_list_parsing():
    s = Settings(cors_origins='["https://a.com","https://b.com"]')
    assert s.cors_origins == ["https://a.com", "https://b.com"]


def test_comma_separated_fallback():
    s = Settings(allowed_upload_mimetypes="application/pdf,text/plain")
    assert "application/pdf" in s.allowed_upload_mimetypes
    assert "text/plain" in s.allowed_upload_mimetypes


def test_validate_llm_provider_mock_ok():
    # Mock never requires external config.
    Settings(llm_provider="mock").validate_llm_provider()


def test_validate_llm_provider_azure_missing():
    s = Settings(llm_provider="azure_foundry", foundry_project_endpoint="", azure_ai_model="")
    with pytest.raises(ConfigurationError) as exc:
        s.validate_llm_provider()
    assert "FOUNDRY_PROJECT_ENDPOINT" in str(exc.value)
    assert "AZURE_AI_MODEL" in str(exc.value)


def test_validate_llm_provider_openai_missing():
    s = Settings(llm_provider="openai_compatible", openai_base_url="", openai_model="")
    with pytest.raises(ConfigurationError):
        s.validate_llm_provider()
