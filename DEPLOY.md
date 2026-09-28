# Deployment

GoalOS is designed for a trusted single user. SQLite and ChromaDB require durable writable storage.

## Local Docker

```powershell
docker compose up --build
```

Persist `goalos.db` and `chroma_db` on a private volume. Keep `.env`, backups, and exports outside source control.

## Demo Data (Cloud Run)

The public Cloud Run demo (`ENVIRONMENT=demo`, see `.github/workflows/deploy.yml`) ships a **fictional** dataset: persona "Alex Chen", 42 days of journal entries, 9 goals across 1-month to 10-year horizons. It is built from `data/demo_seed.csv` through the same import, memory, and scoring code real data uses:

```powershell
python scripts/generate_demo_journal.py data/demo_seed.csv   # only to regenerate the fictional journal
python scripts/build_demo_db.py                               # writes data/demo_goalos.db + data/demo_chroma_db/
```

The demo loader only runs when `ENVIRONMENT=demo`; a local install always uses its own `goalos.db` and `chroma_db`. Never copy a real `goalos.db`, journal CSV, or report generated from one into `data/demo_*` or `reports/`: this repository is public.

## FastAPI

For any non-local API deployment, set:

```text
ENVIRONMENT=production
GOALOS_API_TOKEN=<long-random-secret>
```

Every protected endpoint requires `Authorization: Bearer <GOALOS_API_TOKEN>`. Keep the API behind a trusted network or platform access control; it does not provide multi-user authentication.

## Frontend

The `frontend/` React app is a separate static build (Vite) that talks to the FastAPI API. Build with `npm run build` in `frontend/` and serve the resulting `dist/` from any static host, pointed at the API's URL.
