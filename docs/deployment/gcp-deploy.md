# Deploying Landseer to GCP (Cloud Run + Neon) with GCS backups

End-to-end runbook for the architecture in
[`gcp-cost-estimate.md`](gcp-cost-estimate.md): one Cloud Run service (API + SPA)
backed by Neon Postgres, with a daily `pg_dump` to a GCS bucket in your project.
Target cost ≈ ₹0/month (all within free tiers).

> **Secrets never go in this repo or in chat.** The Neon connection string and the
> API token live only in **Secret Manager** and are injected into Cloud Run by
> *name*. Commands below read secret values from stdin so they don't land in shell
> history. Run everything in **Cloud Shell** (already authenticated; nothing to
> install).

Set these once per shell:

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"          # a Cloud Run region close to your Neon region
export REPO="landseer"               # Artifact Registry repo
export SERVICE="landseer"            # Cloud Run service name
export BUCKET="${PROJECT_ID}-landseer-backups"
gcloud config set project "$PROJECT_ID"
```

---

## 0. Neon (in the Neon console — no API key needed here)

1. If you exposed an API key earlier, **revoke it** (Account → API keys).
2. Create a project; pick a region near `$REGION`.
3. Open the branch → **Connection string** → copy the **Pooled** URI in **libpq
   form** (`postgresql://USER:PASSWORD@...-pooler.REGION.aws.neon.tech/DBNAME?sslmode=require`
   — i.e. `postgresql://`, *not* `postgresql+psycopg2://`). This one form works
   for both SQLAlchemy (it defaults to psycopg2) and `pg_dump`. You'll paste it
   into Secret Manager in step 2 — nowhere else.

## 1. Enable APIs

```bash
gcloud services enable \
  run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com \
  secretmanager.googleapis.com storage.googleapis.com \
  cloudscheduler.googleapis.com
```

## 2. Create secrets (values from stdin — not from argv)

```bash
# Neon pooled connection string — paste it, then press Ctrl-D:
gcloud secrets create landseer-db-url --replication-policy=automatic --data-file=-

# A strong random API token for the app's bearer auth:
openssl rand -base64 32 | tr -d '\n' | gcloud secrets create landseer-api-token --data-file=-
```

## 3. Artifact Registry

```bash
gcloud artifacts repositories create "$REPO" \
  --repository-format=docker --location="$REGION"
```

## 4. Build & deploy the app (Cloud Run)

The service SA needs to read the secrets:

```bash
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
for S in landseer-db-url landseer-api-token; do
  gcloud secrets add-iam-policy-binding "$S" \
    --member="serviceAccount:${RUNTIME_SA}" --role=roles/secretmanager.secretAccessor
done

gcloud run deploy "$SERVICE" \
  --source . \
  --region="$REGION" \
  --allow-unauthenticated \
  --min-instances=0 --max-instances=2 \
  --cpu=1 --memory=512Mi \
  --set-secrets="LANDSEER_DATABASE_URL=landseer-db-url:latest,LANDSEER_API_TOKEN=landseer-api-token:latest" \
  --set-env-vars="LANDSEER_AUTH_REQUIRED=true,LANDSEER_DB_POOL_SIZE=2,LANDSEER_DB_MAX_OVERFLOW=2"
```

Notes:
- `--allow-unauthenticated` lets browsers reach it; **the app enforces its own
  bearer token** (`LANDSEER_AUTH_REQUIRED=true`), so the API stays locked.
- **Do not** set `LANDSEER_DEBUG` — production uses Alembic migrations (step 5),
  not `create_all`.
- Small SQLAlchemy pool because Neon's pooler multiplexes connections.

## 5. Run database migrations (one-off Cloud Run Job on the same image)

```bash
IMAGE="$(gcloud run services describe "$SERVICE" --region="$REGION" --format='value(spec.template.spec.containers[0].image)')"

gcloud run jobs create landseer-migrate \
  --image="$IMAGE" --region="$REGION" \
  --set-secrets="LANDSEER_DATABASE_URL=landseer-db-url:latest" \
  --command="alembic" --args="upgrade,head"
gcloud run jobs execute landseer-migrate --region="$REGION" --wait
```

## 6. Verify

