"""Model provider abstraction.

Returns a LangChain chat model for the configured provider:
- AZURE_FOUNDRY   : langchain_azure_ai.AzureAIOpenAIApiChatModel (Foundry SDK v2)
- OPENAI_COMPATIBLE: langchain_openai.ChatOpenAI against any OpenAI-compatible endpoint
- OLLAMA          : langchain_ollama.ChatOllama (optional local)
- MOCK            : a fully deterministic in-process model (no network, no creds)

Design rules enforced here:
- External providers are imported lazily so a missing optional dependency only
  errors when that provider is actually selected (clear message, no import crash).
- Never silently fall back to another model. If a provider is misconfigured we
  raise ConfigurationError.
- The MOCK provider needs zero external resources and is the test default.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.config import ConfigurationError, get_settings


# --------------------------------------------------------------------------- #
# Mock model — deterministic, offline, no credentials
# --------------------------------------------------------------------------- #
class MockChatModel(BaseChatModel):
    """Deterministic chat model for tests and offline development.

    It does not call any network service. Responses are templated from the last
    user message so they are stable and inspectable. It supports:
      - invoke / ainvoke
      - streaming (astream / stream) yielding AIMessageChunk word chunks
      - bind_tools (no-op wrapper; the agent selects tools deterministically)
      - with_structured_output (returns a JSON-parsing runnable; the mock emits
        a best-effort JSON object derived from the prompt)
    """

    model_name: str = "mock-sahayak"
    temperature: float = 0.0

    # Bumped every invocation so streaming tests can assert progress.
    _call_count: int = 0

    @property
    def _llm_type(self) -> str:
        return "mock-sahayak"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model_name": self.model_name}

    # ---- core generation --------------------------------------------------- #
    def _build_response(self, messages: list[BaseMessage]) -> str:
        """Produce a deterministic, helpful, source-aware reply.

        The mock never invents scheme facts: when the prompt contains
        structured context (schemes, eligibility, documents) it summarises that
        context; otherwise it gives a grounded, scoped reply.
        """
        last_user = ""
        for m in reversed(messages):
            if m.type == "human":
                last_user = m.content if isinstance(m.content, str) else str(m.content)
                break
        text = last_user.lower()

        # Pull any injected context block (the agent passes retrieved facts).
        context_block = ""
        for m in messages:
            if m.type == "system" and "[SAHAYAK_CONTEXT]" in m.content:
                context_block = m.content

        # Intent-flavoured canned answers keep the mock useful end-to-end.
        if any(k in text for k in ["scholarship", "scheme", "benefit", "find"]):
            intro = "Here is what I found based on the registered scheme information."
            if context_block:
                intro += "\n\n" + self._summarise_context(context_block)
            return (
                f"{intro}\n\n"
                "What I found: relevant government opportunities are listed above.\n"
                "Your eligibility: I can run a preliminary check — please share your "
                "state, disability percentage and education level.\n"
                "Your next action: confirm your UDID and NSP OTR status so I can "
                "narrow the list.\n"
                "Official sources: only government portals are cited below."
            )
        if "eligible" in text or "eligibility" in text:
            return (
                "Your eligibility has been evaluated with the deterministic rules "
                "engine. See the eligibility breakdown for satisfied, not-satisfied "
                "and unknown requirements. The AI only explains the result; it does "
                "not change the outcome."
            )
        if "document" in text or "udid" in text or "otr" in text:
            return (
                "For the selected scheme I can show the official document checklist "
                "and flag what is missing. I will never request OTPs, passwords or "
                "banking credentials, and I never claim to register you — you must "
                "complete authentication on the official government portal."
            )
        if context_block:
            return self._summarise_context(context_block)
        return (
            "Namaste. I am Sahayak AI, here to help you discover government benefits "
            "for persons with disabilities and guide you through the application "
            "process. Tell me your state and what you need help with — for example "
            "scholarships, pensions, assistive devices or UDID registration."
        )

    @staticmethod
    def _summarise_context(context_block: str) -> str:
        """Render injected structured context into readable text without inventing facts."""
        # The context marker may appear more than once (instructions + payload);
        # the payload is the LAST occurrence.
        matches = re.findall(r"\[SAHAYAK_CONTEXT\](.*)", context_block, re.S)
        payload = matches[-1].strip() if matches else ""
        if not payload:
            return "No structured context available."
        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, ValueError):
            return payload
        lines: list[str] = []
        schemes = data.get("schemes") or []
        if schemes:
            lines.append("Registered opportunities:")
            for s in schemes:
                name = s.get("official_name") or s.get("scheme_id")
                dept = s.get("department") or "Government"
                status = s.get("scheme_status") or "unknown"
                lines.append(f"- {name} ({dept}) — status: {status}")
        evidence = data.get("retrieved_evidence") or []
        if evidence:
            lines.append("Retrieved evidence:")
            for e in evidence:
                cite = (e.get("citation") or {}) if isinstance(e, dict) else {}
                lines.append(f"- {e.get('text', '')[:200]} (source: {cite.get('url', 'n/a')})")
        elig = data.get("eligibility_result")
        if elig:
            lines.append(f"Eligibility outcome: {elig.get('outcome', 'unknown')}")
        docs = data.get("missing_requirements") or data.get("required_documents")
        if docs:
            lines.append("Documents / requirements: " + ", ".join(str(d) for d in docs))
        sources = data.get("official_sources") or []
        if sources:
            lines.append("Official sources:")
            for s in sources:
                lines.append(f"- {s.get('title', '')}: {s.get('url', '')}")
        return "\n".join(lines) if lines else "No structured context available."

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        self._call_count += 1
        content = self._build_response(list(messages))
        msg = AIMessage(content=content)
        return ChatResult(generations=[ChatGeneration(message=msg)])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ):
        from langchain_core.outputs import ChatGenerationChunk

        content = self._build_response(list(messages))
        for token in content.split():
            yield ChatGenerationChunk(message=AIMessageChunk(content=token + " "))

    # ---- tool / structured-output compatibility --------------------------- #
    def bind_tools(self, tools: list[Any], **kwargs: Any) -> "MockChatModel":
        """The agent selects tools deterministically; tool binding is a no-op.

        Returning self keeps the model usable in code paths that call bind_tools
        without making the mock fake tool-call requests.
        """
        return self

    def with_structured_output(self, schema: Any, **kwargs: Any):
        """Return a runnable that emits a best-effort JSON object for `schema`.

        Only used in optional paths; the agent's intent classification is
        deterministic Python and does not rely on this.
        """
        from langchain_core.runnables import RunnableLambda

        def _emit(messages: list[BaseMessage]) -> dict:
            text = self._build_response(list(messages))
            # Produce a minimal dict that satisfies common boolean/string schemas.
            return {"response": text, "intent": "general_assistance"}

        return RunnableLambda(_emit)


# --------------------------------------------------------------------------- #
# Provider factory
# --------------------------------------------------------------------------- #
def get_chat_model(provider: str | None = None) -> BaseChatModel:
    """Build and return the chat model for the given (or configured) provider."""
    settings = get_settings()
    provider = provider or settings.llm_provider

    if provider == "mock":
        return MockChatModel(temperature=settings.llm_temperature)

    if provider == "azure_foundry":
        return _build_azure_foundry(settings)

    if provider == "openai_compatible":
        return _build_openai_compatible(settings)

    if provider == "ollama":
        return _build_ollama(settings)

    raise ConfigurationError(f"Unknown LLM_PROVIDER '{provider}'.")


def _build_azure_foundry(settings):
    """Microsoft Foundry chat model via langchain-azure-ai (Foundry SDK v2).

    Uses the project endpoint + Entra ID (DefaultAzureCredential). This calls the
    deployed model directly — it does NOT use Foundry Agent Service conversations.
    
    Streaming is enabled by default for real-time token generation.
    """
    settings.validate_llm_provider("azure_foundry")
    try:
        from azure.identity.aio import DefaultAzureCredential  # noqa: F401
        from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ConfigurationError(
            "AZURE_FOUNDRY provider requires 'langchain-azure-ai' and "
            "'azure-identity'. Install them with: pip install langchain-azure-ai "
            "azure-identity"
        ) from exc

    from azure.identity.aio import DefaultAzureCredential

    return AzureAIOpenAIApiChatModel(
        project_endpoint=settings.foundry_project_endpoint,
        credential=DefaultAzureCredential(),
        model=settings.azure_ai_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        streaming=True,  # Enable token streaming
    )


def _build_openai_compatible(settings):
    """OpenAI-compatible hosted model (ChatOpenAI) — Llama, Qwen, etc."""
    settings.validate_llm_provider()
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ConfigurationError(
            "OPENAI_COMPATIBLE provider requires 'langchain-openai'. "
            "Install it with: pip install langchain-openai"
        ) from exc

    return ChatOpenAI(
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout=settings.llm_request_timeout,
        max_retries=settings.llm_retry_count,
    )


def _build_ollama(settings):
    """Optional local Ollama model — never the default."""
    settings.validate_llm_provider()
    try:
        from langchain_ollama import ChatOllama
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ConfigurationError(
            "OLLAMA provider requires 'langchain-ollama'. Install it with: "
            "pip install langchain-ollama"
        ) from exc

    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=settings.llm_temperature,
    )
