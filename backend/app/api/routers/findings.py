"""Findings router — /api/v1/findings"""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import FindingOut, FindingStatus, RejectFindingRequest
from app.api.store import get_finding, list_findings, save_finding
from app.api.routers.auth import get_current_user
from app.db.models import UserDoc
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/findings", tags=["Findings"])


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


@router.get("", response_model=list[FindingOut])
async def list_findings_route(
    workflowId: str | None = None,
    severity: str | None = None,
    agent: str | None = None,
    status: str | None = None,
    file: str | None = None,
    _: UserDoc = Depends(get_current_user),
) -> list[FindingOut]:
    return await list_findings(
        workflow_id=workflowId, severity=severity, agent=agent, status=status, file=file
    )


@router.get("/{finding_id}", response_model=FindingOut)
async def get_finding_route(
    finding_id: str,
    _: UserDoc = Depends(get_current_user),
) -> FindingOut:
    finding = await get_finding(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.post("/{finding_id}/approve", response_model=FindingOut)
async def approve_finding(
    finding_id: str,
    _: UserDoc = Depends(get_current_user),
) -> FindingOut:
    finding = await get_finding(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    now = _now()
    updated_proposal = (
        finding.fixProposal.model_copy(update={"approvedAt": now})
        if finding.fixProposal else None
    )
    updated = finding.model_copy(update={
        "status": FindingStatus.APPROVED,
        "fixProposal": updated_proposal,
        "updatedAt": now,
    })
    await save_finding(updated)
    logger.info("Finding %s approved", finding_id)
    return updated


@router.post("/{finding_id}/reject", response_model=FindingOut)
async def reject_finding(
    finding_id: str,
    body: RejectFindingRequest,
    _: UserDoc = Depends(get_current_user),
) -> FindingOut:
    finding = await get_finding(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    now = _now()
    updated_proposal = (
        finding.fixProposal.model_copy(update={
            "rejectedAt": now,
            "rejectionReason": body.reason or "Rejected by developer",
        }) if finding.fixProposal else None
    )
    updated = finding.model_copy(update={
        "status": FindingStatus.REJECTED,
        "fixProposal": updated_proposal,
        "updatedAt": now,
    })
    await save_finding(updated)
    logger.info("Finding %s rejected: %s", finding_id, body.reason)
    return updated
