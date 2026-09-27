"""
Workflows router — /api/v1/workflows
"""
from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.schemas import (
    AgentSource,
    AgentStepOut,
    ApprovalRequest,
    CodeDiffOut,
    FindingLocationOut,
    FindingOut,
    FindingSeverity,
    FindingStatus,
    FixProposalOut,
    ProductivityMetricsOut,
    ReportOut,
    ReportSectionOut,
    StartWorkflowRequest,
    TestMetricsOut,
    WorkflowRunOut,
    WorkflowStatus,
)
from app.api.store import (
    store,
    get_repository,
    get_workflow,
    list_workflows,
    save_workflow,
    save_repository,
    get_report_by_workflow,
)
from app.api.routers.auth import get_current_user
from app.db.models import UserDoc
from app.api.ws_broker import ws_broker
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/workflows", tags=["Workflows"])

# Ordered pipeline step definitions — mirrors WorkflowStage
_PIPELINE_STEPS = [
    ("inspecting",        "Repository Inspection"),
    ("planning",          "Task Planning"),
    ("analyzing",         "Code Analysis"),
    ("aggregating",       "Finding Aggregation"),
    ("prioritizing",      "Issue Prioritization"),
    ("fix_planning",      "Fix Planning"),
    ("awaiting_approval", "Human Approval"),
    ("modifying",         "Code Modification"),
    ("generating_tests",  "Test Generation"),
    ("running_tests",     "Test Execution"),
    ("analyzing_failures","Failure Analysis"),
    ("reporting",         "Report Generation"),
]

# map backend fix_risk → frontend risk label
_RISK_MAP = {"safe": "low", "moderate": "medium", "high": "high", "not_applicable": "low"}
# map backend severity → frontend severity
_SEV_MAP  = {"critical": FindingSeverity.CRITICAL, "high": FindingSeverity.HIGH,
             "medium": FindingSeverity.MEDIUM, "low": FindingSeverity.LOW}
# map backend source_agent → frontend AgentSource
_AGENT_MAP = {
    "code_review": AgentSource.CODE_REVIEW,
    "test_analysis": AgentSource.TEST_ANALYSIS,
    "security": AgentSource.SECURITY,
    "documentation": AgentSource.DOCUMENTATION,
}


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _make_steps(status: WorkflowStatus = WorkflowStatus.PENDING) -> list[AgentStepOut]:
    return [
        AgentStepOut(id=step_id, name=step_id, label=label, status=status)
        for step_id, label in _PIPELINE_STEPS
    ]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[WorkflowRunOut])
async def list_workflows_route(
    repositoryId: str | None = None,
    current_user: UserDoc = Depends(get_current_user),
) -> list[WorkflowRunOut]:
    return await list_workflows(owner_id=str(current_user.id), repository_id=repositoryId)


