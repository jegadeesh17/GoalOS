# GoalOS — AI Goal Operating System
## Full Product Specification v3.0

---

# 1. Mission

Build an AI-powered personal operating system whose only purpose is helping one user become **1% better every day**.

GoalOS is **not** a habit tracker, **not** a task manager, and **not** a journal app.

It is a **decision-support system** that continuously compares:

- Who I want to become
- Where I currently am
- What I did today
- What I should do tomorrow

and provides personalized coaching to close that gap every single day.

The system evolves with the user and becomes increasingly personalized through accumulated history — both imported past journals and ongoing daily entries.

---

# 2. Core Philosophy

Every feature must satisfy one question:

> "Will this help the user make better decisions tomorrow?"

If not, do not build it.

The application optimizes for:

- **Clarity** — always know the one highest-leverage thing to do
- **Consistency** — reward showing up, not just performing
- **Reflection** — write first, structure second
- **Accountability** — the system remembers what you committed to
- **Momentum** — 7-day trend is more important than any single day

---

# 3. User Profile

- Single user
- Local-first
- Desktop and mobile browser
- No authentication required
- No multi-user support
- No collaboration

**Daily ritual budget:**
- Morning: 15 minutes (unhurried, reflective)
- Evening: 15 minutes (honest, narrative-first)

---

# 4. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python |
| Database | SQLite |
| Memory | ChromaDB |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Charts | Plotly |
| LLM | OpenRouter (model configurable via .env) |
| Config | .env file |

---

# 5. SDLC Model — Phased Iterative Delivery

## Why Phased Iterative?

This project is built solo with a coding agent under token/rate constraints (Claude free tier). Pure Waterfall is too rigid — requirements will clarify as you see the system working. Pure Scrum requires ceremonies that don't make sense for a single developer. 

**Phased Iterative** is the right model here:

- Each phase delivers something **independently runnable and testable**
- Each phase has a **clear entry condition** (what must exist before starting) and **exit condition** (what defines done)
- Phases are **sized to fit within a single coding agent session** to avoid hitting rate limits
- Later phases depend on earlier ones, but you can pause between any two phases without losing progress
- Each phase ends with a working `python -m pytest` passing and a runnable Streamlit app

## Rate Limit Strategy

Each phase is designed to be **one agent session**. When starting a new session:

1. Paste the relevant phase section from this spec
2. Paste the `Project Structure` section
3. Paste the `Data Model` section
4. Tell the agent: *"Phase N is complete. Build Phase N+1."*

This keeps each session focused and avoids context overflow.

---

# 6. The 10 Build Phases

## Phase 1 — Foundation
**What you build:** Project skeleton, database schema, migrations, all repositories, Pydantic models, config loader.

**Entry condition:** Empty folder.

**Exit condition:**
- `python migrations.py` creates all tables with no errors
- All repositories have working CRUD methods
- All Pydantic models validate correctly
- `pytest tests/test_repositories.py` passes

**Files to create:**
```
goalos/
├── app.py                    # Minimal placeholder ("GoalOS loading...")
├── .env.example
├── requirements.txt
├── config/
│   └── settings.py
├── database/
│   ├── connection.py
│   ├── migrations.py
│   └── repositories/
│       ├── __init__.py
│       ├── goal_repository.py
│       ├── log_repository.py
│       ├── score_repository.py
│       ├── memory_repository.py
│       └── coach_repository.py
├── models/
│   ├── __init__.py
│   ├── goal.py
│   ├── daily_log.py
│   ├── weekly_review.py
│   ├── score.py
│   ├── memory.py
│   └── coach_response.py
└── tests/
    ├── __init__.py
    └── test_repositories.py
```

**Prompt to agent:**
> "Build Phase 1 of GoalOS. Create the full project structure, database schema with SQLite migrations, repository layer with CRUD operations, and Pydantic models. Follow the spec exactly. No UI yet. End with pytest passing."

---

## Phase 2 — Analytics Engine
**What you build:** All deterministic score calculations. No AI involved. Pure math.

**Entry condition:** Phase 1 complete.

**Exit condition:**
- All 7 score functions return values in range 0–100
- Edge cases handled (missing data, zero division, empty logs)
- `pytest tests/test_analytics.py` passes with at least 15 test cases

**Files to create:**
```
goalos/
└── services/
    ├── __init__.py
    └── analytics_service.py
tests/
└── test_analytics.py
```

