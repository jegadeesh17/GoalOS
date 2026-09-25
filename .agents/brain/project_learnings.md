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

### 4.5 365-Day Productivity Grid & Calendar Alignment
- **Observation:** Visualizing a full year of 365/366 days in a single continuous matrix can feel disorienting and makes finding specific calendar dates difficult.
- **Solution:** Structured the year into a 12-month grouped grid with 7-column weekday alignment (M-T-W-T-F-S-S) and leading day offsets. Each circle represents a discrete calendar day with visual tiers (high productivity gradient $\ge 70$, solid emerald for standard productive, subtle rings for unlogged past days, amber pulse for today, and dashed rings for future days). Connected every circle to a dedicated slide-over `DayDetailDrawer` showing structured journal data, tasks, reflections, and deep work hours with one-click navigation to the journal.

### 4.6 "Magical, Simple & Light" Design Direction (User Preference, 2026-09-24)
- **User Preference:** Keep the Forest Mist Paper Glass theme (palette, paper surfaces, Plus Jakarta Sans + Newsreader) — no major theme changes. Improvements must make the app feel *magical* yet *simple and light*: magic comes from a few moments that respond to the user (the day dot, the serif voice, the mist), lightness comes from subtraction (fewer repeated metrics, fewer nested cards, fewer uppercase eyebrows).
- **Approved (2026-09-25):** The user reviewed the shipped refinement live and approved it ("everything is okay to me"). Treat this as the established look: build new UI in this style rather than revisiting it.
- **Critique baseline (Impeccable, dual-agent):** 20/40 Nielsen; snapshot in `.impeccable/critique/`. Top issues: horizon banner repeated on 3 views with every number stated twice; the theme's own magic switched off; the user's own words (goal motivations, memories, reflections) rendered as small-sans data instead of Newsreader voice; generic SaaS scaffolding; Analytics as a wall of amber warnings + APM table.

### 4.7 Tailwind 3 Silently Drops Unsupported Utility Values
- **Observation:** `bg-white/88`, `bg-white/86`, `scale-130`, `scale-140`, `ring-3`, `shadow-xs`, `backdrop-blur-xs`, `animate-in slide-in-from-right`, `animate-fadeIn`, and `bg-canvas` never compile under Tailwind 3 (opacity modifiers must come from the opacity scale, e.g. `/90` or `/95`; the others are Tailwind 4 or `tailwindcss-animate` names, or undefined tokens). Consequence: the sticky navbar rendered *transparent* with a 40px `backdrop-blur-2xl` (the runtime-blur cost 4.1 banned), and the drawer/toast entrance animations never played.
- **Solution:** Use only scale values (`/90`, `/95`) or bracket syntax (`bg-white/[.88]`), define custom keyframes in `tailwind.config.js`, and verify a new class by grepping the compiled CSS (`curl -s http://localhost:5173/src/index.css | grep -o '\.bg-white[^ {]*'`).
- **Also:** The root `App.tsx` wrapper's opaque `bg-[#f7f9f7]` paints over the body's watercolor radial washes, so the mist is never visible. (Fixed 2026-09-25: washes now live on a fixed `body::before` layer and the wrapper is transparent.)

### 4.8 Fixed Overlays Inherit `space-y-*` Margins
- **Observation:** `DayDetailDrawer` and `GoalFormModal` render inside `space-y-6` / `space-y-8` containers. Tailwind's `space-y` adds `margin-top` to every non-first child, including a `position: fixed; inset: 0` overlay, so the drawer and modal started 24–32px below the top of the viewport.
- **Solution:** Give fixed overlays `!mt-0` (or render them outside the spaced container or through a portal). Verify with `getBoundingClientRect().top === 0` in a Playwright check.

### 4.9 Journal Autosave Pattern
- **Pattern:** Keep the last-saved snapshot and the latest editable state in refs (`lastSavedRef`, `latestRef`). A debounced effect (1.2s) calls `persist()`, which claims the snapshot *before* the request so overlapping triggers never double-send. Switching dates or tabs flushes immediately (`goToDate` and unmount cleanup), Ctrl/Cmd+S forces a save, and failures fall back to the IndexedDB queue in `offline/journalStash.ts`. Never `setLog(serverResponse)` after an autosave, because that clobbers keystrokes typed during the request.
- **Dates:** Always use `lib/date.ts` (`localDateStr`, `shiftDate`, `weekStartOf`). `toISOString().split('T')[0]` is UTC and opens the previous day between 00:00 and 05:30 IST.
- **Testing without touching data:** Verify autosave with Playwright `page.route('**/api/journal/upsert', ...)` so no writes reach `goalos.db`.

---

## 5. 🛠️ Autonomous Operational Discipline & Memory Retention

### 5.1 Autonomous Knowledge Capture Invariant
- **Rule:** Every user aesthetic preference, workflow directive, and architectural discovery must be immediately written to `.agents/brain/project_learnings.md` and `.agents/brain/evolution_log.md` so the user never needs to repeat requirements across sessions.

### 5.2 Autonomous Git Execution Invariant
- **Rule:** Upon completing any meaningful code edit or feature milestone, the AI agent must autonomously inspect `git status`, verify cleanliness, stage modified files, and execute Conventional Commits (`feat:`, `style:`, `refactor:`, `docs:`, `fix:`) without waiting for explicit user prompts.

### 5.3 Cloud Run Production Isolation & Branching Policy
- **Rule:** Branch `main` is wired directly to Google Cloud Run continuous deployment via `.github/workflows/deploy.yml`. Branch `dev` is dedicated to ongoing local development and personal customizations. Never merge untested or experimental personal changes into `main` without explicit user sign-off to ensure the public resume deployment remains unaffected and stable.

### 5.4 Antigravity CLI Customization & Global Marketplace Plugins
- **Observation:** Global plugins in Google Antigravity CLI (`agy`) reside at `~/.gemini/config/plugins/<name>` and are indexed via `~/.gemini/config/import_manifest.json`. The `wshobson/agents` marketplace generates harness-native plugins via `python tools/generate.py --harness antigravity` and imports them cleanly using `agy plugin install <plugin_path>`.
- **User Preference:** User focuses strictly on Python, backend engineering, architecture, testing, and debugging workflows, excluding JavaScript/TypeScript packages.