def _resolve_repo_path(run_id: str, url: str) -> str:
    """Return a local filesystem path suitable for the orchestrator.

    * If *url* is already a local path that exists, return it as-is.
    * If *url* looks like a remote Git URL (http/https/git@), clone it into
      /app/repos/<run_id> and return that path.

    Raises RuntimeError on clone failure.
    """
    # Detect remote URLs: http(s):// or git@ SSH
    is_remote = url.startswith(("http://", "https://", "git@", "git://", "ssh://"))
    if not is_remote:
        return url  # local path — hand straight through

    clone_dir = Path("/app/repos") / run_id
    clone_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Cloning %s → %s", url, clone_dir)
    try:
        import git  # GitPython
        git.Repo.clone_from(url, clone_dir, depth=1)
    except Exception as exc:
        # Remove the (possibly partially-populated) directory so retries are clean
        import shutil
        shutil.rmtree(clone_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to clone {url}: {exc}") from exc
    return str(clone_dir)


@router.post("", response_model=WorkflowRunOut, status_code=201)
async def start_workflow(
    body: StartWorkflowRequest,
    current_user: UserDoc = Depends(get_current_user),
) -> WorkflowRunOut:
    owner_id = str(current_user.id)
    repo = await get_repository(body.repositoryId, owner_id=owner_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")

    run_id = str(uuid.uuid4())
    now = _now()

    run = WorkflowRunOut(
        id=run_id,
        repositoryId=repo.id,
        repositoryName=repo.name,
        status=WorkflowStatus.RUNNING,
        createdAt=now,
        updatedAt=now,
        steps=_make_steps(WorkflowStatus.PENDING),
        currentStep="inspecting",
    )
    await save_workflow(run, owner_id=owner_id)

    updated_repo = repo.model_copy(update={"status": "analyzing", "updatedAt": now})
    await save_repository(updated_repo, owner_id=owner_id)

    store.set_owner(owner_id)
    thread = threading.Thread(target=_run_orchestrator, args=(run_id, repo.url), daemon=True)
    thread.start()

    logger.info("Workflow %s started for repository %s", run_id, repo.name)
    return run


@router.get("/{workflow_id}", response_model=WorkflowRunOut)
async def get_workflow_route(
    workflow_id: str,
    current_user: UserDoc = Depends(get_current_user),
) -> WorkflowRunOut:
    run = await get_workflow(workflow_id, owner_id=str(current_user.id))
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return run


@router.post("/{workflow_id}/steps/{step_id}/approval", status_code=200)
async def submit_approval(
    workflow_id: str,
    step_id: str,
    body: ApprovalRequest,
    current_user: UserDoc = Depends(get_current_user),
) -> dict[str, str]:
    owner_id = str(current_user.id)
    run = await get_workflow(workflow_id, owner_id=owner_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    updated_steps = []
    for step in run.steps:
        if step.id == step_id:
            updated_steps.append(step.model_copy(update={
                "status": WorkflowStatus.COMPLETED if body.approved else WorkflowStatus.SKIPPED,
                "completedAt": _now(),
                "message": body.note or ("Approved" if body.approved else "Rejected"),
            }))
        else:
            updated_steps.append(step)

    updated_run = run.model_copy(update={"steps": updated_steps, "updatedAt": _now()})
    await save_workflow(updated_run, owner_id=owner_id)

    logger.info("Approval for workflow %s step %s: %s", workflow_id, step_id, body.approved)
    return {"status": "recorded"}


@router.get("/{workflow_id}/report", response_model=ReportOut)
async def get_workflow_report(
    workflow_id: str,
    current_user: UserDoc = Depends(get_current_user),
) -> ReportOut:
    report = await get_report_by_workflow(workflow_id, owner_id=str(current_user.id))
    if report is None:
        raise HTTPException(status_code=404, detail="Report not available yet")
    return report


# ---------------------------------------------------------------------------
# Background orchestrator runner
# ---------------------------------------------------------------------------

def _run_orchestrator(run_id: str, repo_path: str) -> None:
    """Execute the full DevFlow AI pipeline and update the store."""
    from app.services.orchestrator import Orchestrator, OrchestratorError

    def _set_step(step_id: str, status: WorkflowStatus, **kwargs: Any) -> None:
        run = store.get_workflow(run_id)
        if run is None:
            return
        updated_steps = []
        changed_step = None
        for step in run.steps:
            if step.id == step_id:
                update: dict[str, Any] = {"status": status}
                if status == WorkflowStatus.RUNNING:
                    update["startedAt"] = _now()
                elif status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED):
                    update["completedAt"] = _now()
                update.update(kwargs)
                changed_step = step.model_copy(update=update)
                updated_steps.append(changed_step)
            else:
                updated_steps.append(step)
        updated_run = run.model_copy(update={
            "steps": updated_steps,
            "currentStep": step_id,
            "updatedAt": _now(),
        })
        store.set_workflow(updated_run)
        # Broadcast step change to any connected WebSocket clients.
        if changed_step is not None:
            ws_broker.publish(run_id, {
                "type": "step_update",
                "workflowId": run_id,
                "step": changed_step.model_dump(),
                "timestamp": _now(),
            })
        ws_broker.publish(run_id, {
            "type": "workflow_update",
            "workflowId": run_id,
            "workflow": updated_run.model_dump(),
            "timestamp": _now(),
        })

    def _set_run_status(status: WorkflowStatus, **kwargs: Any) -> None:
        run = store.get_workflow(run_id)
        if run is None:
            return
        update: dict[str, Any] = {"status": status, "updatedAt": _now()}
        if status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED):
            update["completedAt"] = _now()
        update.update(kwargs)
        updated_run = run.model_copy(update=update)
        store.set_workflow(updated_run)
        # Broadcast run status change to any connected WebSocket clients.
        ws_broker.publish(run_id, {
            "type": "workflow_update",
            "workflowId": run_id,
            "workflow": updated_run.model_dump(),
            "timestamp": _now(),
        })

    try:
        # Resolve the repo path — clones GitHub URLs into /app/repos/<run_id>
        local_path = _resolve_repo_path(run_id, repo_path)

        # Mark first step running
        _set_step("inspecting", WorkflowStatus.RUNNING)

        orch = Orchestrator(local_path, decisions={})

        # Monkey-patch _transition so we can update step statuses live
        original_transition = orch._transition  # noqa: SLF001

        # Map WorkflowStage values → our step IDs
        _stage_to_step = {
            "inspecting":         "inspecting",
            "planning":           "planning",
            "analyzing":          "analyzing",
            "aggregating":        "aggregating",
            "prioritizing":       "prioritizing",
            "fix_planning":       "fix_planning",
            "awaiting_approval":  "awaiting_approval",
            "modifying":          "modifying",
            "generating_tests":   "generating_tests",
            "running_tests":      "running_tests",
            "analyzing_failures": "analyzing_failures",
            "reporting":          "reporting",
        }
        _prev_step: list[str] = ["inspecting"]

        def _patched_transition(stage):  # type: ignore[no-untyped-def]
            original_transition(stage)
            step_id = _stage_to_step.get(stage.value)
            prev = _prev_step[0]
            if prev and prev != step_id:
                _set_step(prev, WorkflowStatus.COMPLETED)
            if step_id:
                _set_step(step_id, WorkflowStatus.RUNNING)
                _prev_step[0] = step_id

        orch._transition = _patched_transition  # type: ignore[method-assign]  # noqa: SLF001

        result = orch.run()

        # Mark last step done
        if _prev_step[0]:
            _set_step(_prev_step[0], WorkflowStatus.COMPLETED)

        # Ingest findings into store
        _ingest_findings(run_id, orch, result)

        # Build report
        _build_report(run_id, orch, result)

        _set_run_status(
            WorkflowStatus.COMPLETED,
            totalFindings=result.get("prioritized_findings", 0),
            fixedFindings=result.get("applied_fixes", 0),
            testsGenerated=result.get("generated_tests", 0),
            testsPassed=result.get("tests_passed", 0),
        )

        # Update repository status
        run_out = store.get_workflow(run_id)
        if run_out:
            repo = store.get_repo(run_out.repositoryId)
            if repo:
                store.set_repo(repo.model_copy(update={
                    "status": "analyzed",
                    "lastAnalyzedAt": _now(),
                    "lastWorkflowId": run_id,
                    "workflowCount": repo.workflowCount + 1,
                    "updatedAt": _now(),
                }))

        logger.info("Workflow %s completed", run_id)

    except (OrchestratorError, Exception) as exc:
        logger.error("Workflow %s failed: %s", run_id, exc)
        _set_run_status(WorkflowStatus.FAILED, currentStep=None)
        run = store.get_workflow(run_id)
        if run:
            updated_steps = [
                s.model_copy(update={
                    "status": WorkflowStatus.FAILED,
                    "errorMessage": str(exc),
                    "completedAt": _now(),
                }) if s.status == WorkflowStatus.RUNNING else s
                for s in run.steps
            ]
            store.set_workflow(run.model_copy(update={"steps": updated_steps}))


def _ingest_findings(run_id: str, orch: Any, result: dict[str, Any]) -> None:
    """Read prioritized_findings.json and load into the store."""
    import json

    session_dir = Path(result.get("project_context", "")).parent
    pf_path = session_dir / "prioritized_findings.json"
    approved_path = session_dir / "approved_fix_plan.json"
    app_log_path = session_dir / "fix_application_log.json"

    if not pf_path.exists():
        return

    try:
        raw_findings = json.loads(pf_path.read_text(encoding="utf-8"))
    except Exception:
        return

    # Build approved/applied maps from fix plan
    approved_ids: set[str] = set()
    applied_ids: set[str] = set()
    proposals_by_id: dict[str, Any] = {}

    if approved_path.exists():
        try:
            for p in json.loads(approved_path.read_text(encoding="utf-8")):
                fid = p.get("finding_id", "")
                proposals_by_id[fid] = p
                if p.get("status") == "approved":
                    approved_ids.add(fid)
        except Exception:
            pass

    if app_log_path.exists():
        try:
            for entry in json.loads(app_log_path.read_text(encoding="utf-8")):
                if entry.get("outcome") == "APPLIED":
                    applied_ids.add(entry.get("finding_id", ""))
        except Exception:
            pass

    now = _now()
    finding_ids: list[str] = []

    for raw in raw_findings:
        fid_backend = raw.get("id", "")
        fe_id = f"{run_id}_{fid_backend}"

        # Map status
        if fid_backend in applied_ids:
            status = FindingStatus.FIXED
        elif fid_backend in approved_ids:
            status = FindingStatus.PENDING_FIX
        else:
            status = FindingStatus.OPEN

        # Map severity
        sev_raw = raw.get("severity", "low")
        severity = _SEV_MAP.get(sev_raw, FindingSeverity.LOW)

        # Map agent
        agent_raw = raw.get("source_agent", "code_review")
        agent = _AGENT_MAP.get(agent_raw, AgentSource.CODE_REVIEW)

        # Parse location
        location_raw = raw.get("location", "")
        line: int | None = None
        if isinstance(location_raw, str):
            import re
            m = re.search(r"\d+", location_raw)
            if m:
                line = int(m.group())

        location = FindingLocationOut(file=raw.get("file", ""), line=line)

        # Build fix proposal if one exists
        fix_proposal: FixProposalOut | None = None
        p = proposals_by_id.get(fid_backend)
        if p:
            diff_str = p.get("diff", "")
            diff_out = None
            if diff_str:
                # Split unified diff into before/after blocks for display
                before_lines, after_lines = [], []
                for line_str in diff_str.splitlines():
                    if line_str.startswith("-") and not line_str.startswith("---"):
                        before_lines.append(line_str[1:])
                    elif line_str.startswith("+") and not line_str.startswith("+++"):
                        after_lines.append(line_str[1:])
                diff_out = CodeDiffOut(
                    before="\n".join(before_lines),
                    after="\n".join(after_lines),
                    language="python",
                )
            risk_raw = p.get("fix_risk", "safe")
            fix_proposal = FixProposalOut(
                id=f"fp_{fe_id}",
                findingId=fe_id,
                description=p.get("description", ""),
                reason=p.get("rationale", ""),
                risk=_RISK_MAP.get(risk_raw, "low"),
                diff=diff_out,
                affectedFiles=p.get("files_affected", []),
                approvedAt=now if fid_backend in approved_ids else None,
            )

        finding = FindingOut(
            id=fe_id,
            workflowId=run_id,
            severity=severity,
            status=status,
            agent=agent,
            title=raw.get("title", ""),
            description=raw.get("explanation", ""),
            location=location,
            evidence=raw.get("file", ""),
            whyItMatters=raw.get("impact", ""),
            suggestedFix=raw.get("recommended_fix", ""),
            verificationMethod=raw.get("verification_method", ""),
            fixProposal=fix_proposal,
            createdAt=now,
            updatedAt=now,
        )
        store.set_finding(finding)
        finding_ids.append(fe_id)


def _build_report(run_id: str, orch: Any, result: dict[str, Any]) -> None:
    """Build a ReportOut from the session artefacts and persist to store."""
    import json

    session_dir = Path(result.get("project_context", "")).parent
    report_id = str(uuid.uuid4())
    now = _now()

    run = store.get_workflow(run_id)
    if run is None:
        return

    repo = store.get_repo(run.repositoryId)
    repo_name = repo.name if repo else ""
    repo_url = repo.url if repo else ""

    # Severity breakdown
    finding_ids = store.get_finding_ids(run_id)
    sev_counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for fid in finding_ids:
        f = store.get_finding(fid)
        if f:
            sev_counts[f.severity.value] = sev_counts.get(f.severity.value, 0) + 1

    # Test metrics
    test_results: dict[str, Any] = {}
    tr_path = session_dir / "test_results_post_fix.json"
    if tr_path.exists():
        try:
            test_results = json.loads(tr_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    testing = TestMetricsOut(
        beforeCount=0,
        generatedCount=int(result.get("generated_tests", 0)),
        afterCount=int(result.get("generated_tests", 0)),
        passed=int(test_results.get("passed", 0)),
        failed=int(test_results.get("failed", 0)),
        skipped=int(test_results.get("skipped", 0)),
    )

    # Context info
    ctx: dict[str, Any] = {}
    ctx_path = session_dir / "project_context.json"
    if ctx_path.exists():
        try:
            ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    productivity = ProductivityMetricsOut(
        issuesDetected=int(result.get("prioritized_findings", 0)),
        issuesFixed=int(result.get("applied_fixes", 0)),
        testsGenerated=int(result.get("generated_tests", 0)),
        automatedSteps=8,
        manualSteps=11,
    )

    sections = ReportSectionOut(
        repository={
            "name": repo_name,
            "url": repo_url,
            "technologies": [ctx.get("detected_language", "python")],
            "filesAnalyzed": len(ctx.get("source_files", [])),
            "branch": "main",
        },
        analysis={
            "totalIssues": len(finding_ids),
            "severityBreakdown": sev_counts,
            "agentsUsed": ["code_review", "test_analysis", "security", "documentation"],
            "durationSeconds": 0,
        },
        remediation={
            "issuesFixed": int(result.get("applied_fixes", 0)),
            "filesModified": int(result.get("applied_fixes", 0)),
            "developerApprovals": 0,
        },
        testing=testing,
        productivity=productivity,
    )

    report_path = result.get("report", "")
    download_url = f"/api/v1/reports/{report_id}/download" if report_path else None

    report = ReportOut(
        id=report_id,
        workflowId=run_id,
        repositoryId=run.repositoryId,
        repositoryName=repo_name,
        generatedAt=now,
        sections=sections,
        downloadUrl=download_url,
    )
    store.set_report(report)