**Scores to implement:**
1. `goal_alignment_score(tasks, goals)` — keyword + embedding overlap
2. `consistency_score(logs_30d)` — streak + execution rate
3. `health_score(sleep_hours, sleep_quality, workout, energy)` 
4. `learning_score(journal_text, tasks)` — keyword detection
5. `productivity_score(deep_work_hours, tasks_completed, focus)` 
6. `momentum_score(scores_7d)` — linear regression slope
7. `gap_score(goals, logs)` — pace vs required pace
8. `overall_growth_score(all_scores)` — weighted combination

**Prompt to agent:**
> "Build Phase 2 of GoalOS. Implement the analytics service with all 8 deterministic score functions. Use the formulas in the spec exactly. Write comprehensive pytest tests covering normal cases, edge cases, and zero/null inputs."

---

## Phase 3 — Embedding and Memory System
**What you build:** Embedding service with caching, ChromaDB integration, memory retrieval algorithm.

**Entry condition:** Phase 1 complete.

**Exit condition:**
- `EmbeddingService.embed(text)` returns a vector and caches subsequent calls
- Memories can be stored and retrieved from ChromaDB
- Retrieval algorithm ranks by semantic similarity + importance + recency + frequency
- `pytest tests/test_memory.py` passes

**Files to create:**
```
goalos/
└── services/
    ├── embedding_service.py
    └── memory_service.py
tests/
└── test_memory.py
```

**Prompt to agent:**
> "Build Phase 3 of GoalOS. Implement the embedding service using sentence-transformers (all-MiniLM-L6-v2) with in-memory caching, and the memory service backed by ChromaDB. Implement the composite retrieval algorithm from the spec (semantic 40%, importance 30%, recency 20%, frequency 10%). Write tests."

---

## Phase 4 — Journal Import (Historical Data)
**What you build:** Parser and importer for the user's handwritten journal format. This is the most important phase after foundation because it unlocks day-one Coach personalization.

**Entry condition:** Phases 1 and 3 complete.

**Exit condition:**
- Parser correctly extracts all 6 sections from the user's journal format
- Importer stores entries in `daily_logs` and extracts memories into ChromaDB
- Excel/CSV import pipeline works end-to-end
- `pytest tests/test_journal_import.py` passes
- Onboarding summary generates successfully

**The User's Journal Format (from handwritten notebook, transcribed to Excel):**

The user journals daily in a structured handwritten format with these sections:

```
GRATITUDE    grateful for such friendly parents.
             23/6/26

PLANS
10:30-12     Restructuring Quandao planning app
1:30-3       Solve 10 Codekata Problems
3-5          Quandao codebase
5-9/10       Make the Final Project work and learn
10-12        Run and chill
8-9/1+       Codekata 1

TASKS
① Solve 10 Code Kata Problems          X
② Solve 10 Codekata                   X
③ Solve 10 Codekata                   X
④ Solve 10 Codekata                   X
⑤ Solve 10 Codekata
⑥ Prepare for evaluation              X
⑦ Finish evaluation                   X
⑧ Review the GoalOS plan              X

REVIEW       I did great work but not focusing on what matters

TAKEAWAY     Focus and lock in.
```

**Section meanings:**
- `GRATITUDE` — one-line daily gratitude statement
- Date — `DD/MM/YY` or `DD/M/YY` format
- `PLANS` — time-blocked schedule for the day (time range : activity)
- `TASKS` — numbered brain dump of intended tasks; `X` = completed, blank = not completed
- `REVIEW` — end-of-day narrative reflection
- `TAKEAWAY` — single lesson or focus for tomorrow

**Excel Schema (the format the user will export their data to):**

The user should prepare their historical data as an Excel file with these columns:

| Column | Description |
|---|---|
| `date` | DD/MM/YY or YYYY-MM-DD |
| `gratitude` | Text |
| `plans` | Text block: "10:30-12: Task\n1:30-3: Task" |
| `tasks` | Text block: "1. Task [done]\n2. Task [done]\n3. Task" (X or [done] marks completion) |
| `review` | Text |
| `takeaway` | Text |

**What the parser must extract:**
- `date` → `daily_logs.date`
- `gratitude` → stored as `memory` type `achievement` with importance 0.3
- `plans` → parsed into time blocks list → stored in `daily_logs.morning_ai_output` as plan context
- `tasks` → parsed into list of `{text, completed: bool}` → stored in `daily_logs.tasks_completed`
- `task_completion_rate` → `completed_count / total_count` → feeds `productivity_score`
- `review` → `daily_logs.journal_entry` (treated as evening journal)
- `takeaway` → `daily_logs.one_lesson` + extracted as `commitment` or `lesson` memory

**Memory extraction from imported entries:**

