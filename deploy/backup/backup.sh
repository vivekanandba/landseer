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

# pg_dump speaks libpq, not SQLAlchemy: strip a "+driver" (e.g. postgresql+psycopg2://)
# down to postgresql:// so the same secret works whether it's stored in libpq or
# SQLAlchemy form.
DB_LIBPQ="$(printf '%s' "${DATABASE_URL}" | sed -E 's#^postgresql\+[a-z0-9]+://#postgresql://#')"

echo "[backup] pg_dump -> ${LOCAL}"
# Custom format (-Fc): compressed and restorable with pg_restore into any Postgres.
pg_dump "${DB_LIBPQ}" --format=custom --no-owner --no-privileges --file="${LOCAL}"

echo "[backup] upload -> gs://${BUCKET}/${PREFIX}/${FILE}"
gcloud storage cp "${LOCAL}" "gs://${BUCKET}/${PREFIX}/${FILE}"

echo "[backup] done: gs://${BUCKET}/${PREFIX}/${FILE}"
