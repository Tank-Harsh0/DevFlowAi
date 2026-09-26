# DevFlow AI — Project State

## Current Phase: Phase 3 Complete

---

## Phase 0 — Planning / Documentation ✅

Completed tasks:
- Product Requirements Document created (`docs/PRD.md`)
- Architecture Document created (`docs/ARCHITECTURE.md`)
- Project State Document created (`docs/PROJECT_STATE.md`)

---

## Phase 1 — Frontend Foundation ✅

Completed tasks:
- Vite + React + TypeScript scaffold
- Tailwind CSS v4 via `@tailwindcss/vite`
- Path alias `@/` → `src/`
- Design system (CSS `@theme` tokens: background, foreground, card, primary, muted, accent, destructive, border, success, warning, error, info)
- Dark-first palette with `.light` class override
- `useTheme` hook (persists to `localStorage`)
- UI primitives: `Button`, `Card`, `Badge`, `Input`, `Separator`
- `AppLayout` (sidebar + header + `<Outlet />`)
- `Sidebar` with active `NavLink` states
- `Header` with page title, theme toggle, notifications
- React Router v7 with all routes nested under `AppLayout`
- `lib/utils.ts` (`cn`)
- TypeScript types: `workflow.ts`, `finding.ts`, `repository.ts`, `report.ts`
- API services: `api.ts`, `workflows.ts`, `findings.ts`, `repositories.ts`, `reports.ts`
- Hooks: `useWorkflow.ts`, `useWebSocket.ts`

Verification:
- `npm run lint` → 0 errors
- `npm run build` → success

---

## Phase 2 — Core Pages ✅

### Pages implemented
Dashboard, Repositories, Workflow, Findings, Reports, Settings — all with full UI.

### Components created
- `StatusBadge`, `StatCard`, `EmptyState`/`LoadingState`/`ErrorState`
- `AgentActivityFeed`, `WorkflowTimeline`
- `FindingRow`, `FindingDetail`
- `RepositoryCard`

### Mock data
Isolated in `src/mocks/` — `workflows.ts`, `findings.ts`, `repositories.ts`, `reports.ts`.

Verification:
- `npm run lint` → 0 errors
- `npm run build` → success

---

## Phase 3 — Backend Integration ✅

### Backend status
No Python backend code exists yet — only `requirements.txt` is present in `backend/`.
The backend API has not been implemented. Phase 3 therefore focused on:

1. Building the full integration infrastructure so pages connect to the real API the moment it is available.
2. Implementing graceful fallback to mock data when the backend is unreachable.
3. Adding a live backend connectivity indicator in the sidebar.

### What was implemented

#### API Client (`src/services/api.ts`)
- Categorized error messages for 400/401/403/404/409/422/429/500, network errors, and timeouts.
- `checkBackendHealth()` — probes `GET /health` (4 s timeout). Returns `true` if the backend responds (any HTTP status), `false` only on network/timeout failure.
- `WEBSOCKET_URL` auto-derived from `VITE_API_BASE_URL` (`http` → `ws`).

#### Generic data hook (`src/hooks/useApiData.ts`)
- `useApiData<T>` — fetches from real API, falls back to mock data (with `isMock: true`) only on network errors.
- `useApiItem<T>` — single-item variant.
- Mock fallback is NOT triggered on 4xx/5xx errors — those surface normally.

#### Domain hooks
| Hook | Source | Mock fallback |
|------|--------|---------------|
| `useRepositories` | `repositoriesService.list()` | `mockRepositories` |
| `useWorkflows` | `workflowsService.list()` | `mockWorkflows` |
| `useFindings` | `findingsService.list()` | `mockFindings` |
| `useReports` | `reportsService.list()` | `mockReports` |

#### Backend connectivity (`src/hooks/useBackendStatus.tsx`)
- React context + provider wrapping the whole app.
- Polls `GET /health` every 30 s.
- Sidebar shows: `● Connected`, `● Offline`, or `● Connecting...`

#### Pages wired to real API
All pages now call their domain hooks. When the backend is up, they show real data. When unreachable, they show mock data with a clearly labelled amber notice.

| Page | Hook used | Mock fallback | Loading/Error states |
|------|-----------|---------------|----------------------|
| Dashboard | `useWorkflows`, `useFindings` | ✅ | ✅ |
| Repositories | `useRepositories` | ✅ | ✅ (+ retry) |
| Workflow | `useWorkflows`, `useWebSocket` | ✅ | ✅ (+ retry) |
| Findings | `useFindings` | ✅ | ✅ (+ retry) |
| Reports | `useReports` | ✅ | ✅ (+ retry) |
| Settings | — | — | — |

#### Repositories page
- Add Repository form is now live — submits to `POST /api/v1/repositories`.
- Error from backend displayed inline.
- On success, repository list is refetched.

#### Findings page
- Approve/Reject actions now call `POST /api/v1/workflows/{workflowId}/steps/{stepId}/approval`.
- On success, findings list is refetched.