For each imported entry, run the Reflection Coach (lightweight version, no full LLM call needed in Phase 4 — use keyword rules):

- If `review` contains "but not" or "however" or "except" → tag as `lesson` memory
- If `takeaway` starts with a verb → tag as `commitment` memory, importance 0.7
- If `gratitude` is non-empty → tag as `achievement` memory, importance 0.3
- If same task appears uncompleted 3+ days → tag as `distraction` memory

**Files to create:**
```
goalos/
└── services/
    └── journal_import_service.py
tests/
└── test_journal_import.py
```

**`JournalImportService` interface:**
```python
class JournalImportService:

    def import_from_excel(self, file_path: str) -> ImportResult:
        """
        Reads Excel file with columns:
        date, gratitude, plans, tasks, review, takeaway
        Returns ImportResult with counts and errors.
        """

    def import_from_text_block(self, raw_text: str) -> ImportResult:
        """
        Parses raw pasted text using the handwritten journal format.
        Auto-detects dates. Handles missing sections gracefully.
        """

    def parse_entry(self, row: dict) -> ParsedEntry:
        """
        Converts a raw row/dict into a structured ParsedEntry.
        Handles date parsing (DD/MM/YY, YYYY-MM-DD, DD/M/YY).
        Handles task parsing (numbered list, completion markers X / [done] / ✓).
        Handles plan parsing (time range : activity).
        """

    def store_entry(self, entry: ParsedEntry) -> None:
        """
        Stores in daily_logs.
        Extracts and stores memories via rule-based extraction.
        Embeds journal text and stores in ChromaDB.
        """

    def generate_onboarding_summary(self) -> str:
        """
        After all entries imported, generates:
        - Total days imported
        - Most common gratitude themes
        - Most common task categories
        - Most common takeaway themes
        - Observable patterns (e.g. "You completed tasks at 74% rate")
        Returns a formatted string for display in History page.
        """
```

**ImportResult model:**
```python
class ImportResult(BaseModel):
    total_entries: int
    successfully_imported: int
    skipped_duplicates: int
    errors: list[str]
    memories_extracted: int
    date_range: tuple[date, date]
    onboarding_summary: str
```

**Prompt to agent:**
> "Build Phase 4 of GoalOS. Implement the journal import service. The user journals in a structured format with sections: GRATITUDE, date, PLANS (time blocks), TASKS (numbered with X for completion), REVIEW, TAKEAWAY. Import must support Excel files and raw text. Parse all sections, store in daily_logs, extract memories using rule-based logic (no LLM needed yet), embed journal text into ChromaDB. Generate an onboarding summary after import. Write comprehensive tests."

---

## Phase 5 — OpenRouter Client and AI Pipelines
**What you build:** LLM client + all 6 coaching pipelines as callable Python functions.

**Entry condition:** Phases 1 and 3 complete.

**Exit condition:**
- `OpenRouterClient.complete()` works with retry logic and JSON parsing
- All 6 pipelines return valid structured JSON matching their output schemas
- Pipelines fail gracefully (return cached/default output if LLM fails)
- Manual test: run morning pipeline with sample data, verify output structure

**Files to create:**
```
goalos/
├── ai/
│   ├── __init__.py
│   ├── openrouter_client.py
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── morning_coach.py
│   │   ├── evening_coach.py
│   │   ├── weekly_coach.py
│   │   ├── goal_alignment_coach.py
│   │   ├── reflection_coach.py
│   │   └── future_self_coach.py
│   └── prompts/
│       ├── morning.txt
│       ├── evening.txt
│       ├── weekly.txt
│       ├── goal_alignment.txt
│       ├── reflection.txt
│       └── future_self.txt
```

**OpenRouter client spec:**
```python
class OpenRouterClient:
    def complete(
        self,
        system_prompt: str,
        user_message: str,
        response_format: dict = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        max_retries: int = 3
    ) -> dict | str:
        # Retry on 429/500 with exponential backoff
        # Parse JSON when response_format provided
        # Return raw string otherwise
        # Log every request with latency
```

**Default model:** `anthropic/claude-3.5-sonnet` (via .env `OPENROUTER_MODEL`)

**All 6 pipeline output schemas — see Section 10 of this spec.**

**Prompt to agent:**
> "Build Phase 5 of GoalOS. Implement the OpenRouter LLM client with retry logic, JSON parsing, and structured logging. Then implement all 6 AI coaching pipelines: morning, evening, weekly, goal alignment, reflection, and future self. Each pipeline must assemble context from DB/ChromaDB, build the prompt, call the LLM, parse the output, and return valid structured JSON. Write prompt files for each pipeline. Handle LLM failures gracefully with fallback outputs."

