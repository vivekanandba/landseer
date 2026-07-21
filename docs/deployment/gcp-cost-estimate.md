# Landseer on Google Cloud — cost estimate

**Goal:** understand the monthly cost of running Landseer on a personal GCP
project, with a target budget of **under ₹100/month**, before deploying anything.

> **Bottom line (read this first).** ₹100/month is ≈ **US $1.04**. GCP's *Always
> Free* tier can run Landseer's compute, disk and static frontend for **₹0** — but
> a permanently-reachable public app has a hard practical floor set by two charges
> that each, on their own, blow the ₹100 target:
>
> | Budget-killer | ~Cost/month (incl. 18% GST) | Why it applies |
> |---|---|---|
> | **External IPv4 address** (in-use, on a VM) | **~₹420** | A public VM needs a routable IPv4; GCP charges $0.005/hr for it since 2024. |
> | **Cloud SQL** (smallest Postgres) | **~₹1,100** | A *managed* database. Avoidable — Landseer also runs on SQLite. |
>
> **You can stay under ₹100/month only by avoiding both:** run a single
> Always-Free `e2-micro` VM with **SQLite** (no Cloud SQL), and avoid the IPv4
> charge (IPv6-only, or front it with a free tunnel such as Cloudflare Tunnel).
> That lands at **≈ ₹0–50/month**. A "just works over IPv4" deployment is
> **≈ ₹420/month**; a managed, production-shaped one is **≈ ₹1,100–1,700/month**.

---

## Assumptions

