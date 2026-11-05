# Sahayak AI — Architecture

## System overview

```
┌─────────────────────────────────────────────────────────┐
│                     Client (Browser / Voice)             │
└─────────────────┬────────────────────────────────────────┘
                  │  HTTPS
┌─────────────────▼────────────────────────────────────────┐
│              FastAPI  (uvicorn, async)                    │
│   /api/v1/health  /chat  /schemes  /eligibility          │
│   /documents  /applications  /speech  /admin             │
│                                                           │
│  Middleware: RequestId │ CORS │ SecurityHeaders │ Errors  │
└─────────────────┬────────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────────┐
│                  Chat Service                             │
│   session & message persistence  │  user isolation       │
└─────────────────┬────────────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────────────┐
│             Sahayak LangGraph Agent                       │
│                                                           │
│  START → detect_language → classify_intent → load_profile│
│        → route_request                                    │
│               ├── discover (scheme registry search)       │
│               ├── evaluate (deterministic rules engine)   │
│               ├── documents (doc checklist & missing)     │
│               ├── application (checklist + readiness)     │
│               ├── udid_otr (UDID / NSP OTR guidance)      │
│               └── general (web search / fallback)        │
│        → retrieve_evidence (vector store RAG)            │
│        → validate_information (confidence / freshness)   │
│        → generate_response (LLM explains, never decides) │
│  END                                                      │
└───────┬─────────────────────────────────────┬────────────┘
        │                                     │
┌───────▼──────────────┐         ┌────────────▼────────────┐
│  Deterministic        │         │   LLM Provider           │
│  Eligibility Engine   │         │   (Azure Foundry /       │
│  (Python rules,       │         │    OpenAI-compat /       │
│   Pydantic predicates)│         │    Ollama / Mock)        │
└──────────────────────┘         └─────────────────────────┘
        │                                     │
┌───────▼──────────────────────────────────────────────────┐
│   Services & Retrieval                                     │
│   SchemeService  │  RetrievalService  │  DocumentService  │
│   ApplicationService  │  LanguageService  │  ChatService  │
│   SearchService (Tavily)  │  SpeechService (Azure Speech) │
└───────┬──────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────┐
│   Data stores                                              │
│   SQLite (dev) / PostgreSQL (prod) — SQLAlchemy async     │
│   InMemoryVectorStore (dev) / Chroma / Azure AI Search    │
│   Local filesystem uploads / Azure Blob (prod)            │
└──────────────────────────────────────────────────────────┘
```

## Key design choices

### 1. Deterministic eligibility
Eligibility is **never** decided by the LLM. Python rules (`EligibilityRule` Pydantic models) produce a typed `EligibilityResult`. The LLM reads the result and explains it in plain language. This prevents hallucinated eligibility claims.

### 2. Scheme registry
Schemes are loaded from versioned JSON files in `data/`. Each scheme carries `confidence_status=needs_verification` until officially verified. Mock data is never presented as verified government information. The source registry tracks every claim back to an official URL.

### 3. Provider abstraction
`get_chat_model()` and `get_embeddings()` are the only points that know about providers. Everything else consumes `BaseChatModel` and `Embeddings` interfaces. Adding a new provider requires changes only in `model_factory.py` and `embeddings.py`.

### 4. Graph routing
The LangGraph `route_request` conditional edge uses deterministic Python (keyword rules), not LLM intent classification. This means the routing is testable, reproducible, and does not depend on the LLM being available.

### 5. User isolation
Every DB query is scoped by `user_id`. Documents, sessions and applications carry `owner_id` and the service layer raises `PermissionError` before returning data. Personal documents are never ingested into the shared knowledge base.

### 6. Voice separation
Speech STT/TTS is an optional integration layer behind `SpeechToTextProvider` and `TextToSpeechProvider` interfaces. Missing speech credentials never block startup or the text API.

## Production topology (Azure)

| Component | Azure service |
|---|---|
| Backend API | Azure Container Apps |
| Database | Azure Database for PostgreSQL |
| Vector search | Azure AI Search or pgvector |
| Document storage | Azure Blob Storage |
| Speech | Azure AI Speech |
| LLM | Azure Foundry (Managed Identity) |
| Identity | Microsoft Entra ID |
| Secrets | Azure Key Vault (Container App secret refs) |
| Registry | Azure Container Registry |
