# Deployment

GoalOS is designed for a trusted single user. SQLite and ChromaDB require durable writable storage.

## Local Docker

```powershell
docker compose up --build
```

Persist `goalos.db` and `chroma_db` on a private volume. Keep `.env`, backups, and exports outside source control.

## FastAPI

For any non-local API deployment, set:

```text
ENVIRONMENT=production
GOALOS_API_TOKEN=<long-random-secret>
```

Every protected endpoint requires `Authorization: Bearer <GOALOS_API_TOKEN>`. Keep the API behind a trusted network or platform access control; it does not provide multi-user authentication.

## Frontend

The `frontend/` React app is a separate static build (Vite) that talks to the FastAPI API. Build with `npm run build` in `frontend/` and serve the resulting `dist/` from any static host, pointed at the API's URL.
