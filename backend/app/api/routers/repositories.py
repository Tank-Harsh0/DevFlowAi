"""
Repositories router — /api/v1/repositories

Endpoints:
  GET    /api/v1/repositories           List all registered repositories
  POST   /api/v1/repositories           Register a new repository (local path)
  GET    /api/v1/repositories/{id}      Get a single repository
  DELETE /api/v1/repositories/{id}      Remove a repository
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from app.api.schemas import AddRepositoryRequest, RepositoryOut, RepositoryStatus
from app.api.store import store
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/repositories", tags=["Repositories"])


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


@router.get("", response_model=list[RepositoryOut])
def list_repositories() -> list[RepositoryOut]:
    """Return all registered repositories."""
    return list(store.repositories.values())


@router.post("", response_model=RepositoryOut, status_code=201)
def add_repository(body: AddRepositoryRequest) -> RepositoryOut:
    """Register a local repository path for analysis."""
    repo_id = str(uuid.uuid4())
    now = _now()

    # Derive a display name from the URL/path if not provided
    name = body.name or body.url.rstrip("/").split("/")[-1]

    repo = RepositoryOut(
        id=repo_id,
        name=name,
        url=body.url,
        defaultBranch=body.defaultBranch or "main",
        status=RepositoryStatus.IDLE,
        createdAt=now,
        updatedAt=now,
    )
    store.repositories[repo_id] = repo
    logger.info("Repository registered: %s (%s)", name, repo_id)
    return repo


@router.get("/{repository_id}", response_model=RepositoryOut)
def get_repository(repository_id: str) -> RepositoryOut:
    """Return a single repository by ID."""
    repo = store.repositories.get(repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.delete("/{repository_id}", status_code=204)
def remove_repository(repository_id: str) -> None:
    """Remove a repository from the store."""
    if repository_id not in store.repositories:
        raise HTTPException(status_code=404, detail="Repository not found")
    del store.repositories[repository_id]
    logger.info("Repository removed: %s", repository_id)
