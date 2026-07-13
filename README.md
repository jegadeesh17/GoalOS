# GoalOS

GoalOS is a privacy-first, single-user coaching application. It links long-term goals and milestones to daily tasks, keeps local journal memory in SQLite and ChromaDB, and offers optional OpenRouter coaching only after explicit consent.

## What it does

- Morning planning and evening reflection without destructive overwrites.
- Measurable goals, milestones, and goal-linked tasks.
- Repairable hybrid memory retrieval with lifecycle controls.
- Explainable coaching with source/evidence and deterministic local fallbacks.
- Portable JSON export and automatic backup before local data reset.

## Local setup (Windows)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
streamlit run app/app.py
```

Copy `.env.example` to `.env` to configure an optional OpenRouter key. Enable **Allow remote AI coaching** in Settings before any journal content is sent remotely.

Run the API locally with `uvicorn api.main:app --port 8000`. Set `GOALOS_API_TOKEN` before hosting it; callers then send `Authorization: Bearer <token>`.

## Development checks

```powershell
python -m pytest -q
ruff check .
mypy api ai config database models services
python scripts/generate_retrieval_eval.py
docker build .
```

See [the updated specification](docs/PROJECT_SPEC.md), [deployment guidance](DEPLOY.md), and [security guidance](SECURITY.md).
