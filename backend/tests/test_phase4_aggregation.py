"""
Integration tests — Phase 4: Aggregation & Prioritization.

Verifies:
  - FindingAggregator merges correctly and deduplicates overlapping locations.
  - IssuePrioritizer produces Critical→High→Medium→Low ordering.
  - Full orchestrator run produces deduplicated_findings.json and
    prioritized_findings.json with valid schemas.
  - Detection rate: documents which of the 13 predefined issues are detected.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.models.finding import Finding, FixRisk, Severity, SourceAgent
from app.services.finding_aggregator import FindingAggregator
from app.services.issue_prioritizer import IssuePrioritizer
from app.services.repository_inspector import RepositoryInspector

SAMPLE_PROJECT = (Path(__file__).parent.parent.parent / "sample-project").resolve()


@pytest.fixture(scope="module")
def sample_context():
    return RepositoryInspector().inspect(str(SAMPLE_PROJECT))


def _make_finding(
    fid: str,
    agent: SourceAgent = SourceAgent.CODE_REVIEW,
    severity: Severity = Severity.MEDIUM,
    file: str = "main.py",
    location: str = "line 10",
    fix_risk: FixRisk = FixRisk.SAFE,
) -> Finding:
    return Finding(
        id=fid,
        source_agent=agent,
        title=f"Finding {fid}",
        severity=severity,
        file=file,
        location=location,
        explanation="explanation",
        impact="impact",
        recommended_fix="fix",
        verification_method="verify",
        fix_risk=fix_risk,
    )


# ---------------------------------------------------------------------------
# FindingAggregator unit tests
# ---------------------------------------------------------------------------


class TestFindingAggregator:
    def test_empty_input_returns_empty(self):
        assert FindingAggregator().aggregate([]) == []

    def test_single_finding_passes_through(self):
        f = _make_finding("CR-001")
        result = FindingAggregator().aggregate([f])
        assert len(result) == 1
        assert result[0].id == "CR-001"

    def test_distinct_locations_not_merged(self):
        findings = [
            _make_finding("CR-001", location="line 10"),
            _make_finding("CR-002", location="line 20"),
        ]
        result = FindingAggregator().aggregate(findings)
        assert len(result) == 2

    def test_same_file_and_line_are_merged(self):
        """Two findings from different agents at the same location → 1 merged."""
        findings = [
            _make_finding("CR-001", agent=SourceAgent.CODE_REVIEW, location="line 15"),
            _make_finding("SA-001", agent=SourceAgent.SECURITY, location="line 15"),
        ]
        result = FindingAggregator().aggregate(findings)
        assert len(result) == 1

    def test_merge_retains_highest_severity(self):
        findings = [
            _make_finding("CR-001", agent=SourceAgent.CODE_REVIEW,
                          severity=Severity.MEDIUM, location="line 15"),
            _make_finding("SA-001", agent=SourceAgent.SECURITY,
                          severity=Severity.CRITICAL, location="line 15"),
        ]
        result = FindingAggregator().aggregate(findings)
        assert result[0].severity == Severity.CRITICAL

    def test_merge_retains_highest_fix_risk(self):
        findings = [
            _make_finding("CR-001", agent=SourceAgent.CODE_REVIEW,
                          fix_risk=FixRisk.SAFE, location="line 15"),
            _make_finding("SA-001", agent=SourceAgent.SECURITY,
                          fix_risk=FixRisk.HIGH, location="line 15"),
        ]
        result = FindingAggregator().aggregate(findings)
        assert result[0].fix_risk == FixRisk.HIGH

    def test_line_number_variants_are_grouped(self):
        """Cross-agent findings: 'line 42' and 'line 42, function foo()' → merged."""
        findings = [
            _make_finding("CR-001", agent=SourceAgent.CODE_REVIEW, location="line 42"),
            _make_finding("SA-001", agent=SourceAgent.SECURITY,
                          location="line 42, function create_todo"),
        ]
        result = FindingAggregator().aggregate(findings)
        assert len(result) == 1

    def test_different_files_not_merged(self):
        findings = [
            _make_finding("CR-001", file="main.py", location="line 10"),
            _make_finding("SA-001", file="config.py", location="line 10"),
        ]
        result = FindingAggregator().aggregate(findings)
        assert len(result) == 2

    def test_file_level_locations_grouped(self):
        """Cross-agent file-level findings at the same file are merged."""
        findings = [
            _make_finding("DA-001", agent=SourceAgent.DOCUMENTATION,
                          location="file-level", file="README.md"),
            _make_finding("TA-001", agent=SourceAgent.TEST_ANALYSIS,
                          location="file-level", file="README.md"),
        ]
        result = FindingAggregator().aggregate(findings)
        assert len(result) == 1

    def test_same_agent_same_location_kept_separate(self):
        """Same agent reporting two issues at the same line → NOT merged."""
        findings = [
            _make_finding("DA-001", agent=SourceAgent.DOCUMENTATION,
                          location="file-level", file="README.md"),
            _make_finding("DA-002", agent=SourceAgent.DOCUMENTATION,
                          location="file-level", file="README.md"),
        ]
        result = FindingAggregator().aggregate(findings)
        assert len(result) == 2

    def test_output_findings_are_valid_finding_objects(self, sample_context):
        from app.agents.code_review import CodeReviewAgent
        from app.agents.security import SecurityAgent
        raw = CodeReviewAgent().analyze(sample_context) + SecurityAgent().analyze(sample_context)
        result = FindingAggregator().aggregate(raw)
        for f in result:
            assert isinstance(f, Finding)
            assert f.id
            assert f.severity in list(Severity)


# ---------------------------------------------------------------------------
# IssuePrioritizer unit tests
# ---------------------------------------------------------------------------


class TestIssuePrioritizer:
    def test_empty_input_returns_empty(self):
        assert IssuePrioritizer().prioritize([]) == []

    def test_single_finding_returned(self):
        f = _make_finding("CR-001", severity=Severity.HIGH)
        result = IssuePrioritizer().prioritize([f])
        assert len(result) == 1

    def test_critical_before_high(self):
        findings = [
            _make_finding("CR-001", severity=Severity.HIGH),
            _make_finding("SA-001", severity=Severity.CRITICAL),
        ]
        result = IssuePrioritizer().prioritize(findings)
        assert result[0].severity == Severity.CRITICAL
        assert result[1].severity == Severity.HIGH

    def test_full_severity_order(self):
        findings = [
            _make_finding("D", severity=Severity.LOW),
            _make_finding("B", severity=Severity.HIGH),
            _make_finding("C", severity=Severity.MEDIUM),
            _make_finding("A", severity=Severity.CRITICAL),
        ]
        result = IssuePrioritizer().prioritize(findings)
        assert [f.severity for f in result] == [
            Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW
        ]

    def test_same_severity_sorted_by_file(self):
        findings = [
            _make_finding("CR-001", severity=Severity.HIGH, file="z_file.py"),
            _make_finding("CR-002", severity=Severity.HIGH, file="a_file.py"),
        ]
        result = IssuePrioritizer().prioritize(findings)
        assert result[0].file == "a_file.py"
        assert result[1].file == "z_file.py"

    def test_input_list_not_mutated(self):
        findings = [
            _make_finding("D", severity=Severity.LOW),
            _make_finding("A", severity=Severity.CRITICAL),
        ]
        original_order = [f.id for f in findings]
        IssuePrioritizer().prioritize(findings)
        assert [f.id for f in findings] == original_order


# ---------------------------------------------------------------------------
# Orchestrator integration — full pipeline artefacts
# ---------------------------------------------------------------------------


class TestOrchestratorPhase4:
    def test_run_produces_deduplicated_findings_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(SAMPLE_PROJECT)).run()
        session_dir = Path(result["project_context"]).parent
        assert (session_dir / "deduplicated_findings.json").exists()

    def test_run_produces_prioritized_findings_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(SAMPLE_PROJECT)).run()
        session_dir = Path(result["project_context"]).parent
        assert (session_dir / "prioritized_findings.json").exists()

    def test_deduplicated_json_is_valid_finding_list(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(SAMPLE_PROJECT)).run()
        session_dir = Path(result["project_context"]).parent
        raw = json.loads((session_dir / "deduplicated_findings.json").read_text())
        assert isinstance(raw, list)
        assert len(raw) > 0
        for item in raw:
            Finding(**item)  # must not raise

    def test_prioritized_json_starts_with_critical_or_high(self, tmp_path, monkeypatch):
        """First finding must be Critical or High — the most severe issues are first."""
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(SAMPLE_PROJECT)).run()
        session_dir = Path(result["project_context"]).parent
        raw = json.loads((session_dir / "prioritized_findings.json").read_text())
        first_severity = raw[0]["severity"]
        assert first_severity in ("critical", "high"), (
            f"Expected first finding to be critical/high, got: {first_severity}"
        )

    def test_prioritized_findings_correctly_ordered(self, tmp_path, monkeypatch):
        """No finding of lower severity should appear before a higher-severity finding."""
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(SAMPLE_PROJECT)).run()
        session_dir = Path(result["project_context"]).parent
        raw = json.loads((session_dir / "prioritized_findings.json").read_text())
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        severities = [order[item["severity"]] for item in raw]
        assert severities == sorted(severities), (
            "Findings are not in severity order: "
            + str([item["severity"] for item in raw])
        )

    def test_result_dict_has_finding_counts(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator
        result = Orchestrator(str(SAMPLE_PROJECT)).run()
        assert "raw_findings" in result
        assert "deduplicated_findings" in result
        assert "prioritized_findings" in result
        assert result["raw_findings"] >= result["deduplicated_findings"]  # type: ignore[operator]

    def test_workflow_reaches_complete_stage(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.models.workflow import WorkflowStage
        from app.services.orchestrator import Orchestrator
        orch = Orchestrator(str(SAMPLE_PROJECT))
        orch.run()
        assert orch.state.stage == WorkflowStage.COMPLETE


# ---------------------------------------------------------------------------
# Detection rate — which of the 13 predefined issues are detected?
# ---------------------------------------------------------------------------


class TestDetectionRate:
    """
    Acceptance criterion AC-04: detect at least 10 of the 13 predefined issues.

    This test runs the full pipeline and checks for evidence that each
    predefined issue was detected. It documents the result without failing
    the test suite on partial detection — the count is reported and the
    minimum threshold is asserted.
    """

    # Keywords matched against concatenated title+explanation of all findings.
    # Each value is "/"-separated alternatives; ANY match counts as detected.
    PREDEFINED_ISSUES = {
        "SP-01": "hardcoded / connection string / credentials",
        "SP-02": "input validation / arbitrary dict / create_todo",
        "SP-03": "update_one / unchecked / silent update",
        "SP-04": "delete_one / unchecked / silent delete",
        "SP-05": "objectid / invalid id / 500 crash",
        "SP-06": "no test files / untested / entire codebase",
        "SP-07": "unbounded / no pagination / no limit",
        "SP-08": "module level / dependency injection / duplicate",
        "SP-09": "magic string / collection name",
        "SP-10": "invalid objectid / missing invalid / ta-050",
        "SP-11": "readme / how to run / setup",
        "SP-12": "docstring",
        "SP-13": "unused import / datetime",
    }

    def test_detection_rate_meets_minimum(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr("app.services.session_manager.SESSIONS_ROOT", tmp_path)
        from app.services.orchestrator import Orchestrator

        result = Orchestrator(str(SAMPLE_PROJECT)).run()
        session_dir = Path(result["project_context"]).parent
        all_findings = json.loads(
            (session_dir / "prioritized_findings.json").read_text()
        )

        # Build a searchable text blob from all finding titles + explanations
        finding_text = " ".join(
            (f.get("title", "") + " " + f.get("explanation", "")).lower()
            for f in all_findings
        )

        detected: list[str] = []
        not_detected: list[str] = []

        for issue_id, keywords_str in self.PREDEFINED_ISSUES.items():
            # Issue is "detected" if any keyword appears anywhere in the findings
            keywords = [kw.strip() for kw in keywords_str.split("/")]
            found = any(kw in finding_text for kw in keywords)
            if found:
                detected.append(issue_id)
            else:
                not_detected.append(issue_id)

        detection_rate = len(detected) / len(self.PREDEFINED_ISSUES)

        # Print a summary (visible with pytest -v -s)
        print(f"\n\nDetection Rate: {len(detected)}/{len(self.PREDEFINED_ISSUES)}"
              f" ({detection_rate:.0%})")
        print(f"  Detected:     {detected}")
        print(f"  Not detected: {not_detected}")

        # Minimum threshold from AC-04: 10 of 13
        assert len(detected) >= 10, (
            f"Detection rate below threshold: {len(detected)}/13 detected. "
            f"Not detected: {not_detected}"
        )
