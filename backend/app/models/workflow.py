"""
Domain models for Phase 2 — Orchestrator Skeleton.

These are pure Pydantic models used as structured data across services.
They are not API schemas (those live in app/schemas/).
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Workflow state machine
# ---------------------------------------------------------------------------


class WorkflowStage(StrEnum):
    """Ordered stages of a DevFlow AI workflow run.

    Each stage name maps directly to the component that owns it.
    """

    IDLE = "idle"
    INSPECTING = "inspecting"
    PLANNING = "planning"
    ANALYZING = "analyzing"          # subagents running
    AGGREGATING = "aggregating"
    PRIORITIZING = "prioritizing"
    FIX_PLANNING = "fix_planning"
    AWAITING_APPROVAL = "awaiting_approval"
    MODIFYING = "modifying"
    GENERATING_TESTS = "generating_tests"
    RUNNING_TESTS = "running_tests"
    ANALYZING_FAILURES = "analyzing_failures"
    REPORTING = "reporting"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowState(BaseModel):
    """Tracks the current execution state of a workflow run."""

    session_id: str
    stage: WorkflowStage = WorkflowStage.IDLE
    repository_path: str
    error: str | None = None


# ---------------------------------------------------------------------------
# Repository Inspector output
# ---------------------------------------------------------------------------


class FileEntry(BaseModel):
    """Metadata about a single repository file."""

    path: str                              # relative to repo root
    size_bytes: int
    readable: bool = True
    skipped_reason: str | None = None      # e.g. "exceeds size limit"


class ProjectContext(BaseModel):
    """Structured output produced by the Repository Inspector.

    Saved to session_dir/project_context.json after inspection.
    """

    repository_path: str
    detected_language: str = "unknown"
    detected_test_framework: str = "unknown"

    # Categorised file listings (relative paths)
    source_files: list[FileEntry] = Field(default_factory=list)
    test_files: list[FileEntry] = Field(default_factory=list)
    doc_files: list[FileEntry] = Field(default_factory=list)
    manifest_files: list[FileEntry] = Field(default_factory=list)
    other_files: list[FileEntry] = Field(default_factory=list)

    # Raw content for files small enough to read (keyed by relative path)
    file_contents: dict[str, str] = Field(default_factory=dict)

    # Files that could not be read (relative paths)
    unreadable_files: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Task Planner output
# ---------------------------------------------------------------------------


class AgentTask(BaseModel):
    """Describes one analysis task for a subagent."""

    agent: str                             # e.g. "code_review"
    enabled: bool = True
    skip_reason: str | None = None         # populated when enabled=False


class ExecutionPlan(BaseModel):
    """Structured output produced by the Task Planner.

    Saved to session_dir/execution_plan.json after planning.
    """

    session_id: str
    repository_path: str
    tasks: list[AgentTask] = Field(default_factory=list)
    parallel_supported: bool = False       # IBM Bob 2.0 parallel API not yet validated
    notes: list[str] = Field(default_factory=list)
