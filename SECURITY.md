# Security and privacy

GoalOS is a single-user, local-first application. Never commit journals, exports, SQLite databases, Chroma data, `.env` files, or API tokens.

- Remote AI is disabled until the user explicitly grants consent in Settings.
- Set `GOALOS_API_TOKEN` before exposing FastAPI outside a trusted local environment. `ENVIRONMENT=production` refuses to start without it.
- Use the JSON export and automatic local backup before moving or resetting data.
- Report vulnerabilities privately to the repository owner; do not include personal journal content in reports.
- The public Cloud Run demo runs with `ENVIRONMENT=demo` and no `GOALOS_API_TOKEN`, so its API is unauthenticated. It serves only the fictional demo dataset (see `DEPLOY.md`); never load real data into a deployment without setting `ENVIRONMENT=production` and a token.