| Assumption | Value |
|---|---|
| Currency conversion | **1 USD ≈ ₹96.5** (spot, 21 Jul 2026) |
| India GST | **18%** added to GCP charges for an India billing address (0% only with a valid GSTIN on a Google Asia Pacific contract) |
| Region | `us-central1` (Iowa) — cheapest and one of the three Always-Free regions |
| Network tier | **Standard** (required to stay in the free egress allowance) |
| Scale | Personal / single-operator: a few hundred requests a day, DB well under 1 GB, egress well under 1 GB/month |
| App shape | FastAPI backend serving the static SPA at `/app` (same origin), one small container/process |
| Prices | *Indicative*, list price, as of Jul 2026 — always re-check in the [GCP Pricing Calculator](https://cloud.google.com/products/calculator) for your exact config |

All rupee figures below are **inclusive of 18% GST** unless noted (USD × 96.5 × 1.18).

---

## What Landseer needs

- **Compute** — one small always-on (or scale-to-zero) process for the API.
- **Static frontend** — a handful of small files; served by the API itself
  (`/app`), so no separate hosting cost.
- **Database** — SQLAlchemy. Runs on **SQLite** (a file on disk) *or* PostgreSQL.
  This single choice is the biggest cost lever.
- **Public endpoint** — an HTTPS URL reachable from a browser.
- **Egress** — small (JSON + a small cached SPA bundle).

---

## GCP Always Free tier (the ₹0 building blocks)

These recur every month at no charge (not a trial), within limits:

| Service | Always-Free allowance | Enough for Landseer? |
|---|---|---|
| Compute Engine | 1× **e2-micro** (2 shared vCPU, 1 GB), in `us-west1`/`us-east1`/`us-central1` only; 730 hrs/mo (i.e. 24×7) | ✅ runs the API |
| Persistent Disk | **30 GB Standard** PD (not SSD/Balanced) | ✅ OS + SQLite DB + app |
| Network egress | **1 GB/mo** from North America (excludes China & Australia) | ✅ at personal scale |
| Cloud Storage | 5 GB-months (US regional) | ✅ backups if wanted |
| Cloud Run | 2M requests, 180k vCPU-s, 360k GiB-s /mo; free `*.run.app` HTTPS URL | ✅ compute, ⚠️ no durable DB |
| Artifact Registry | 0.5 GB storage | ✅ one small image |

**Not free / watch out:** external **IPv4** address, Cloud SQL, SSD/Balanced
disks, Premium network tier, snapshots (~$0.026/GB-mo), egress above 1 GB
(~$0.12/GB ≈ ₹14/GB incl. GST), egress to China/Australia.

---

## Option A — Always-Free `e2-micro` + SQLite  ★ recommended for this budget

Run Landseer on one free `e2-micro`, database on a SQLite file on the free 30 GB
disk, SPA served by the app. Standard network tier.

| Line item | USD/mo | ₹/mo (incl. GST) |
|---|---:|---:|
| e2-micro compute (Always Free) | 0.00 | **0** |
| 30 GB Standard persistent disk (Always Free) | 0.00 | **0** |
| SQLite database (a file — no service) | 0.00 | **0** |
| Egress ≤ 1 GB (Always Free) | 0.00 | **0** |
| **Subtotal (compute+storage+DB)** | **0.00** | **0** |
| External **IPv4** address (if used) | 3.66 | **~416** |
| **Total, IPv6-only / tunnelled** | **~0** | **≈ 0–50** |
| **Total, with public IPv4** | **~3.7** | **≈ 420** |

**To actually stay under ₹100** you must avoid the IPv4 charge:
- **IPv6-only** external address (currently not billed like IPv4) — simplest on
  GCP, but only reachable by IPv6-capable clients. *Verify the IPv6 charge before
  relying on it.*
- **Free tunnel** (e.g. Cloudflare Tunnel, off-GCP): the VM keeps no public IP;
  the tunnel gives a free HTTPS hostname. Keeps you fully in the free tier.
- Or run the VM **only when needed** (stop it when idle) so the IPv4 accrues few
  hours.

**Trade-offs:** single instance (no HA); you patch/secure the VM yourself;
SQLite is single-writer (fine for one operator). This is the honest sub-₹100 path.

---

## Option B — Cloud Run (free URL) + a database

Cloud Run gives a **free HTTPS URL** and, at personal scale, **₹0** compute (well
under the 2M-request / 180k-vCPU-s free tier) — and **no IPv4 charge**. The catch
is persistence:

| DB choice | ₹/mo (incl. GST) | Notes |
|---|---:|---|
| SQLite in the container | — | ❌ not durable: lost on redeploy/scale, not shared across instances |
| **Cloud SQL** (db-f1-micro + 10 GB) | **~1,100** | ✅ managed Postgres, but ~11× the budget |
| Firestore (free tier) | ~0 | ✅ free, but ❌ requires rewriting Landseer's SQLAlchemy data layer |

**Verdict:** Cloud Run compute is effectively free, but there is **no durable
GCP-managed SQL database that fits ₹100/month**. Great option *once* you can
spend ~₹1,100/mo for Cloud SQL, or if you invest in a Firestore rewrite.

---

## Option C — Managed / production-shaped (for later)

Cloud Run (or a bigger VM) + Cloud SQL + a few extras, when Landseer is "real":

| Line item | ₹/mo (incl. GST) |
|---|---:|
| Cloud Run (light real traffic) | ~0–200 |
| Cloud SQL db-f1-micro + 10 GB, no HA | ~1,100 |
| External IPv4 (if VM instead of Cloud Run) | ~416 |
| Egress, snapshots, Artifact Registry | ~100–300 |
| **Typical total** | **≈ 1,100–1,700** |
| + High Availability (Cloud SQL) | roughly **2×** the DB cost |

---

## Recommendation

For **< ₹100/month today**: **Option A** — one Always-Free `e2-micro` in
`us-central1`, Landseer on **SQLite**, SPA served by the app, **Standard**
network tier, and **no billed IPv4** (IPv6-only or a free tunnel). Expected bill:
**≈ ₹0**, with only accidental overages (egress > 1 GB, a snapshot, an SSD disk)
to guard against.

Move to **Option C** (Cloud Run + Cloud SQL) when the app has real users and a
~₹1,100+/month budget — that's where managed backups, HA and painless scaling
start to matter.

---

## Constraining the cost (do this before deploying)

GCP **budgets alert but do not hard-stop spending** — plan accordingly:

1. **Set a Cloud Billing budget.** Billing → Budgets & alerts → create a budget
   of e.g. **₹100/mo** (or ₹500 for headroom) with email alerts at **50 / 90 /
   100 %** of budget. (Free.)
2. **Hard cap (optional but recommended for a personal card):** wire the budget's
   Pub/Sub topic to a Cloud Function that **disables billing** on the project when
   spend crosses the cap — the only way to *actually* stop charges. See
   [Cloud: disable billing to stop usage](https://cloud.google.com/billing/docs/how-to/notify#cap_disable_billing_to_stop_usage).
3. **Stay inside Always Free by construction:** `e2-micro` only, **Standard** PD
   (not SSD/Balanced), **Standard** network tier, one of the 3 free US regions,
   no external IPv4, no Cloud SQL, egress < 1 GB.
4. **Quota guardrails:** cap Compute Engine CPU quota low so nothing can scale up
   accidentally.
5. **Watch the classic surprises:** in-use IPv4, egress to China/Australia,
   snapshots, load balancers, NAT gateways, and leaving SSD disks around.

---

## Sources

- [Google Cloud Free Tier — features & limits (overview)](https://aatayyab.wordpress.com/2026/06/26/google-cloud-free-tier-services-and-limits/) and [Compute getting started](https://cloud.google.com/free/docs/compute-getting-started)
- [Cloud Run pricing](https://cloud.google.com/run/pricing)
- [Cloud SQL pricing 2026 (indicative)](https://www.usage.ai/blogs/gcp/cloud-sql/pricing/) · [Bytebase Cloud SQL pricing](https://www.bytebase.com/dbcost/cloudsql-pricing/)
- [No more free external IPs on Google Cloud — cost](https://www.doit.com/blog/no-more-free-external-ips-on-google-cloud-how-much-will-it-cost-you)
- [VPC / network egress pricing](https://cloud.google.com/vpc/network-pricing) · [Disk & image pricing](https://cloud.google.com/compute/disks-image-pricing)
- [Taxes in your country (India GST) — Cloud Billing](https://docs.cloud.google.com/billing/docs/resources/vat-overview)
- FX: USD→INR spot, 21 Jul 2026 (~₹96.36) — [exchangerates.org.uk](https://www.exchangerates.org.uk/USD-INR-spot-exchange-rates-history-2026.html)
- [GCP Pricing Calculator](https://cloud.google.com/products/calculator) — verify your exact configuration

*Figures are indicative list prices as of July 2026 and exclude sustained-use/committed-use
discounts and any promotional credits. Re-verify in the Pricing Calculator before committing spend.*
