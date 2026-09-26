"""
Beanie-backed async CRUD helpers.

All public functions are async and use the Beanie Document API directly.
The `_BGStore` singleton is kept for the background orchestrator thread,
which runs synchronous code and calls these helpers via asyncio.run_coroutine_threadsafe.
"""
from __future__ import annotations

import asyncio
from typing import Any

from app.api.schemas import (
    AgentStepOut,
    CodeDiffOut,
    FindingLocationOut,
    FindingOut,
    FindingSeverity,
    FindingStatus,
    FixProposalOut,
    ProductivityMetricsOut,
    ReportOut,
    ReportSectionOut,
    RepositoryOut,
    RepositoryStatus,
    TestMetricsOut,
    WorkflowRunOut,
    WorkflowStatus,
)
from app.db.models import (
    FindingDoc,
    RepositoryDoc,
    ReportDoc,
    WorkflowRunDoc,
)


# ---------------------------------------------------------------------------
# Serialisation helpers  (Document → Pydantic schema)
# ---------------------------------------------------------------------------

def _repo_to_out(doc: RepositoryDoc) -> RepositoryOut:
    return RepositoryOut(
        id=doc.repo_id,
        name=doc.name,
        url=doc.url,
        description=doc.description,
        defaultBranch=doc.default_branch,
        language=doc.language,
        languages=doc.languages,
        status=RepositoryStatus(doc.status),
        lastAnalyzedAt=doc.last_analyzed_at,
        createdAt=doc.created_at,
        updatedAt=doc.updated_at,
        workflowCount=doc.workflow_count,
        lastWorkflowId=doc.last_workflow_id,
    )


def _workflow_to_out(doc: WorkflowRunDoc) -> WorkflowRunOut:
    steps = [AgentStepOut(**s) for s in doc.steps]
    return WorkflowRunOut(
        id=doc.run_id,
        repositoryId=doc.repository_id,
        repositoryName=doc.repository_name,
        status=WorkflowStatus(doc.status),
        createdAt=doc.created_at,
        updatedAt=doc.updated_at,
        completedAt=doc.completed_at,
        steps=steps,
        totalFindings=doc.total_findings,
        fixedFindings=doc.fixed_findings,
        testsGenerated=doc.tests_generated,
        testsPassed=doc.tests_passed,
        currentStep=doc.current_step,
    )


def _finding_to_out(doc: FindingDoc) -> FindingOut:
    location = FindingLocationOut(**doc.location) if doc.location else FindingLocationOut(file="")

    fix_proposal: FixProposalOut | None = None
    if doc.fix_proposal:
        fp = dict(doc.fix_proposal)
        diff_raw = fp.pop("diff", None)
        diff_out = CodeDiffOut(**diff_raw) if diff_raw else None
        fix_proposal = FixProposalOut(diff=diff_out, **fp)

    return FindingOut(
        id=doc.finding_id,
        workflowId=doc.workflow_id,
        severity=FindingSeverity(doc.severity),
        status=FindingStatus(doc.status),
        agent=doc.agent,  # type: ignore[arg-type]
        title=doc.title,
        description=doc.description,
        location=location,
        evidence=doc.evidence,
        whyItMatters=doc.why_it_matters,
        suggestedFix=doc.suggested_fix,
        verificationMethod=doc.verification_method,
        fixProposal=fix_proposal,
        createdAt=doc.created_at,
        updatedAt=doc.updated_at,
    )


def _report_to_out(doc: ReportDoc) -> ReportOut:
    s = doc.sections
    testing_raw = s.get("testing", {})
    prod_raw = s.get("productivity", {})
    sections = ReportSectionOut(
        repository=s.get("repository", {}),
        analysis=s.get("analysis", {}),
        remediation=s.get("remediation", {}),
        testing=TestMetricsOut(**testing_raw) if testing_raw else TestMetricsOut(),
        productivity=ProductivityMetricsOut(**prod_raw) if prod_raw else ProductivityMetricsOut(),
    )
    return ReportOut(
        id=doc.report_id,
        workflowId=doc.workflow_id,
        repositoryId=doc.repository_id,
        repositoryName=doc.repository_name,
        generatedAt=doc.generated_at,
        sections=sections,
        downloadUrl=doc.download_url,
    )


