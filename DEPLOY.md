# Deployment

GoalOS is designed for a trusted single user. SQLite and ChromaDB require durable writable storage.

## Local Docker

```powershell
docker compose up --build
```

Persist `goalos.db` and `chroma_db` on a private volume. Keep `.env`, backups, and exports outside source control.

## Cloud Run

Pushing to `main` (or `feat/coach-chat-ui`) runs `.github/workflows/deploy.yml`, which builds the `Dockerfile` and deploys it. The workflow has no path filter, so any push to those branches redeploys, documentation-only pushes included. Deploys can also be started by hand (`workflow_dispatch`).

| Setting | Value (from `deploy.yml`) |
| :--- | :--- |
| Cloud Run service | `goalos-api` |
| Region | `asia-south1` |
| Artifact Registry repository | `ml-apis` |
| GitHub secrets used | `GCP_SA_KEY`, `GCP_PROJECT_ID` |
| Resources | 2Gi memory, 1 CPU, 300 s timeout, 0 to 2 instances |
| Environment variable set | `ENVIRONMENT=demo` |
| Access | `--allow-unauthenticated`; no `GOALOS_API_TOKEN` is set, so the API is open |

The image is multi-stage: a Node 20 stage builds the React app, a Python 3.11 stage installs `requirements.txt`, and the runner copies the built `frontend/dist` next to the API. FastAPI serves the SPA itself at `/app`, so no separate static host is used on Cloud Run. The container listens on `$PORT` (default 8080). The image holds the fictional demo database, not a real one. The deploy workflow does not run tests; `ci.yml` does (pytest, ruff, mypy, the retrieval eval script and a Docker build on Python 3.11).

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

The `frontend/` React app is a Vite build. The `Dockerfile` bundles `frontend/dist` into the API image and FastAPI serves it at `/app`. For local development, `npm run dev` in `frontend/` serves it on port 5173 and proxies `/api` to `http://localhost:8000`. To host it elsewhere, build with `npm run build` and serve `dist/` from a static host; the client calls the API under `/api`, so the host must route that path to FastAPI.
