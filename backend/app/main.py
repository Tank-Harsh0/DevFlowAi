"""
DevFlow AI — FastAPI application factory.

Phase 1: Foundation.
  - CORS configuration for the React frontend.
  - Health endpoint.
  - Consistent error response structure.
  - Logging initialised on startup.

Phase 6+ API:
  - /api/v1/repositories  — CRUD for registered repositories
  - /api/v1/workflows     — Start/monitor/approve workflow runs
  - /api/v1/findings      — List/approve/reject findings
  - /api/v1/reports       — Access final reports
"""
from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import findings, reports, repositories, workflows
from app.api.routers import ws as ws_router
from app.api.routers import auth as auth_router
from app.api.ws_broker import ws_broker
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.database import init_db, close_db

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    import asyncio
    configure_logging()
    await init_db()
    ws_broker.set_loop(asyncio.get_running_loop())
    logger.info("Starting %s v%s (%s)", settings.app_name, settings.app_version, settings.app_env)
    yield
    await close_db()
    logger.info("Shutting down %s", settings.app_name)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.app_name,
        description="AI-powered developer workflow automation platform.",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS — allows the React dev server (Vite default: 5173) to call the API
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------------------------
    # Request timing middleware
    # -----------------------------------------------------------------------

    @application.middleware("http")
    async def add_process_time_header(request: Request, call_next):  # type: ignore[no-untyped-def]
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        return response

    # -----------------------------------------------------------------------
    # Global exception handler — never expose stack traces to clients
    # -----------------------------------------------------------------------

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                    "details": {},
                }
            },
        )

    # -----------------------------------------------------------------------
    # Routes — health
    # -----------------------------------------------------------------------

    @application.get("/health", tags=["Health"])
    def health_check() -> dict[str, str]:
        """Return service health status.

        Used by load balancers, container orchestrators, and the frontend
        to confirm the API is reachable.
        """
        return {
            "status": "healthy",
            "service": "devflow-ai",
            "version": settings.app_version,
            "environment": settings.app_env,
        }

    # -----------------------------------------------------------------------
    # Routes — API v1
    # -----------------------------------------------------------------------

    API_PREFIX = "/api/v1"
    application.include_router(auth_router.router,  prefix=API_PREFIX)
    application.include_router(repositories.router, prefix=API_PREFIX)
    application.include_router(workflows.router,    prefix=API_PREFIX)
    application.include_router(findings.router,     prefix=API_PREFIX)
    application.include_router(reports.router,      prefix=API_PREFIX)
    # WebSocket routes — must be registered without a prefix so the path
    # /api/v1/ws/workflows/{id} is built correctly by the router itself.
    application.include_router(ws_router.router,    prefix=API_PREFIX)

    return application


app = create_app()
