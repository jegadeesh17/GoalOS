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
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# --- Stage 3: Minimal Production Runner ---
FROM python:3.11-slim AS runner
WORKDIR /app
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends curl sqlite3 && rm -rf /var/lib/apt/lists/*

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
COPY --chown=appuser:appgroup utils.py utils.py
COPY --chown=appuser:appgroup data/demo_seed.csv data/demo_seed.csv
COPY --chown=appuser:appgroup data/demo_goalos.db /app/goalos.db
COPY --chown=appuser:appgroup data/demo_goalos.db /app/data/demo_goalos.db
COPY --chown=appuser:appgroup data/demo_chroma_db/ /app/chroma_db/
COPY --chown=appuser:appgroup data/demo_chroma_db/ /app/data/demo_chroma_db/

RUN chown -R appuser:appgroup /app


USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
