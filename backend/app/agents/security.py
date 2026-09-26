"""
Security Agent.

Identifies security-relevant issues in source code and manifests via
static analysis only.

Issues targeted in sample-project/:
  SP-01 — hardcoded MongoDB connection string with credentials
  SP-02 — no input validation on todo text
  SP-05 — ObjectId not validated before use (invalid ID → 500 crash)

Mandatory disclaimer (SUBAGENT_SPEC.md §3):
  Output is wrapped in SecurityAgentOutput which includes the disclaimer field.

Constraints:
  - Must not claim the project is completely secure.
  - Must not claim to have performed dynamic testing.
  - All findings are high or critical fix_risk by default.
  - Flag only issues with evidence in the provided code.
"""
from __future__ import annotations

import re

from app.agents.base import BaseAgent
from app.models.finding import Finding, FixRisk, SecurityAgentOutput, Severity, SourceAgent
from app.models.workflow import ProjectContext

# ── Patterns ────────────────────────────────────────────────────────────────

# MongoClient("mongodb://...") with inline credentials
_HARDCODED_URI_RE = re.compile(
    r"""MongoClient\s*\(\s*["']mongodb://[^"']*:[^"']+@[^"']+["']""",
    re.MULTILINE,
)

# Route handlers that accept a raw dict input without a Pydantic model
_RAW_DICT_PARAM_RE = re.compile(
    r"""def \w+\([^)]*:\s*dict\b""",
    re.MULTILINE,
)

# ObjectId() called directly with a user-supplied variable (no prior validation)
_UNVALIDATED_OBJECTID_RE = re.compile(
    r"""ObjectId\s*\(\s*\w+_id\s*\)""",
    re.MULTILINE,
)


