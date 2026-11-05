# Model Configuration

## Providers

Sahayak AI supports four LLM providers selectable via `LLM_PROVIDER`. The mock provider requires no credentials and is the default.

### MOCK (default, offline)

```
LLM_PROVIDER=mock
```

No dependencies, no credentials, fully deterministic. Used by the full test suite.

---

### AZURE_FOUNDRY

Uses `langchain-azure-ai` (Foundry SDK v2, **not** the deprecated Azure AI Inference SDK).

```
LLM_PROVIDER=azure_foundry
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
AZURE_AI_MODEL=gpt-4.1
AZURE_TENANT_ID=<your-tenant-id>
```

**Authentication**: `azure.identity.aio.DefaultAzureCredential`

- Locally: `az login`
- Container: Managed Identity (no secret required)
- Required role: **Foundry User** on the Foundry resource

**Important**: This integration calls the deployed model directly via LangChain. It does NOT use the Foundry Agent Service conversation API (`conversations.create()` or `AIProjectClient.get_openai_client(agent_name=...)`).

```python
from azure.identity.aio import DefaultAzureCredential
from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel

model = AzureAIOpenAIApiChatModel(
    project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
    model="gpt-4.1",
)
```

Install: `pip install langchain-azure-ai azure-identity`

---

### OPENAI_COMPATIBLE

Works with any OpenAI-compatible inference endpoint — hosted Llama, Qwen, Mistral, etc.

```
LLM_PROVIDER=openai_compatible
OPENAI_BASE_URL=https://your-endpoint/v1
OPENAI_API_KEY=your-key
OPENAI_MODEL=Llama-3.1-70B-Instruct
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1024
LLM_REQUEST_TIMEOUT=60
LLM_RETRY_COUNT=2
```

Install: `pip install langchain-openai`

---

### OLLAMA (optional local)

```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

Install: `pip install langchain-ollama`

Ollama is not the default and is never required. The app starts without it.

---

## Embedding providers

```
EMBEDDING_PROVIDER=mock          # default, offline
EMBEDDING_PROVIDER=azure_foundry # uses FOUNDRY_PROJECT_ENDPOINT + AZURE_AI_EMBEDDING_MODEL
EMBEDDING_PROVIDER=openai_compatible
```

The chat model and the embedding model can use different providers.

---

## Failure behaviour

If a selected provider is misconfigured:

- `ConfigurationError` is raised at startup with the exact missing variable names.
- The application **never** silently falls back to another model.
- The MOCK provider is always available as a fallback for development.

---

## Streaming

`POST /api/v1/chat/sessions/{id}/stream` returns Server-Sent Events. With the MOCK provider, streaming is word-by-word. With Azure Foundry or OpenAI-compatible models, token streaming is used where the model supports it.
