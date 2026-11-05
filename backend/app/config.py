"""Application configuration via environment variables (pydantic-settings).

All secrets come from the environment — nothing is hardcoded. Optional
provider settings (Foundry, OpenAI-compatible, Ollama, search, speech) are
kept as plain strings so the application can start without them and surface
a useful configuration error only when the corresponding provider is selected.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "Sahayak AI"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ---- LLM provider ----
    llm_provider: Literal["azure_foundry", "openai_compatible", "ollama", "mock"] = "mock"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1024
    llm_request_timeout: int = 60
    llm_retry_count: int = 2

    # ---- Microsoft Foundry ----
    foundry_project_endpoint: str = ""
    azure_ai_model: str = ""
    azure_tenant_id: str = ""

    # ---- OpenAI-compatible hosted models ----
    openai_base_url: str = ""
    openai_api_key: str = ""
    openai_model: str = ""

    # ---- Ollama (optional local) ----
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""

    # ---- Database ----
    database_url: str = "sqlite+aiosqlite:///./sahayak.db"

    # ---- Embeddings ----
    embedding_provider: Literal["azure_foundry", "openai_compatible", "mock"] = "mock"
    azure_ai_embedding_model: str = ""

    # ---- Vector store ----
    vector_store: Literal["memory", "chroma"] = "memory"
    chroma_persist_directory: str = "./data/vector_store"

    # ---- Government web search ----
    search_provider: Literal["tavily", "none"] = "none"
    tavily_api_key: str = ""

    # ---- Speech (optional) ----
    speech_provider: Literal["azure_speech", "none"] = "none"
    azure_speech_key: str = ""
    azure_speech_region: str = ""

    # ---- File uploads ----
    upload_dir: str = "./data/uploads"
    max_upload_mb: int = 10
    allowed_upload_mimetypes: list[str] = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    # ---- Auth ----
    auth_provider: Literal["none", "oidc"] = "none"
    oidc_issuer: str = ""
    oidc_audience: str = ""
    dev_user_id: str = "dev-user"

    @field_validator("cors_origins", "allowed_upload_mimetypes", mode="before")
    @classmethod
    def _parse_json_list(cls, v):
        """Allow a JSON-encoded string list from env files."""
        if isinstance(v, str):
            import json

            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                # Fall back to comma-separated form.
                return [item.strip() for item in v.split(",") if item.strip()]
        return v

    # ---- Derived helpers ----
    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    @property
    def sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    def validate_llm_provider(self) -> None:
        """Raise a useful, actionable error if a selected provider lacks config.

        Called at startup so misconfiguration fails loudly rather than at the
        first request. The MOCK provider never requires any external config.
        """
        provider = self.llm_provider
        missing: list[str] = []
        if provider == "azure_foundry":
            if not self.foundry_project_endpoint:
                missing.append("FOUNDRY_PROJECT_ENDPOINT")
            if not self.azure_ai_model:
                missing.append("AZURE_AI_MODEL")
        elif provider == "openai_compatible":
            if not self.openai_base_url:
                missing.append("OPENAI_BASE_URL")
            if not self.openai_model:
                missing.append("OPENAI_MODEL")
            if not self.openai_api_key:
                missing.append("OPENAI_API_KEY")
        elif provider == "ollama":
            if not self.ollama_model:
                missing.append("OLLAMA_MODEL")
        if missing:
            raise ConfigurationError(
                f"LLM_PROVIDER='{provider}' is missing required settings: "
                + ", ".join(missing)
                + ". Set them in your .env file."
            )


class ConfigurationError(RuntimeError):
    """Raised when the active configuration is incomplete or invalid."""
    pass


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
