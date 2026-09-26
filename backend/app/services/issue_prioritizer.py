"""
Issue Prioritizer.

Sorts deduplicated findings by severity (Critical → High → Medium → Low),
then alphabetically by file path within the same severity level.

ARCHITECTURE.md §3 Issue Prioritizer:
  Input:  deduplicated_findings.json
  Output: prioritized_findings.json
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.models.finding import Finding, Severity

logger = get_logger(__name__)

_SEVERITY_RANK: dict[Severity, int] = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
}


class IssuePrioritizer:
    """Sorts a deduplicated finding list by severity then file path."""

    def prioritize(self, findings: list[Finding]) -> list[Finding]:
        """Return findings sorted Critical → High → Medium → Low.

        Within the same severity, findings are sorted by file path so the
        output is deterministic and easy to scan.

        Args:
            findings: Deduplicated findings from FindingAggregator.

        Returns:
            New sorted list. Input list is not modified.
        """
        if not findings:
            return []

        sorted_findings = sorted(
            findings,
            key=lambda f: (_SEVERITY_RANK[f.severity], f.file, f.id),
        )

        counts = {s: 0 for s in Severity}
        for f in sorted_findings:
            counts[f.severity] += 1

        logger.info(
            "Prioritizer: %d findings — critical=%d high=%d medium=%d low=%d",
            len(sorted_findings),
            counts[Severity.CRITICAL],
            counts[Severity.HIGH],
            counts[Severity.MEDIUM],
            counts[Severity.LOW],
        )
        return sorted_findings
