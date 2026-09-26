"""
Task Planner.

Produces an ExecutionPlan from a ProjectContext.

Responsibilities (ARCHITECTURE.md §3):
- Decide which agents to enable based on available file types.
- Mark agents as disabled (with reason) when relevant files are absent.
- Record whether parallel execution is supported.
- Does NOT perform any analysis.
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.models.workflow import AgentTask, ExecutionPlan, ProjectContext

logger = get_logger(__name__)

# The four standard analysis agents, in the order they will run sequentially
# if parallel dispatch is not available.
_ALL_AGENTS = ["code_review", "test_analysis", "security", "documentation"]


class TaskPlanner:
    """Determines which agents to run and produces an ExecutionPlan."""

    def plan(self, session_id: str, context: ProjectContext) -> ExecutionPlan:
        """Create an ExecutionPlan from *context*.

        Args:
            session_id: The current workflow session identifier.
            context:    The ProjectContext produced by the Repository Inspector.

        Returns:
            An ExecutionPlan with each agent task enabled or disabled.
        """
        tasks: list[AgentTask] = []
        notes: list[str] = []

        has_source = len(context.source_files) > 0
        has_tests  = len(context.test_files) > 0
        has_docs   = len(context.doc_files) > 0

        # Code Review — requires source files
        if has_source:
            tasks.append(AgentTask(agent="code_review"))
        else:
            tasks.append(AgentTask(
                agent="code_review",
                enabled=False,
                skip_reason="No source files detected in repository",
            ))
            notes.append("code_review skipped: no source files")

        # Test Analysis — requires source files (test files absence is itself a finding)
        if has_source:
            tasks.append(AgentTask(agent="test_analysis"))
            if not has_tests:
                notes.append(
                    "test_analysis: no existing test files found; agent will report coverage gap"
                )
        else:
            tasks.append(AgentTask(
                agent="test_analysis",
                enabled=False,
                skip_reason="No source files detected in repository",
            ))
            notes.append("test_analysis skipped: no source files")

        # Security — requires source or manifest files
        if has_source or len(context.manifest_files) > 0:
            tasks.append(AgentTask(agent="security"))
        else:
            tasks.append(AgentTask(
                agent="security",
                enabled=False,
                skip_reason="No source or manifest files detected",
            ))
            notes.append("security skipped: no source or manifest files")

        # Documentation — runs even without docs (absence of docs is a finding)
        tasks.append(AgentTask(agent="documentation"))
        if not has_docs:
            notes.append("documentation: no documentation files found; agent will report this gap")

        # IBM Bob 2.0 parallel dispatch is not yet validated (IMPLEMENTATION_PLAN §Phase 2)
        parallel_supported = False
        notes.append(
            "Parallel dispatch: not yet validated against IBM Bob 2.0 API; "
            "agents will run sequentially"
        )

        logger.info(
            "Execution plan: %d tasks enabled, %d disabled | parallel=%s",
            sum(1 for t in tasks if t.enabled),
            sum(1 for t in tasks if not t.enabled),
            parallel_supported,
        )

        return ExecutionPlan(
            session_id=session_id,
            repository_path=context.repository_path,
            tasks=tasks,
            parallel_supported=parallel_supported,
            notes=notes,
        )