# ---------------------------------------------------------------------------
# Repository CRUD
# ---------------------------------------------------------------------------

async def list_repositories() -> list[RepositoryOut]:
    docs = await RepositoryDoc.find_all().to_list()
    return [_repo_to_out(d) for d in docs]


async def get_repository(repo_id: str) -> RepositoryOut | None:
    doc = await RepositoryDoc.find_one(RepositoryDoc.repo_id == repo_id)
    return _repo_to_out(doc) if doc else None


async def save_repository(out: RepositoryOut) -> None:
    doc = await RepositoryDoc.find_one(RepositoryDoc.repo_id == out.id)
    data: dict[str, Any] = dict(
        repo_id=out.id,
        name=out.name,
        url=out.url,
        description=out.description,
        default_branch=out.defaultBranch or "main",
        language=out.language,
        languages=out.languages,
        status=out.status.value if hasattr(out.status, "value") else out.status,
        last_analyzed_at=out.lastAnalyzedAt,
        created_at=out.createdAt,
        updated_at=out.updatedAt,
        workflow_count=out.workflowCount,
        last_workflow_id=out.lastWorkflowId,
    )
    if doc is None:
        await RepositoryDoc(**data).insert()
    else:
        await doc.set(data)


async def delete_repository(repo_id: str) -> bool:
    doc = await RepositoryDoc.find_one(RepositoryDoc.repo_id == repo_id)
    if doc is None:
        return False
    await doc.delete()
    return True


# ---------------------------------------------------------------------------
# Workflow CRUD
# ---------------------------------------------------------------------------

async def list_workflows(repository_id: str | None = None) -> list[WorkflowRunOut]:
    query = WorkflowRunDoc.find_all() if not repository_id else \
        WorkflowRunDoc.find(WorkflowRunDoc.repository_id == repository_id)
    docs = await query.sort(-WorkflowRunDoc.created_at).to_list()
    return [_workflow_to_out(d) for d in docs]


async def get_workflow(workflow_id: str) -> WorkflowRunOut | None:
    doc = await WorkflowRunDoc.find_one(WorkflowRunDoc.run_id == workflow_id)
    return _workflow_to_out(doc) if doc else None


async def save_workflow(out: WorkflowRunOut) -> None:
    doc = await WorkflowRunDoc.find_one(WorkflowRunDoc.run_id == out.id)
    data: dict[str, Any] = dict(
        run_id=out.id,
        repository_id=out.repositoryId,
        repository_name=out.repositoryName,
        status=out.status.value if hasattr(out.status, "value") else out.status,
        created_at=out.createdAt,
        updated_at=out.updatedAt,
        completed_at=out.completedAt,
        steps=[s.model_dump() for s in out.steps],
        total_findings=out.totalFindings,
        fixed_findings=out.fixedFindings,
        tests_generated=out.testsGenerated,
        tests_passed=out.testsPassed,
        current_step=out.currentStep,
    )
    if doc is None:
        await WorkflowRunDoc(**data).insert()
    else:
        await doc.set(data)


# ---------------------------------------------------------------------------
# Finding CRUD
# ---------------------------------------------------------------------------

