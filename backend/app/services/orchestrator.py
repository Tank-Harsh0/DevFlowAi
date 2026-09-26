"""
Orchestrator.

The main workflow state machine. Coordinates all pipeline stages.

Phase 5 additions:
  - FIX_PLANNING stage: FixPlanner generates fix_plan.json.
  - AWAITING_APPROVAL stage: ApprovalGate records decisions → approved_fix_plan.json.
  - MODIFYING stage: CodeModifier applies approved diffs → fix_application_log.json.
  - decisions param on Orchestrator.__init__ for non-interactive (test) use.
"""
from __future__ import annotations

from app.agents.code_review import CodeReviewAgent
from app.agents.documentation import DocumentationAgent
from app.agents.security import SecurityAgent
from app.agents.test_analysis import TestingAnalysisAgent
from app.core.logging import get_logger
from app.models.finding import Finding, SecurityAgentOutput
from app.models.fix_proposal import FixProposal, ProposalStatus
from app.models.workflow import ExecutionPlan, ProjectContext, WorkflowStage, WorkflowState
from app.services.approval_gate import ApprovalGate
from app.services.code_modifier import CodeModifier
from app.services.finding_aggregator import FindingAggregator
from app.services.fix_planner import FixPlanner
from app.services.issue_prioritizer import IssuePrioritizer
from app.services.repository_inspector import RepositoryInspector
from app.services.session_manager import SessionManager
from app.services.task_planner import TaskPlanner

logger = get_logger(__name__)


class OrchestratorError(Exception):
    """Raised when the orchestrator cannot continue."""