#### Reports page
- Export button enabled when `report.downloadUrl` is provided by backend.
- `window.open(downloadUrl)` used — no frontend PDF generation.

#### Workflow page
- `useWebSocket` wired: connects to `ws://.../api/v1/ws/workflows/{workflowId}` when a running workflow is selected.
- WebSocket connection status shown inline (`connected`/`connecting`/`disconnected`).
- WebSocket only enabled when backend is live (`!isMock`) and workflow is running.
- `step_update` and `workflow_update` events merged into local React state in real time.

#### Environment
- `frontend/.env.example` created with documentation.
- Only `VITE_API_BASE_URL` and optional `VITE_WS_URL` are frontend environment variables.
- No secrets in frontend configuration.

#### Components added
- `src/components/ui/mock-notice.tsx` — `MockDataNotice` renders when `isMock === true`.

### Mock data remaining
Mock data files remain in `src/mocks/` and serve as fallback only when the backend is unreachable. They are not shown silently — every page clearly labels mock data with a notice.

### Integrated endpoints (ready for backend implementation)

| Method | Endpoint | Page | Status |
|--------|----------|------|--------|
| GET | `/health` | Sidebar | Integration ready |
| GET | `/api/v1/repositories` | Repositories | Integration ready |
| POST | `/api/v1/repositories` | Repositories | Integration ready |
| GET | `/api/v1/workflows` | Workflow, Dashboard | Integration ready |
| GET | `/api/v1/workflows/{id}` | Workflow detail | Integration ready |
| POST | `/api/v1/workflows/{id}/steps/{stepId}/approval` | Findings | Integration ready |
| GET | `/api/v1/findings` | Findings | Integration ready |
| GET | `/api/v1/reports` | Reports | Integration ready |
| GET | `/api/v1/workflows/{id}/report` | Reports | Integration ready |
| WS | `/api/v1/ws/workflows/{id}` | Workflow | Integration ready |

### Remaining backend dependencies

All endpoints listed above are unimplemented in the backend (`backend/` has only `requirements.txt`).

The frontend will automatically switch from mock data to real data the moment each endpoint responds correctly.

### Verification

```
npm run lint   → ✅ 0 errors, 0 warnings
npm run build  → ✅ success (800 kB JS, 32.5 kB CSS)
```

Build warning: single JS chunk > 500 kB due to Recharts. Will be addressed in Phase 7 (code splitting).

### Known issues / limitations

- Backend not yet implemented — all API calls fall back to mock data.
- `GET /api/v1/repositories/{id}`, `DELETE /api/v1/repositories/{id}` wired in service layer but not yet used by UI (individual repo detail page not in scope).
- `GET /api/v1/workflows/{id}` wired in `useWorkflow.ts` hook (Phase 1 legacy) but Phase 3 pages use `useWorkflows` list hook. Individual workflow detail can be wired in Phase 4.
- Server-side filtering for findings (`?severity=`, `?agent=`) is wired in `findingsService.list()` but the UI currently sends no filter params (all filtering is client-side). This can be switched to server-side filtering in Phase 5 when the backend supports it.

### CORS requirement (for backend developer)
When the backend is running, it must allow the frontend origin:
```
http://localhost:5173
```
FastAPI CORS middleware must include this origin.

---

## Phase 4 — Workflow Visualization and Real-Time Agent Activity (NOT STARTED)

Pending explicit approval.

Tasks:
- Connect "Run Workflow" button to `POST /api/v1/workflows` and navigate to Workflow page.
- Wire `useWorkflow` individual hook to Workflow detail view.
- Enhanced real-time step progress once WebSocket is live.
- Human approval flow UI for `waiting_approval` step status.

---

## Phase 5 — Findings and Approval (NOT STARTED)

Tasks:
- Switch findings filtering to server-side when backend supports query params.
- Code diff display (when `fixProposal.diff` is provided).
- Full approval flow with confirmation dialog.

---

## Phase 6 — Metrics and Reports (NOT STARTED)

Tasks:
- Wire productivity metrics to actual backend report data.

---

## Phase 7 — Polish (NOT STARTED)

Tasks:
- Code splitting (Recharts/Vite `build.rolldownOptions.output.codeSplitting`).
- Animations.
- Accessibility audit.
- Responsive improvements.

---

## Security Notes

- `frontend/.env` contains only `VITE_API_BASE_URL` (public config). No secrets.
- `frontend/.env.example` is committed and documents all allowed frontend env vars.
- The root `.env` (backend config) contains `MONGODB_URI`. This is **outside the frontend scope**.
  - The frontend source (`src/`) has zero references to `MONGODB_URI`.
  - The variable is not `VITE_`-prefixed and will never be in the browser bundle.
  - The root `.env` is git-ignored.
  - **Recommendation for backend developer:** ensure the MongoDB connection string is not logged to `stdout`/`stderr` during server startup.
