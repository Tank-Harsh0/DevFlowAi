"""
Fix Planner.

For each finding in the prioritized list, determines:
  - Whether a code fix is applicable (NOT_APPLICABLE findings → skip).
  - The fix risk (carried directly from the Finding).
  - A concrete unified diff for SAFE and MODERATE fixes.
  - A written recommendation for HIGH risk fixes (no diff applied).

Output: fix_plan.json  — list of FixProposal objects.

Constraints (ARCHITECTURE.md §3):
  - Does not modify any files.
  - Produces diffs by generating the intended new content and diffing in memory.
  - HIGH risk fixes: no diff, status=PENDING, marked recommendation-only.
  - NOT_APPLICABLE findings: excluded from the plan entirely.
"""
from __future__ import annotations

import difflib
import re

from app.core.logging import get_logger
from app.models.finding import Finding, FixRisk
from app.models.fix_proposal import FixProposal, ProposalStatus

logger = get_logger(__name__)


class FixPlanner:
    """Generates fix proposals from prioritized findings."""

    def plan(
        self,
        findings: list[Finding],
        file_contents: dict[str, str],
    ) -> list[FixProposal]:
        """Create one FixProposal per actionable finding.

        Args:
            findings:      Prioritized findings (from IssuePrioritizer).
            file_contents: Dict of relative_path → file content
                           (from ProjectContext.file_contents).

        Returns:
            List of FixProposal objects.  NOT_APPLICABLE findings are skipped.
        """
        proposals: list[FixProposal] = []

        for finding in findings:
            if finding.fix_risk == FixRisk.NOT_APPLICABLE:
                logger.debug(
                    "Skipping %s — fix_risk=not_applicable", finding.id
                )
                continue

            proposal = self._build_proposal(finding, file_contents)
            if proposal:
                proposals.append(proposal)

        logger.info(
            "Fix Planner: %d findings → %d proposals",
            len(findings),
            len(proposals),
        )
        return proposals

    # ------------------------------------------------------------------
    # Per-finding proposal builders
    # ------------------------------------------------------------------

    def _build_proposal(
        self, finding: Finding, file_contents: dict[str, str]
    ) -> FixProposal | None:
        """Dispatch to the appropriate fix builder based on finding ID prefix."""
        builders = {
            "CR-": self._fix_code_review,
            "SA-": self._fix_security,
            "DA-": self._fix_documentation,
            # TA- findings are all NOT_APPLICABLE; handled above
        }
        for prefix, builder in builders.items():
            if finding.id.startswith(prefix):
                return builder(finding, file_contents)

        # Unknown prefix — generate a generic recommendation-only proposal
        return self._generic_proposal(finding)

    # ------------------------------------------------------------------
    # Code Review fixes
    # ------------------------------------------------------------------

    def _fix_code_review(
        self, finding: Finding, file_contents: dict[str, str]
    ) -> FixProposal | None:
        content = file_contents.get(finding.file, "")
        if not content:
            return self._generic_proposal(finding)

        title_lower = finding.title.lower()

        if "update_one" in title_lower or "update" in title_lower and "unchecked" in title_lower:
            return self._fix_unchecked_write(finding, content, "update_one", "matched")
        if "delete_one" in title_lower or "delete" in title_lower and "unchecked" in title_lower:
            return self._fix_unchecked_write(finding, content, "delete_one", "deleted")
        if "unbounded" in title_lower or "pagination" in title_lower:
            return self._fix_unbounded_query(finding, content)
        if "unused import" in title_lower:
            return self._fix_unused_import(finding, content)
        if "magic string" in title_lower or "collection name" in title_lower:
            return self._fix_magic_string(finding, content)
        if "module level" in title_lower or "dependency injection" in title_lower:
            # Moderate risk — provide recommendation only (no auto-diff)
            return FixProposal(
                finding_id=finding.id,
                fix_risk=finding.fix_risk,
                description=(
                    "Extract the database client into a FastAPI dependency function "
                    "so each route handler receives a db reference via Depends()."
                ),
                rationale=finding.explanation,
                files_affected=[finding.file],
                diff="",    # moderate — diff shown to developer after approval
                verification_method=finding.verification_method,
                status=ProposalStatus.PENDING,
            )

        return self._generic_proposal(finding)

    def _fix_unchecked_write(
        self,
        finding: Finding,
        content: str,
        operation: str,
        count_attr: str,
    ) -> FixProposal:
        """Wrap the unchecked db write call to check the result count."""
        # Find the call start with a simple header pattern, then extract the
        # full call by counting parentheses so multi-line args are handled.
        header_pattern = re.compile(
            rf"""([ \t]*)(db\[["'][^"']+["']\]\.{operation}\s*)(\()""",
            re.MULTILINE,
        )
        new_content = content
        m = header_pattern.search(content)
        if m:
            indent = m.group(1)
            prefix = m.group(2)          # e.g. 'db["todos"].update_one'
            paren_start = m.start(3)     # position of the opening '('
            # Walk forward balancing parentheses to find the full call end
            call_end = _find_closing_paren(content, paren_start)
            full_call = prefix + content[paren_start: call_end + 1]
            replacement = (
                f"{indent}result = {full_call}\n"
                f"{indent}if result.{count_attr}_count == 0:\n"
                f'{indent}    raise HTTPException(status_code=404, detail="Not found")'
            )
            new_content = content[: m.start()] + replacement + content[call_end + 1 :]

        diff = _unified_diff(content, new_content, finding.file)
        return FixProposal(
            finding_id=finding.id,
            fix_risk=finding.fix_risk,
            description=(
                f"Assign the result of {operation}() and raise HTTP 404 "
                "when the matched/deleted count is zero."
            ),
            rationale=finding.explanation,
            files_affected=[finding.file],
            diff=diff,
            verification_method=finding.verification_method,
            status=ProposalStatus.PENDING,
        )

    def _fix_unbounded_query(self, finding: Finding, content: str) -> FixProposal:
        """Add .limit(100) to the bare .find() call as a safe default."""
        pattern = re.compile(
            r"""(db\[["'][^"']+["']\]\.find\s*\([^)]*\))(?!\s*\.\s*limit)""",
            re.MULTILINE,
        )
        new_content = pattern.sub(r"\1.limit(100)", content)
        diff = _unified_diff(content, new_content, finding.file)
        return FixProposal(
            finding_id=finding.id,
            fix_risk=finding.fix_risk,
            description="Add .limit(100) to the unbounded .find() call as a safe default cap.",
            rationale=finding.explanation,
            files_affected=[finding.file],
            diff=diff,
            verification_method=finding.verification_method,
            status=ProposalStatus.PENDING,
        )

    def _fix_unused_import(self, finding: Finding, content: str) -> FixProposal:
        """Remove the unused import line."""
        # Extract the import name from the finding title: 'Unused import: "datetime"'
        m = re.search(r'"([^"]+)"', finding.title)
        name = m.group(1) if m else None
        new_content = content
        if name:
            # Remove the line that imports this name
            lines = content.splitlines(keepends=True)
            new_lines = [
                ln for ln in lines
                if not re.match(
                    rf"""^\s*import\s+{re.escape(name)}\s*(#.*)?$""", ln.rstrip()
                )
            ]
            new_content = "".join(new_lines)

        diff = _unified_diff(content, new_content, finding.file)
        return FixProposal(
            finding_id=finding.id,
            fix_risk=finding.fix_risk,
            description=f'Remove the unused import: "{name}".',
            rationale=finding.explanation,
            files_affected=[finding.file],
            diff=diff,
            verification_method=finding.verification_method,
            status=ProposalStatus.PENDING,
        )

    def _fix_magic_string(self, finding: Finding, content: str) -> FixProposal:
        """Replace inline 'todos' collection references with a constant."""
        constant = "TODOS_COLLECTION = 'todos'"
        # Add constant after the last import block
        import_end = 0
        for m in re.finditer(r"^(?:import|from)\s+\S+", content, re.MULTILINE):
            import_end = m.end()

        # Replace all db["todos"] / db['todos'] with db[TODOS_COLLECTION]
        new_content = re.sub(r"""db\[["']todos["']\]""", "db[TODOS_COLLECTION]", content)
        # Insert the constant after the last import
        insert_pos = content.find("\n", import_end) + 1
        new_content = (
            new_content[:insert_pos]
            + f"\n{constant}\n"
            + new_content[insert_pos:]
        )
        diff = _unified_diff(content, new_content, finding.file)
        return FixProposal(
            finding_id=finding.id,
            fix_risk=finding.fix_risk,
            description=(
                "Extract the 'todos' collection name into a module-level constant "
                "TODOS_COLLECTION and reference it everywhere."
            ),
            rationale=finding.explanation,
            files_affected=[finding.file],
            diff=diff,
            verification_method=finding.verification_method,
            status=ProposalStatus.PENDING,
        )

    # ------------------------------------------------------------------
    # Security fixes
    # ------------------------------------------------------------------

    def _fix_security(
        self, finding: Finding, file_contents: dict[str, str]
    ) -> FixProposal | None:
        content = file_contents.get(finding.file, "")
        if not content:
            return self._generic_proposal(finding)

        title_lower = finding.title.lower()

        if "hardcoded" in title_lower or "connection string" in title_lower:
            return self._fix_hardcoded_uri(finding, content)
        if "input validation" in title_lower or "arbitrary dict" in title_lower:
            return self._fix_raw_dict_input(finding, content)
        if "objectid" in title_lower or "invalid id" in title_lower:
            return self._fix_unvalidated_objectid(finding, content)

        return self._generic_proposal(finding)

    def _fix_hardcoded_uri(self, finding: Finding, content: str) -> FixProposal:
        """Replace the hardcoded MongoClient URI with os.getenv()."""
        pattern = re.compile(
            r"""MongoClient\s*\(\s*["']mongodb://[^"']+["']\s*\)""",
            re.MULTILINE,
        )
        new_content = content
        if pattern.search(content):
            # Ensure os is imported
            if "import os" not in content:
                new_content = "import os\n" + content
            new_content = pattern.sub(
                "MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))",
                new_content,
            )
        diff = _unified_diff(content, new_content, finding.file)
        return FixProposal(
            finding_id=finding.id,
            fix_risk=finding.fix_risk,
            description=(
                "Read the MongoDB URI from the MONGODB_URI environment variable "
                "instead of hardcoding it in source."
            ),
            rationale=finding.explanation,
            files_affected=[finding.file],
            diff=diff,
            verification_method=finding.verification_method,
            status=ProposalStatus.PENDING,
        )

    def _fix_raw_dict_input(self, finding: Finding, content: str) -> FixProposal:
        """Add a note — this is moderate risk (requires Pydantic model addition)."""
        return FixProposal(
            finding_id=finding.id,
            fix_risk=FixRisk.MODERATE,
            description=(
                "Replace the raw `dict` parameter with a Pydantic model "
                "(e.g. class TodoCreate(BaseModel): text: str = Field(..., min_length=1)). "
                "This requires adding a new model class — moderate risk."
            ),
            rationale=finding.explanation,
            files_affected=[finding.file],
            diff="",   # moderate — developer reviews before applying
            verification_method=finding.verification_method,
            status=ProposalStatus.PENDING,
        )

    def _fix_unvalidated_objectid(self, finding: Finding, content: str) -> FixProposal:
        """Wrap each ObjectId(todo_id) call in a try/except."""
        pattern = re.compile(
            r"""([ \t]*)(todo\w*_id\s*=\s*[^\n]*\n)?([ \t]*)(ObjectId\s*\(\s*(\w+_id)\s*\))""",
            re.MULTILINE,
        )

        def _wrap(m: re.Match) -> str:  # type: ignore[type-arg]
            indent = m.group(3) or m.group(1) or "    "
            inner = m.group(4)
            var_name = m.group(5)
            prefix = m.group(1) or ""
            pre = m.group(2) or ""
            return (
                f"{pre}{prefix}try:\n"
                f"{indent}    _oid = {inner}\n"
                f"{indent}except Exception:\n"
                f"{indent}    raise HTTPException(status_code=400, "
                f"detail='Invalid ID format')\n"
                f"{indent}{var_name.replace('_id', '')} = {{'_id': _oid}}"
            )

        new_content = pattern.sub(_wrap, content)
        diff = _unified_diff(content, new_content, finding.file)
        return FixProposal(
            finding_id=finding.id,
            fix_risk=finding.fix_risk,
            description=(
                "Wrap the ObjectId() call in a try/except and raise HTTP 400 "
                "for invalid ID formats."
            ),
            rationale=finding.explanation,
            files_affected=[finding.file],
            diff=diff,
            verification_method=finding.verification_method,
            status=ProposalStatus.PENDING,
        )

    # ------------------------------------------------------------------
    # Documentation fixes
    # ------------------------------------------------------------------

    def _fix_documentation(
        self, finding: Finding, file_contents: dict[str, str]
    ) -> FixProposal | None:
        """Documentation fixes are safe but require human editing — no auto-diff."""
        return FixProposal(
            finding_id=finding.id,
            fix_risk=FixRisk.SAFE,
            description=(
                f"Address the documentation issue: {finding.title}. "
                "This requires manual editing of the relevant document."
            ),
            rationale=finding.explanation,
            files_affected=[finding.file],
            diff="",  # cannot auto-generate documentation content
            verification_method=finding.verification_method,
            status=ProposalStatus.PENDING,
        )

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    def _generic_proposal(self, finding: Finding) -> FixProposal:
        return FixProposal(
            finding_id=finding.id,
            fix_risk=finding.fix_risk,
            description=finding.recommended_fix,
            rationale=finding.explanation,
            files_affected=[finding.file],
            diff="",
            verification_method=finding.verification_method,
            status=ProposalStatus.PENDING,
        )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _find_closing_paren(text: str, open_pos: int) -> int:
    """Return the index of the ')' that closes the '(' at *open_pos*.

    Handles nested parentheses. Returns *open_pos* if not found.
    """
    depth = 0
    for i in range(open_pos, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return open_pos  # malformed — return start as fallback


def _unified_diff(original: str, modified: str, filename: str) -> str:
    """Generate a unified diff string between two file contents."""
    if original == modified:
        return ""
    # Use default lineterm so each header line gets its own newline.
    diff_lines = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    ))
    return "".join(diff_lines)