class Orchestrator:
    """Manages a single DevFlow AI workflow run.

    Usage::

        orchestrator = Orchestrator("/path/to/repo")
        result = orchestrator.run()
    """

    def __init__(
        self,
        repository_path: str,
        decisions: dict[str, ProposalStatus] | None = None,
    ) -> None:
        """Create an Orchestrator.

        Args:
            repository_path: Absolute or relative path to the target repository.
            decisions:       Optional pre-supplied approval decisions keyed by
                             finding_id.  When None, the gate prompts stdin
                             (interactive mode).  Pass a dict for non-interactive
                             use (tests, API).
        """
        self._repo_path = repository_path
        self._session = SessionManager.new()
        self._state = WorkflowState(
            session_id=self._session.session_id,
            stage=WorkflowStage.IDLE,
            repository_path=repository_path,
        )
        self._inspector = RepositoryInspector()
        self._planner = TaskPlanner()
        self._aggregator = FindingAggregator()
        self._prioritizer = IssuePrioritizer()
        self._fix_planner = FixPlanner()
        self._approval_gate = ApprovalGate(decisions=decisions)
        self._agents = {
            "code_review": CodeReviewAgent(),
            "test_analysis": TestingAnalysisAgent(),
            "security": SecurityAgent(),
            "documentation": DocumentationAgent(),
        }

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> WorkflowState:
        return self._state

    @property
    def session_id(self) -> str:
        return self._session.session_id

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> dict[str, object]:
        """Execute the full pipeline through remediation.

        Returns a summary dict with session_id, stage, artefact paths, and counts.
        Raises OrchestratorError if any stage fails.
        """
        self._session.create()
        try:
            context       = self._run_inspection()
            plan          = self._run_planning(context)
            raw_findings  = self._run_agents(context, plan)
            dedup         = self._run_aggregation(raw_findings)
            prioritized   = self._run_prioritization(dedup)
            proposals     = self._run_fix_planning(prioritized, context)
            approved      = self._run_approval(proposals)
            applied       = self._run_modification(approved)
            self._transition(WorkflowStage.COMPLETE)
            return {
                "session_id": self.session_id,
                "stage": self._state.stage.value,
                "project_context": str(self._session.session_dir / "project_context.json"),
                "execution_plan": str(self._session.session_dir / "execution_plan.json"),
                "raw_findings": len(raw_findings),
                "deduplicated_findings": len(dedup),
                "prioritized_findings": len(prioritized),
                "proposals": len(proposals),
                "approved_fixes": sum(
                    1 for p in approved if p.status == ProposalStatus.APPROVED
                ),
                "applied_fixes": sum(
                    1 for p in applied if p.status == ProposalStatus.APPLIED
                ),
            }
        except OrchestratorError:
            raise
        except Exception as exc:
            self._fail(str(exc))
            raise OrchestratorError(str(exc)) from exc
        finally:
            self._session.close()

    # ------------------------------------------------------------------
    # Stage runners
    # ------------------------------------------------------------------

    def _run_inspection(self) -> ProjectContext:
        self._transition(WorkflowStage.INSPECTING)
        self._session.log(
            "INFO", "Orchestrator", f"Repository Inspector starting: {self._repo_path}"
        )

        context = self._inspector.inspect(self._repo_path)

        # Persist to session directory
        self._session.write_json("project_context.json", context.model_dump())
        self._session.log(
            "INFO", "Orchestrator",
            f"Repository Inspector complete: {len(context.source_files)} source, "
            f"{len(context.test_files)} test, {len(context.doc_files)} doc files | "
            f"lang={context.detected_language} framework={context.detected_test_framework}",
        )
        return context

    def _run_agents(
        self, context: ProjectContext, plan: ExecutionPlan
    ) -> list[Finding]:
        """Run each enabled agent sequentially and persist findings to disk.

        ARCHITECTURE.md §7: parallel dispatch not yet validated against IBM Bob 2.0.
        Sequential fallback is documented in the session log.
        """
        self._transition(WorkflowStage.ANALYZING)
        self._session.log(
            "INFO", "Orchestrator",
            "Agent dispatch starting (sequential — IBM Bob 2.0 parallel API unverified)",
        )

        all_findings: list[Finding] = []

        # File names per agent
        output_files = {
            "code_review": "findings_code.json",
            "test_analysis": "findings_tests.json",
            "security": "findings_security.json",
            "documentation": "findings_docs.json",
        }

        for task in plan.tasks:
            if not task.enabled:
                self._session.log(
                    "INFO", "Orchestrator",
                    f"Skipping agent {task.agent}: {task.skip_reason}",
                )
                continue

            agent = self._agents.get(task.agent)
            if agent is None:
                self._session.log(
                    "WARNING", "Orchestrator",
                    f"No implementation for agent '{task.agent}' — skipped",
                )
                continue

            self._session.log("INFO", task.agent, f"Agent {task.agent} starting")
            findings = agent.safe_analyze(context)
            self._session.log(
                "INFO", task.agent,
                f"Agent {task.agent} complete: {len(findings)} finding(s)",
            )

            # Security output requires the mandatory disclaimer wrapper
            if task.agent == "security":
                wrapped = SecurityAgentOutput(findings=findings)
                self._session.write_json(
                    output_files[task.agent], wrapped.model_dump()
                )
            else:
                self._session.write_json(
                    output_files[task.agent],
                    [f.model_dump() for f in findings],
                )

            all_findings.extend(findings)

        self._session.log(
            "INFO", "Orchestrator",
            f"All agents complete. Total findings: {len(all_findings)}",
        )
        return all_findings

    def _run_aggregation(self, raw_findings: list[Finding]) -> list[Finding]:
        """AGGREGATING stage — merge and deduplicate findings."""
        self._transition(WorkflowStage.AGGREGATING)
        self._session.log("INFO", "Orchestrator", "Finding Aggregator starting")

        dedup = self._aggregator.aggregate(raw_findings)

        self._session.write_json(
            "deduplicated_findings.json", [f.model_dump() for f in dedup]
        )
        self._session.log(
            "INFO", "Orchestrator",
            f"Aggregation complete: {len(raw_findings)} raw → {len(dedup)} deduplicated",
        )
        return dedup

    def _run_prioritization(self, dedup_findings: list[Finding]) -> list[Finding]:
        """PRIORITIZING stage — sort by severity."""
        self._transition(WorkflowStage.PRIORITIZING)
        self._session.log("INFO", "Orchestrator", "Issue Prioritizer starting")

        prioritized = self._prioritizer.prioritize(dedup_findings)

        self._session.write_json(
            "prioritized_findings.json", [f.model_dump() for f in prioritized]
        )
        self._session.log(
            "INFO", "Orchestrator",
            f"Prioritization complete: {len(prioritized)} findings ordered by severity",
        )
        return prioritized

    def _run_fix_planning(
        self, prioritized: list[Finding], context: ProjectContext
    ) -> list[FixProposal]:
        """FIX_PLANNING stage — generate proposals for each actionable finding."""
        self._transition(WorkflowStage.FIX_PLANNING)
        self._session.log("INFO", "Orchestrator", "Fix Planner starting")

        proposals = self._fix_planner.plan(prioritized, context.file_contents)

        self._session.write_json(
            "fix_plan.json", [p.model_dump() for p in proposals]
        )
        self._session.log(
            "INFO", "Orchestrator",
            f"Fix Planner complete: {len(proposals)} proposals generated",
        )
        return proposals

    def _run_approval(self, proposals: list[FixProposal]) -> list[FixProposal]:
        """AWAITING_APPROVAL stage — collect developer decisions."""
        self._transition(WorkflowStage.AWAITING_APPROVAL)
        self._session.log("INFO", "Orchestrator", "Approval Gate starting")

        approved = self._approval_gate.review(proposals)

        self._session.write_json(
            "approved_fix_plan.json", [p.model_dump() for p in approved]
        )
        n_approved = sum(1 for p in approved if p.status == ProposalStatus.APPROVED)
        self._session.log(
            "DECISION", "Orchestrator",
            f"Approval Gate complete: {n_approved}/{len(approved)} approved",
        )
        return approved

    def _run_modification(
        self, approved: list[FixProposal]
    ) -> list[FixProposal]:
        """MODIFYING stage — apply approved diffs with backup + syntax check."""
        self._transition(WorkflowStage.MODIFYING)
        self._session.log("INFO", "Orchestrator", "Code Modifier starting")

        modifier = CodeModifier(self._repo_path)
        updated, log = modifier.apply_approved(approved)

        self._session.write_json("fix_application_log.json", log)
        n_applied = sum(1 for p in updated if p.status == ProposalStatus.APPLIED)
        n_failed  = sum(1 for p in updated if p.status == ProposalStatus.FAILED)
        self._session.log(
            "CHANGE", "Orchestrator",
            f"Code Modifier complete: {n_applied} applied, {n_failed} failed",
        )
        return updated

    def _run_planning(self, context: ProjectContext) -> ExecutionPlan:
        self._transition(WorkflowStage.PLANNING)
        self._session.log("INFO", "Orchestrator", "Task Planner starting")

        plan = self._planner.plan(self._session.session_id, context)

        self._session.write_json("execution_plan.json", plan.model_dump())
        enabled = [t.agent for t in plan.tasks if t.enabled]
        disabled = [t.agent for t in plan.tasks if not t.enabled]
        self._session.log(
            "DECISION", "Orchestrator",
            f"Execution plan: enabled={enabled} disabled={disabled} "
            f"parallel={plan.parallel_supported}",
        )
        return plan

    # ------------------------------------------------------------------
    # State machine helpers
    # ------------------------------------------------------------------

    def _transition(self, stage: WorkflowStage) -> None:
        previous = self._state.stage
        self._state.stage = stage
        logger.info(
            "Stage transition: %s → %s  (session=%s)", previous.value, stage.value, self.session_id
        )

    def _fail(self, reason: str) -> None:
        self._state.stage = WorkflowStage.FAILED
        self._state.error = reason
        self._session.log("ERROR", "Orchestrator", f"Workflow failed: {reason}")
        logger.error("Workflow %s failed: %s", self.session_id, reason)
