"""
Fix Proposal domain model.

Schema defined in ARCHITECTURE.md §4 Fix Proposal Object.
Produced by the Fix Planner; consumed by the Human Approval Gate and Code Modifier.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from app.models.finding import FixRisk


class ProposalStatus(StrEnum):
    PENDING  = "pending"
    APPROVED = "approved"
    SKIPPED  = "skipped"
    REJECTED = "rejected"
    APPLIED  = "applied"
    FAILED   = "failed"   # apply attempted but code modifier reverted it


class FixProposal(BaseModel):
    """A single proposed code change for one finding.

    Schema matches ARCHITECTURE.md §4 Fix Proposal Object exactly.
    """

    finding_id: str               # e.g. "CR-001"
    fix_risk: FixRisk
    description: str              # what the fix does
    rationale: str                # why this fix is correct
    files_affected: list[str]     # relative paths
    diff: str                     # unified diff format (or "" if not_applicable)
    verification_method: str
    status: ProposalStatus = ProposalStatus.PENDING
