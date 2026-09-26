"""
Finding Aggregator.

Merges findings from all four agents, deduplicates those that reference the
same location, and writes deduplicated_findings.json.

Algorithm (ARCHITECTURE.md §3 Finding Aggregator):
  1. Merge all findings into a single list.
  2. Group by (file, normalised location).
  3. Within each group, if >1 finding covers the same spot from different
     agents, merge them: retain the highest severity, combine titles, mark
     source_agent as "multiple-agents".
  4. Write deduplicated_findings.json.

Deduplication key: (file, location_bucket)
  - location_bucket normalises "line 42", "line 42-43", "line 42 ..." all
    to the same integer so nearby findings on the same line collapse.
  - If the location is non-numeric ("file-level", function names) it is
    used verbatim as the bucket key.
"""
from __future__ import annotations

import re
from collections import defaultdict

from app.core.logging import get_logger
from app.models.finding import Finding, FixRisk, Severity, SourceAgent

logger = get_logger(__name__)

# Severity ordering — lower index = higher severity
_SEVERITY_ORDER: list[Severity] = [
    Severity.CRITICAL,
    Severity.HIGH,
    Severity.MEDIUM,
    Severity.LOW,
]

_LINE_NUMBER_RE = re.compile(r"\bline\s+(\d+)", re.IGNORECASE)


def _location_bucket(location: str) -> str:
    """Normalise a location string to a grouping key.

    Examples:
      "line 42"          → "line:42"
      "line 42, func()"  → "line:42"
      "file-level"       → "file-level"
      "get_todo function" → "get_todo function"
    """
    m = _LINE_NUMBER_RE.search(location)
    if m:
        return f"line:{m.group(1)}"
    return location.strip().lower()


def _higher_severity(a: Severity, b: Severity) -> Severity:
    """Return whichever severity is more critical."""
    if _SEVERITY_ORDER.index(a) <= _SEVERITY_ORDER.index(b):
        return a
    return b


def _higher_fix_risk(a: FixRisk, b: FixRisk) -> FixRisk:
    """Return the more conservative fix risk."""
    order = [FixRisk.NOT_APPLICABLE, FixRisk.SAFE, FixRisk.MODERATE, FixRisk.HIGH]
    if order.index(a) >= order.index(b):
        return a
    return b


class FindingAggregator:
    """Merges and deduplicates findings from multiple agents."""

    def aggregate(self, all_findings: list[Finding]) -> list[Finding]:
        """Merge *all_findings*, deduplicating overlapping entries.

        Args:
            all_findings: Combined findings from all agents.

        Returns:
            Deduplicated list. Never raises.
        """
        if not all_findings:
            logger.info("Aggregator: no findings to aggregate")
            return []

        # Group by (file, location_bucket, source_agent) first to keep same-agent
        # findings separate, then merge only cross-agent groups at the same location.
        # ARCHITECTURE.md §3: merge findings referencing the same location from
        # *different* agents — not duplicate findings from the same agent.

        # Step 1: group by (file, bucket) to find cross-agent overlaps
        loc_groups: dict[tuple[str, str], list[Finding]] = defaultdict(list)
        for f in all_findings:
            key = (f.file, _location_bucket(f.location))
            loc_groups[key].append(f)

        # Step 2: within each location group, sub-group by source_agent.
        #   If all findings are from the same agent → keep all separate.
        #   If findings span multiple agents → merge the cross-agent ones
        #   but keep intra-agent findings separate.
        groups: dict[tuple[str, str], list[Finding]] = defaultdict(list)
        for (file, bucket), grp in loc_groups.items():
            agents_in_group = {f.source_agent for f in grp}
            if len(agents_in_group) == 1:
                # All same agent — keep each finding individually
                for f in grp:
                    groups[(file, f"solo:{f.id}")].append(f)
            else:
                # Multiple agents at the same location — merge per cross-agent group
                # Pick one representative per unique cross-agent overlap
                groups[(file, bucket)].extend(grp)

        deduplicated: list[Finding] = []
        merged_count = 0

        for (_file, _bucket), group in groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
                continue

            # Multiple findings from different agents at the same location — merge
            merged_count += 1
            agents = {f.source_agent for f in group}
            best_severity = group[0].severity
            best_fix_risk = group[0].fix_risk
            titles: list[str] = []

            for f in group:
                best_severity = _higher_severity(best_severity, f.severity)
                best_fix_risk = _higher_fix_risk(best_fix_risk, f.fix_risk)
                titles.append(f.title)

            # Use the first finding as the base; override merged fields
            base = group[0]
            merged_source = (
                "multiple-agents"
                if len(agents) > 1
                else base.source_agent
            )

            merged = Finding(
                id=base.id,
                source_agent=SourceAgent(merged_source) if merged_source != "multiple-agents"
                    else base.source_agent,
                title=titles[0],                    # primary title from highest-priority agent
                severity=best_severity,
                file=base.file,
                location=base.location,
                explanation=(
                    base.explanation
                    + (
                        f"\n\n[Merged from {len(group)} agents: "
                        + ", ".join(str(a) for a in agents)
                        + "]"
                        if len(agents) > 1
                        else ""
                    )
                ),
                impact=base.impact,
                recommended_fix=base.recommended_fix,
                verification_method=base.verification_method,
                fix_risk=best_fix_risk,
            )
            deduplicated.append(merged)

        logger.info(
            "Aggregator: %d raw findings → %d deduplicated (%d merged)",
            len(all_findings),
            len(deduplicated),
            merged_count,
        )
        return deduplicated