---

## Phase 6 — Coach Service (Context Assembler)
**What you build:** The orchestration layer that ties analytics + memory + AI into a single callable service. Also builds the conversational Coach logic.

**Entry condition:** Phases 2, 3, and 5 complete.

**Exit condition:**
- `CoachService.get_morning_coaching(date)` returns full morning output
- `CoachService.get_evening_coaching(date, log)` returns full evening output
- `CoachService.chat(message, history)` returns grounded conversational response
- Context assembly always includes goals, logs, memories, commitments, past advice

**Files to create:**
```
goalos/
└── services/
    └── coach_service.py
```

**`CoachService` interface:**
```python
class CoachService:

    def build_context(self, date: date, query: str = "") -> dict:
        """
        Assembles:
        - All active goals
        - Last 7 daily logs
        - Current scores
        - Latest weekly review
        - Top 5 relevant memories (semantic query)
        - Unfulfilled commitments
        - Last 3 coach responses
        """

    def get_morning_coaching(self, date: date, log: DailyLog) -> dict:
        """Runs morning pipeline. Stores output in coach_responses."""

    def get_evening_coaching(self, date: date, log: DailyLog) -> dict:
        """Runs evening pipeline. Extracts and stores memories. Stores output."""

    def get_weekly_coaching(self, week_start: date) -> dict:
        """Runs weekly pipeline. Stores in weekly_reviews table."""

    def chat(self, message: str, history: list[dict]) -> dict:
        """
        Retrieves full context. Runs conversational response.
        Extracts commitments. Stores memory if significant.
        """
```

**Prompt to agent:**
> "Build Phase 6 of GoalOS. Implement the CoachService as the central orchestration layer. It must assemble the full context block (goals, logs, memories, commitments, past advice, scores) before every AI call. Implement morning, evening, weekly, and conversational chat methods. Ensure memories are stored after every evening and weekly session. Ensure commitments detected in chat are stored with type='commitment'."

---

## Phase 7 — Dashboard and Vision & Goals Pages
**What you build:** The two most important pages. Dashboard is the daily landing page. Vision & Goals is the foundation of all AI reasoning.

**Entry condition:** Phases 1, 2, 5, and 6 complete.

**Exit condition:**
- Dashboard loads in under 2 seconds
- All 8 dashboard sections display correctly
- Goals can be created, edited, and updated
- AI alignment check runs on goal hierarchy

**Files to create:**
```
goalos/
├── pages/
│   ├── 1_Dashboard.py
│   └── 2_Vision_Goals.py
└── components/
    ├── __init__.py
    ├── score_card.py
    └── goal_card.py
```

**Dashboard sections:**
1. Today's Focus (from today's morning log top_priority)
2. Current Streak (consecutive days with morning or evening completed)
3. Yesterday's Overall Growth Score with delta indicator
4. 7-day sparkline (Plotly)
5. Monthly bar chart (Plotly)
6. Goal Progress cards (one per active goal)
7. Gap Score with interpretation
8. Today's single recommendation (from CoachService, cached)
9. Quote from user's own goals (AI-generated from goal reasons)

**Dashboard intelligence:** Below each metric, one AI-generated interpretation sentence. Load all interpretations as a single batch call to avoid multiple LLM calls.

**Prompt to agent:**
> "Build Phase 7 of GoalOS. Create the Dashboard page and Vision & Goals page in Streamlit. Dashboard must show all 8 sections from the spec with Plotly charts, and include AI-generated interpretations (one batch LLM call). Vision & Goals must support full CRUD for all goal horizons with category/status filters and an AI alignment check."

---

## Phase 8 — Morning and Evening Pages
**What you build:** The two daily ritual pages. These are the primary data entry surfaces.

**Entry condition:** Phases 5 and 6 complete.

**Exit condition:**
- Morning form collects all fields, submits, triggers morning coaching pipeline
- Evening form: journal textarea is first, structured fields are second
- AI pre-fills win and lesson from journal text
- Evening submission triggers score calculation and memory extraction
- Fast Mode toggle works on morning page
- Both pages detect if already submitted today and show "edit" mode

**Files to create:**
```
goalos/
└── pages/
    ├── 3_Morning_Planning.py
    └── 4_Evening_Reflection.py
```

**Morning page flow:**
1. Check if morning already submitted today → if yes, show output + edit button
2. Step 1: Free-write fields (on my mind, intention, anxiety, anticipation)
3. Step 2: Structured fields (sleep, energy, mood, focus, hours, constraints) — hidden if Fast Mode on
4. Step 3: Priorities (top priority, 2 supporting tasks)
5. Submit → run `CoachService.get_morning_coaching()` → display output card
6. Cache output — do not regenerate unless user clicks "Regenerate"

