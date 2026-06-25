# GoalOS — Streamlit Deploy Guide (Beginner Friendly)

GoalOS runs as a **Streamlit app**.

## 1) Run locally first

```powershell
cd c:\Users\jegad\GoalOS
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`.

---

## 2) Deploy to Streamlit Community Cloud (free)

1. Push your code to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**.
4. Select:
   - Repository: your `GoalOS` repo
   - Branch: `main`
   - Main file path: `app.py`
5. Open **Advanced settings** and add secrets:
   - `OPENROUTER_API_KEY`
   - `OPENROUTER_MODEL`
   - `DB_PATH`
   - `CHROMA_PATH`
6. Click **Deploy**.

---

## 3) Streamlit Cloud secrets format

Paste this in the Streamlit **Secrets** box:

```toml
OPENROUTER_API_KEY = "your-key"
OPENROUTER_MODEL = "anthropic/claude-3.5-sonnet"
DB_PATH = "/mount/src/goalos.db"
CHROMA_PATH = "/mount/src/chroma_db"
LOG_LEVEL = "INFO"
```

Replace only `OPENROUTER_API_KEY` with your real key.

---

## 4) Important notes for personal use

- Streamlit Cloud free apps are internet-reachable by URL.
- Do not share the URL if this is personal.
- Never commit real secrets into GitHub.

---

## 5) Stack

| Layer | Tech |
|-------|------|
| UI + App | Streamlit |
| Data | SQLite, ChromaDB |
| AI | OpenRouter |
| Hosting | Streamlit Community Cloud |
