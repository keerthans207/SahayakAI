FROM python:3.11-slim

# Security: run as non-root.
RUN groupadd -r sahayak && useradd -r -g sahayak sahayak

WORKDIR /app

# Install OS deps (for lxml, pypdf, etc.).
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Separate layer for pip deps (cache-friendly).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "sqlalchemy[asyncio]" greenlet asyncpg

# Copy source.
COPY . .

# Data directories (vector store, uploads).
RUN mkdir -p /app/data/vector_store /app/data/uploads \
    && chown -R sahayak:sahayak /app/data

USER sahayak

ENV APP_ENV=production \
    LLM_PROVIDER=azure_foundry \
    VECTOR_STORE=memory \
    EMBEDDING_PROVIDER=mock \
    SEARCH_PROVIDER=none \
    SPEECH_PROVIDER=none \
    AUTH_PROVIDER=none \
    UPLOAD_DIR=/app/data/uploads

EXPOSE 8000

# Health check for container orchestration.
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