**Evening page flow:**
1. Check if evening already submitted today → if yes, show output + edit button
2. Journal textarea first (large, prominent, no word limit)
3. After journal written: show structured fields
4. AI pre-fills "one win" and "one lesson" from journal text (highlight pre-filled fields)
5. Submit → run `CoachService.get_evening_coaching()` → display output card
6. Show commitment detected (if any) as a highlighted callout
7. Show tomorrow's first task prominently

**Prompt to agent:**
> "Build Phase 8 of GoalOS. Create the Morning Planning and Evening Reflection pages. Morning must have Fast Mode toggle and a 3-step flow (free-write → structured → priorities). Evening must have journal textarea first, then structured fields, with AI pre-filling win and lesson from journal text. Both pages must detect if already submitted today and support editing. Trigger coaching pipelines on submit and cache outputs."

---

## Phase 9 — Weekly Review, History, and Coach Pages
**What you build:** The three remaining pages.

**Entry condition:** Phases 4, 5, 6, and 8 complete.

**Exit condition:**
- Weekly Review auto-generates on Sunday or on demand
- History shows full timeline with semantic search working
- Journal import UI works in History page (Excel upload + text paste)
- Onboarding summary displays after first import
- Coach page has conversational interface with full context grounding
- Suggested starters appear on first open each day

**Files to create:**
```
goalos/
└── pages/
    ├── 5_Weekly_Review.py
    ├── 6_History.py
    └── 7_Coach.py
└── components/
    ├── timeline_entry.py
    └── memory_card.py
```

**History page must include:**
- Import section at the top (collapsible): Excel upload + raw text paste tabs
- Onboarding summary display (after import)
- Timeline view: daily entries → weekly summaries → monthly summaries
- Semantic search bar (queries ChromaDB, returns ranked results)
- Filter by type (log, weekly, memory, coaching)

**Coach page must include:**
- Chat interface with message history
- Sidebar showing: active memories used, goals referenced, commitments tracked
- Suggested conversation starters (refreshed daily)
- "What does my future self say?" button → triggers Future Self Coach

**Prompt to agent:**
> "Build Phase 9 of GoalOS. Create the Weekly Review, History, and Coach pages. Weekly Review must auto-generate from the last 7 daily logs and include drift detection. History must include the journal import UI (Excel + text paste), onboarding summary display, full timeline, and ChromaDB semantic search. Coach must be a full conversational interface grounded in goals/memories/history, with a sidebar showing context used and a Future Self button."

---

## Phase 10 — Polish, Testing, and Excel Import Completion
**What you build:** End-to-end testing, UI polish, error handling, and completing the historical Excel data import for the first real use.

**Entry condition:** All phases 1–9 complete.

**Exit condition:**
- `pytest` passes all test files
- App runs without errors on a fresh machine from `requirements.txt`
- Historical journals successfully imported from Excel
- Onboarding summary generated and visible
- Coach has full 1–2 months of context
- All Streamlit pages load without errors
- Error messages are user-friendly (no raw tracebacks)

**Tasks in this phase:**

1. **Run full test suite** — fix any failures
2. **UI polish:**
   - Consistent color theme across all pages
   - Mobile-responsive layout (Streamlit columns)
   - Loading spinners on all AI calls
   - Empty states for pages with no data yet
3. **Error handling audit:**
   - Every AI call has a graceful fallback
   - DB errors surface as friendly messages
   - Import errors show per-row details, not full crash
4. **Excel import — first real use:**
   - Prepare the Excel file from your handwritten journals
   - Run import via the History page
   - Verify onboarding summary
   - Verify Coach has full historical context
5. **Settings page** (minimal):
   - Change OpenRouter model
   - View DB stats (total entries, total memories)
   - Clear all data (with confirmation)
6. **Performance:**
   - Verify embedding cache is working
   - Verify daily AI outputs are cached and not regenerating on page refresh

**Prompt to agent:**
> "Build Phase 10 of GoalOS. This is the polish and completion phase. Run all tests and fix failures. Add loading spinners, empty states, and consistent styling. Audit all error handling — every AI call and DB operation must fail gracefully. Add a minimal Settings page with model config, DB stats, and data reset. Verify the full app runs cleanly end to end."

---

# 7. Project Structure

