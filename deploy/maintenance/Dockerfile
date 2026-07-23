# Combined maintenance image for landseer: Alembic migrations + pg_dump backup.
# Base matches the app image (python:3.12-slim) so backend/requirements.txt
# installs identically; add the Postgres 17 client for pg_dump and the GCS
# client library for uploads (no gcloud needed). Build context = repo root.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

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

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install -r /app/backend/requirements.txt google-cloud-storage

COPY backend /app/backend
COPY deploy/maintenance/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY deploy/maintenance/upload.py /usr/local/bin/upload.py
RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /app/backend
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["all"]
