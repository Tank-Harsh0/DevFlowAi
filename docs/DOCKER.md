# DevFlow AI — Docker Development Guide

Version: 1.0

---

## Requirements

| Tool | Minimum version | Notes |
|---|---|---|
| Docker Desktop | 4.x | Includes Docker Engine and Docker Compose V2 |
| Docker Compose | 2.x | Bundled with Docker Desktop; `docker compose` (no hyphen) |

No other local dependencies are required. Node.js and Python do **not** need to
be installed on the host machine to run the project with Docker.

---

## Architecture

```
                    Docker Compose (devflow_network)
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
      Frontend            Backend             MongoDB
    Vite dev server      FastAPI/uvicorn      MongoDB 7
     :5173 (host)         :8000 (host)       :27017 (host)
          │                   │
          │  HTTP/WS           │  MongoDB protocol
          └───────────────────┘
              (browser calls localhost:8000)
              (backend calls mongodb:27017)
```

- The **browser** accesses the backend at `http://localhost:8000` (host network).
- Inside the container network, the **backend** reaches MongoDB at
  `mongodb://mongodb:27017/devflowai` (using the Compose service name `mongodb`,
  not `localhost`).
- The **frontend** container does not connect directly to MongoDB.

---

## Environment Setup

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in any values required for your local setup.

   The defaults work out-of-the-box for local Docker development:

   ```env
   MONGODB_URI=mongodb://mongodb:27017/devflowai
   VITE_API_BASE_URL=http://localhost:8000
   BACKEND_CORS_ORIGINS=http://localhost:5173
   ```

3. Optional — add your API key when AI agent features are needed:

   ```env
   GOOGLE_API_KEY=your-key-here
   ```

   Never commit `.env` to version control.

---

## Start

Build images and start all services:

```bash
docker compose up --build
```

Services start in this order:
1. `mongodb` — waits for its own health check to pass.
2. `backend` — starts after MongoDB is healthy.
3. `frontend` — starts after the backend container is running.

Once started:

| Service | URL |
|---|---|
| Frontend (Vite) | http://localhost:5173 |
| Backend (FastAPI) | http://localhost:8000 |
| Backend API docs | http://localhost:8000/docs |
| Backend health | http://localhost:8000/health |
| MongoDB | mongodb://localhost:27017 |

---

## Stop

Stop containers and preserve all data:

```bash
docker compose down
```

Stop containers **and delete all MongoDB data**:

```bash
docker compose down -v
```

> **Warning:** `docker compose down -v` removes the `devflow_mongodb_data`
> volume. All database records are permanently deleted. Use this only when you
> want a clean reset.

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
docker compose logs -f mongodb
```

Check which containers are running and their status:

```bash
docker compose ps
```

---

## Rebuild

After changing `requirements.txt`, `package.json`, or a `Dockerfile`, rebuild
images from scratch:

```bash
docker compose down
docker compose build --no-cache
docker compose up
```

To rebuild a single service without stopping others:

```bash
docker compose build --no-cache backend
docker compose up -d --no-deps backend
```

---

## Hot Reload

Both services support hot reload in development mode.

### Frontend — Vite HMR

The `frontend/` directory is mounted as a volume into the container. Saving any
file in `frontend/src/` triggers Vite's Hot Module Replacement immediately.
No container restart is needed.

### Backend — uvicorn `--reload`

The `backend/` directory is mounted as a volume. Saving any `.py` file triggers
uvicorn's reloader. The FastAPI process restarts automatically.

> **Note on node_modules and .venv:** The `docker-compose.yml` uses anonymous
> volume mounts (`/app/node_modules` and `/app/.venv`) to prevent the host
> directory from overriding the packages installed inside the image. If you add
> a new npm package or Python dependency, rebuild the affected image:
> `docker compose build --no-cache frontend` or `backend`.

---

## Database

### Volume

MongoDB data is stored in the named Docker volume `devflow_mongodb_data`.

```
docker volume ls | grep devflow
```

This volume **persists across** `docker compose down`. Data is only deleted
when you run `docker compose down -v` or explicitly remove the volume:

```bash
docker volume rm devflow_mongodb_data
```

### Direct Access

MongoDB is exposed on host port `27017` so you can connect with:

- **MongoDB Compass:** `mongodb://localhost:27017`
- **mongosh:** `mongosh mongodb://localhost:27017`

### Connection String

Inside Docker (backend service):

```
mongodb://mongodb:27017/devflowai
```

From the host machine:

```
mongodb://localhost:27017/devflowai
```

---

## WebSocket

The backend uses WebSocket connections for real-time workflow updates.
uvicorn supports WebSocket natively — no additional configuration is required.

The frontend connects to:

```
ws://localhost:8000/api/v1/ws/workflows/{workflowId}
```

This URL is derived automatically from `VITE_API_BASE_URL` (`http` → `ws`).
No WebSocket-specific environment variable is needed unless the WS endpoint
is on a different host.

---

## CORS

The backend allows the Vite dev server origin by default:

```
http://localhost:5173
```

This is controlled by the `BACKEND_CORS_ORIGINS` environment variable in
`.env`. To allow additional origins, add them as a comma-separated list:

```env
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:4173
```

---

## Ports

| Service | Container port | Host port | Protocol |
|---|---|---|---|
| Frontend | 5173 | 5173 | HTTP (Vite dev server) |
| Backend | 8000 | 8000 | HTTP + WebSocket |
| MongoDB | 27017 | 27017 | MongoDB wire protocol |

To use different host ports, edit `docker-compose.yml` or override with a
`docker-compose.override.yml` file (see Docker Compose documentation).

---

## Troubleshooting

### Frontend cannot reach backend

- Confirm `VITE_API_BASE_URL=http://localhost:8000` (not the container name).
  The browser resolves this URL, not the container.
- Check backend logs: `docker compose logs -f backend`
- Check CORS: the backend must include `http://localhost:5173` in
  `BACKEND_CORS_ORIGINS`.

### Backend cannot connect to MongoDB

- Confirm `MONGODB_URI=mongodb://mongodb:27017/devflowai` (service name, not
  `localhost`).
- Check MongoDB health: `docker compose ps` should show `mongodb` as `healthy`.
- Check MongoDB logs: `docker compose logs -f mongodb`

### Port already in use

If port 5173, 8000, or 27017 is occupied by another process, change the host
port in `docker-compose.yml`:

```yaml
ports:
  - "5174:5173"   # maps host 5174 → container 5173
```

Then update `VITE_API_BASE_URL` and `BACKEND_CORS_ORIGINS` to match.

### Image not updating after code change

For dependency changes (new packages), rebuild the image:

```bash
docker compose build --no-cache <service>
```

For source code changes, hot reload handles this automatically.

---

## Security Notes

- `.env` is git-ignored and must never be committed.
- `VITE_API_BASE_URL` is a public variable (visible in the browser bundle).
  It must never contain secrets.
- `GOOGLE_API_KEY`, `MONGODB_URI`, and any AI provider tokens must remain
  backend-only environment variables. They are never prefixed with `VITE_`.
- MongoDB is exposed on the host only for local development convenience.
  Remove the `27017` port mapping before deploying to any shared environment.
