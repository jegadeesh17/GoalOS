# 📚 GoalOS Project Learnings & Knowledge Base

This document records the accumulated technical discoveries, bug fixes, edge cases, and performance optimizations identified across the GoalOS codebase.

---

## 1. 🗄️ Persistence & SQLite Learnings

### 1.1 FTS5 Virtual Table Rebuilds
- **Observation:** When dropping and re-creating SQLite tables during schema resets, FTS5 virtual tables (`memory_fts`) require explicit re-population or synchronization.
- **Solution:** Always run `MemoryService.reconcile_index()` after any bulk migration or restore operation.
- **Pattern:** Keep SQLite triggers or explicit repository hooks in `database/repositories/memory_repository.py` to keep `memory_fts` in sync with table `memories`.

### 1.2 ChromaDB Concurrent Access on Windows
- **Observation:** On Windows, ChromaDB's duckdb/sqlite backend can throw file lock errors if multiple threads or processes instantiate `PersistentClient` with different path casing or un-canonicalized paths.
- **Solution:** Canonicalize all Chroma paths using `str(Path(chroma_path).resolve())` and cache instances in `_COLLECTIONS` dictionary within `services/memory_service.py`.

### 1.3 Transactional Migrations
- **Observation:** Running DDL statements outside transaction blocks can leave the SQLite database in an inconsistent state if a migration step fails halfway.
- **Solution:** All migrations in `database/migrations.py` execute within `with get_db() as conn: conn.execute("BEGIN IMMEDIATE")` blocks.

---

## 2. ⚡ Hybrid RAG & Embeddings Learnings

### 2.1 MMR Diversity Threshold
- **Observation:** In personal journals, users frequently write repetitive phrases (e.g. "Did 2 hours of deep work today"). Standard vector search returned 5 near-identical memories.
- **Solution:** Added Maximal Marginal Relevance (MMR) text similarity pruning. If candidate cosine similarity $> 0.94$ with an already accepted memory, it is discarded in favor of diverse insights.

### 2.2 CPU-Only Embedding Fallback
- **Observation:** Running large embedding models on laptops without GPU acceleration introduced 200-400ms latency per query.
- **Solution:** Using `all-MiniLM-L6-v2` via `sentence-transformers` provides < 15ms CPU inference. If `sentence-transformers` is unavailable, `EmbeddingService` falls back to deterministic SHA-256 dimension hashing to ensure zero crash rate.

---

## 3. 🤖 AI Coaching & Tool Calling Learnings

### 3.1 Pydantic Model Parsing from LLM Output
- **Observation:** Some LLMs output markdown code blocks (```json ... ```) even when instructed to return pure JSON.
- **Solution:** `ai/openrouter_client.py` strips leading/trailing markdown blocks, parses JSON leniently, and validates against Pydantic models with graceful error fallback.

### 3.2 Dynamic Context Truncation
- **Observation:** When users have 500+ past logs, passing raw history into the LLM context window exhausts token limits and increases API costs.
- **Solution:** Context is dynamically curated: top 5 hybrid RAG memories + active multi-horizon goals + 7-day rolling performance metrics.

---

## 4. 🎨 Frontend & Design System Learnings

### 4.1 Frosted Glass Performance
- **Observation:** Heavy backdrop blur on large grid items (3,640 weeks) caused minor frame drops during scroll on low-spec screens.
- **Solution:** Applied `backdrop-blur-md` only to static navigation bars and modal overlays. Discrete week blocks in `LifeCalendar.tsx` use pure CSS colors with transition states.

### 4.2 Non-Redundant Metric Presentation
- **Observation:** Showing total weeks lived in multiple cards caused visual clutter and desynchronization.
- **Solution:** Centralized in `LifeProgressBanner.tsx` with unified props passed from `LifeCalendarService`.
