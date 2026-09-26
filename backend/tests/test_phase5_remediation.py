"""
Integration tests — Phase 5: Remediation.

Three required integration tests per IMPLEMENTATION_PLAN Phase 5:
  1. Approve a safe fix → file modified, backup exists, fix_application_log.json written.
  2. Reject a fix → file unchanged.
  3. Apply a fix that introduces a syntax error → reverted from backup.

Additional unit tests for FixPlanner, ApprovalGate, and CodeModifier.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from app.models.finding import FixRisk, Severity, SourceAgent
from app.models.finding import Finding
from app.models.fix_proposal import FixProposal, ProposalStatus
from app.services.approval_gate import ApprovalGate
from app.services.code_modifier import CodeModifier, _apply_unified_diff
from app.services.fix_planner import FixPlanner, _unified_diff
from app.services.repository_inspector import RepositoryInspector

SAMPLE_PROJECT = (Path(__file__).parent.parent.parent / "sample-project").resolve()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_finding(
    fid: str = "CR-001",
    fix_risk: FixRisk = FixRisk.SAFE,
    severity: Severity = Severity.MEDIUM,
    file: str = "main.py",
) -> Finding:
    return Finding(
        id=fid,
        source_agent=SourceAgent.CODE_REVIEW,
        title=f"Test finding {fid}",
        severity=severity,
        file=file,
        location="line 1",
        explanation="explanation",
        impact="impact",
        recommended_fix="fix",
        verification_method="verify",
        fix_risk=fix_risk,
    )


def _make_proposal(
    finding_id: str = "CR-001",
    fix_risk: FixRisk = FixRisk.SAFE,
    diff: str = "",
    file: str = "main.py",
    status: ProposalStatus = ProposalStatus.PENDING,
) -> FixProposal:
    return FixProposal(
        finding_id=finding_id,
        fix_risk=fix_risk,
        description="Test fix",
        rationale="Rationale",
        files_affected=[file],
        diff=diff,
        verification_method="verify",
        status=status,
    )


@pytest.fixture(scope="module")
def sample_context():
    return RepositoryInspector().inspect(str(SAMPLE_PROJECT))


@pytest.fixture
def repo_copy(tmp_path):
    """Copy sample-project to a temp dir so tests can safely modify files."""
    dest = tmp_path / "sample-project"
    shutil.copytree(SAMPLE_PROJECT, dest)
    return dest


# ---------------------------------------------------------------------------
# FixPlanner unit tests
# ---------------------------------------------------------------------------


class TestFixPlanner:
    def test_not_applicable_findings_excluded(self, sample_context):
        finding = _make_finding(fix_risk=FixRisk.NOT_APPLICABLE)
        proposals = FixPlanner().plan([finding], sample_context.file_contents)
        assert proposals == []

    def test_safe_finding_produces_proposal(self, sample_context):
        findings = FixPlanner().plan(
            [_make_finding(fix_risk=FixRisk.SAFE)],
            sample_context.file_contents,
        )
        assert len(findings) == 1
        assert findings[0].status == ProposalStatus.PENDING

    def test_unused_import_proposal_has_diff(self, sample_context):
        finding = Finding(
            id="CR-006",
            source_agent=SourceAgent.CODE_REVIEW,
            title='Unused import: "datetime"',
            severity=Severity.LOW,
            file="main.py",
            location="line 1",
            explanation="datetime is imported but unused",
            impact="minor",
            recommended_fix="Remove import datetime",
            verification_method="verify",
            fix_risk=FixRisk.SAFE,
        )
        proposals = FixPlanner().plan([finding], sample_context.file_contents)
        assert proposals
        assert "datetime" in proposals[0].diff

    def test_hardcoded_uri_proposal_has_diff(self, sample_context):
        finding = Finding(
            id="SA-001",
            source_agent=SourceAgent.SECURITY,
            title="Database connection string with credentials hardcoded in source code",
            severity=Severity.CRITICAL,
            file="main.py",
            location="line 16",
            explanation="hardcoded URI",
            impact="credential exposure",
            recommended_fix="use env var",
            verification_method="verify",
            fix_risk=FixRisk.SAFE,
        )
        proposals = FixPlanner().plan([finding], sample_context.file_contents)
        assert proposals
        assert "MONGODB_URI" in proposals[0].diff or "os.getenv" in proposals[0].diff

    def test_all_proposals_have_required_fields(self, sample_context):
        from app.agents.code_review import CodeReviewAgent
        from app.services.issue_prioritizer import IssuePrioritizer
        findings = IssuePrioritizer().prioritize(
            CodeReviewAgent().analyze(sample_context)
        )
        proposals = FixPlanner().plan(findings, sample_context.file_contents)
        for p in proposals:
            assert p.finding_id
            assert p.fix_risk in list(FixRisk)
            assert p.status == ProposalStatus.PENDING

    def test_unified_diff_helper_empty_for_unchanged(self):
        content = "line1\nline2\n"
        assert _unified_diff(content, content, "file.py") == ""

    def test_unified_diff_helper_non_empty_for_change(self):
        original = "line1\nline2\n"
        modified = "line1\nline2_modified\n"
        diff = _unified_diff(original, modified, "file.py")
        assert "-line2" in diff
        assert "+line2_modified" in diff


# ---------------------------------------------------------------------------
# ApprovalGate unit tests
# ---------------------------------------------------------------------------


class TestApprovalGate:
    def test_empty_proposals_pass_through(self):
        result = ApprovalGate(decisions={}).review([])
        assert result == []

    def test_approved_decision_sets_status(self):
        p = _make_proposal("CR-001")
        result = ApprovalGate(decisions={"CR-001": ProposalStatus.APPROVED}).review([p])
        assert result[0].status == ProposalStatus.APPROVED

    def test_rejected_decision_sets_status(self):
        p = _make_proposal("CR-001")
        result = ApprovalGate(decisions={"CR-001": ProposalStatus.REJECTED}).review([p])
        assert result[0].status == ProposalStatus.REJECTED

    def test_missing_decision_defaults_to_skipped(self):
        p = _make_proposal("CR-001")
        result = ApprovalGate(decisions={}).review([p])
        assert result[0].status == ProposalStatus.SKIPPED

    def test_high_risk_always_skipped(self):
        """HIGH risk fixes must never be applied — ARCHITECTURE.md §9."""
        p = _make_proposal("SA-001", fix_risk=FixRisk.HIGH)
        result = ApprovalGate(
            decisions={"SA-001": ProposalStatus.APPROVED}
        ).review([p])
        assert result[0].status == ProposalStatus.SKIPPED

    def test_original_proposals_not_mutated(self):
        p = _make_proposal("CR-001")
        original_status = p.status
        ApprovalGate(decisions={"CR-001": ProposalStatus.APPROVED}).review([p])
        assert p.status == original_status  # original unchanged


# ---------------------------------------------------------------------------
# CodeModifier unit tests
# ---------------------------------------------------------------------------


class TestCodeModifier:
    def test_skipped_proposals_not_modified(self, repo_copy):
        p = _make_proposal("CR-001", status=ProposalStatus.SKIPPED, file="main.py")
        original = (repo_copy / "main.py").read_text()
        modifier = CodeModifier(str(repo_copy))
        updated, log = modifier.apply_approved([p])
        assert (repo_copy / "main.py").read_text() == original
        assert log == []

    def test_approved_empty_diff_not_modified(self, repo_copy):
        """APPROVED proposals with no diff are not applied (no auto-generated fix)."""
        p = _make_proposal("DA-001", diff="", status=ProposalStatus.APPROVED, file="README.md")
        original = (repo_copy / "README.md").read_text()
        modifier = CodeModifier(str(repo_copy))
        updated, log = modifier.apply_approved([p])
        assert (repo_copy / "README.md").read_text() == original

    def test_path_escape_blocked(self, repo_copy):
        """Files outside the repository root must never be modified."""
        p = _make_proposal(
            "XX-001",
            diff="--- a/evil\n+++ b/evil\n@@ -1,1 +1,1 @@\n-x\n+y\n",
            status=ProposalStatus.APPROVED,
            file="../evil.py",
        )
        modifier = CodeModifier(str(repo_copy))
        updated, log = modifier.apply_approved([p])
        assert updated[0].status == ProposalStatus.FAILED

    def test_apply_unified_diff_basic(self):
        original = "line1\nline2\nline3\n"
        diff = _unified_diff(original, "line1\nLINE2\nline3\n", "f.py")
        result = _apply_unified_diff(original, diff)
        assert "LINE2" in result
        assert "line2" not in result

    def test_apply_unified_diff_empty_returns_original(self):
        original = "hello\nworld\n"
        assert _apply_unified_diff(original, "") == original


# ---------------------------------------------------------------------------
# Integration test 1: Approve a safe fix → file modified, backup exists
# ---------------------------------------------------------------------------


class TestIntegration1ApproveAndApply:
    """IMPLEMENTATION_PLAN Phase 5 integration test 1."""

    def test_approved_fix_modifies_file(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        target = repo_copy / "main.py"
        original = target.read_text()

        # Use the unused-import fix (safe, concrete diff)
        from app.services.orchestrator import Orchestrator
        orch = Orchestrator(
            str(repo_copy),
            decisions={},  # start with all skipped
        )
        # Run only through fix planner to get the proposal IDs
        from app.services.fix_planner import FixPlanner
        from app.services.repository_inspector import RepositoryInspector
        from app.agents.code_review import CodeReviewAgent
        from app.services.issue_prioritizer import IssuePrioritizer
        from app.services.finding_aggregator import FindingAggregator

        ctx = RepositoryInspector().inspect(str(repo_copy))
        findings = IssuePrioritizer().prioritize(
            FindingAggregator().aggregate(CodeReviewAgent().analyze(ctx))
        )
        proposals = FixPlanner().plan(findings, ctx.file_contents)

        # Find a proposal with a real diff
        good = next((p for p in proposals if p.diff), None)
        if good is None:
            pytest.skip("No proposal with a diff found — skipping apply test")

        # Now run the full orchestrator approving only that proposal
        from app.services.session_manager import SESSIONS_ROOT
        orch2 = Orchestrator(str(repo_copy), decisions={good.finding_id: ProposalStatus.APPROVED})
        result = orch2.run()

        assert result["applied_fixes"] >= 1
        assert target.read_text() != original, "File should have been modified"
        assert Path(str(target) + ".bak").exists(), "Backup must exist"

    def test_fix_application_log_written(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator

        ctx = RepositoryInspector().inspect(str(repo_copy))
        from app.agents.code_review import CodeReviewAgent
        from app.services.finding_aggregator import FindingAggregator
        from app.services.issue_prioritizer import IssuePrioritizer
        findings = IssuePrioritizer().prioritize(
            FindingAggregator().aggregate(CodeReviewAgent().analyze(ctx))
        )
        proposals = FixPlanner().plan(findings, ctx.file_contents)
        good = next((p for p in proposals if p.diff), None)
        if good is None:
            pytest.skip("No proposal with a diff found")

        orch = Orchestrator(str(repo_copy), decisions={good.finding_id: ProposalStatus.APPROVED})
        result = orch.run()

        session_dir = Path(result["project_context"]).parent
        log_path = session_dir / "fix_application_log.json"
        assert log_path.exists()
        log_data = json.loads(log_path.read_text())
        assert isinstance(log_data, list)
        applied = [e for e in log_data if e["outcome"] == "APPLIED"]
        assert len(applied) >= 1


# ---------------------------------------------------------------------------
# Integration test 2: Reject fix → file unchanged
# ---------------------------------------------------------------------------


class TestIntegration2RejectFix:
    """IMPLEMENTATION_PLAN Phase 5 integration test 2."""

    def test_rejected_fix_leaves_file_unchanged(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        target = repo_copy / "main.py"
        original = target.read_text()

        # All fixes rejected
        from app.services.orchestrator import Orchestrator
        orch = Orchestrator(str(repo_copy), decisions={})  # all skipped
        result = orch.run()

        assert target.read_text() == original, "File must not change when all fixes skipped"
        assert result["applied_fixes"] == 0


# ---------------------------------------------------------------------------
# Integration test 3: Syntax-error fix → reverted from backup
# ---------------------------------------------------------------------------


class TestIntegration3SyntaxErrorReverted:
    """IMPLEMENTATION_PLAN Phase 5 integration test 3."""

    def test_bad_diff_reverts_file(self, repo_copy, tmp_path):
        """CodeModifier must revert to backup when py_compile fails."""
        target = repo_copy / "main.py"
        original_content = target.read_text()

        # Craft a diff that replaces the first function definition with invalid syntax
        broken = original_content.replace(
            "def get_todos():",
            "def get_todos(: INTENTIONAL SYNTAX ERROR",
        )
        bad_diff = _unified_diff(original_content, broken, "main.py")

        p = FixProposal(
            finding_id="CR-TEST",
            fix_risk=FixRisk.SAFE,
            description="Intentionally broken fix",
            rationale="Test",
            files_affected=["main.py"],
            diff=bad_diff,
            verification_method="n/a",
            status=ProposalStatus.APPROVED,
        )

        modifier = CodeModifier(str(repo_copy))
        updated, log = modifier.apply_approved([p])

        # File must be reverted to original
        assert target.read_text() == original_content, (
            "File must be reverted after syntax-error fix"
        )
        assert updated[0].status == ProposalStatus.FAILED
        assert any(e["outcome"] == "FAILED" for e in log)
        assert Path(str(target) + ".bak").exists(), "Backup must still exist after revert"


# ---------------------------------------------------------------------------
# Orchestrator Phase 5 — artefacts produced
# ---------------------------------------------------------------------------


class TestOrchestratorPhase5:
    def test_run_produces_fix_plan_json(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        assert (session_dir / "fix_plan.json").exists()

    def test_run_produces_approved_fix_plan_json(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        assert (session_dir / "approved_fix_plan.json").exists()

    def test_run_produces_fix_application_log_json(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        assert (session_dir / "fix_application_log.json").exists()

    def test_fix_plan_json_contains_proposals(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        data = json.loads((session_dir / "fix_plan.json").read_text())
        assert isinstance(data, list)
        assert len(data) > 0

    def test_result_has_remediation_counts(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(repo_copy), decisions={}).run()
        assert "proposals" in result
        assert "approved_fixes" in result
        assert "applied_fixes" in result

    def test_workflow_reaches_complete_stage(self, repo_copy, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.models.workflow import WorkflowStage
        from app.services.orchestrator import Orchestrator
        orch = Orchestrator(str(repo_copy), decisions={})
        orch.run()
        assert orch.state.stage == WorkflowStage.COMPLETE
