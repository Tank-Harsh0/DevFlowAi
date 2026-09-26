"""
Code Review Agent.

Analyzes Python source files for functional bugs, code quality issues, and
maintainability problems.

Issues targeted in sample-project/:
  SP-03 — update_todo silently succeeds when ID doesn't exist
  SP-04 — delete_todo silently succeeds when ID doesn't exist
  SP-07 — get_todos has no pagination (unbounded query)
  SP-08 — duplicate database connection logic across handlers
  SP-09 — magic string "todos" used in every handler
  SP-13 — unused import (datetime)

Constraints (SUBAGENT_SPEC.md §1):
  - Read-only; no command execution; no file modification.
  - Report only issues observable in the provided code.
"""
from __future__ import annotations

import ast
import re

from app.agents.base import BaseAgent
from app.models.finding import Finding, FixRisk, Severity, SourceAgent
from app.models.workflow import ProjectContext

# ── Patterns ────────────────────────────────────────────────────────────────

# mongo write operations whose result is NOT captured
_UNCHECKED_WRITE_RE = re.compile(
    r"""^\s*(?:db\[["']?\w+["']?\]\.)(update_one|update_many|delete_one|delete_many)\s*\(""",
    re.MULTILINE,
)

# mongo find without .limit()
_UNBOUNDED_FIND_RE = re.compile(
    r"""db\[["']?\w+["']?\]\.find\s*\([^)]*\)(?!\s*\.\s*limit)""",
    re.MULTILINE,
)

# magic string "todos" (collection name repeated inline)
_MAGIC_COLLECTION_RE = re.compile(r"""db\[["']todos["']\]""")

# MongoClient(...) constructed inline (not via a shared dependency)
_INLINE_CLIENT_RE = re.compile(r"""MongoClient\s*\(""")


