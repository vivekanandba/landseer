# Running Landseer locally

The backend runs against any SQLAlchemy URL. For a zero-setup local run, use a
SQLite file. All commands are run from `backend/` and invoke the interpreter
directly (the bundled `venv` has stale console-script shebangs).

## 1. See Smart Matching results immediately (no server)

```bash
venv/bin/python scripts/seed_demo.py
```

This seeds a local `./landseer_demo.db` with a handful of Vellore properties and
a sample preference, then prints the ranked recommendations (with deal-breaker
reasons for anything disqualified).

## 2. Explore the whole API interactively

Start the server against the **same** database, with `DEBUG` on so tables are
created automatically:

```bash
LANDSEER_DEBUG=true \
LANDSEER_DATABASE_URL=sqlite+pysqlite:///./landseer_demo.db \
  venv/bin/python -m uvicorn app.main:app --reload
```

Then open the interactive docs: **http://localhost:8000/docs**

Useful endpoints:
- `POST /api/v1/properties` — add a property.
- `POST /api/v1/preferences` — define requirements (budget, size, locations, required features, weight overrides).
- `GET  /api/v1/preferences/{name}/recommendations` — ranked matches with scores + deal-breaker reasons (`?include_disqualified=false` to hide fails).
- `GET  /health` — liveness.

Seed the demo data first (step 1) so the recommendations endpoint has something
to rank, or create properties via `POST /api/v1/properties`.

## Database migrations (Alembic)

`DEBUG=true` auto-creates tables for local convenience. For a real (Postgres)
database, bootstrap and evolve the schema with Alembic instead — run from `backend/`:

```bash
LANDSEER_DATABASE_URL=postgresql+psycopg2://user:pass@localhost/landseer \
  venv/bin/python -m alembic upgrade head
```

- Generate a new migration after changing models:
  `venv/bin/python -m alembic revision --autogenerate -m "describe change"`.
- The test suite does **not** use Alembic — it builds the schema via `create_all`
  on in-memory SQLite (so migrations are a Postgres/production concern only).

## Authentication

The `/api/v1` surface is gated by a static bearer token. It is **open by default**
(no token) for local/dev/test convenience; set `LANDSEER_API_TOKEN` to require it:

```bash
LANDSEER_API_TOKEN=some-long-random-string ... uvicorn app.main:app
# then: curl -H "Authorization: Bearer some-long-random-string" .../api/v1/properties
```

`/health`, `/ready`, and `/docs` are always open. Any non-local deployment should
set the token (the app logs a warning at startup when it is unset). To fail
*closed* — refuse to boot if the token is missing — also set
`LANDSEER_AUTH_REQUIRED=true` in that environment.

## Notes

- Env vars use the `LANDSEER_` prefix (see `app/config.py`).
