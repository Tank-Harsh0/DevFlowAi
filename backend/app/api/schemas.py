"""
API schemas — Pydantic models for request/response serialisation.

These match the TypeScript types in frontend/src/types/ exactly so
the frontend can deserialise responses without mapping.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared / enums
# ---------------------------------------------------------------------------

class WorkflowStatus(StrEnum):
    PENDING          = "pending"
    RUNNING          = "running"
    COMPLETED        = "completed"
    FAILED           = "failed"
    SKIPPED          = "skipped"
    WAITING_APPROVAL = "waiting_approval"


class RepositoryStatus(StrEnum):
    IDLE      = "idle"
    ANALYZING = "analyzing"
    ANALYZED  = "analyzed"
    ERROR     = "error"


class FindingSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"
    INFO     = "info"


class FindingStatus(StrEnum):
    OPEN                = "open"
    IN_REVIEW           = "in_review"
    APPROVED            = "approved"
    REJECTED            = "rejected"
    PENDING_FIX         = "pending_fix"
    FIXED               = "fixed"
    VERIFIED            = "verified"
    VERIFICATION_FAILED = "verification_failed"
    DISMISSED           = "dismissed"


class AgentSource(StrEnum):
    CODE_REVIEW   = "code_review"
    TEST_ANALYSIS = "test_analysis"
    SECURITY      = "security"
    DOCUMENTATION = "documentation"


# ---------------------------------------------------------------------------
# Repository schemas
# ---------------------------------------------------------------------------

class RepositoryOut(BaseModel):
    id: str
    name: str
    url: str
    description: str | None = None
    defaultBranch: str | None = None
    language: str | None = None
    languages: list[str] = Field(default_factory=list)
    status: RepositoryStatus = RepositoryStatus.IDLE
    lastAnalyzedAt: str | None = None
    createdAt: str
    updatedAt: str
    workflowCount: int = 0
    lastWorkflowId: str | None = None


class AddRepositoryRequest(BaseModel):
    url: str
    name: str | None = None
    defaultBranch: str | None = "main"


# ---------------------------------------------------------------------------
# Workflow / step schemas
# ---------------------------------------------------------------------------

class AgentStepOut(BaseModel):
    id: str
    name: str
    label: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    progress: int | None = None
    startedAt: str | None = None
    completedAt: str | None = None
    findingsCount: int | None = None
    message: str | None = None
    errorMessage: str | None = None


class WorkflowRunOut(BaseModel):
    id: str
    repositoryId: str
    repositoryName: str
    status: WorkflowStatus
    createdAt: str
    updatedAt: str
    completedAt: str | None = None
    steps: list[AgentStepOut] = Field(default_factory=list)
    totalFindings: int | None = None
    fixedFindings: int | None = None
    testsGenerated: int | None = None
    testsPassed: int | None = None
    currentStep: str | None = None


class StartWorkflowRequest(BaseModel):
    repositoryId: str


class ApprovalRequest(BaseModel):
    approved: bool
    note: str | None = None


# ---------------------------------------------------------------------------
# Finding schemas
# ---------------------------------------------------------------------------

class FindingLocationOut(BaseModel):
    file: str
    line: int | None = None
    endLine: int | None = None
    column: int | None = None
    function: str | None = None


class CodeDiffOut(BaseModel):
    before: str
    after: str
    language: str | None = None


class FixProposalOut(BaseModel):
    id: str
    findingId: str
    description: str
    reason: str
    risk: str  # "low" | "medium" | "high"
    diff: CodeDiffOut | None = None
    affectedFiles: list[str] = Field(default_factory=list)
    approvedAt: str | None = None
    rejectedAt: str | None = None
    rejectionReason: str | None = None


class FindingOut(BaseModel):
    id: str
    workflowId: str
    severity: FindingSeverity
    status: FindingStatus
    agent: AgentSource
    title: str
    description: str
    location: FindingLocationOut
    evidence: str | None = None
    whyItMatters: str | None = None
    suggestedFix: str | None = None
    verificationMethod: str | None = None
    fixProposal: FixProposalOut | None = None
    createdAt: str
    updatedAt: str


class RejectFindingRequest(BaseModel):
    reason: str | None = None


# ---------------------------------------------------------------------------
# Report schemas
# ---------------------------------------------------------------------------

class TestMetricsOut(BaseModel):
    beforeCount: int = 0
    generatedCount: int = 0
    afterCount: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0


class ProductivityMetricsOut(BaseModel):
    manualDurationMinutes: int = 0
    aiDurationMinutes: int = 0
    timeSavedMinutes: int = 0
    reductionPercent: float = 0.0
    manualSteps: int = 11
    automatedSteps: int = 8
    developerInterventions: int = 0
    issuesDetected: int = 0
    issuesFixed: int = 0
    testsGenerated: int = 0
    reworkIterations: int = 1


class SeverityBreakdownOut(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class ReportSectionOut(BaseModel):
    repository: dict[str, Any]
    analysis: dict[str, Any]
    remediation: dict[str, Any]
    testing: TestMetricsOut
    productivity: ProductivityMetricsOut


class ReportOut(BaseModel):
    id: str
    workflowId: str
    repositoryId: str
    repositoryName: str
    generatedAt: str
    sections: ReportSectionOut
    downloadUrl: str | None = None
