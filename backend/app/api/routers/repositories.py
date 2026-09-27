"""Repositories router — /api/v1/repositories"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import AddRepositoryRequest, RepositoryOut, RepositoryStatus
from app.api.store import delete_repository, get_repository, list_repositories, save_repository
from app.api.routers.auth import get_current_user
from app.db.models import UserDoc
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/repositories", tags=["Repositories"])


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


@router.get("", response_model=list[RepositoryOut])
async def list_repos(
    current_user: UserDoc = Depends(get_current_user),
) -> list[RepositoryOut]:
    return await list_repositories(owner_id=str(current_user.id))


@router.post("", response_model=RepositoryOut, status_code=201)
async def add_repository(
    body: AddRepositoryRequest,
    current_user: UserDoc = Depends(get_current_user),
) -> RepositoryOut:
    now = _now()
    name = body.name or body.url.rstrip("/").split("/")[-1]
    repo = RepositoryOut(
        id=str(uuid.uuid4()),
        name=name,
        url=body.url,
        defaultBranch=body.defaultBranch or "main",
        status=RepositoryStatus.IDLE,
        createdAt=now,
        updatedAt=now,
    )
    await save_repository(repo, owner_id=str(current_user.id))
    logger.info("Repository registered: %s (%s)", name, repo.id)
    return repo


@router.get("/{repository_id}", response_model=RepositoryOut)
async def get_repo(
    repository_id: str,
    current_user: UserDoc = Depends(get_current_user),
) -> RepositoryOut:
    repo = await get_repository(repository_id, owner_id=str(current_user.id))
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.delete("/{repository_id}", status_code=204)
async def remove_repository(
    repository_id: str,
    current_user: UserDoc = Depends(get_current_user),
) -> None:
    if not await delete_repository(repository_id, owner_id=str(current_user.id)):
        raise HTTPException(status_code=404, detail="Repository not found")
    logger.info("Repository removed: %s", repository_id)
