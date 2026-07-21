# Landseer — FastAPI API + bundled SPA, container image for Cloud Run.
#
# Build context is the REPO ROOT so that backend/ and frontend/ are copied as
# siblings (the SPA static mount in app/main.py resolves ../../frontend).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first, for layer caching.
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Application code + the static SPA (kept as siblings — see note above).
COPY backend /app/backend
COPY frontend /app/frontend

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

WORKDIR /app/backend
# Cloud Run injects $PORT (default 8080). Shell form so the variable expands.
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
