# Landseer — gap analysis (spec vs. built)

Reference: the original `README.md` (features, tech stack, testing goals, Phase 1–5
roadmap) plus this engagement's asks (backend hardening, deploy to GCP under a tight
budget). Status as of 2026-07-22.

> The README roadmap checkboxes are **stale** — nearly all of Phases 1–5 is built.
> This is the accurate picture.

## 1. Product features

| Area (README) | Status | Notes |
|---|---|---|
| Property management (subdivisions, neighbors, activity, notes) | ✅ Done | |
| Broker management + performance metrics | ✅ Done | |
| Document vault + verification + expiry | ✅ Done | |
| OCR extraction | ⚠️ Interface only | Simulated provider works; **real Tesseract/Vision gated** (binary/API key) |
| Survey visualization + KML + GeoJSON map | ✅ Done | Map renders in the SPA |
| Google My Maps auto-upload | ❌ Gated | Stub; needs Google OAuth |
| Smart matching (scoring, deal-breakers, recommendations) | ✅ Done | |
| Comparison (table/features/investment) + PDF export | ✅ Done | |
| Automation: expiry reminders, price alerts, follow-ups | ✅ Done | Pull-based; `LogNotifier` |
| OneDrive import | ⚠️ Partial | `VirtualFileSource` for tests; **real OneDrive gated** (MS Graph creds) |
| Email/SMTP delivery of notifications | ❌ Gated | Needs SMTP creds |

## 2. Beyond the spec (added this engagement)

Bearer-token **auth**, **rate limiting**, **structured logging + request IDs + error
envelope**, **data-integrity constraints/indexes**, **connection pooling**, **typed
response models**, **Alembic migrations**, **CI**, and a full **GCP deployment**
(Cloud Run + Neon + daily GCS backups + budget) — none of which were in the README.

## 3. Deliberate deviations from the README stack

| README said | We built | Why |
|---|---|---|
| React / Next.js / TS / Tailwind / shadcn | Dependency-free vanilla SPA | Offline sandbox can't install a JS toolchain; ports cleanly later |
| PostgreSQL + **PostGIS** | Postgres (Neon), lat/lng floats | Portability + SQLite test parity; PostGIS unused |
| Celery + Redis | Synchronous/pull-based notifications | No async workload at this scale |
| Jest + Cypress | `node:test` unit tests; no E2E | Toolchain constraint |
| Nginx | Cloud Run serves the SPA (same-origin) | Free HTTPS, one deployable |

## 4. Deferred — credential/infra-gated (cannot finish without inputs)

Real OCR (Tesseract/Vision), OneDrive import (MS Graph), Google My Maps (OAuth),
SMTP email. Each has its interface/seam built; only the credential + wiring remain.

## 5. Not yet done — completable now (the actual backlog)

| Item | Priority | Notes |
|---|---|---|
| **CI/CD (CD) pipeline + versioning** | **P0 (this task)** | Model on `resumefit`: keyless WIF, version SoT, tag-driven releases, auto-deploy on merge |
| Surface app **version** (`APP_VERSION`) in `/health` | P0 | Comes with versioning |
| Custom domain on Cloud Run | P1 | Optional; currently `*.run.app` |
| Frontend **Next.js/TS port** | P1 | Needs a networked env (npm registry) |
| E2E tests (Playwright/Cypress) | P2 | Needs JS toolchain |
| `DELETE` endpoints (e.g. property) + UI actions | P2 | Noticed none exist |
| Restore drill automation / backup monitoring | P2 | Backup runs; restore is documented, not automated |

## 6. Open — your observations

You mentioned "a lot of changes" now that you can see it running. Those are almost
certainly **UI/UX and product changes** I can't infer from the spec. Add them here (or
tell me) and I'll fold them into this backlog and sequence them:

- _(to be filled in — e.g. layout, fields, workflows, naming, mobile, etc.)_