```
goalos/
├── app.py
├── .env
├── .env.example
├── requirements.txt
│
├── config/
│   └── settings.py
│
├── database/
│   ├── connection.py
│   ├── migrations.py
│   └── repositories/
│       ├── __init__.py
│       ├── goal_repository.py
│       ├── log_repository.py
│       ├── score_repository.py
│       ├── memory_repository.py
│       └── coach_repository.py
│
├── models/
│   ├── __init__.py
│   ├── goal.py
│   ├── daily_log.py
│   ├── weekly_review.py
│   ├── score.py
│   ├── memory.py
│   └── coach_response.py
│
├── services/
│   ├── __init__.py
│   ├── analytics_service.py
│   ├── memory_service.py
│   ├── embedding_service.py
│   ├── journal_import_service.py
│   └── coach_service.py
│
├── ai/
│   ├── __init__.py
│   ├── openrouter_client.py
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── morning_coach.py
│   │   ├── evening_coach.py
│   │   ├── weekly_coach.py
│   │   ├── goal_alignment_coach.py
│   │   ├── reflection_coach.py
│   │   └── future_self_coach.py
│   └── prompts/
│       ├── morning.txt
│       ├── evening.txt
│       ├── weekly.txt
│       ├── goal_alignment.txt
│       ├── reflection.txt
│       └── future_self.txt
│
├── pages/
│   ├── 1_Dashboard.py
│   ├── 2_Vision_Goals.py
│   ├── 3_Morning_Planning.py
│   ├── 4_Evening_Reflection.py
│   ├── 5_Weekly_Review.py
│   ├── 6_History.py
│   └── 7_Coach.py
│
├── components/
│   ├── __init__.py
│   ├── score_card.py
│   ├── goal_card.py
│   ├── timeline_entry.py
│   └── memory_card.py
│
└── tests/
    ├── __init__.py
    ├── test_repositories.py
    ├── test_analytics.py
    ├── test_memory.py
    └── test_journal_import.py
```

---

# 8. Data Model

## Tables

### User
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    life_vision TEXT,
    five_year_vision TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Goals
```sql
CREATE TABLE goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    horizon TEXT NOT NULL,
    deadline DATE,
    priority INTEGER DEFAULT 3,
    progress REAL DEFAULT 0.0,
    status TEXT DEFAULT 'active',
    reason TEXT,
    success_criteria TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### DailyLogs
```sql
CREATE TABLE daily_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,

    -- Morning fields
    morning_completed BOOLEAN DEFAULT FALSE,
    sleep_hours REAL,
    sleep_quality INTEGER,
    energy_level INTEGER,
    mood_morning INTEGER,
    expected_focus INTEGER,
    available_hours REAL,
    calendar_constraints TEXT,
    free_write TEXT,
    intention TEXT,
    anxiety TEXT,
    anticipation TEXT,
    top_priority TEXT,
    supporting_task_1 TEXT,
    supporting_task_2 TEXT,

    -- Journal import fields (mapped from handwritten format)
    gratitude TEXT,
    time_blocks TEXT,                -- JSON: [{"start":"10:30","end":"12:00","activity":"..."}]
    planned_tasks TEXT,              -- JSON: [{"text":"...","completed":false}]

    -- Evening fields
    evening_completed BOOLEAN DEFAULT FALSE,
    journal_entry TEXT,
    tasks_completed TEXT,
    task_completion_rate REAL,       -- computed: completed/total from planned_tasks
    deep_work_hours REAL,
    workout_completed BOOLEAN,
    workout_notes TEXT,
    biggest_distraction TEXT,
    mood_evening INTEGER,
    one_win TEXT,
    one_lesson TEXT,
    takeaway TEXT,                   -- from journal import TAKEAWAY section

    -- AI outputs
    morning_ai_output TEXT,
    evening_ai_output TEXT,

    -- Import metadata
    imported BOOLEAN DEFAULT FALSE,
    import_source TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### WeeklyReviews
```sql
CREATE TABLE weekly_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    ai_output TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Scores
```sql
CREATE TABLE scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    scope TEXT NOT NULL,
    goal_alignment_score REAL,
    consistency_score REAL,
    health_score REAL,
    learning_score REAL,
    productivity_score REAL,
    momentum_score REAL,
    overall_growth_score REAL,
    gap_score REAL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### CoachResponses
```sql
CREATE TABLE coach_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_type TEXT NOT NULL,
    user_message TEXT,
    ai_response TEXT NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Memories
```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    type TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    source_date DATE,
    source_type TEXT,
    source_id INTEGER,
    recency_score REAL,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Settings
