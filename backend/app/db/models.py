"""
MongoDB document models (Beanie ODM).

Each class maps 1-to-1 with a MongoDB collection.
Beanie uses Pydantic v2 under the hood, so all field types are validated.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from beanie import Document, Indexed
from pydantic import Field


def _utcnow() -> str:
    return datetime.now(tz=UTC).isoformat()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class UserDoc(Document):
    email: Indexed(str, unique=True)  # type: ignore[valid-type]
    username: Indexed(str, unique=True)  # type: ignore[valid-type]
    hashed_password: str
    is_active: bool = True
    created_at: str = Field(default_factory=_utcnow)
    updated_at: str = Field(default_factory=_utcnow)

    class Settings:
        name = "users"


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------

class RepositoryDoc(Document):
    repo_id: Indexed(str, unique=True)  # type: ignore[valid-type]  # the UUID we expose to clients
    name: str
    url: str
    description: str | None = None
    default_branch: str = "main"
    language: str | None = None
    languages: list[str] = Field(default_factory=list)
    status: str = "idle"
    last_analyzed_at: str | None = None
    created_at: str = Field(default_factory=_utcnow)
    updated_at: str = Field(default_factory=_utcnow)
    workflow_count: int = 0
    last_workflow_id: str | None = None

    class Settings:
        name = "repositories"


# ---------------------------------------------------------------------------
# Workflow runs
# ---------------------------------------------------------------------------

class WorkflowRunDoc(Document):
    run_id: Indexed(str, unique=True)  # type: ignore[valid-type]
    repository_id: str
    repository_name: str
    status: str = "pending"
    created_at: str = Field(default_factory=_utcnow)
    updated_at: str = Field(default_factory=_utcnow)
    completed_at: str | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)
    total_findings: int | None = None
    fixed_findings: int | None = None
    tests_generated: int | None = None
    tests_passed: int | None = None
    current_step: str | None = None

    class Settings:
        name = "workflow_runs"


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

class FindingDoc(Document):
    finding_id: Indexed(str, unique=True)  # type: ignore[valid-type]
    workflow_id: Indexed(str)  # type: ignore[valid-type]
    severity: str
    status: str
    agent: str
    title: str
    description: str = ""
    location: dict[str, Any] = Field(default_factory=dict)
    evidence: str | None = None
    why_it_matters: str | None = None
    suggested_fix: str | None = None
    verification_method: str | None = None
    fix_proposal: dict[str, Any] | None = None
    created_at: str = Field(default_factory=_utcnow)
    updated_at: str = Field(default_factory=_utcnow)

    class Settings:
        name = "findings"


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class ReportDoc(Document):
    report_id: Indexed(str, unique=True)  # type: ignore[valid-type]
    workflow_id: Indexed(str, unique=True)  # type: ignore[valid-type]
    repository_id: str
    repository_name: str
    generated_at: str = Field(default_factory=_utcnow)
    sections: dict[str, Any] = Field(default_factory=dict)
    download_url: str | None = None

    class Settings:
        name = "reports"


# All document classes — passed to Beanie.init_beanie()
ALL_DOCUMENTS = [UserDoc, RepositoryDoc, WorkflowRunDoc, FindingDoc, ReportDoc]
