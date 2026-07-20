# Landseer frontend

A dependency-free single-page app for the Landseer API — property search,
recommendations, side-by-side comparison, brokers, and a dashboard.

## Why vanilla (for now)

The README's target stack is Next.js/React/TypeScript. This first cut is
intentionally **build-free** (plain HTML + CSS + ES-module JavaScript, no
`npm install`) so it runs anywhere the API runs, with zero toolchain — which is
what the current environment supports. Migrating to the documented Next.js +
TypeScript + shadcn stack is a follow-up for an environment with registry
access; the API client (`js/api.js`) and view structure map cleanly onto it.

## Running

The backend serves this directory at **`/app`** when it's present (see
`backend/app/main.py`), so the simplest path is to run the API and open the UI
same-origin (no CORS, shares the API token):

```bash
# from backend/
LANDSEER_DEBUG=true \
LANDSEER_DATABASE_URL=sqlite+pysqlite:///./landseer_demo.db \
  venv/bin/python -m uvicorn app.main:app --reload
# then open http://localhost:8000/app/  (root / redirects here)
```

Seed demo data first with `venv/bin/python scripts/seed_demo.py` so there are
properties and a "My Ideal Plot" preference to explore.

To point the UI at a **different** API host, or to supply a **bearer token**
(when `LANDSEER_API_TOKEN` is set), use the in-app **⚙ Settings** dialog — both
are stored in `localStorage`.

## Layout

- `index.html` — app shell (sidebar nav, topbar, view container).
- `styles.css` — design tokens (light/dark) + components; status/feature colors
  come from the validated data-viz palette.
- `js/api.js` — fetch client, base-URL/token config, error normalization.
- `js/ui.js` — DOM builder (`h`), formatters (₹/sqft), shared widgets
  (badges, match-score meter, tables).
- `js/app.js` — hash router + views: Dashboard, Properties (list + detail with a
  GeoJSON boundary map), Recommendations, Compare, Brokers.

## Screens

| Route | What |
|-------|------|
| `#/` | KPI tiles, alerts (expiries / price moves / follow-ups), recent activity |
| `#/properties` | Filterable list (location, price); click through to detail |
| `#/properties/:id` | Facts, features, subdivisions, neighbors, documents, boundary SVG |
| `#/recommendations` | Properties scored vs a preference, with deal-breaker reasons |
| `#/compare` | Pick plots → typed table + colored features + investment view |
| `#/brokers` | Contacts with shown/conversion performance |
