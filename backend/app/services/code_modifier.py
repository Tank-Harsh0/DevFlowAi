"""
Code Modifier.

Applies approved fix proposals to repository files.

For each APPROVED proposal with a non-empty diff:
  1. Create a backup: file.py → file.py.bak
  2. Apply the change.
  3. Verify syntax with py_compile.
  4. If syntax check fails: revert from backup, mark proposal FAILED.
  5. Log every action to fix_application_log.json.

Constraints (ARCHITECTURE.md §3 Code Modifier, §10):
  - Only modifies files inside the target repository directory.
  - Creates backup before EVERY modification.
  - Reverts from backup on syntax failure.
  - All actions logged with CHANGE audit level.
  - Does not modify files outside the repository root.
"""
from __future__ import annotations

import py_compile
import shutil
import tempfile
from pathlib import Path

from app.core.logging import get_logger
from app.models.fix_proposal import FixProposal, ProposalStatus

logger = get_logger(__name__)


class CodeModifier:
    """Applies approved diffs to repository files with backup and safety checks."""

    def __init__(self, repository_root: str) -> None:
        self._root = Path(repository_root).resolve()

    def apply_approved(
        self, proposals: list[FixProposal]
    ) -> tuple[list[FixProposal], list[dict[str, object]]]:
        """Apply all APPROVED proposals that have a non-empty diff.

        Args:
            proposals: Fix proposals (after approval gate).

        Returns:
            Tuple of:
              - Updated proposals list (APPLIED or FAILED status).
              - fix_application_log entries (list of dicts).
        """
        log: list[dict[str, object]] = []
        updated: list[FixProposal] = []

        for proposal in proposals:
            if proposal.status != ProposalStatus.APPROVED or not proposal.diff:
                updated.append(proposal)
                continue

            result, entry = self._apply_one(proposal)
            updated.append(result)
            log.append(entry)

        applied = sum(1 for p in updated if p.status == ProposalStatus.APPLIED)
        failed  = sum(1 for p in updated if p.status == ProposalStatus.FAILED)
        logger.info(
            "Code Modifier: %d applied, %d failed, %d skipped/rejected",
            applied, failed,
            len(proposals) - applied - failed,
        )
        return updated, log

    # ------------------------------------------------------------------
    # Single-proposal application
    # ------------------------------------------------------------------

    def _apply_one(
        self, proposal: FixProposal
    ) -> tuple[FixProposal, dict[str, object]]:
        """Apply one proposal. Returns updated proposal + log entry."""
        # Identify target file (use first file in files_affected)
        if not proposal.files_affected:
            return (
                proposal.model_copy(update={"status": ProposalStatus.FAILED}),
                self._log_entry(proposal, "FAILED", "No files_affected listed"),
            )

        rel_path = proposal.files_affected[0]
        target = (self._root / rel_path).resolve()

        # Safety: never modify outside the repository root
        try:
            target.relative_to(self._root)
        except ValueError:
            msg = f"Path escape attempt blocked: {target}"
            logger.error(msg)
            return (
                proposal.model_copy(update={"status": ProposalStatus.FAILED}),
                self._log_entry(proposal, "FAILED", msg),
            )

        if not target.exists():
            msg = f"Target file not found: {target}"
            logger.warning(msg)
            return (
                proposal.model_copy(update={"status": ProposalStatus.FAILED}),
                self._log_entry(proposal, "FAILED", msg),
            )

        original = target.read_text(encoding="utf-8")
        backup = Path(str(target) + ".bak")

        # 1. Create backup
        shutil.copy2(target, backup)
        logger.info("CHANGE: backup created: %s", backup)

        # 2. Apply the diff → produce new content
        new_content = _apply_unified_diff(original, proposal.diff)

        # 3. Write new content
        target.write_text(new_content, encoding="utf-8")
        logger.info("CHANGE: %s written", target)

        # 4. Syntax check
        syntax_ok, syntax_error = _check_syntax(target)
        if not syntax_ok:
            # Revert
            shutil.copy2(backup, target)
            logger.warning(
                "Syntax check failed for %s — reverted. Error: %s", target, syntax_error
            )
            return (
                proposal.model_copy(update={"status": ProposalStatus.FAILED}),
                self._log_entry(
                    proposal, "FAILED",
                    f"Syntax error after apply; reverted from backup. {syntax_error}",
                    backup_path=str(backup),
                ),
            )

        logger.info("CHANGE: %s applied and verified (syntax OK)", rel_path)
        return (
            proposal.model_copy(update={"status": ProposalStatus.APPLIED}),
            self._log_entry(
                proposal, "APPLIED", "Applied and syntax check passed",
                backup_path=str(backup),
            ),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _log_entry(
        proposal: FixProposal,
        outcome: str,
        message: str,
        backup_path: str = "",
    ) -> dict[str, object]:
        return {
            "finding_id": proposal.finding_id,
            "fix_risk": proposal.fix_risk.value,
            "files_affected": proposal.files_affected,
            "outcome": outcome,
            "message": message,
            "backup_path": backup_path,
        }


# ---------------------------------------------------------------------------
# Diff application
# ---------------------------------------------------------------------------


def _apply_unified_diff(original: str, diff: str) -> str:
    """Apply a unified diff to *original* and return the patched content.

    Handles the output of difflib.unified_diff (with default lineterm).
    Each diff line retains its own newline from the source or diff.
    """
    import re as _re  # noqa: PLC0415

    if not diff:
        return original

    hunk_re = _re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

    original_lines = original.splitlines(keepends=True)
    result: list[str] = list(original_lines)
    offset = 0  # cumulative line-count shift from already-applied hunks

    diff_lines = diff.splitlines(keepends=True)
    i = 0
    # Skip --- / +++ header lines
    while i < len(diff_lines) and diff_lines[i].startswith(("---", "+++")):
        i += 1

    while i < len(diff_lines):
        m = hunk_re.match(diff_lines[i])
        if not m:
            i += 1
            continue

        src_start = int(m.group(1)) - 1  # convert to 0-based
        i += 1

        # Collect the hunk body until the next @@ or end
        body: list[tuple[str, str]] = []
        while i < len(diff_lines):
            dl = diff_lines[i]
            if hunk_re.match(dl):
                break
            if dl.startswith("\\ "):  # "\ No newline at end of file"
                i += 1
                continue
            if dl.startswith(" "):
                body.append((" ", dl[1:]))
            elif dl.startswith("-"):
                body.append(("-", dl[1:]))
            elif dl.startswith("+"):
                body.append(("+", dl[1:]))
            i += 1

        # Replace lines in result
        adj_start = src_start + offset
        src_count = sum(1 for t, _ in body if t in (" ", "-"))
        new_lines  = [ln for t, ln in body if t in (" ", "+")]

        result[adj_start : adj_start + src_count] = new_lines
        offset += len(new_lines) - src_count

    return "".join(result)


def _check_syntax(path: Path) -> tuple[bool, str]:
    """Return (True, "") if the file is syntactically valid Python, else (False, error)."""
    if path.suffix.lower() != ".py":
        return True, ""   # only check Python files
    try:
        py_compile.compile(str(path), doraise=True)
        return True, ""
    except py_compile.PyCompileError as exc:
        return False, str(exc)
