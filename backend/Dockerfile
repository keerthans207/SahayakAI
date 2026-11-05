FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system sahayak && \
    useradd --system \
        --gid sahayak \
        --create-home \
        --home-dir /home/sahayak \
        --shell /usr/sbin/nologin \
        sahayak

WORKDIR /app

# Install backend dependencies.
COPY backend/requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install -r /app/requirements.txt && \
    python -m pip check

# Copy application code.
COPY backend/ /app/

# Copy official scheme data separately from mutable application data.
COPY data/ /app/seed-data/

# Copy operational scripts.
COPY scripts/ /app/scripts/

# Persistent runtime directories.
RUN mkdir -p \
    /app/data/uploads \
    /app/data/vector_store \
    /app/seed-data \
    /app/scripts \
    && chown -R sahayak:sahayak /app/data

ENV APP_ENV=production \
    LLM_PROVIDER=mock \
    VECTOR_STORE=memory \
    EMBEDDING_PROVIDER=mock \
    SEARCH_PROVIDER=none \
    SPEECH_PROVIDER=none \
    AUTH_PROVIDER=none \
    SCHEME_DATA_DIR=/app/seed-data \
    UPLOAD_DIR=/app/data/uploads \
    CHROMA_PERSIST_DIRECTORY=/app/data/vector_store

USER sahayak

EXPOSE 8000

HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=30s \
    --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
