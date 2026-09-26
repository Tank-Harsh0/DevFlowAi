"""
Base class for all DevFlow AI analysis agents.

Each agent receives a ProjectContext, performs read-only static analysis,
and returns a list of Finding objects.

IBM Bob 2.0 dependency note:
  Subagents are plain Python classes for the MVP. The IBM Bob 2.0
  subagent dispatch API has not been validated. This is recorded in
  PROJECT_STATE.md under "Not Yet Verified". If the IBM Bob 2.0 agent
  wrapper API becomes available, subagents can be adapted to extend it
  without changing the Finding schema or the orchestrator's call site.

Constraints (SUBAGENT_SPEC.md general rules):
  - Read-only: never modify files.
  - Do not execute commands.
  - Do not communicate with other agents.
  - Report only issues supported by evidence in the provided code.
  - Never claim exhaustive coverage.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.logging import get_logger
from app.models.finding import Finding
from app.models.workflow import ProjectContext


class BaseAgent(ABC):
    """Abstract base for all analysis agents."""

    def __init__(self) -> None:
        self.logger = get_logger(f"agents.{self.name}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier used in logs and finding IDs, e.g. 'code_review'."""

    @abstractmethod
    def analyze(self, context: ProjectContext) -> list[Finding]:
        """Perform static analysis and return findings.

        Args:
            context: The ProjectContext produced by the Repository Inspector.

        Returns:
            A (possibly empty) list of Finding objects. Never raises —
            errors are logged and an empty list is returned so the orchestrator
            can continue with available findings.
        """

    def safe_analyze(self, context: ProjectContext) -> list[Finding]:
        """Wrapper that catches unexpected errors so the workflow continues.

        ARCHITECTURE.md §8: Subagent failure does not stop the workflow.
        """
        try:
            findings = self.analyze(context)
            self.logger.info("%s complete: %d finding(s)", self.name, len(findings))
            return findings
        except Exception as exc:  # noqa: BLE001
            self.logger.error("%s failed unexpectedly: %s", self.name, exc)
            return []
