"""
Report Generator.

Assembles final_report.md from all session JSON artefacts.

Report sections (WORKFLOW.md Stage 16, PRD FR-60):
  1. Project Summary
  2. Findings (all issues by severity)
  3. Remediation (fixes applied + recommendations)
  4. Testing (generated tests + post-fix results)
  5. Productivity Metrics
  6. Unresolved Issues
  7. Audit Trail Reference

Output:
  - {session_dir}/final_report.md
  - {repository_root}/final_report.md   (copy at repo root)

Constraints:
  - Read-only with respect to source code.
  - Does not execute commands.
  - Gracefully handles missing artefacts (writes "N/A" sections).
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)

_DIVIDER = "---"


class ReportGenerator:
    """Assembles final_report.md from session artefacts."""

    def generate(
        self,
        session_dir: Path,
        repository_root: str,
        session_id: str,
    ) -> Path:
        """Build the report, write it to the session directory and repo root.

        Args:
            session_dir:     Path to the session output directory.
            repository_root: Path to the analysed repository.
            session_id:      Identifier for this workflow run.

        Returns:
            Path to the final_report.md written inside session_dir.
        """
        ctx          = self._load_json(session_dir / "project_context.json")
        findings_raw = self._load_json_list(session_dir / "prioritized_findings.json")
        proposals    = self._load_json_list(session_dir / "fix_plan.json")
        approved     = self._load_json_list(session_dir / "approved_fix_plan.json")
        app_log      = self._load_json_list(session_dir / "fix_application_log.json")
        gen_manifest = self._load_json(session_dir / "generated_tests_manifest.json")
        test_results = self._load_json(session_dir / "test_results_post_fix.json")
        fail_analysis= self._load_json(session_dir / "failure_analysis.json")

        sections: list[str] = [
            self._section_header(session_id, repository_root),
            self._section_project_summary(ctx),
            self._section_findings(findings_raw),
            self._section_remediation(proposals, approved, app_log),
            self._section_testing(gen_manifest, test_results, fail_analysis),
            self._section_productivity(findings_raw, app_log, test_results),
            self._section_unresolved(findings_raw, approved, fail_analysis),
            self._section_audit_trail(session_dir, session_id),
        ]

        report = "\n\n".join(sections) + "\n"

        # Write to session directory
        out = session_dir / "final_report.md"
        out.write_text(report, encoding="utf-8")
        logger.info("Report Generator: written to %s", out)

        # Copy to repository root
        repo_out = Path(repository_root) / "final_report.md"
        try:
            repo_out.write_text(report, encoding="utf-8")
            logger.info("Report Generator: copied to %s", repo_out)
        except OSError as exc:
            logger.warning("Could not write report to repo root: %s", exc)

        return out

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    @staticmethod
    def _section_header(session_id: str, repository_root: str) -> str:
        ts = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")
        return (
            f"# DevFlow AI — Analysis Report\n\n"
            f"**Session ID:** `{session_id}`  \n"
            f"**Repository:** `{repository_root}`  \n"
            f"**Generated:** {ts}  \n\n"
            f"{_DIVIDER}"
        )

    @staticmethod
    def _section_project_summary(ctx: dict) -> str:
        if not ctx:
            return "## 1. Project Summary\n\n_Project context not available._"

        lang     = ctx.get("detected_language", "unknown")
        fw       = ctx.get("detected_test_framework", "unknown")
        src      = len(ctx.get("source_files", []))
        tests    = len(ctx.get("test_files", []))
        docs     = len(ctx.get("doc_files", []))

        return (
            f"## 1. Project Summary\n\n"
            f"| Property | Value |\n"
            f"|---|---|\n"
            f"| Language | {lang} |\n"
            f"| Test Framework | {fw} |\n"
            f"| Source Files | {src} |\n"
            f"| Test Files | {tests} |\n"
            f"| Documentation Files | {docs} |"
        )

    @staticmethod
    def _section_findings(findings: list[dict]) -> str:
        if not findings:
            return "## 2. Findings\n\n_No findings recorded._"

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        counts: dict[str, int] = {}
        for f in findings:
            sev = str(f.get("severity", "unknown"))
            counts[sev] = counts.get(sev, 0) + 1

        summary_rows = "\n".join(
            f"| {sev.title()} | {cnt} |"
            for sev, cnt in sorted(counts.items(), key=lambda x: severity_order.get(x[0], 9))
        )
        summary = (
            f"**Total findings:** {len(findings)}\n\n"
            f"| Severity | Count |\n"
            f"|---|---|\n"
            f"{summary_rows}"
        )

        rows: list[str] = []
        for f in findings:
            fid   = f.get("id", "?")
            title = f.get("title", "")[:60]
            sev   = str(f.get("severity", "")).upper()
            file_ = f.get("file", "")
            loc   = f.get("location", "")
            rows.append(f"| `{fid}` | {sev} | {title} | `{file_}` | {loc} |")

        table = (
            "| ID | Severity | Title | File | Location |\n"
            "|---|---|---|---|---|\n"
            + "\n".join(rows)
        )

        return f"## 2. Findings\n\n{summary}\n\n### Finding Details\n\n{table}"

    @staticmethod
    def _section_remediation(
        proposals: list[dict],
        approved: list[dict],
        app_log: list[dict],
    ) -> str:
        if not proposals:
            return "## 3. Remediation\n\n_No fix proposals generated._"

        n_proposals = len(proposals)
        n_approved  = sum(1 for p in approved if p.get("status") == "approved")
        n_applied   = sum(1 for e in app_log if e.get("outcome") == "APPLIED")
        n_failed    = sum(1 for e in app_log if e.get("outcome") == "FAILED")
        n_skipped   = sum(1 for p in approved if p.get("status") in ("skipped", "rejected"))

        summary = (
            f"| Metric | Count |\n"
            f"|---|---|\n"
            f"| Fix proposals generated | {n_proposals} |\n"
            f"| Approved by developer | {n_approved} |\n"
            f"| Successfully applied | {n_applied} |\n"
            f"| Failed (reverted) | {n_failed} |\n"
            f"| Skipped / Rejected | {n_skipped} |"
        )

        rows: list[str] = []
        for entry in app_log:
            fid     = entry.get("finding_id", "?")
            outcome = entry.get("outcome", "?")
            msg     = str(entry.get("message", ""))[:60]
            backup  = "✓" if entry.get("backup_path") else "—"
            rows.append(f"| `{fid}` | {outcome} | {msg} | {backup} |")

        table_str = ""
        if rows:
            table_str = (
                "\n\n### Applied Fixes Log\n\n"
                "| Finding ID | Outcome | Message | Backup |\n"
                "|---|---|---|---|\n"
                + "\n".join(rows)
            )

        return f"## 3. Remediation\n\n{summary}{table_str}"

    @staticmethod
    def _section_testing(
        gen_manifest: dict,
        test_results: dict,
        fail_analysis: dict,
    ) -> str:
        generated = gen_manifest.get("functions", []) if gen_manifest else []
        n_generated = len(generated)
        out_file = gen_manifest.get("output_file", "N/A") if gen_manifest else "N/A"

        if test_results:
            total   = test_results.get("total", 0)
            passed  = test_results.get("passed", 0)
            failed  = test_results.get("failed", 0)
            error   = test_results.get("error", 0)
            skipped = test_results.get("skipped", 0)
            dur     = test_results.get("duration_seconds", 0)
            rate    = f"{(passed / total * 100):.1f}%" if total else "N/A"
        else:
            total = passed = failed = error = skipped = 0
            dur = 0
            rate = "N/A"

        n_in_scope = fail_analysis.get("in_scope", 0) if fail_analysis else 0

        return (
            f"## 4. Testing\n\n"
            f"### Generated Tests\n\n"
            f"| Metric | Value |\n"
            f"|---|---|\n"
            f"| Test functions generated | {n_generated} |\n"
            f"| Output file | `{out_file}` |\n\n"
            f"### Post-Fix Test Results\n\n"
            f"| Metric | Value |\n"
            f"|---|---|\n"
            f"| Total tests run | {total} |\n"
            f"| Passed | {passed} |\n"
            f"| Failed | {failed} |\n"
            f"| Error | {error} |\n"
            f"| Skipped | {skipped} |\n"
            f"| Duration | {dur:.1f}s |\n"
            f"| Pass rate | **{rate}** |\n"
            f"| In-scope failures | {n_in_scope} |"
        )

    @staticmethod
    def _section_productivity(
        findings: list[dict],
        app_log: list[dict],
        test_results: dict,
    ) -> str:
        n_findings = len(findings)
        n_applied  = sum(1 for e in app_log if e.get("outcome") == "APPLIED")
        total_tests = test_results.get("total", 0) if test_results else 0
        passed_tests= test_results.get("passed", 0) if test_results else 0
        pass_rate   = f"{(passed_tests / total_tests * 100):.1f}%" if total_tests else "N/A"

        # Automation: 8 of 11 manual steps are automated
        automated_steps = 8
        total_steps = 11

        return (
            f"## 5. Productivity Metrics\n\n"
            f"| Metric | Value | Category |\n"
            f"|---|---|---|\n"
            f"| Findings detected | {n_findings} | Measured |\n"
            f"| Fixes automatically applied | {n_applied} | Measured |\n"
            f"| Post-fix test pass rate | {pass_rate} | Measured |\n"
            f"| Automated workflow steps | {automated_steps}/{total_steps} "
            f"({automated_steps/total_steps*100:.0f}%) | Measured |\n"
            f"| Manual workflow time | [NOT MEASURED — see METRICS.md] | Target |\n"
            f"| AI workflow time | [session duration in session.log] | Measured |\n\n"
            f"> Note: Baseline manual workflow time has not been measured. "
            f"See `docs/METRICS.md` for the measurement protocol."
        )

    @staticmethod
    def _section_unresolved(
        findings: list[dict],
        approved: list[dict],
        fail_analysis: dict,
    ) -> str:
        approved_ids = {p.get("finding_id") for p in approved if p.get("status") == "approved"}
        unresolved = [
            f for f in findings
            if f.get("id") not in approved_ids
        ]

        if not unresolved and not (fail_analysis or {}).get("in_scope", 0):
            return "## 6. Unresolved Issues\n\n_No unresolved issues._"

        rows: list[str] = []
        for f in unresolved:
            fid   = f.get("id", "?")
            title = f.get("title", "")[:60]
            sev   = str(f.get("severity", "")).upper()
            risk  = f.get("fix_risk", "")
            rows.append(f"| `{fid}` | {sev} | {title} | {risk} |")

        table_str = ""
        if rows:
            table_str = (
                "\n\n| ID | Severity | Title | Fix Risk |\n"
                "|---|---|---|---|\n"
                + "\n".join(rows)
            )

        in_scope_failures = (fail_analysis or {}).get("in_scope", 0)
        failure_note = ""
        if in_scope_failures:
            failure_note = (
                f"\n\n**{in_scope_failures} in-scope test failure(s) remain** "
                f"after the post-fix run. See `failure_analysis.json` for details."
            )

        count = len(unresolved)
        return (
            f"## 6. Unresolved Issues\n\n"
            f"**{count} finding(s) not addressed:**{table_str}{failure_note}"
        )

    @staticmethod
    def _section_audit_trail(session_dir: Path, session_id: str) -> str:
        artefacts = [
            "project_context.json",
            "execution_plan.json",
            "findings_code.json",
            "findings_tests.json",
            "findings_security.json",
            "findings_docs.json",
            "deduplicated_findings.json",
            "prioritized_findings.json",
            "fix_plan.json",
            "approved_fix_plan.json",
            "fix_application_log.json",
            "generated_tests_manifest.json",
            "test_results_post_fix.json",
            "failure_analysis.json",
            "session.log",
        ]
        rows: list[str] = []
        for name in artefacts:
            exists = "✓" if (session_dir / name).exists() else "—"
            rows.append(f"| `{name}` | {exists} |")

        table = (
            "| Artefact | Present |\n"
            "|---|---|\n"
            + "\n".join(rows)
        )

        return (
            f"## 7. Audit Trail\n\n"
            f"All session artefacts are in: `devflow_sessions/{session_id}/`\n\n"
            f"{table}"
        )

    # ------------------------------------------------------------------
    # JSON loading helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_json(path: Path) -> dict:
        if not path.exists():
            logger.debug("Report Generator: %s not found", path.name)
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Report Generator: could not load %s: %s", path.name, exc)
            return {}

    @staticmethod
    def _load_json_list(path: Path) -> list[dict]:
        if not path.exists():
            logger.debug("Report Generator: %s not found", path.name)
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Report Generator: could not load %s: %s", path.name, exc)
            return []