class CodeReviewAgent(BaseAgent):
    """Detects functional bugs and code quality issues in Python source files."""

    @property
    def name(self) -> str:
        return "code_review"

    def analyze(self, context: ProjectContext) -> list[Finding]:
        findings: list[Finding] = []
        counter = 1

        source_paths = {f.path for f in context.source_files}

        for rel_path, content in context.file_contents.items():
            if rel_path not in source_paths:
                continue

            findings.extend(self._check_unchecked_writes(rel_path, content, counter))
            counter += len(findings) - (counter - 1)

            findings.extend(self._check_unbounded_find(rel_path, content, counter))
            counter = len(findings) + 1

            findings.extend(self._check_magic_collection_string(rel_path, content, counter))
            counter = len(findings) + 1

            findings.extend(self._check_duplicate_client(rel_path, content, counter))
            counter = len(findings) + 1

            findings.extend(self._check_unused_imports(rel_path, content, counter))
            counter = len(findings) + 1

        return findings

    # ── Individual checks ───────────────────────────────────────────────────

    def _check_unchecked_writes(
        self, path: str, content: str, start: int
    ) -> list[Finding]:
        """SP-03, SP-04 — write result not captured/checked."""
        out: list[Finding] = []
        n = start
        for m in _UNCHECKED_WRITE_RE.finditer(content):
            op = m.group(1)          # update_one | delete_one | …
            line_no = content[: m.start()].count("\n") + 1
            kind = "update" if "update" in op else "delete"
            out.append(Finding(
                id=f"CR-{n:03d}",
                source_agent=SourceAgent.CODE_REVIEW,
                title=f"Result of {op}() is not checked — silent {kind} of non-existent document",
                severity=Severity.HIGH,
                file=path,
                location=f"line {line_no}",
                explanation=(
                    f"The call to {op}() is not assigned to a variable, so "
                    f"matched_count / deleted_count is never verified. "
                    f"When the target document does not exist the function "
                    f"returns a 200 response anyway."
                ),
                impact=(
                    "API clients cannot tell whether the operation actually "
                    "affected a document. Clients sending a wrong ID receive "
                    "a success response."
                ),
                recommended_fix=(
                    f"Assign the result and check the count:\n"
                    f"  result = db[...].{op}(...)\n"
                    f"  if result.{'matched' if kind == 'update' else 'deleted'}"
                    f"_count == 0:\n"
                    f"      raise HTTPException(status_code=404, detail='Not found')"
                ),
                verification_method=(
                    "Call the endpoint with a non-existent ID and confirm "
                    "HTTP 404 is returned."
                ),
                fix_risk=FixRisk.SAFE,
            ))
            n += 1
        return out

    def _check_unbounded_find(
        self, path: str, content: str, start: int
    ) -> list[Finding]:
        """SP-07 — .find() without .limit()."""
        out: list[Finding] = []
        n = start
        for m in _UNBOUNDED_FIND_RE.finditer(content):
            line_no = content[: m.start()].count("\n") + 1
            out.append(Finding(
                id=f"CR-{n:03d}",
                source_agent=SourceAgent.CODE_REVIEW,
                title="Unbounded database query — no pagination or limit applied",
                severity=Severity.MEDIUM,
                file=path,
                location=f"line {line_no}",
                explanation=(
                    "The .find() call retrieves all documents from the collection "
                    "without a .limit() or skip/offset parameters. As the collection "
                    "grows this query becomes progressively slower and returns "
                    "unbounded amounts of data."
                ),
                impact=(
                    "Memory exhaustion and slow responses under load; "
                    "potential denial of service if the collection is large."
                ),
                recommended_fix=(
                    "Add a limit and optional skip parameter:\n"
                    "  db['todos'].find().skip(skip).limit(limit)\n"
                    "Accept limit and skip as query parameters with sensible defaults."
                ),
                verification_method=(
                    "Call GET /todos with a large collection and confirm only the "
                    "page size is returned."
                ),
                fix_risk=FixRisk.SAFE,
            ))
            n += 1
        return out

    def _check_magic_collection_string(
        self, path: str, content: str, start: int
    ) -> list[Finding]:
        """SP-09 — inline collection name string."""
        matches = _MAGIC_COLLECTION_RE.findall(content)
        if len(matches) < 2:  # one use is acceptable; multiple is a smell
            return []
        first_line = content[: _MAGIC_COLLECTION_RE.search(content).start()].count("\n") + 1  # type: ignore[union-attr]
        return [Finding(
            id=f"CR-{start:03d}",
            source_agent=SourceAgent.CODE_REVIEW,
            title='Magic string "todos" repeated as collection name in every handler',
            severity=Severity.MEDIUM,
            file=path,
            location=f"multiple locations (first at line {first_line})",
            explanation=(
                f'The collection name "todos" appears as a literal string '
                f"{len(matches)} times. A typo in any one occurrence would cause "
                f"a silent bug at runtime."
            ),
            impact=(
                "Maintenance burden; renaming the collection requires editing "
                "every handler individually."
            ),
            recommended_fix=(
                "Define a module-level constant:\n"
                "  TODOS_COLLECTION = 'todos'\n"
                "and reference it as db[TODOS_COLLECTION] throughout."
            ),
            verification_method=(
                "Search for db[\"todos\"] and confirm zero results after refactor."
            ),
            fix_risk=FixRisk.SAFE,
        )]

    def _check_duplicate_client(
        self, path: str, content: str, start: int
    ) -> list[Finding]:
        """SP-08 — MongoClient constructed at module level (shared across all handlers)."""
        matches = _INLINE_CLIENT_RE.findall(content)
        if len(matches) != 1:
            return []
        line_no = content[: _INLINE_CLIENT_RE.search(content).start()].count("\n") + 1  # type: ignore[union-attr]
        return [Finding(
            id=f"CR-{start:03d}",
            source_agent=SourceAgent.CODE_REVIEW,
            title="Database client constructed at module level with no dependency injection",
            severity=Severity.MEDIUM,
            file=path,
            location=f"line {line_no}",
            explanation=(
                "MongoClient is instantiated once at module import time and accessed "
                "globally in every route handler. This couples every handler directly "
                "to the database and makes the handlers impossible to unit-test in "
                "isolation without a real database."
            ),
            impact=(
                "Low testability; no connection pooling configuration; "
                "cannot swap the database implementation for testing."
            ),
            recommended_fix=(
                "Extract database access into a FastAPI dependency:\n"
                "  def get_db(): yield client['tododb']\n"
                "  @app.get('/todos')\n"
                "  def get_todos(db=Depends(get_db)): ..."
            ),
            verification_method=(
                "Unit tests can pass a mock database via the dependency "
                "without connecting to MongoDB."
            ),
            fix_risk=FixRisk.MODERATE,
        )]

    def _check_unused_imports(
        self, path: str, content: str, start: int
    ) -> list[Finding]:
        """SP-13 — unused import detected via AST."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []

        imported: dict[str, int] = {}  # name → line number
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported[name] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported[name] = node.lineno

        # Collect all names actually used in the AST (excluding import nodes)
        used: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used.add(node.value.id)

        out: list[Finding] = []
        n = start
        for name, line_no in imported.items():
            if name not in used:
                out.append(Finding(
                    id=f"CR-{n:03d}",
                    source_agent=SourceAgent.CODE_REVIEW,
                    title=f'Unused import: "{name}"',
                    severity=Severity.LOW,
                    file=path,
                    location=f"line {line_no}",
                    explanation=(
                        f'"{name}" is imported but never referenced in the file. '
                        "Unused imports add noise, increase import time, and can "
                        "mislead readers into thinking the module is a dependency."
                    ),
                    impact="Minor: code clarity and maintainability.",
                    recommended_fix=f'Remove the line: import {name}',
                    verification_method=(
                        "Run a linter (e.g. ruff) and confirm no unused-import "
                        "warnings remain."
                    ),
                    fix_risk=FixRisk.SAFE,
                ))
                n += 1
        return out