async def list_findings(
    workflow_id: str | None = None,
    severity: str | None = None,
    agent: str | None = None,
    status: str | None = None,
    file: str | None = None,
) -> list[FindingOut]:
    conditions = []
    if workflow_id:
        conditions.append(FindingDoc.workflow_id == workflow_id)
    if severity:
        conditions.append(FindingDoc.severity == severity)
    if agent:
        conditions.append(FindingDoc.agent == agent)
    if status:
        conditions.append(FindingDoc.status == status)

    docs = await (FindingDoc.find(*conditions) if conditions else FindingDoc.find_all()).to_list()
    outs = [_finding_to_out(d) for d in docs]
    if file:
        outs = [f for f in outs if file in f.location.file]
    return sorted(outs, key=lambda f: (
        {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(f.severity.value, 9),
        f.createdAt,
    ))


async def get_finding(finding_id: str) -> FindingOut | None:
    doc = await FindingDoc.find_one(FindingDoc.finding_id == finding_id)
    return _finding_to_out(doc) if doc else None


async def save_finding(out: FindingOut) -> None:
    doc = await FindingDoc.find_one(FindingDoc.finding_id == out.id)
    fp_dict: dict[str, Any] | None = None
    if out.fixProposal:
        fp_dict = out.fixProposal.model_dump()

    data: dict[str, Any] = dict(
        finding_id=out.id,
        workflow_id=out.workflowId,
        severity=out.severity.value if hasattr(out.severity, "value") else out.severity,
        status=out.status.value if hasattr(out.status, "value") else out.status,
        agent=out.agent.value if hasattr(out.agent, "value") else out.agent,
        title=out.title,
        description=out.description,
        location=out.location.model_dump(),
        evidence=out.evidence,
        why_it_matters=out.whyItMatters,
        suggested_fix=out.suggestedFix,
        verification_method=out.verificationMethod,
        fix_proposal=fp_dict,
        created_at=out.createdAt,
        updated_at=out.updatedAt,
    )
    if doc is None:
        await FindingDoc(**data).insert()
    else:
        await doc.set(data)


async def get_finding_ids(workflow_id: str) -> list[str]:
    docs = await FindingDoc.find(
        FindingDoc.workflow_id == workflow_id,
    ).project(FindingDoc).to_list()
    return [d.finding_id for d in docs]


# ---------------------------------------------------------------------------
# Report CRUD
# ---------------------------------------------------------------------------

async def list_reports() -> list[ReportOut]:
    docs = await ReportDoc.find_all().sort(-ReportDoc.generated_at).to_list()
    return [_report_to_out(d) for d in docs]


async def get_report(report_id: str) -> ReportOut | None:
    doc = await ReportDoc.find_one(ReportDoc.report_id == report_id)
    return _report_to_out(doc) if doc else None


async def get_report_by_workflow(workflow_id: str) -> ReportOut | None:
    doc = await ReportDoc.find_one(ReportDoc.workflow_id == workflow_id)
    return _report_to_out(doc) if doc else None


async def save_report(out: ReportOut) -> None:
    doc = await ReportDoc.find_one(ReportDoc.report_id == out.id)
    data: dict[str, Any] = dict(
        report_id=out.id,
        workflow_id=out.workflowId,
        repository_id=out.repositoryId,
        repository_name=out.repositoryName,
        generated_at=out.generatedAt,
        sections=out.sections.model_dump(),
        download_url=out.downloadUrl,
    )
    if doc is None:
        await ReportDoc(**data).insert()
    else:
        await doc.set(data)


# ---------------------------------------------------------------------------
# Background thread store shim
# Routes the sync orchestrator thread into the running async event loop.
# ---------------------------------------------------------------------------

def _run(coro):  # type: ignore[no-untyped-def]
    """Submit a coroutine to the running event loop from a non-async thread."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result(timeout=30)
    return asyncio.run(coro)


class _BGStore:
    """Sync façade used by the background orchestrator thread."""

    def get_repo(self, repo_id: str) -> RepositoryOut | None:
        return _run(get_repository(repo_id))

    def set_repo(self, out: RepositoryOut) -> None:
        _run(save_repository(out))

    def get_workflow(self, workflow_id: str) -> WorkflowRunOut | None:
        return _run(get_workflow(workflow_id))

    def set_workflow(self, out: WorkflowRunOut) -> None:
        _run(save_workflow(out))

    def get_finding_ids(self, workflow_id: str) -> list[str]:
        return _run(get_finding_ids(workflow_id))

    def get_finding(self, finding_id: str) -> FindingOut | None:
        return _run(get_finding(finding_id))

    def set_finding(self, out: FindingOut) -> None:
        _run(save_finding(out))

    def get_report_by_workflow(self, workflow_id: str) -> ReportOut | None:
        return _run(get_report_by_workflow(workflow_id))

    def set_report(self, out: ReportOut) -> None:
        _run(save_report(out))


store = _BGStore()