class SecurityAgent(BaseAgent):
    """Detects security issues via static analysis of source and manifest files."""

    @property
    def name(self) -> str:
        return "security"

    def analyze(self, context: ProjectContext) -> list[Finding]:
        """Return findings list (without disclaimer wrapper).

        The orchestrator calls safe_analyze() → analyze(), then wraps
        the list in SecurityAgentOutput when writing to disk.
        """
        findings: list[Finding] = []
        n = 1

        source_paths = {f.path for f in context.source_files}

        for rel_path, content in context.file_contents.items():
            if rel_path not in source_paths:
                continue

            hardcoded = self._check_hardcoded_credentials(rel_path, content, n)
            findings.extend(hardcoded)
            n += len(hardcoded)

            raw_dict = self._check_unvalidated_input(rel_path, content, n)
            findings.extend(raw_dict)
            n += len(raw_dict)

            objectid = self._check_unvalidated_objectid(rel_path, content, n)
            findings.extend(objectid)
            n += len(objectid)

        return findings

    def analyze_with_disclaimer(self, context: ProjectContext) -> SecurityAgentOutput:
        """Run analysis and return the full output including the mandatory disclaimer."""
        return SecurityAgentOutput(findings=self.safe_analyze(context))

    # ── Checks ──────────────────────────────────────────────────────────────

    def _check_hardcoded_credentials(
        self, path: str, content: str, start: int
    ) -> list[Finding]:
        """SP-01 — hardcoded connection string."""
        out: list[Finding] = []
        n = start
        for m in _HARDCODED_URI_RE.finditer(content):
            line_no = content[: m.start()].count("\n") + 1
            out.append(Finding(
                id=f"SA-{n:03d}",
                source_agent=SourceAgent.SECURITY,
                title="Database connection string with credentials hardcoded in source code",
                severity=Severity.CRITICAL,
                file=path,
                location=f"line {line_no}",
                explanation=(
                    "The MongoDB connection string, including the username and "
                    "password, is written as a string literal in the source file. "
                    "Anyone with read access to this file — or to the repository "
                    "history — can obtain the database credentials."
                ),
                impact=(
                    "Credential exposure in version control. Unauthorized database "
                    "access if the repository is public or shared. Credentials "
                    "cannot be rotated without changing source code."
                ),
                recommended_fix=(
                    "Read the connection string from an environment variable:\n"
                    "  import os\n"
                    "  MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')\n"
                    "  client = MongoClient(MONGODB_URI)\n"
                    "Add MONGODB_URI to .env.example. Ensure .env is in .gitignore."
                ),
                verification_method=(
                    "Search the source file for 'MongoClient(' and confirm no "
                    "string literal containing credentials is present."
                ),
                fix_risk=FixRisk.SAFE,
            ))
            n += 1
        return out

    def _check_unvalidated_input(
        self, path: str, content: str, start: int
    ) -> list[Finding]:
        """SP-02 — route handler accepts raw dict instead of Pydantic model."""
        out: list[Finding] = []
        n = start
        for m in _RAW_DICT_PARAM_RE.finditer(content):
            line_no = content[: m.start()].count("\n") + 1
            fn_name = re.match(r"def (\w+)", m.group().strip())
            fn_label = fn_name.group(1) if fn_name else "unknown function"
            out.append(Finding(
                id=f"SA-{n:03d}",
                source_agent=SourceAgent.SECURITY,
                title=f"No input validation in {fn_label}() — accepts arbitrary dict",
                severity=Severity.CRITICAL,
                file=path,
                location=f"line {line_no}, {fn_label}()",
                explanation=(
                    f"{fn_label}() accepts its request body as a plain Python "
                    "dict with no schema validation. FastAPI will pass any JSON "
                    "object — including empty payloads, excessively large payloads, "
                    "or payloads containing unexpected keys — directly to the "
                    "database insertion call."
                ),
                impact=(
                    "Empty strings, null values, and unexpected fields are "
                    "persisted to the database without restriction. An attacker "
                    "can inject arbitrary data. No length limits prevent resource "
                    "exhaustion."
                ),
                recommended_fix=(
                    "Define a Pydantic model for the request body:\n"
                    "  class TodoCreate(BaseModel):\n"
                    "      text: str = Field(..., min_length=1, max_length=500)\n"
                    f"Replace the dict parameter with the model:\n"
                    f"  def {fn_label}(todo: TodoCreate): ..."
                ),
                verification_method=(
                    "POST /todos with an empty body and confirm HTTP 422 "
                    "(Unprocessable Entity) is returned."
                ),
                fix_risk=FixRisk.SAFE,
            ))
            n += 1
        return out

    def _check_unvalidated_objectid(
        self, path: str, content: str, start: int
    ) -> list[Finding]:
        """SP-05 — ObjectId() called without prior validation."""
        out: list[Finding] = []
        n = start
        for m in _UNVALIDATED_OBJECTID_RE.finditer(content):
            line_no = content[: m.start()].count("\n") + 1
            out.append(Finding(
                id=f"SA-{n:03d}",
                source_agent=SourceAgent.SECURITY,
                title="User-supplied ID passed to ObjectId() without validation — causes 500 crash",
                severity=Severity.HIGH,
                file=path,
                location=f"line {line_no}",
                explanation=(
                    "bson.ObjectId() raises bson.errors.InvalidId when the "
                    "supplied string is not a valid 24-character hex ObjectId. "
                    "This exception is not caught, so any request with a "
                    "malformed ID returns an HTTP 500 Internal Server Error."
                ),
                impact=(
                    "Any client or attacker can trivially trigger 500 errors by "
                    "sending a non-hex ID. Unhandled exceptions may leak "
                    "stack traces depending on server configuration."
                ),
                recommended_fix=(
                    "Validate the ID format before calling ObjectId():\n"
                    "  from bson import ObjectId\n"
                    "  from bson.errors import InvalidId\n"
                    "  try:\n"
                    "      oid = ObjectId(todo_id)\n"
                    "  except InvalidId:\n"
                    "      raise HTTPException(status_code=400, "
                    "detail='Invalid ID format')"
                ),
                verification_method=(
                    "Send a request with id='abc' and confirm HTTP 400 is "
                    "returned, not 500."
                ),
                fix_risk=FixRisk.SAFE,
            ))
            n += 1
        return out
