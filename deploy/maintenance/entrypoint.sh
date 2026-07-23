#!/usr/bin/env bash
#
# Combined maintenance entrypoint for landseer — merges the former
# landseer-migrate (Alembic) and landseer-backup (pg_dump -> GCS) jobs.
#
#   migrate  -> alembic upgrade head      (needs LANDSEER_DATABASE_URL)
#   backup   -> pg_dump -> gs://$BACKUP_BUCKET/backups/   (needs DATABASE_URL)
#   all      -> migrate then backup       (default; weekly scheduler)
set -euo pipefail

CMD="${1:-all}"

run_migrate() {
  echo "[maint] migrate (alembic upgrade head)"
  cd /app/backend
  alembic upgrade head
  echo "[maint] migrate done"
}

run_backup() {
  : "${DATABASE_URL:?DATABASE_URL is required for backup}"
  : "${BACKUP_BUCKET:?BACKUP_BUCKET is required for backup}"
  local prefix bucket stamp file local_path db
  prefix="${BACKUP_PREFIX:-backups}"
  bucket="${BACKUP_BUCKET#gs://}"
  stamp="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
  file="landseer-${stamp}.dump"
  local_path="/tmp/${file}"
  # Trim whitespace and strip any SQLAlchemy "+driver" so libpq accepts the URL.
  db="$(printf '%s' "${DATABASE_URL}" | tr -d '[:space:]' | sed -E 's#^postgresql\+[a-z0-9]+://#postgresql://#')"
  echo "[maint] backup -> gs://${bucket}/${prefix}/${file}"
  pg_dump "${db}" --format=custom --no-owner --no-privileges --file="${local_path}"
  python /usr/local/bin/upload.py "${bucket}" "${local_path}" "${prefix}/${file}"
  rm -f "${local_path}"
  echo "[maint] backup done"
}

case "$CMD" in
  migrate) run_migrate ;;
  backup)  run_backup ;;
  all)     run_migrate; run_backup ;;
  *) echo "usage: entrypoint.sh [migrate|backup|all]"; exit 2 ;;
esac
