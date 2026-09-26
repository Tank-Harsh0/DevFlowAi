# DevFlow AI — Docker Development Guide

Version: 2.0

---

## Architecture

```
Browser
   │
   │  HTTP / WebSocket
   ▼
Frontend container          http://localhost:5173
(Vite dev server)
   │
   │  HTTP / WebSocket (via VITE_API_BASE_URL)
   ▼
Backend container           http://localhost:8000
(FastAPI / uvicorn)
```

**MongoDB is NOT containerised.** The FastAPI backend does not yet have a
database integration layer (Phase 6+). When MongoDB integration is added in a
future phase, the backend will connect to an external MongoDB Atlas cluster
using the `MONGODB_URI` environment variable — no local MongoDB container
will ever be required.

---

## Requirements

| Tool | Notes |
|---|---|
| Docker Desktop | Includes Docker Engine and Compose V2 |

Node.js and Python do not need to be installed on the host machine to run
the project with Docker.

---

## Environment Setup

Copy the root example file to create your local environment:

```powershell
Copy-Item .env.example .env
```

Or on Linux / macOS:

```bash
cp .env.example .env
```

The defaults in `.env.example` work out-of-the-box for local Docker development:

```env
APP_ENV=development
LOG_LEVEL=INFO
BACKEND_CORS_ORIGINS=http://localhost:5173
VITE_API_BASE_URL=http://localhost:8000
```

Never commit `.env` to version control. It is git-ignored by default.

---

## Start

```bash
docker compose up --build
```

Both containers start in this order:
1. `backend` — FastAPI / uvicorn on port 8000.
2. `frontend` — Vite dev server on port 5173 (depends on backend being started).

Once running:

| Service | URL |
|---|---|
| Frontend (Vite) | http://localhost:5173 |
| Backend (FastAPI) | http://localhost:8000 |
| Backend API docs | http://localhost:8000/docs |
| Backend health | http://localhost:8000/health |

---

## Stop

```bash
docker compose down
```

---

## Logs

Tail all service logs:

```bash
docker compose logs -f
```

Tail a specific service:

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

Check container status:

```bash
docker compose ps
```

---

## Rebuild

After changing `requirements.txt`, `package.json`, or either `Dockerfile`,
rebuild from scratch:

```bash
docker compose down
docker compose build --no-cache
docker compose up
```

Rebuild a single service without stopping the other:

```bash
docker compose build --no-cache backend
docker compose up -d --no-deps backend
```

---

## Hot Reload

Both services support hot reload in development mode.

### Frontend — Vite HMR

`frontend/` is mounted as a volume. Saving any file in `frontend/src/`
triggers Vite's Hot Module Replacement immediately — no restart needed.

### Backend — uvicorn `--reload`

`backend/` is mounted as a volume. Saving any `.py` file triggers uvicorn's
reloader and the FastAPI process restarts automatically.

> **Note:** If you add a new npm package or Python dependency, the Docker image
> must be rebuilt to install it:
> ```bash
> docker compose build --no-cache frontend  # or backend
> ```

---

## WebSocket

The backend supports WebSocket natively via uvicorn. No proxy is required.

The frontend derives the WebSocket URL automatically:

```
VITE_API_BASE_URL=http://localhost:8000
→ WebSocket URL = ws://localhost:8000
→ WS endpoint = ws://localhost:8000/api/v1/ws/workflows/{id}
```

To override, set `VITE_WS_URL` in your `.env` file.

---

## CORS

The backend allows `http://localhost:5173` by default (controlled by
`BACKEND_CORS_ORIGINS`). To add more origins:

```env
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:4173
```

---

## Ports

| Service | Container port | Host port |
|---|---|---|
| Frontend | 5173 | 5173 |
| Backend | 8000 | 8000 |

---

## Database (Future — MongoDB Atlas)

The backend does **not** currently connect to any database.

When Phase 6 MongoDB integration is implemented:

- The backend will use **MongoDB Atlas** (cloud-hosted, external).
- No MongoDB container will be added to `docker-compose.yml`.
- Add the connection string to `.env`:

  ```env
  MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/devflowai
  ```

- Uncomment the `MONGODB_URI` line in `docker-compose.yml`.

---

## Troubleshooting

### Frontend cannot reach backend

- Confirm `VITE_API_BASE_URL=http://localhost:8000` (not the service name).
  The browser resolves this URL, not Docker.
- Check backend logs: `docker compose logs -f backend`
- Confirm `http://localhost:5173` is in `BACKEND_CORS_ORIGINS`.

### Port already in use

Change the host port in `docker-compose.yml`:

```yaml
ports:
  - "5174:5173"   # map host 5174 → container 5173
```

Then update `VITE_API_BASE_URL` and `BACKEND_CORS_ORIGINS` to match.

### Image not updating after adding a dependency

Rebuild the affected image:

```bash
docker compose build --no-cache <service>
```

---

## Security

- `.env` is git-ignored and must never be committed.
- `VITE_API_BASE_URL` and `VITE_WS_URL` are public variables (visible in the
  browser bundle). They must never contain secrets.
- `MONGODB_URI`, `GOOGLE_API_KEY`, and any AI provider tokens are backend-only.
  They must never be prefixed with `VITE_`.
