# Architecture Decisions - GoalOS

> Lightweight architecture decision records (ADRs). The system description is in [ARCHITECTURE_AND_SPECIFICATIONS.md](./ARCHITECTURE_AND_SPECIFICATIONS.md); dated implementation plans are in [plans/](./plans/).

Rationale here comes only from recorded sources: the project's earlier private decision notes, commit messages, code comments and the code itself. Where no reason was recorded, the entry says so. Every entry ends with an `Evidence:` line naming a commit or `file:line`.

ADR-01 to ADR-06 were ported from the earlier private notes (where they were numbered ADR-001 to ADR-006), which are no longer tracked. Claims in those notes that the repository cannot back up (prompt-token reduction percentages, "sub-millisecond" interactions, "asynchronous" telemetry) were dropped, and ADR-05 was rewritten to match the code. ADR-07 to ADR-09 are new.

---

## ADR-01: SQLite as source of truth, ChromaDB as a repairable vector index

**Context:** GoalOS needs relational queries (goals, daily logs, milestones, scores) and vector similarity search over memories. The earlier notes record that a vector database alone adds operational complexity for structured data, and that SQLite alone has no vector index.
**Decision:** Store everything in SQLite (`goalos.db`), including an FTS5 table `memory_fts` for keyword search. Index memory embeddings in ChromaDB (`chroma_db/`, cosine space) as a second write. If the Chroma write fails or Chroma is unavailable, the SQLite row is marked `index_status = 'pending'`; `MemoryService.reconcile_index()` re-indexes active rows and deletes vectors whose rows are gone.
**Alternatives rejected:** A single vector database for all data; SQLite alone (both as recorded above).
**Consequences:** Setup needs no external service and a locked or missing Chroma store does not lose a memory. Each memory costs two writes. `reconcile_index()` exists but no route or UI calls it, and `DELETE /memories/{id}` removes only the SQLite row (`api/main.py:587-593`).
**Evidence:** `services/memory_service.py:60-80` (store), `:87-100` (pending on failure), `:180-198` (reconcile); `database/migrations.py:206` (`memory_fts`); `reconcile_index` first appears in commit `0b2e736`.

---

## ADR-02: React 18 + TypeScript + Vite frontend replaces Streamlit

**Context:** The first UI was Streamlit. The earlier notes record that its full-page re-runs made the 3,640-week life calendar and the goal checklists slow and flickery; no measurement is recorded.
**Decision:** Build the UI as a React 18 + TypeScript + Vite + Tailwind single-page app that talks to the FastAPI backend over REST, and remove the Streamlit app.
**Alternatives rejected:** Staying on Streamlit (reason above).
**Consequences:** Two processes in development (Vite on 5173, FastAPI on 8000), started together by `run_app.bat`; in production FastAPI serves the built SPA at `/app` (see ADR-06).
**Evidence:** commit `1ae963a` (adds the React frontend and expanded REST API); commit `94d6a0f` (removes the legacy Streamlit app); `frontend/vite.config.ts:65-73` (dev proxy).

---

## ADR-03: Deterministic rule engines as the offline and no-consent fallback

**Context:** GoalOS can run with no `OPENROUTER_API_KEY`, offline, or with `remote_ai_consent` off, and must still answer. Journal text goes to a remote model only after explicit consent.
**Decision:** Every AI entry point checks consent and key first and otherwise returns local rule-engine output with a `fallback_reason`. The guided pipelines return `source: "heuristic_fallback"` (`fallback_progress`, `fallback_future_self`); the chat coordinator returns `source: "deterministic_rules"`. A remote error also falls back the same way.
**Alternatives rejected:** None recorded.
**Consequences:** The app works with no network and no cost. Fallback text is templated and less conversational than a model's. The fallback chat reply reports a fixed recommendation list and a fixed confidence of 0.75, not a learned one.
**Evidence:** `ai/pipelines/coordinator.py:94-106` (consent/key gate), `:280-338` (fallback); `ai/pipelines/_base.py:181,262` (`heuristic_fallback`); `services/coach_service.py:75-77,190-196,209-212`.

---

## ADR-04: Five-factor composite memory ranking

**Context:** The earlier notes record that pure cosine similarity returns semantically close but stale or trivial memories while missing important lessons and recent commitments.
**Decision:** Rank candidates by `0.35*semantic + 0.15*lexical + 0.25*importance + 0.15*recency + 0.10*frequency`. Semantic is `max(0, 1 - cosine distance)`; lexical is 1 when the FTS5 search also returned the memory; recency is exponential decay with a 30-day half-life (0.5 when the memory has no source date); frequency is `ln(n+1)/ln(100)` capped at 1. Candidates below 0.08 are dropped, and near-duplicates (text similarity above 0.94) are skipped.
**Alternatives rejected:** Cosine similarity alone (reason above).
**Consequences:** Important and recent insights surface more often. The weights are fixed constants with no recorded tuning, and every retrieval increments each returned memory's access count.
**Evidence:** `services/memory_service.py:103-113` (recency, frequency, weights), `:117-153` (retrieval, 0.08 cutoff, 0.94 diversity filter); introduced in commit `1597a55`.

---

## ADR-05: Coordinator that pre-fetches domain data, with session blackboard and telemetry

