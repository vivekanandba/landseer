#!/usr/bin/env bash
# Dump the Neon Postgres database and upload it to a GCS bucket.
# Runs as a Cloud Run Job (triggered daily by Cloud Scheduler).
#
# Required environment:
#   DATABASE_URL   Neon (pooled) connection string — injected from Secret Manager.
#   BACKUP_BUCKET  Target bucket, as "my-bucket" or "gs://my-bucket".
# Optional:
#   BACKUP_PREFIX  Object path prefix (default "backups").
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_BUCKET:?BACKUP_BUCKET is required}"
PREFIX="${BACKUP_PREFIX:-backups}"
BUCKET="${BACKUP_BUCKET#gs://}"

STAMP="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
FILE="landseer-${STAMP}.dump"
LOCAL="/tmp/${FILE}"

echo "[backup] pg_dump -> ${LOCAL}"
# Custom format (-Fc): compressed and restorable with pg_restore into any Postgres.
pg_dump "${DATABASE_URL}" --format=custom --no-owner --no-privileges --file="${LOCAL}"

echo "[backup] upload -> gs://${BUCKET}/${PREFIX}/${FILE}"
gcloud storage cp "${LOCAL}" "gs://${BUCKET}/${PREFIX}/${FILE}"

echo "[backup] done: gs://${BUCKET}/${PREFIX}/${FILE}"
