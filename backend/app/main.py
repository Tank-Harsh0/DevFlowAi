"""
DevFlow AI — FastAPI application factory.

Phase 1: Foundation.
  - CORS configuration for the React frontend.
  - Health endpoint.
  - Consistent error response structure.
  - Logging initialised on startup.
"""
from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    configure_logging()
    logger.info("Starting %s v%s (%s)", settings.app_name, settings.app_version, settings.app_env)
    yield
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
    # Routes
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

    return application


app = create_app()
