"""
Logging configuration.

Sets up a structured logger for the application. Log level is controlled
by the LOG_LEVEL environment variable via Settings.
"""
from __future__ import annotations

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """Configure root logger with a consistent format."""
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    date_format = "%Y-%m-%dT%H:%M:%S"

    logging.basicConfig(
        level=settings.log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Suppress noisy third-party loggers at WARNING unless we're in DEBUG
    if settings.log_level != "DEBUG":
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.

    Usage::

        from app.core.logging import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)
