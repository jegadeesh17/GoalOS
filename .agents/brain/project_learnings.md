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

### 1.4 SQLite Context Nesting and Connection Deadlocks
- **Observation:** In batch processing scripts, wrapping an outer loop in `with get_db() as conn:` while calling internal services (such as `MemoryService.store()`) that invoke their own `with get_db()` write transactions creates uncommitted lock contention in SQLite on Windows, causing processes to hang indefinitely.
- **Solution:** Pre-fetch any necessary read data (e.g., mapping dates to `daily_logs` IDs) in an isolated `get_db()` block and let it commit/close before iterating through service store calls.

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

### 3.3 Free-Tier Model Evaluation & Rate Limit Throttling
- **Observation:** Free-tier OpenRouter models enforce strict burst limits (10-20 RPM). Unthrottled automated evals fail with HTTP 429 errors within 10 calls.
- **Solution:** Integrated `RateLimiter` using leaky bucket interval spacing ($\ge 4.29$s between requests) with exponential backoff and jitter. Created automated pre-flight health checks to auto-substitute candidate models with healthy backups (`qwen`, `gemma-2`, `mistral`) if an endpoint is busy or offline.
- **Benchmark Outcome:** In 45-scenario evaluation across live free models, `nvidia/nemotron-3-super-120b-a12b:free` won 1st place with a 76.8% composite score, 93.3% grounding, and 14/15 successful completions, closely followed by `minimax/minimax-m3:free` (74.4%). `nvidia/nemotron-3-super-120b-a12b:free` is configured as default in `.env`.

### 3.4 Generic-Looking Output Is Often a Render Bug, Not a Grounding Bug
- **Observation:** A user reported every AI Coach screen (Future Self, Goal Alignment, morning/evening pipelines) showing the identical generic directive ("Focus on relentless execution of today's #1 priority") regardless of their actual journal data. The pipelines themselves were correctly returning rich, pipeline-specific JSON (`message` for future-self; `alignment_narrative`/`aligned_goals`/`neglected_goals`/`recommendation` for goal-alignment) — but `AICoachView.tsx` only ever read `mentor_rule`/`rule`/`core_insight`/`coaching` off the result, none of which those pipelines set, so it silently fell back to a hardcoded string every time and buried the real payload in a collapsed "Raw Structured Output" panel.
- **Solution:** Before assuming a prompt/grounding problem, check what the UI actually reads off the pipeline response versus what the pipeline actually returns — a field-name mismatch between backend and frontend is indistinguishable from bad AI output to the end user. Render each pipeline's real fields explicitly (`renderStructuredBody` in `AICoachView.tsx`) and only show the generic fallback when a result truly has none of the expected fields.
- **Related:** This surfaced alongside a second bug — the chat's `remote_ai_consent` was never sent from `AICoachView`, so the backend's `True` default silently overrode a user who had switched remote AI off in Settings. Any boolean consent/privacy flag needs its storage-to-call-site path traced explicitly; a safe-looking backend default can defeat a toggle at just one missed call site.

### 3.5 AI Coach Freeze & Timeout Auto-Failover
- **Observation:** When using congested 120B parameter models (such as `nvidia/nemotron-3-super-120b-a12b:free`) on OpenRouter, endpoints frequently queued or hung past 18 seconds. `OpenRouterClient` retried the exact same stalled model 3 times (57s total delay) and never failed over on timeouts or network exceptions. Furthermore, `frontend/src/api/client.ts` Axios instance had no timeout (`timeout: 0`), resulting in indefinite UI hangs on the AI Coach tab.
- **Solution:** 
  1. Updated primary default model to `google/gemma-4-31b-it:free` (rich, articulate, high-EQ mentor persona with sub-4s response times).
  2. Implemented immediate model rotation in `OpenRouterClient` on any `httpx.TimeoutException`, network error, or HTTP 5xx response, rotating through healthy candidate fallbacks (`google/gemma-4-26b-a4b-it:free`, `nex-agi/nex-n2.5-pro:free`, `nex-agi/nex-n2.5-mini:free`, `nvidia/nemotron-3.5-lightning:free`).
  3. Added a 45s safety timeout to the frontend Axios instance and updated loading state feedback in `AICoachView.tsx`.

---

## 4. 🎨 Frontend & Design System Learnings

### 4.1 Zero-Lag Compositor & Paper Glass Optimization
- **Observation:** Combining continuous, dynamic CSS Gaussian blurs (`filter: blur(70px)` with keyframe morph animations) underneath multi-layer `backdrop-filter: blur(20px)` glass panels forced the browser GPU compositor to re-rasterize full-screen matrix blurs on every single frame (60-120fps), creating heavy lag and page load delays during tab switching.
- **Solution:** Replaced dynamic runtime DOM blurs with pre-computed, GPU-cached CSS multi-stop radial gradient washes on the body canvas. Standardized `.glass-panel` and `.glass-card-interactive` on crisp, high-performance opaque paper glass (`background: rgba(255, 255, 255, 0.94)`), eliminating 100% of viewport repaint lag while preserving the serene watercolor aesthetic.

### 4.2 Non-Redundant Metric Presentation
- **Observation:** Showing total weeks lived in multiple cards caused visual clutter and desynchronization.
- **Solution:** Centralized in `LifeProgressBanner.tsx` with unified props passed from `LifeCalendarService`.

### 4.3 Watercolor Watermark & Paper Glass Contrast
- **Observation:** Excessive saturation in background gradients makes dark text harder to read and creates a flashy, robotic aesthetic.
- **Solution:** Embody an Ultra-Minimal Paper Glass design with diffuse, low-opacity floating watercolor blooms (sage, eucalyptus, moss, dewy morning sun). Text uses high-contrast deep forest slate (`#0F291E` / `#0F172A`), providing pristine typographic legibility while keeping the theme calm, light, and organic.

### 4.4 Smooth Humanized Typography & Anti-Robotic Textualizer
- **Observation:** Over-reliance on utilitarian fonts (raw Inter) and aggressive uppercase labels (`PLAN (SCHEDULE)`, `GRATITUDE`) made the application feel mechanical, robotic, and tiring to read.
- **Solution:** 
  - Standardized on **Plus Jakarta Sans** as primary UI font for soothing geometric curvature, high legibility, and modern warmth.
  - Paired with **Newsreader** editorial serif typography for mentor directives, life visions, and reflective insights.
  - Replaced aggressive uppercase labels with calm, readable title-case / sentence-case labels and subpixel antialiasing (`-webkit-font-smoothing: antialiased`).

---

## 5. 🛠️ Autonomous Operational Discipline & Memory Retention

### 5.1 Autonomous Knowledge Capture Invariant
- **Rule:** Every user aesthetic preference, workflow directive, and architectural discovery must be immediately written to `.agents/brain/project_learnings.md` and `.agents/brain/evolution_log.md` so the user never needs to repeat requirements across sessions.

### 5.2 Autonomous Git Execution Invariant
- **Rule:** Upon completing any meaningful code edit or feature milestone, the AI agent must autonomously inspect `git status`, verify cleanliness, stage modified files, and execute Conventional Commits (`feat:`, `style:`, `refactor:`, `docs:`, `fix:`) without waiting for explicit user prompts.
