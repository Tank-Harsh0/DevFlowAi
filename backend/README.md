# DevFlow AI — Backend

Python backend for the DevFlow AI developer workflow automation platform.

---

## Python Version

```
Python 3.12
```

---

## Virtual Environment Setup

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows PowerShell
```

---

## Dependency Installation

```bash
pip install -r requirements.txt
```

---

## Environment Configuration

```bash
cp .env.example .env
# Edit .env as needed
```

Key variables:

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Runtime environment |
| `LOG_LEVEL` | `INFO` | Log verbosity |
| `BACKEND_CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins (comma-separated) |

---

## Start the API

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

---

## API Documentation

FastAPI auto-generates interactive docs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Run Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

---

## Linting

```bash
ruff check .
```

Fix auto-fixable issues:

```bash
ruff check . --fix
```

---

## Type Checking

```bash
mypy app/
```

---

## Current Backend State

**Phase 1 — Foundation** is complete.

Implemented:
- FastAPI application factory (`app/main.py`)
- Pydantic-settings configuration (`app/core/config.py`)
- Structured logging (`app/core/logging.py`)
- CORS middleware for the React frontend
- `GET /health` endpoint
- Global exception handler (no stack traces exposed to clients)
- Smoke tests and health endpoint tests

**Phase 2 and beyond are not yet implemented.**

---

## Known Limitations

- No database. State is in-memory only (will be session JSON files in Phase 2+).
- No authentication. The API is open (acceptable for the local-only MVP).
- Agents are not yet implemented.
