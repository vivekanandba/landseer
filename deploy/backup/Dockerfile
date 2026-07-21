# Backup runner: PostgreSQL 17 client (pg_dump) + gcloud (for GCS upload).
# Built by Cloud Build at deploy time; run as a Cloud Run Job on a schedule.
# Build context is the REPO ROOT (to COPY deploy/backup/backup.sh).
FROM google/cloud-sdk:slim

# PostgreSQL client 17 (must be >= the Neon server version) via the PGDG apt repo.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates gnupg lsb-release \
 && install -d /usr/share/keyrings \
 && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
      | gpg --dearmor -o /usr/share/keyrings/pgdg.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/pgdg.gpg] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
      > /etc/apt/sources.list.d/pgdg.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends postgresql-client-17 \
 && rm -rf /var/lib/apt/lists/*

COPY deploy/backup/backup.sh /usr/local/bin/backup.sh
RUN chmod +x /usr/local/bin/backup.sh

ENTRYPOINT ["/usr/local/bin/backup.sh"]