```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

# 9. Historical Data — Excel Preparation Guide

Before running the import in Phase 10, prepare your handwritten journals as an Excel file.

## Excel Column Definitions

| Column | Required | Format | Example |
|---|---|---|---|
| `date` | Yes | DD/MM/YY or YYYY-MM-DD | `23/6/26` or `2026-06-23` |
| `gratitude` | No | Plain text | `grateful for such friendly parents` |
| `plans` | No | One time block per line: `HH:MM-HH:MM: Activity` | `10:30-12: Restructuring Quandao` |
| `tasks` | No | One task per line; add `[done]` or `X` for completed | `1. Solve 10 Codekata [done]` |
| `review` | No | Plain text, any length | `I did great work but not focusing on what matters` |
| `takeaway` | No | Plain text | `Focus and lock in` |

## Tips for Preparation

- Use one row per day
- If a section is blank for a day, leave the cell empty (do not write "N/A")
- Tasks: number them (`1.`, `2.`, etc.) and mark completed with `[done]`, `X`, or `✓`
- Plans: write each time block on a new line within the same cell (Alt+Enter in Excel)
- Date format: the parser handles both `23/6/26` and `2026-06-23` — use whichever is easier

## What the Import Will Produce

After import, the system will:
- Populate `daily_logs` for every imported date
- Extract `task_completion_rate` per day
- Extract `gratitude` → memory (achievement, importance 0.3)
- Extract `takeaway` → memory (commitment or lesson, importance 0.7)
- Detect patterns (e.g. recurring uncompleted tasks) → memory (pattern, importance 0.8)
- Embed all journal + review text into ChromaDB
- Generate an onboarding summary visible in the History page

---

# 10. AI Coaching Engine

## Shared Context Block

Every AI pipeline must begin by assembling this context:

```python
def build_context(date: date, query: str = "") -> dict:
    return {
        "user_vision": get_user_vision(),
        "active_goals": get_active_goals(),
        "recent_logs": get_daily_logs(last_n=7),
        "current_scores": get_scores(date),
        "recent_weekly_review": get_latest_weekly_review(),
        "relevant_memories": retrieve_memories(query, top_k=5),
        "unfulfilled_commitments": get_commitments(status="pending"),
        "recent_coach_advice": get_coach_responses(last_n=3)
    }
```

## Pipeline Output Schemas

### Morning Coach
```json
{
  "focus_statement": "string",
  "suggested_work_order": ["string"],
  "risk_prediction": "string",
  "one_thing_to_avoid": "string",
  "motivational_message": "string",
  "goal_connection": "string",
  "confidence": 0.0
}
```

### Evening Coach
```json
{
  "journal_insights": ["string"],
  "scores": {
    "goal_alignment_score": 0.0,
    "consistency_score": 0.0,
    "health_score": 0.0,
    "learning_score": 0.0,
    "productivity_score": 0.0
  },
  "one_thing_done_well": "string",
  "one_improvement": "string",
  "tomorrow_first_task": "string",
  "pattern_detected": "string",
  "commitment_extracted": "string | null",
  "memories_to_store": [],
  "confidence": 0.0
}
```

### Weekly Coach
```json
{
  "week_summary": "string",
  "wins": ["string"],
  "failures": ["string"],
  "most_productive_day": "string",
  "least_productive_day": "string",
  "recurring_distractions": ["string"],
  "recurring_strengths": ["string"],
  "weekly_score": 0.0,
  "patterns_detected": ["string"],
  "drift_detected": "string | null",
  "one_improvement": "string",
  "future_self_message": "string",
  "confidence": 0.0
}
```

### Goal Alignment Coach
```json
{
  "alignment_narrative": "string",
  "aligned_goals": ["string"],
  "neglected_goals": ["string"],
  "recommendation": "string",
  "confidence": 0.0
}
```

### Reflection Coach
```json
{
  "insights": ["string"],
  "commitments": ["string"],
  "patterns": ["string"],
  "memories_to_store": [
    {"text": "string", "type": "string", "importance": 0.0}
  ],
  "confidence": 0.0
}
```

### Future Self Coach
```json
{
  "message": "string",
  "written_from_age": 35,
  "key_things_referenced": ["string"],
  "confidence": 0.0
}
```

**Future Self Coach must:**
- Reference specific recurring struggles from memory
- Acknowledge what the user has been avoiding
- Never be generic or motivational-poster-like
- Sound like someone who lived through this exact period

---

# 11. Analytics Engine

All scores are deterministic — calculated before any AI call. Range: 0–100.

```python
# Goal Alignment Score
alignment = embedding_similarity(tasks_text, goals_text) * 100

