"""
Finding domain model.

Schema defined in ARCHITECTURE.md §4 and SUBAGENT_SPEC.md.
All four analysis agents produce lists of Finding objects.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FixRisk(StrEnum):
    SAFE = "safe"
    MODERATE = "moderate"
    HIGH = "high"
    NOT_APPLICABLE = "not_applicable"


class SourceAgent(StrEnum):
    CODE_REVIEW = "code_review"
    TEST_ANALYSIS = "test_analysis"
    SECURITY = "security"
    DOCUMENTATION = "documentation"


class Finding(BaseModel):
    """A single issue found by an analysis agent.

    Schema matches ARCHITECTURE.md §4 Finding Object exactly.
    """

    id: str                        # e.g. "CR-001"
    source_agent: SourceAgent
    title: str
    severity: Severity
    file: str                      # relative path, or "unknown"
    location: str                  # line number, function name, or "file-level"
    explanation: str
    impact: str
    recommended_fix: str
    verification_method: str
    fix_risk: FixRisk


class SecurityAgentOutput(BaseModel):
    """Wrapper for Security Agent output.

    SUBAGENT_SPEC.md §3 requires a mandatory disclaimer field at the top level.
    """

    disclaimer: str = (
        "This analysis is limited to static code inspection. "
        "It does not guarantee that the project is free from all security vulnerabilities. "
        "Dynamic, runtime, or infrastructure-level vulnerabilities are not covered."
    )
    findings: list[Finding]
