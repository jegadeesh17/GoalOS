# GoalOS — LLM Interview Prep

## 90-second pitch (memorize)

> GoalOS is a personal AI operating system I built with Streamlit, SQLite, ChromaDB, and OpenRouter. Users journal daily; insights become vector memories. When coaching runs, the system either retrieves ranked memories via RAG or uses an LLM agent that calls tools — `search_memories` and `get_active_goals` — to fetch only relevant context before generating a mentor rule. I use composite ranking — 40% semantic, 30% importance, 20% recency, 10% frequency — not naive top-k retrieval. The architecture is Repository → Service → Pipeline → UI, with 65+ pytest tests, retry logic, free-model fallback, and graceful degradation when the API is unavailable. Limitation: small personal corpus early on; I evaluate with a manual rubric on retrieval relevance and response usefulness.

## RAG — know cold

| Step | What happens |
|------|----------------|
| Embed | `all-MiniLM-L6-v2` via sentence-transformers |
| Store | SQLite + ChromaDB (cosine HNSW) |
| Query | Embed user text → ChromaDB `n_results = top_k * 3` |
| Rank | Composite score (40/30/20/10) |
| Inject | Top memories in coach prompt or via tool result |
| Generate | OpenRouter JSON mode |

**"Is this RAG?"** — Yes. Retrieve relevant documents from a vector store, rank them, inject into LLM context, generate grounded output. No fine-tuning.

## Tool calling — know cold

**Without tools:** `CoachService.build_context()` dumps all goals, logs, scores, memories into one prompt.

**With tools:** LLM sees tool schemas → calls `search_memories("gym")` → Python runs `MemoryService.retrieve()` → result sent back → LLM writes rule using only fetched data.

**Files:** `ai/tools.py`, `OpenRouterClient.complete_with_tools()`, `agent_morning_coach.py`

## MCP — one sentence

"MCP exposes the same tool functions via a standard protocol for external AI clients. I implemented in-app tool calling; MCP would wrap `execute_tool()` without changing business logic."

## Likely questions

| Question | Answer |
|----------|--------|
| Why ChromaDB? | Local-first, single-user, no cloud cost, fast enough |
| Why OpenRouter? | Swap models via config; free-tier fallback |
| Prevent hallucination? | Retrieval/tools inject real history; prompts say use only provided specifics; eval rubric flags hallucinations |
| Biggest weakness? | Small corpus early; retrieval improves with more journals |
| Scale to multi-user? | Auth + tenant-scoped Chroma collections + API layer |

## Daily drill (60 min)

- 20 min SQL (joins, windows)
- 20 min Python/pandas
- 20 min timed GoalOS pitch + one follow-up answer

## Demo commands

```powershell
cd c:\Users\jegad\projects\GoalOS
pytest -q
streamlit run app/app.py
```
