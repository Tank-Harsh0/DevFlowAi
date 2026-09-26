"""
Documentation Agent.

Assesses the completeness and accuracy of project documentation.

Issues targeted in sample-project/:
  SP-11 — README missing setup instructions, env vars, and API endpoints
  SP-12 — no docstrings on any route handler

Constraints (SUBAGENT_SPEC.md §4):
  - Do not evaluate writing style or grammar.
  - Only flag factual inaccuracies or missing required information.
  - If no documentation exists at all, report a single Critical finding.
"""
from __future__ import annotations

import ast
import re

from app.agents.base import BaseAgent
from app.models.finding import Finding, FixRisk, Severity, SourceAgent
from app.models.workflow import ProjectContext

# Minimum README sections (SUBAGENT_SPEC.md §4)
_REQUIRED_README_SECTIONS = [
    ("prerequisites", ["prerequisite", "requirement", "python version", "requires"]),
    ("installation", ["install", "pip install", "setup"]),
    ("environment variables", ["env", "environment variable", ".env", "os.getenv", "config"]),
    ("how to run", ["uvicorn", "run the", "start the", "python -m", "how to run"]),
    ("how to test", ["pytest", "test", "run test"]),
    ("api endpoints", ["endpoint", "route", "api", "/todos", "GET", "POST"]),
]

# FastAPI route decorator pattern
_ROUTE_RE = re.compile(
    r"""@\w+\.(get|post|put|patch|delete)\s*\(\s*["']([^"']+)["']""",
    re.MULTILINE,
)


def _readme_has_section(content: str, keywords: list[str]) -> bool:
    lower = content.lower()
    return any(kw.lower() in lower for kw in keywords)


def _functions_without_docstrings(content: str) -> list[tuple[str, int]]:
    """Return (function_name, line_no) for every top-level function with no docstring."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    missing: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            has_doc = (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            )
            if not has_doc:
                missing.append((node.name, node.lineno))
    return missing


class DocumentationAgent(BaseAgent):
    """Checks README completeness and docstring coverage."""

    @property
    def name(self) -> str:
        return "documentation"

    def analyze(self, context: ProjectContext) -> list[Finding]:
        findings: list[Finding] = []

        readme_content = self._find_readme(context)
        if readme_content is None:
            # No documentation at all — single Critical finding (SUBAGENT_SPEC.md §4)
            findings.append(Finding(
                id="DA-001",
                source_agent=SourceAgent.DOCUMENTATION,
                title="No README or documentation files found in the repository",
                severity=Severity.CRITICAL,
                file="README.md",
                location="file-level (missing)",
                explanation=(
                    "The repository contains no README or documentation files. "
                    "A developer cannot determine the project's purpose, "
                    "how to set it up, or how to use it."
                ),
                impact=(
                    "Onboarding is impossible without reading all source code. "
                    "The project is not suitable for handoff or open-source use."
                ),
                recommended_fix=(
                    "Create README.md with at minimum: project description, "
                    "prerequisites, installation, environment variables, "
                    "how to run, and API endpoint list."
                ),
                verification_method="README.md exists and covers all required sections.",
                fix_risk=FixRisk.SAFE,
            ))
        else:
            readme_path = self._find_readme_path(context)
            findings.extend(
                self._check_readme_sections(readme_path or "README.md", readme_content)
            )

        findings.extend(self._check_docstrings(context))
        return findings

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _find_readme(self, context: ProjectContext) -> str | None:
        for doc_file in context.doc_files:
            if "readme" in doc_file.path.lower():
                return context.file_contents.get(doc_file.path)
        return None

    def _find_readme_path(self, context: ProjectContext) -> str | None:
        for doc_file in context.doc_files:
            if "readme" in doc_file.path.lower():
                return doc_file.path
        return None

    # ── Checks ──────────────────────────────────────────────────────────────

    def _check_readme_sections(
        self, readme_path: str, content: str
    ) -> list[Finding]:
        """SP-11 — README missing required sections."""
        out: list[Finding] = []
        n = 1

        for section_name, keywords in _REQUIRED_README_SECTIONS:
            if not _readme_has_section(content, keywords):
                out.append(Finding(
                    id=f"DA-{n:03d}",
                    source_agent=SourceAgent.DOCUMENTATION,
                    title=f'README is missing section: "{section_name}"',
                    severity=Severity.MEDIUM,
                    file=readme_path,
                    location="file-level",
                    explanation=(
                        f'The README does not contain a "{section_name}" section '
                        f"(checked for keywords: {keywords[:2]}...). "
                        f"A developer reading the README cannot find this information."
                    ),
                    impact=(
                        f"Onboarding friction: developers must examine source code "
                        f"to discover {section_name} information."
                    ),
                    recommended_fix=(
                        f'Add a "{section_name.title()}" section to README.md '
                        f"covering the relevant information."
                    ),
                    verification_method=(
                        f"README.md contains a {section_name} section with "
                        f"accurate and complete information."
                    ),
                    fix_risk=FixRisk.SAFE,
                ))
                n += 1
        return out

    def _check_docstrings(self, context: ProjectContext) -> list[Finding]:
        """SP-12 — public functions with no docstring."""
        out: list[Finding] = []
        n = 20  # reserve DA-001..DA-019 for README sections

        source_paths = {f.path for f in context.source_files}
        for rel_path, content in context.file_contents.items():
            if rel_path not in source_paths:
                continue

            missing = _functions_without_docstrings(content)
            if not missing:
                continue

            # Batch into one finding per file to avoid flooding the report
            fn_list = ", ".join(f"{name}() (line {ln})" for name, ln in missing[:5])
            if len(missing) > 5:
                fn_list += f" … and {len(missing) - 5} more"

            out.append(Finding(
                id=f"DA-{n:03d}",
                source_agent=SourceAgent.DOCUMENTATION,
                title=f"{len(missing)} function(s) in {rel_path} have no docstring",
                severity=Severity.LOW,
                file=rel_path,
                location=f"multiple locations: {fn_list}",
                explanation=(
                    f"{len(missing)} function(s) in this file have no docstring. "
                    "Docstrings are the primary source of inline documentation "
                    "for functions and are used by IDEs, auto-generated docs, "
                    "and the Documentation Agent."
                ),
                impact=(
                    "Reduced code readability. IDEs cannot show contextual help. "
                    "Auto-generated API documentation is incomplete."
                ),
                recommended_fix=(
                    "Add a one-line docstring to each function:\n"
                    '  def my_function():\n      """Brief description."""'
                ),
                verification_method=(
                    "Run a docstring linter (e.g. pydocstyle or ruff D rules) "
                    "and confirm zero missing-docstring warnings."
                ),
                fix_risk=FixRisk.SAFE,
            ))
            n += 1
        return out
