# GoalOS — Streamlit Cloud Deployment

## Prerequisites

- GitHub repo: [github.com/jegadeesh17/GoalOS](https://github.com/jegadeesh17/GoalOS)
- [OpenRouter](https://openrouter.ai) API key
- [Streamlit Community Cloud](https://share.streamlit.io) account (sign in with GitHub)

## Deploy (5 steps)

1. **Push latest `main`** to `github.com/jegadeesh17/GoalOS`.

2. Open [share.streamlit.io](https://share.streamlit.io) → **New app**.

3. **Repository:** `jegadeesh17/GoalOS`  
   **Branch:** `main`  
   **Main file path:** `app/app.py`

4. **Advanced settings → Secrets** — paste:

```toml
OPENROUTER_API_KEY = "sk-or-v1-..."
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
DB_PATH = "goalos.db"
CHROMA_PATH = "chroma_db"
LOG_LEVEL = "INFO"
```

Use a `:free` model for demos without paid credits. Paths are relative to the app root on Streamlit Cloud.

5. Click **Deploy**. First boot may take 3–5 minutes (sentence-transformers download).

## After deploy

- Copy the app URL (e.g. `https://goalos.streamlit.app`) into your resume and LinkedIn.
- Pin the repo on GitHub: Profile → **Customize your pins** → select **GoalOS**.

## Local smoke test before push

```powershell
cd c:\Users\jegad\projects\GoalOS
pip install -r requirements.txt
pytest -q
streamlit run app/app.py
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| App crashes on startup | Check Secrets tab; `OPENROUTER_API_KEY` must be set |
| Embedding model slow | Normal on cold start; subsequent runs use cache |
| AI returns fallback text | Verify API key and model name; try a `:free` model |
| ChromaDB errors | Ensure `CHROMA_PATH` is writable (use relative path above) |
