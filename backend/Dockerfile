# =============================================================================
# Backend — FastAPI / Python 3.12
#
# Single-stage image suitable for both local development (with volume mounts)
# and production-style deployments.
#
# Entry point: app.main:app
# Server:      uvicorn on 0.0.0.0:8000
# =============================================================================
FROM python:3.12-slim

# Keep Python output unbuffered so logs appear in real time in Docker.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# ── System dependencies ───────────────────────────────────────────────────────
# curl  — used by the Docker health check (see docker-compose.yml).
# git   — required by GitPython to clone remote repositories.
# gcc + libffi-dev — needed if any transitive dependency compiles C extensions.
# Clean up apt cache in the same layer to keep the image lean.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        git \
        gcc \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ───────────────────────────────────────────────────────
# Copy only the requirements file first so Docker can cache this layer.
# The full source is copied afterwards — dependency cache is only invalidated
# when requirements.txt changes, not on every code edit.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
COPY . .

# ── Runtime ───────────────────────────────────────────────────────────────────
EXPOSE 8000

# Use uvicorn with --reload when the source directory is volume-mounted for
# local development. The reload flag is harmless in production (no watcher
# overhead when no files change), but the recommended approach for production
# is to remove --reload and run with multiple workers via gunicorn+uvicorn.
#
# --host 0.0.0.0    — required so the server accepts connections from other
#                     containers (frontend) and the host machine.
# --reload-dir app  — only watch the application source directory, not cloned
#                     repos written into /app/repos/ during workflow runs.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "app"]
