"""
Findings router — /api/v1/findings

Endpoints:
  GET   /api/v1/findings              List findings (with optional filters)
  GET   /api/v1/findings/{id}         Get a single finding
  POST  /api/v1/findings/{id}/approve Approve the fix proposal
  POST  /api/v1/findings/{id}/reject  Reject the fix proposal
"""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from app.api.schemas import FindingOut, FindingStatus, RejectFindingRequest
from app.api.store import store
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/findings", tags=["Findings"])


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


@router.get("", response_model=list[FindingOut])
def list_findings(
    workflowId: str | None = None,
    severity: str | None = None,
    agent: str | None = None,
    status: str | None = None,
    file: str | None = None,
) -> list[FindingOut]:
    """Return findings, optionally filtered."""
    findings = list(store.findings.values())

    if workflowId:
        ids = store.workflow_findings.get(workflowId, [])
        findings = [f for f in findings if f.id in ids]
    if severity:
        findings = [f for f in findings if f.severity.value == severity]
    if agent:
        findings = [f for f in findings if f.agent.value == agent]
    if status:
        findings = [f for f in findings if f.status.value == status]
    if file:
        findings = [f for f in findings if file in f.location.file]

    return sorted(findings, key=lambda f: (
        {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(f.severity.value, 9),
        f.createdAt,
    ))


@router.get("/{finding_id}", response_model=FindingOut)
def get_finding(finding_id: str) -> FindingOut:
    """Return a single finding by ID."""
    finding = store.findings.get(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.post("/{finding_id}/approve", response_model=FindingOut)
def approve_finding(finding_id: str) -> FindingOut:
    """Approve the fix proposal for a finding."""
    finding = store.findings.get(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")

    now = _now()
    updated_proposal = None
    if finding.fixProposal:
        updated_proposal = finding.fixProposal.model_copy(update={"approvedAt": now})

    updated = finding.model_copy(update={
        "status": FindingStatus.APPROVED,
        "fixProposal": updated_proposal,
        "updatedAt": now,
    })
    store.findings[finding_id] = updated
    logger.info("Finding %s approved", finding_id)
    return updated


@router.post("/{finding_id}/reject", response_model=FindingOut)
def reject_finding(finding_id: str, body: RejectFindingRequest) -> FindingOut:
    """Reject the fix proposal for a finding."""
    finding = store.findings.get(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")

    now = _now()
    updated_proposal = None
    if finding.fixProposal:
        updated_proposal = finding.fixProposal.model_copy(update={
            "rejectedAt": now,
            "rejectionReason": body.reason or "Rejected by developer",
        })

    updated = finding.model_copy(update={
        "status": FindingStatus.REJECTED,
        "fixProposal": updated_proposal,
        "updatedAt": now,
    })
    store.findings[finding_id] = updated
    logger.info("Finding %s rejected: %s", finding_id, body.reason)
    return updated
