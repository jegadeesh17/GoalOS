# 🛠️ GoalOS Troubleshooting Knowledge Base & Runbooks

This document provides immediate diagnostic playbooks and resolutions for known errors, environment quirks, and runtime issues.

---

## 1. 🗄️ Database & Vector Store Issues

### 1.1 ChromaDB Client Locking Error
- **Symptom:** `sqlite3.OperationalError: database is locked` or Chroma initialization failure when querying memories.
- **Diagnosis:** Multiple `PersistentClient` instances opened concurrently with differing path formats.
- **Resolution:**
  1. Use `MemoryService.clear_collection_cache()` to reset cached client singletons.
  2. Verify that Chroma paths are always resolved with `Path(path).resolve()`.

### 1.2 SQLite Migration Version Desynchronization
- **Symptom:** Missing column error (e.g. `no such column: remote_ai_consent`).
- **Diagnosis:** A migration was partially applied or the database file was restored from an older backup.
- **Resolution:**
  1. Run `database/migrations.py` directly or trigger `startup()` in `api/main.py`.
  2. Verify version in table `schema_migrations` matches latest migration index.

### 1.3 FTS5 Lexical Search Zero Results
- **Symptom:** `MemoryRepository.search_text()` returns empty list despite exact keywords existing in `memories`.
- **Diagnosis:** `memory_fts` virtual table was not populated during raw data insert.
- **Resolution:** Execute `MemoryService.reconcile_index()` to rebuild both FTS5 rows and ChromaDB embeddings.

---

## 2. 🌐 API & Network Issues

### 2.1 413 Payload Too Large
- **Symptom:** Frontend receives HTTP 413 error during journal save or data import.
- **Diagnosis:** Payload exceeds `MAX_REQUEST_BYTES` (512KB).
- **Resolution:** Check attached base64 images or oversized logs. Text journal imports should be batched under 512KB.

### 2.2 401 Unauthorized in Production Mode
- **Symptom:** REST API requests fail with 401 Unauthorized.
- **Diagnosis:** `ENVIRONMENT=production` is set in `.env` without providing `Authorization: Bearer <TOKEN>` in request headers.
- **Resolution:** Pass the configured `GOALOS_API_TOKEN` header or set `ENVIRONMENT=development` for local mode.

---

## 3. 🎨 Frontend & Build Issues

### 3.1 Vite CORS Block During Local Dev
- **Symptom:** Browser console reports `Access-Control-Allow-Origin` error when making API requests from `http://localhost:5173`.
- **Diagnosis:** FastAPI backend is running without CORS middleware or port 8000 is not accessible.
- **Resolution:** Ensure FastAPI has `CORSMiddleware` active with `allow_origins=["*"]` in `api/main.py`.

### 3.2 Blank Screen or Hydration Errors
- **Symptom:** Vite loads but renders a blank white screen.
- **Diagnosis:** Syntax error or unhandled null reference in React component state.
- **Resolution:** Inspect browser console, verify TypeScript compilation via `npm run build` inside `frontend/`.