**Context:** As coaching grew to cover goals, journal, memory and the life calendar, the earlier notes record the aim of giving each chat turn only domain-relevant context, keeping multi-turn state locally, and tracking token use and cost.
**Decision:** `CoordinatorPipeline.chat` classifies the message into one of five intents with keyword rules, runs the matching reads itself (active goals, last 3 logs, FTS memory search, lifespan stats) and pastes the results into the prompt, then makes one completion call that carries no tool definitions. The model does not choose or call tools. Multi-turn state is stored in SQLite (`coach_sessions`, `coach_messages`, a JSON `blackboard`). Each LLM call writes a span (model, tokens, latency, estimated USD) to `ai_telemetry`. Domain toolkits (8 tools in `ai/tools/`) exist as a registry with declared schemas; they are used by the benchmark and the tests, and by `complete_with_tools`, which no production path calls.
**Alternatives rejected:** Passing every tool definition on every turn (the original rationale in the earlier notes; the code never did this either, since it pre-fetches instead). Correction of the earlier notes: they described the coordinator as injecting domain-scoped tools into the model prompt; the code does not.
**Consequences:** Behaviour is predictable and cheap, and the intent routing is only as good as its keyword lists. The calendar read is silently skipped on the remote path because it reads dict fields as attributes (`coordinator.py:157`). Telemetry is a synchronous insert wrapped in `try/except`, not an asynchronous write. Tool arguments are not validated against their schemas by the registry.
**Evidence:** commit `92cfa63` (coordinator, sessions, telemetry, toolkits); commit `c53ef11` (coordinator grounding, timeout handling and fallback resilience); `ai/pipelines/coordinator.py:41-64` (intent rules), `:108-169` (pre-fetch, then one `complete` call); `ai/openrouter_client.py:63` (`complete`), `:261` (`complete_with_tools`); `services/observability_service.py:64-91`; `database/migrations.py:236-278` (migration 5); `tests/test_tool_calling.py:84-91` (the only caller of `complete_with_tools`).

---

## ADR-06: One router mounted at `/api` and at the root

**Context:** In development Vite proxied `/api` and stripped the prefix, hiding a mismatch. On Cloud Run FastAPI serves the SPA at `/app`, and the SPA's HTTP client uses `baseURL: '/api'`, so every production API call returned 404.
**Decision:** Register all endpoints on one `APIRouter`, mount it at `/api` (shown in OpenAPI) and again at the root with `include_in_schema=False` for tests, scripts and older callers, and make the Vite proxy keep the `/api` prefix.
**Alternatives rejected:** None recorded.
**Consequences:** Production and development routes agree and the schema is not duplicated. Every route exists at two paths.
**Evidence:** commit `eb3bc78` (dual-mount APIRouter); `api/main.py:788-789`; `frontend/src/api/client.ts:4` (`baseURL: '/api'`); `frontend/vite.config.ts:65-73`.

---

## ADR-07: Goal alignment measured from task-to-goal links

**Context:** The migration 9 docstring says goal alignment is "measured from links between tasks and goals, not word overlap". The commit message adds that unreviewed tasks are excluded rather than counted as misaligned, and that the monthly report no longer guesses 50 for alignment.
**Decision:** A task resolves to a goal by, in order: an explicit saved link (`task_links`, kind `goal` or `none`), then a unique match against the cue words the user wrote on a goal, otherwise it is unreviewed and left out. Alignment is the share of reviewed completed tasks in a 14-day window that serve a goal, and is unknown (`None`) with fewer than 5 reviewed tasks. Saving or removing a link re-scores every day.
**Alternatives rejected:** Word-overlap matching (the migration docstring: "not word overlap").
**Consequences:** Alignment stays unknown until the user has reviewed enough tasks, instead of showing a made-up score. The user must link tasks once (the Goals page lists the unlinked ones).
**Evidence:** commit `fa141ac`; `services/task_link_service.py:42-51` (resolution order); `services/analytics_service.py:16-17,69`; `database/migrations.py:333-342` (migration 9).

---

## ADR-08: Stored monthly snapshots with frozen goal state

**Context:** Month-by-month trends need numbers that do not shift when later edits or new imports land, and per-goal history must survive a goal being deleted or renewed.
**Decision:** Store one row per month in `monthly_snapshots` (`provisional` until the month has ended and the last logged day is its last day, then `final`), recomputed from the daily logs on journal saves (facts only) and on import or `POST /analytics/monthly/recompute` (facts plus the lever analysis). Freeze each goal's state for the month in `monthly_goal_results`, which deliberately has no foreign key to `goals`.
**Alternatives rejected:** None recorded.
**Consequences:** Past months are stable and cheap to read, at the cost of recompute logic and two more tables. Lever results are statistical associations, and the output says so.
**Evidence:** commit `fa141ac`; `database/migrations.py:295-331` (migration 8, including the "No FK to goals on purpose" comment); `services/monthly_analytics_service.py:292-324` (recompute and the final/provisional rule).

---

## ADR-09: User-written pace points for goal pacing

**Context:** Pacing assumed a straight line from a goal's start value to its target at the deadline. The commit message records that this reads a back-loaded goal (net worth, for example) as behind for years.
**Decision:** A goal may carry dated expected values ("pace points", `goal_pace_points`). Expected pace then follows those points joined by straight segments, the on-pace band (10% of the span) scales to the segment the date falls in, the result reports `path: "custom"`, and the least-squares projection is dropped. Goals without points behave as before. The curve is never assumed: it is only what the user wrote.
**Alternatives rejected:** Assuming a curve shape (the module docstring: "the curve is never assumed").
**Consequences:** Back-loaded goals are judged on their own scale. The user has to write the path; there is no default curve. Exposed through `/goals/{id}/pace-points`.
**Evidence:** commit `9d191eb`; `services/yearly_pacing_service.py:1-12,53-67`; `database/migrations.py:345-353` (migration 10); `api/main.py:407-424`.
