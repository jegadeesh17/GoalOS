# ============================================================================
# Multi-Stage Production Dockerfile for GoalOS (React + FastAPI on GCP Cloud Run)
# ============================================================================

# --- Stage 1: Build React Vite Frontend ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python Dependency Builder ---
FROM python:3.11-slim AS python-builder
# WITH_ML=1 adds torch + sentence-transformers (requirements-ml.txt) for real embeddings.
# Cloud Run runs ENVIRONMENT=demo, which uses the hash embedder, so the default build leaves them out.
ARG WITH_ML=0
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-ml.txt ./
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --no-compile --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir --no-compile -r requirements.txt
# CPU-only torch first: the PyPI wheel pulls in CUDA packages and Cloud Run has no GPU.
RUN if [ "$WITH_ML" = "1" ]; then \
        /opt/venv/bin/pip install --no-cache-dir --no-compile torch --index-url https://download.pytorch.org/whl/cpu && \
        /opt/venv/bin/pip install --no-cache-dir --no-compile -r requirements-ml.txt; \
    fi
# Trim what the runtime never uses: bundled test suites, bytecode, and pip/setuptools themselves.
RUN find /opt/venv -type d \( -name tests -o -name test \) -prune -exec rm -rf {} + && \
    find /opt/venv -name "*.pyc" -delete && \
    find /opt/venv -type d -name __pycache__ -empty -delete && \
    cd /opt/venv/lib/python3.11/site-packages && \
    rm -rf pip pip-*.dist-info setuptools setuptools-*.dist-info pkg_resources _distutils_hack distutils-precedence.pth && \
    rm -f /opt/venv/bin/pip /opt/venv/bin/pip3*

# --- Stage 3: Minimal Production Runner ---
FROM python:3.11-slim AS runner
WORKDIR /app
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

COPY --from=python-builder /opt/venv /opt/venv
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

COPY --chown=appuser:appgroup ai/ ai/
COPY --chown=appuser:appgroup api/ api/
COPY --chown=appuser:appgroup config/ config/
COPY --chown=appuser:appgroup configs/ configs/
COPY --chown=appuser:appgroup database/ database/
COPY --chown=appuser:appgroup models/ models/
COPY --chown=appuser:appgroup services/ services/
COPY --chown=appuser:appgroup scripts/ scripts/
COPY --chown=appuser:appgroup data/demo_seed.csv data/demo_seed.csv
COPY --chown=appuser:appgroup data/demo_goalos.db /app/goalos.db
COPY --chown=appuser:appgroup data/demo_goalos.db /app/data/demo_goalos.db
COPY --chown=appuser:appgroup data/demo_chroma_db/ /app/chroma_db/
COPY --chown=appuser:appgroup data/demo_chroma_db/ /app/data/demo_chroma_db/

# Non-recursive: only the dirs the app writes to (SQLite journal files sit beside /app/goalos.db,
# backups/ is created in /app, ChromaDB writes to /app/chroma_db). Copied files keep their --chown.
RUN chown appuser:appgroup /app /app/chroma_db


USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
