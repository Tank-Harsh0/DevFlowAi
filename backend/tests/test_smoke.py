"""
Smoke test — verifies the application package can be imported without errors.

This is the first test that should pass after Phase 1 setup.
"""
from app.core.config import settings
from app.core.logging import get_logger
from app.main import app


def test_app_importable() -> None:
    """The FastAPI application object must be importable."""
    assert app is not None


def test_settings_importable() -> None:
    """Settings must load without raising."""
    assert settings.app_name == "DevFlow AI"


def test_get_logger_returns_logger() -> None:
    """get_logger must return a stdlib Logger."""
    import logging

    logger = get_logger("test")
    assert isinstance(logger, logging.Logger)