# Consistency Score
streak_component = min(streak_days / 30, 1.0) * 40
execution_component = (completed_days_30 / 30) * 60
consistency = streak_component + execution_component

# Health Score
sleep = normalize(sleep_hours, 4, 9) * 40
workout = 30 if workout_completed else 0
energy = normalize(energy_level, 1, 5) * 30
health = sleep + workout + energy

# Learning Score
keywords = ["read","studied","learned","practiced","course","book","research","codekata","coding"]
matches = count_matches(journal + tasks, keywords)
learning = min(matches * 20, 100)

# Productivity Score
deep_work = normalize(deep_work_hours, 0, 6) * 50
tasks_done = min(task_completion_rate, 1.0) * 30
focus = normalize(expected_focus, 1, 5) * 20
productivity = deep_work + tasks_done + focus

# Momentum Score (linear regression on 7-day overall scores)
slope = linear_regression_slope(scores_7d)
momentum = normalize(slope, -10, 10) * 100

# Gap Score (pace vs required pace per goal)
gap = aggregate_weighted_gaps_across_goals()

# Overall Growth Score
overall = (
    goal_alignment * 0.30 +
    consistency    * 0.25 +
    health         * 0.15 +
    productivity   * 0.15 +
    learning       * 0.10 +
    momentum       * 0.05
)
```

---

# 12. Memory System

## Memory Types

| Type | Trigger | Importance |
|---|---|---|
| `goal` | Goal created/updated | 0.9 |
| `failure` | Documented failure | 0.8 |
| `achievement` | Win / milestone / gratitude | 0.7 |
| `lesson` | "I learned / I realized" | 0.8 |
| `commitment` | "I will / I'll / tomorrow I" | 0.7 |
| `excuse` | Same reason appears 3x | 0.6 |
| `distraction` | Same distraction 3x | 0.6 |
| `routine` | Successful repeated pattern | 0.7 |
| `breakthrough` | High-impact insight | 0.9 |
| `journal_insight` | AI extraction from journal | 0.6 |
| `pattern` | Behavioral pattern across logs | 0.7 |

## Retrieval Algorithm

```python
composite_score = (
    semantic_similarity * 0.40 +
    importance          * 0.30 +
    recency             * 0.20 +  # exp decay, 30-day half-life
    frequency           * 0.10    # log(access_count + 1)
)
```

---

# 13. Engineering Standards

- Modular architecture — no page file contains business logic
- Strong typing — all function signatures typed
- Pydantic models for all data structures
- Repository pattern for all data access
- No raw SQL outside repository files
- Every AI call wrapped in try/except with graceful fallback
- Streamlit `@st.cache_data` with TTL on all expensive DB queries
- Embeddings cached in memory during session
- Structured logging to `goalos.log`
- `pytest` for all analytics, memory, and import functions

## Environment Configuration
```env
OPENROUTER_API_KEY=
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
DB_PATH=./goalos.db
CHROMA_PATH=./chroma_db
LOG_LEVEL=INFO
```

---

# 14. Success Criteria

1. Morning ritual: 15 minutes, unhurried
2. Evening ritual: 15 minutes, journal-first
3. AI remembers everything — no re-explaining context
4. Every recommendation grounded in goals, scores, and memory
5. User always knows one highest-leverage action for tomorrow
6. Historical import gives day-one personalization
7. After 90 days, Coach surfaces patterns user couldn't notice manually
8. After 6 months, Future Self message feels written by someone who actually knows you

---

# 15. Phase Summary Table

| Phase | What You Build | Depends On | Delivers |
|---|---|---|---|
| 1 | Foundation (DB, models, repos) | Nothing | Runnable schema + CRUD |
| 2 | Analytics Engine (all scores) | Phase 1 | Deterministic scoring |
| 3 | Embedding + Memory System | Phase 1 | ChromaDB retrieval |
| 4 | Journal Import (your format) | Phases 1, 3 | Historical data ready |
| 5 | OpenRouter + AI Pipelines | Phases 1, 3 | All 6 coaches callable |
| 6 | Coach Service (orchestration) | Phases 2, 3, 5 | Unified coach API |
| 7 | Dashboard + Vision & Goals | Phases 1, 2, 5, 6 | First usable UI |
| 8 | Morning + Evening Pages | Phases 5, 6 | Daily ritual works |
| 9 | Weekly, History, Coach Pages | Phases 4, 5, 6, 8 | Full app complete |
| 10 | Polish + Real Data Import | All phases | Production-ready |

---

*GoalOS v3.0 — Built for one user. Ten phases. One purpose: 1% better every day.*
