"""
Unit tests — Phase 3: Subagents.

Each test class verifies that its agent detects the specific predefined
issues from sample-project/main.py.

Predefined issues targeted:
  Code Review:     SP-03, SP-04, SP-07, SP-08, SP-09, SP-13
  Test Analysis:   SP-06, SP-10
  Security:        SP-01, SP-02, SP-05
  Documentation:   SP-11, SP-12

The tests run against real sample-project/ content via the Repository
Inspector, matching the actual integration scenario.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.agents.code_review import CodeReviewAgent
from app.agents.documentation import DocumentationAgent
from app.agents.security import SecurityAgent
from app.agents.test_analysis import TestingAnalysisAgent
from app.models.finding import Finding, FixRisk, SecurityAgentOutput, Severity, SourceAgent
from app.services.repository_inspector import RepositoryInspector

SAMPLE_PROJECT = (Path(__file__).parent.parent.parent / "sample-project").resolve()


@pytest.fixture(scope="module")
def sample_context():
    """Inspect sample-project/ once for all agent tests."""
    return RepositoryInspector().inspect(str(SAMPLE_PROJECT))


# ---------------------------------------------------------------------------
# Finding schema validation
# ---------------------------------------------------------------------------


class TestFindingSchema:
    def test_finding_requires_all_fields(self):
        f = Finding(
            id="CR-001",
            source_agent=SourceAgent.CODE_REVIEW,
            title="Test",
            severity=Severity.HIGH,
            file="main.py",
            location="line 1",
            explanation="explanation",
            impact="impact",
            recommended_fix="fix",
            verification_method="verify",
            fix_risk=FixRisk.SAFE,
        )
        assert f.id == "CR-001"

    def test_security_output_has_disclaimer(self):
        out = SecurityAgentOutput(findings=[])
        assert "static code inspection" in out.disclaimer.lower()
        assert out.findings == []

    def test_finding_serialises_to_dict(self):
        f = Finding(
            id="SA-001",
            source_agent=SourceAgent.SECURITY,
            title="Test",
            severity=Severity.CRITICAL,
            file="main.py",
            location="line 1",
            explanation="e",
            impact="i",
            recommended_fix="r",
            verification_method="v",
            fix_risk=FixRisk.HIGH,
        )
        d = f.model_dump()
        assert d["source_agent"] == "security"
        assert d["severity"] == "critical"
        assert d["fix_risk"] == "high"


# ---------------------------------------------------------------------------
# Code Review Agent
# ---------------------------------------------------------------------------


class TestCodeReviewAgent:
    def test_returns_findings_list(self, sample_context):
        findings = CodeReviewAgent().analyze(sample_context)
        assert isinstance(findings, list)
        assert len(findings) > 0

    def test_all_findings_have_code_review_source(self, sample_context):
        findings = CodeReviewAgent().analyze(sample_context)
        assert all(f.source_agent == SourceAgent.CODE_REVIEW for f in findings)

    def test_detects_unchecked_update_sp03(self, sample_context):
        """SP-03 — update_todo silently succeeds when ID not found."""
        findings = CodeReviewAgent().analyze(sample_context)
        titles = [f.title.lower() for f in findings]
        assert any("update" in t for t in titles), (
            f"Expected finding about unchecked update_one. Titles: {titles}"
        )

    def test_detects_unchecked_delete_sp04(self, sample_context):
        """SP-04 — delete_todo silently succeeds when ID not found."""
        findings = CodeReviewAgent().analyze(sample_context)
        titles = [f.title.lower() for f in findings]
        assert any("delete" in t for t in titles), (
            f"Expected finding about unchecked delete_one. Titles: {titles}"
        )

    def test_detects_unbounded_query_sp07(self, sample_context):
        """SP-07 — get_todos returns all docs with no pagination."""
        findings = CodeReviewAgent().analyze(sample_context)
        titles = [f.title.lower() for f in findings]
        assert any("unbounded" in t or "pagination" in t or "limit" in t for t in titles), (
            f"Expected finding about unbounded query. Titles: {titles}"
        )

    def test_detects_magic_string_sp09(self, sample_context):
        """SP-09 — magic string 'todos' repeated in every handler."""
        findings = CodeReviewAgent().analyze(sample_context)
        titles = [f.title.lower() for f in findings]
        assert any("magic" in t or "todos" in t or "collection" in t for t in titles), (
            f"Expected finding about magic collection string. Titles: {titles}"
        )

    def test_detects_unused_import_sp13(self, sample_context):
        """SP-13 — unused import 'datetime'."""
        findings = CodeReviewAgent().analyze(sample_context)
        titles = [f.title.lower() for f in findings]
        assert any("unused import" in t or "datetime" in t for t in titles), (
            f"Expected finding about unused import. Titles: {titles}"
        )

    def test_finding_ids_are_unique(self, sample_context):
        findings = CodeReviewAgent().analyze(sample_context)
        ids = [f.id for f in findings]
        assert len(ids) == len(set(ids)), f"Duplicate finding IDs: {ids}"

    def test_minimum_three_findings(self, sample_context):
        """IMPLEMENTATION_PLAN Phase 3 exit criterion: ≥3 known issues detected."""
        findings = CodeReviewAgent().analyze(sample_context)
        assert len(findings) >= 3, (
            f"Code Review Agent detected only {len(findings)} findings; expected ≥3"
        )


# ---------------------------------------------------------------------------
# Test Analysis Agent
# ---------------------------------------------------------------------------


class TestTestAnalysisAgent:
    def test_returns_findings_list(self, sample_context):
        findings = TestingAnalysisAgent().analyze(sample_context)
        assert isinstance(findings, list)

    def test_all_findings_have_test_analysis_source(self, sample_context):
        findings = TestingAnalysisAgent().analyze(sample_context)
        assert all(f.source_agent == SourceAgent.TEST_ANALYSIS for f in findings)

    def test_detects_no_tests_sp06(self, sample_context):
        """SP-06 — no test files exist at all."""
        findings = TestingAnalysisAgent().analyze(sample_context)
        titles = [f.title.lower() for f in findings]
        assert any("no test" in t or "untested" in t for t in titles), (
            f"Expected finding about missing tests. Titles: {titles}"
        )

    def test_detects_invalid_id_gap_sp10(self, sample_context):
        """SP-10 — no test for invalid ObjectId input."""
        findings = TestingAnalysisAgent().analyze(sample_context)
        titles = [f.title.lower() for f in findings]
        assert any("invalid" in t or "objectid" in t or "id" in t for t in titles), (
            f"Expected finding about missing invalid-ID test. Titles: {titles}"
        )

    def test_minimum_two_findings(self, sample_context):
        """IMPLEMENTATION_PLAN Phase 3: ≥2 known gaps detected."""
        findings = TestingAnalysisAgent().analyze(sample_context)
        assert len(findings) >= 2, (
            f"Test Analysis Agent detected only {len(findings)} findings; expected ≥2"
        )

    def test_finding_ids_are_unique(self, sample_context):
        findings = TestingAnalysisAgent().analyze(sample_context)
        ids = [f.id for f in findings]
        assert len(ids) == len(set(ids)), f"Duplicate finding IDs: {ids}"


# ---------------------------------------------------------------------------
# Security Agent
# ---------------------------------------------------------------------------


class TestSecurityAgent:
    def test_returns_findings_list(self, sample_context):
        findings = SecurityAgent().analyze(sample_context)
        assert isinstance(findings, list)

    def test_all_findings_have_security_source(self, sample_context):
        findings = SecurityAgent().analyze(sample_context)
        assert all(f.source_agent == SourceAgent.SECURITY for f in findings)

    def test_detects_hardcoded_credentials_sp01(self, sample_context):
        """SP-01 — hardcoded MongoDB connection string."""
        findings = SecurityAgent().analyze(sample_context)
        titles = [f.title.lower() for f in findings]
        assert any(
            "hardcoded" in t or "credential" in t or "connection string" in t
            for t in titles
        ), f"Expected finding about hardcoded credentials. Titles: {titles}"

    def test_hardcoded_credential_is_critical(self, sample_context):
        findings = SecurityAgent().analyze(sample_context)
        cred_findings = [
            f for f in findings
            if "hardcoded" in f.title.lower() or "credential" in f.title.lower()
        ]
        assert cred_findings, "No credential finding found"
        assert cred_findings[0].severity == Severity.CRITICAL

    def test_detects_no_input_validation_sp02(self, sample_context):
        """SP-02 — raw dict input, no Pydantic validation."""
        findings = SecurityAgent().analyze(sample_context)
        titles = [f.title.lower() for f in findings]
        assert any("validation" in t or "dict" in t or "input" in t for t in titles), (
            f"Expected finding about missing input validation. Titles: {titles}"
        )

    def test_detects_unvalidated_objectid_sp05(self, sample_context):
        """SP-05 — ObjectId() called without validation."""
        findings = SecurityAgent().analyze(sample_context)
        titles = [f.title.lower() for f in findings]
        assert any("objectid" in t or "500" in t or "invalid id" in t for t in titles), (
            f"Expected finding about unvalidated ObjectId. Titles: {titles}"
        )

    def test_analyze_with_disclaimer_has_disclaimer(self, sample_context):
        """SUBAGENT_SPEC §3 — mandatory disclaimer must be present."""
        output = SecurityAgent().analyze_with_disclaimer(sample_context)
        assert isinstance(output, SecurityAgentOutput)
        assert len(output.disclaimer) > 20
        assert "static" in output.disclaimer.lower()

    def test_disclaimer_serialises_to_json(self, sample_context):
        output = SecurityAgent().analyze_with_disclaimer(sample_context)
        data = json.loads(output.model_dump_json())
        assert "disclaimer" in data
        assert "findings" in data

    def test_finding_ids_are_unique(self, sample_context):
        findings = SecurityAgent().analyze(sample_context)
        ids = [f.id for f in findings]
        assert len(ids) == len(set(ids)), f"Duplicate finding IDs: {ids}"


# ---------------------------------------------------------------------------
# Documentation Agent
# ---------------------------------------------------------------------------


class TestDocumentationAgent:
    def test_returns_findings_list(self, sample_context):
        findings = DocumentationAgent().analyze(sample_context)
        assert isinstance(findings, list)

    def test_all_findings_have_documentation_source(self, sample_context):
        findings = DocumentationAgent().analyze(sample_context)
        assert all(f.source_agent == SourceAgent.DOCUMENTATION for f in findings)

    def test_detects_missing_readme_sections_sp11(self, sample_context):
        """SP-11 — README missing setup, env vars, API endpoint docs."""
        findings = DocumentationAgent().analyze(sample_context)
        readme_findings = [f for f in findings if "README" in f.file or "readme" in f.file]
        assert len(readme_findings) >= 1, (
            f"Expected at least one README-related finding. All: {[f.title for f in findings]}"
        )

    def test_detects_missing_docstrings_sp12(self, sample_context):
        """SP-12 — no docstrings on route handlers."""
        findings = DocumentationAgent().analyze(sample_context)
        titles = [f.title.lower() for f in findings]
        assert any("docstring" in t for t in titles), (
            f"Expected finding about missing docstrings. Titles: {titles}"
        )

    def test_finding_ids_are_unique(self, sample_context):
        findings = DocumentationAgent().analyze(sample_context)
        ids = [f.id for f in findings]
        assert len(ids) == len(set(ids)), f"Duplicate finding IDs: {ids}"


# ---------------------------------------------------------------------------
# Orchestrator integration — agents produce findings_*.json
# ---------------------------------------------------------------------------


class TestOrchestratorPhase3:
    def test_run_produces_findings_code_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(SAMPLE_PROJECT), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        assert (session_dir / "findings_code.json").exists()

    def test_run_produces_findings_tests_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(SAMPLE_PROJECT), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        assert (session_dir / "findings_tests.json").exists()

    def test_run_produces_findings_security_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(SAMPLE_PROJECT), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        assert (session_dir / "findings_security.json").exists()

    def test_run_produces_findings_docs_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(SAMPLE_PROJECT), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        assert (session_dir / "findings_docs.json").exists()

    def test_security_json_has_disclaimer(self, tmp_path, monkeypatch):
        """SUBAGENT_SPEC §3 — security output must have top-level disclaimer."""
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(SAMPLE_PROJECT), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        data = json.loads((session_dir / "findings_security.json").read_text())
        assert "disclaimer" in data, "Security output missing 'disclaimer' field"

    def test_total_findings_greater_than_zero(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(SAMPLE_PROJECT), decisions={}).run()
        assert result["raw_findings"] > 0

    def test_findings_json_are_valid_finding_objects(self, tmp_path, monkeypatch):
        """Each item in findings_code.json must deserialise to a valid Finding."""
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(SAMPLE_PROJECT), decisions={}).run()
        session_dir = Path(result["project_context"]).parent
        raw = json.loads((session_dir / "findings_code.json").read_text())
        for item in raw:
            f = Finding(**item)
            assert f.id.startswith("CR-")