```bash
URL="$(gcloud run services describe "$SERVICE" --region="$REGION" --format='value(status.url)')"
curl -s "$URL/health"        # {"status":"ok",...}
curl -s "$URL/ready"         # {"status":"ready"}  == Cloud Run reached Neon
curl -s -o /dev/null -w '%{http_code}\n' "$URL/api/v1/properties"   # 401 (auth on)
```

Open **`$URL/app/`**, go to **⚙ Settings**, paste the API token (read it with
`gcloud secrets versions access latest --secret=landseer-api-token`), and create a
property.

## 7. Backups → GCS

```bash
# Bucket + 30-day lifecycle
gcloud storage buckets create "gs://${BUCKET}" --location="$REGION" --uniform-bucket-level-access
printf '{"rule":[{"action":{"type":"Delete"},"condition":{"age":30}}]}' > /tmp/lifecycle.json
gcloud storage buckets update "gs://${BUCKET}" --lifecycle-file=/tmp/lifecycle.json

# Build the backup image (context = repo root; Dockerfile at deploy/backup).
# _IMG is expanded by the shell here, then passed to Cloud Build as a substitution.
gcloud builds submit . --config=deploy/backup/cloudbuild.yaml \
  --substitutions=_IMG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/backup:latest"

# Backup job SA: read the DB secret + write to the bucket
gcloud secrets add-iam-policy-binding landseer-db-url \
  --member="serviceAccount:${RUNTIME_SA}" --role=roles/secretmanager.secretAccessor
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member="serviceAccount:${RUNTIME_SA}" --role=roles/storage.objectAdmin

gcloud run jobs create landseer-backup \
  --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/backup:latest" \
  --region="$REGION" \
  --set-secrets="DATABASE_URL=landseer-db-url:latest" \
  --set-env-vars="BACKUP_BUCKET=${BUCKET}"

# Test it once, then confirm the object exists
gcloud run jobs execute landseer-backup --region="$REGION" --wait
gcloud storage ls "gs://${BUCKET}/backups/"
```

Schedule daily (02:00 UTC), invoking the job via its Admin API. The scheduler's
service account needs permission to run the job:

```bash
gcloud run jobs add-iam-policy-binding landseer-backup --region="$REGION" \
  --member="serviceAccount:${RUNTIME_SA}" --role=roles/run.invoker

gcloud scheduler jobs create http landseer-backup-daily \
  --location="$REGION" --schedule="0 2 * * *" \
  --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/landseer-backup:run" \
  --http-method=POST \
  --oauth-service-account-email="$RUNTIME_SA"
```

## 8. Restore drill (do this once — an untested backup isn't a backup)

```bash
# Into any fresh Postgres (here, a throwaway local one):
docker run -d --name pgtest -e POSTGRES_PASSWORD=x -p 5433:5432 postgres:17
gcloud storage cp "gs://${BUCKET}/backups/$(gcloud storage ls gs://${BUCKET}/backups/ | tail -1 | xargs basename)" /tmp/latest.dump
pg_restore --clean --if-exists --no-owner -d "postgresql://postgres:x@localhost:5433/postgres" /tmp/latest.dump
# Recovery in real life = provision Postgres anywhere -> pg_restore -> point
# LANDSEER_DATABASE_URL at it -> redeploy. Alembic can also build a fresh schema
# from scratch: `alembic upgrade head`.
```

## 9. Budget guardrail

Billing → **Budgets & alerts** → create a budget (e.g. ₹100 or ₹500 headroom)
with email alerts at **50 / 90 / 100 %**. GCP budgets *alert* but don't hard-stop;
for a hard cap wire the budget's Pub/Sub topic to a Cloud Function that
[disables billing](https://cloud.google.com/billing/docs/how-to/notify#cap_disable_billing_to_stop_usage).

---

## Redeploys

- **App code:** `gcloud run deploy $SERVICE --source . --region=$REGION` (secrets/env persist).
- **Schema change:** ship the Alembic migration, then re-run the migrate job (step 5).
- **Rotate the API token:** add a new secret version, then redeploy (picks up `:latest`).

## Free-tier watch-list

Scale-to-zero (`--min-instances=0`), Standard networking, ≤ 3 Scheduler jobs,
bucket < 5 GB, one small Artifact Registry repo, egress low. The classic
surprises (external IPv4, Cloud SQL, snapshots) don't apply to this design.
