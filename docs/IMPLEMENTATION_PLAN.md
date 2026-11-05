# Sahayak AI — Implementation Plan

## Phase 1 — Repository Audit (COMPLETE)

**Finding:** The workspace at `c:\Users\USER\Downloads\SahayakAI` is empty. This is a greenfield
project — no existing FastAPI app, no Foundry Agent Service conversation code, no broken imports
to reconcile, no existing routes or tests.

**Environment confirmed:**
- Python 3.11.6, pip 26.1.2, git 2.52.0 on Windows (PowerShell).
- LangChain 1.2.x (LTS), LangGraph 1.x (LTS), `langchain-azure-ai` 1.2.x are the current stable
  releases. The Foundry chat model class is
  `langchain_azure_ai.chat_models.AzureAIOpenAIApiChatModel` (Foundry SDK v2), configured with a
  project endpoint and Entra ID credential — NOT the retired Foundry Agent Service conversation
  API.

**Decisions:**
- Build the full modular structure described in the master prompt.
- Use `langgraph.graph.StateGraph` for the explicit multi-node agent workflow.
- Use a typed state schema (`TypedDict` with the `add_messages` reducer for the conversation
  history) plus Pydantic models for eligibility rules, schemes, and API I/O.
- Keep every external/optional dependency (Azure Foundry, Ollama, Chroma, Tavily, Speech) behind
  a clean provider abstraction with lazy imports, so the application starts and the full test
  suite passes with the MOCK provider and in-memory vector store and NO network access.
- Deterministic eligibility lives in Python; the LLM only explains results.

## Phase 2 — Core Backend
Configuration (`pydantic-settings`), model provider abstraction (Azure Foundry / OpenAI-compatible
/ Ollama / Mock), async database (SQLAlchemy + aiosqlite/Postgres), health checks, chat sessions,
message persistence.

## Phase 3 — LangGraph Agent
Typed state, language detection, intent classification, model factory, agent tools (scheme search,
government search, eligibility, document, application), conditional routing, retrieval routing,
response generation, conversation-state persistence.

## Phase 4 — Knowledge & Schemes
Scheme registry (seeded JSON), government-source registry, PDF/DOCX/TXT/HTML ingestion, chunking,
embedding providers, vector-store abstraction (in-memory default for dev/test, Chroma for
persistence), retrieval with metadata + citations, content-hash dedup, source freshness checks.

## Phase 5 — Eligibility & Applications
Deterministic eligibility engine (Pydantic rules), missing-requirement detection, UDID & NSP OTR
guidance, document checklists, application readiness report, application progress tracking.

## Phase 6 — Multilingual & Voice
Language service (detection, preference, switching, official-name preservation), optional Azure
Speech STT/TTS behind the speech abstraction. Voice never blocks startup.

## Phase 7 — Quality & Deployment
Automated tests (model, agent, eligibility, RAG, security, API, language, end-to-end cases),
Dockerfile, docker-compose, README, API/security/model/architecture docs.
