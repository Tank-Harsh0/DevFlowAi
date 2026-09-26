"""
MongoDB connection and Beanie ODM initialisation.

Beanie 2.x uses pymongo's native async client (AsyncMongoClient), not Motor.
Call `init_db()` once at application startup (inside the FastAPI lifespan).
"""
from __future__ import annotations

import os

from pymongo.asynchronous.mongo_client import AsyncMongoClient

from app.db.models import ALL_DOCUMENTS

_MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/devflow")
_DB_NAME = os.getenv("MONGODB_DB_NAME", "devflow")

# Module-level client — created once, reused for the process lifetime.
_client: AsyncMongoClient | None = None  # type: ignore[type-arg]


async def init_db() -> None:
    """Connect to MongoDB and initialise Beanie with all document models."""
    global _client
    from beanie import init_beanie

    _client = AsyncMongoClient(_MONGODB_URI)
    db = _client[_DB_NAME]
    await init_beanie(database=db, document_models=ALL_DOCUMENTS)


async def close_db() -> None:
    """Cleanly close the MongoDB connection pool on shutdown."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
