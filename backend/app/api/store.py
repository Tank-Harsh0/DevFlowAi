"""
In-memory data store.

For the MVP there is no database. All state lives here as Python dicts
keyed by ID. This is sufficient for a single-process demo run.

Import the singleton `store` from this module in all routers.
"""
from __future__ import annotations

from app.api.schemas import (
    FindingOut,
    ReportOut,
    RepositoryOut,
    WorkflowRunOut,
)


class InMemoryStore:
    """Thread-safe-ish (single process) in-memory store."""

    def __init__(self) -> None:
        self.repositories: dict[str, RepositoryOut] = {}
        self.workflows: dict[str, WorkflowRunOut] = {}
        self.findings: dict[str, FindingOut] = {}
        self.reports: dict[str, ReportOut] = {}

        # Map workflow_id → list[finding_id] for fast lookup
        self.workflow_findings: dict[str, list[str]] = {}
        # Map workflow_id → report_id
        self.workflow_report: dict[str, str] = {}

    def clear(self) -> None:
        """Reset — used in tests."""
        self.repositories.clear()
        self.workflows.clear()
        self.findings.clear()
        self.reports.clear()
        self.workflow_findings.clear()
        self.workflow_report.clear()


# Singleton — imported by all routers
store = InMemoryStore()
