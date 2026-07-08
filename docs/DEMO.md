# GoalOS — Demo Script

5-minute interview walkthrough for the agentic coaching system.

## Prerequisites

```bash
pip install -r requirements.txt
# Optional: set OPENROUTER_API_KEY in .env for live LLM responses
pytest -q
```

## 1. Tests (30 sec)

```bash
pytest -q
```

Expect all repository, memory, tool-calling, and analytics tests to pass.

## 2. Retrieval eval (1 min)

```bash
python scripts/generate_retrieval_eval.py
type reports\evaluation.md
```

Explain composite ranking: semantic + importance + recency + frequency.

## 3. FastAPI tool-calling demo (2 min)

```bash
uvicorn api.main:app --reload --port 8000
```

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/coach/morning -H "Content-Type: application/json" -d "{\"gratitude\":\"Grateful for focus time\",\"tasks\":[{\"text\":\"90 min deep work on portfolio\",\"priority\":1}]}"
```

Point out `mentor_rule`, `tools_used`, and `source` fields in the response.

## 4. Streamlit UI (1 min)

```bash
streamlit run app/app.py
```

Journal page → Save Morning & Get Mentor Rule → show persisted coaching output.

## Checklist

- [ ] `pytest -q` green
- [ ] `reports/evaluation.md` has 5-query hit/miss table
- [ ] `/health` returns memory and log counts
- [ ] Morning coach returns structured JSON
