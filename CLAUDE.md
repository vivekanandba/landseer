# Landseer — contributor & agent guide

Land search and evaluation system for Vellore, Tamil Nadu. Python/FastAPI backend
with a SQLAlchemy data layer and a full BDD (behave) + TDD (pytest) suite.

## Standing workflow convention — always ship through a reviewed PR

**Never commit product changes straight to `main`, and never merge unreviewed code.**
Every change follows the loop documented in [`docs/development/pr-review-loop.md`](docs/development/pr-review-loop.md):

1. Work on a feature branch; open a PR as soon as there's something to show, and keep it raised.
2. Run the **reviewer ↔ dev loop**: review the diff adversarially and post comments, resolve every
   comment in code (suite stays green), then re-review. Repeat until a review pass is clean.
3. Approve and merge (squash + delete branch) only once the suite is green and no finding is open.

The loop is meant to run end-to-end autonomously. See the doc for the exact `gh` commands and the
self-approval caveat.

## Backend commands (run from `backend/`)

The bundled `venv` was created at a different path, so console-script shebangs are stale — always
invoke tools through the interpreter:

- Unit/integration tests: `venv/bin/python -m pytest -q`
- BDD suite: `venv/bin/python -m behave` (one feature: `... -m behave features/<name>.feature`)

Both suites must be green before merge. Current baseline: 5 features / 42 scenarios / 302 steps
(behave) and 42 pytest tests.

## Layout

- `backend/app/models` — SQLAlchemy models (property, broker, document, comparison).
- `backend/app/services` — HTTP-free domain logic; driven by both the API and the BDD steps.
- `backend/app/api` — FastAPI routers.
- `backend/features` — Gherkin features + step definitions (one steps file per feature).
- `backend/tests` — `unit/` (service/model) and `integration/` (API) pytest suites.

## Committing

Branch off `main` first if needed. End commit messages with the co-author + session trailers
already used in this repo's history.
