# GoalOS — Agentic Coaching System with RAG Memory
---
### **Project Overview**
GoalOS is an agentic personal coaching system that combines deterministic analytics, composite memory retrieval (ChromaDB + SQLite), and LLM tool-calling to guide daily execution against long-term goals. It is a personal AI operating system — not a habit tracker — helping one user align daily actions with 1-, 5-, and 10-year goals.

**Interview pitch:** *"I built an agentic coaching system with composite memory retrieval, LLM tool-calling for on-demand context, FastAPI deployment, and 70+ pytest tests — with transparent fallbacks when the LLM API is unavailable."*

**Repository:** [github.com/jegadeesh17/GoalOS](https://github.com/jegadeesh17/GoalOS)  
**Full specification:** [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md)  
**Live demo:** [Streamlit Cloud](https://share.streamlit.io) — see [DEPLOY.md](DEPLOY.md)

---
### **Key Features**
- Single-user, local-first architecture (SQLite + ChromaDB)
- Daily logging and weekly reflection workflow
- Composite memory retrieval: 40% semantic + 30% importance + 20% recency + 10% frequency
- LLM tool-calling for morning coaching (`search_memories`, `get_active_goals`)
- Session-specific coach pipelines (morning, evening, weekly, reflection)
- FastAPI `POST /coach/morning` with structured JSON output
- Graceful fallbacks: API failure → static coach → rule-based fallback
- 70+ pytest tests across repositories, memory, analytics, and API

---
### **Dataset**
- **Source:** Personal journal and goal data entered via Streamlit UI
- **Structured store:** SQLite (`goalos.db`) — goals, logs, scores, commitments
- **Vector store:** ChromaDB (`chroma_db/`) — embedded memory snippets
- **Embeddings:** `all-MiniLM-L6-v2` via sentence-transformers (hash fallback for offline tests)
- **No public dataset** — import journals through the app or seed demo memories

---
### **Project Structure**
```text
GoalOS/
├── app/
│   ├── app.py                  # Streamlit entry (multi-page)
│   └── pages/                  # Streamlit views
├── api/main.py                 # FastAPI coach endpoint
├── database/repositories/      # Data access layer
├── services/                   # CoachService, MemoryService, AnalyticsService
├── ai/
│   ├── pipelines/              # Session-specific prompting + agent morning coach
│   ├── tools.py                # LLM tool schemas and execution
│   └── openrouter_client.py    # Retries, JSON parse, tool loop
├── tests/                      # pytest suite
├── docs/DEMO.md                # Interview walkthrough
├── reports/evaluation.md       # Retrieval eval report
├── requirements.txt
└── README.md
```

---
### **How It Works**
1. User writes logs and goals in Streamlit UI.
2. Logs and goals persist via SQLite repositories.
3. `MemoryService` embeds insights and stores in ChromaDB + SQLite.
4. On coaching, `CoachService` runs the agent morning pipeline (or static/evening/weekly pipelines).
5. LLM calls tools via `ai/tools.py` → `MemoryService.retrieve()` and `GoalRepository`.
6. OpenRouter returns structured JSON; output is persisted and shown in UI.

**RAG flow:** Embed → ChromaDB retrieve → composite rank → prompt inject → generate.

**Architecture pattern:** Repository → Service → Pipeline → UI/API (no LangChain).

---
### **Model Performance**
- **Tests:** 70+ pytest passing (`pytest -q`)
- **Retrieval eval:** 5-query manual check — avg relevance 0.40/2.0 on sparse demo corpus (`reports/evaluation.md`)
- **Regenerate eval:** `python scripts/generate_retrieval_eval.py`
- **Manual rubric:** `docs/goalos_eval_template.csv`, `docs/goalos_eval_notes.md`

Disclose honestly: personal corpus may be small early on; eval is lightweight rubric-based.

---
### **Interactive Application Deployment**
```powershell
# Streamlit UI
streamlit run app/app.py

# FastAPI
uvicorn api.main:app --reload --port 8000
```

**Streamlit Cloud:** See [DEPLOY.md](DEPLOY.md). Secrets example (`.streamlit/secrets.toml`):
```toml
OPENROUTER_API_KEY = "your-key"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
DB_PATH = "goalos.db"
CHROMA_PATH = "chroma_db"
```

---
### **Technology Stack**
| Layer | Technology |
|-------|------------|
| UI | Streamlit |
| API | FastAPI |
| Database | SQLite |
| Memory store | ChromaDB |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| LLM | OpenRouter (`OPENROUTER_MODEL` configurable) |
| Tests | pytest |

---
### **Getting Started**

#### **1. Clone Repository**
```bash
git clone https://github.com/jegadeesh17/GoalOS.git
cd GoalOS
```

#### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

#### **3. Launch Notebook**
GoalOS has no training notebook — use Streamlit UI and `docs/DEMO.md`. See `docs/interview_llm_prep.md` for RAG/LLM concepts.

#### **4. Launch Dashboard**
```bash
pytest -q
python scripts/generate_retrieval_eval.py
streamlit run app/app.py
```

Copy `.env.example` → `.env` and set `OPENROUTER_API_KEY` for live LLM coaching.

---
### **Example Use Case**
**Input:** *"I planned deep work but delayed it for meetings. What should I fix tomorrow?"*

**Output:** One mentor rule, a concrete next-day action, and referenced memories/commitments from prior logs (via tool calling or retrieval).

---
### **Future Improvements**
- MCP wrapper for external agents (tools already exist in-process)
- Multi-user auth and tenant isolation
- Automated LLM-judge evaluation pipeline
- Larger personal corpus for stronger retrieval diversity

---
### **Contributors**
- **Jegadeesh D** — [GitHub](https://github.com/jegadeesh17) | [LinkedIn](https://linkedin.com/in/jegadeesh17)

---
### **License**
MIT License
