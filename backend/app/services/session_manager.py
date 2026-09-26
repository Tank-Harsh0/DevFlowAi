"""
Session Manager.

Creates and manages the per-run session output directory.
Writes structured audit log entries to session.log.

Session directory layout (per ARCHITECTURE.md §5):

    devflow_sessions/
    └── {session_id}/          e.g. 20260926T130000
        ├── project_context.json
        ├── execution_plan.json
        ├── findings_*.json
        ├── ...
        └── session.log

The session_id is a compact ISO-8601 timestamp: YYYYMMDDTHHmmss.
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)

# Root directory for all sessions — relative to the working directory of the process.
# In production this would be configurable; for the MVP it lives next to the runner.
SESSIONS_ROOT = Path("devflow_sessions")

# Audit log levels (ARCHITECTURE.md §11)
_AUDIT_LEVELS = {"INFO", "WARNING", "ERROR", "DECISION", "CHANGE"}


class SessionManager:
    """Creates and manages a single workflow session directory."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.session_dir: Path = SESSIONS_ROOT / session_id
        self._log_path: Path = self.session_dir / "session.log"
        self._file_handler: logging.FileHandler | None = None

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def create(self) -> Path:
        """Create the session directory and open the audit log file.

        Returns the session directory path.
        Raises FileExistsError if the session directory already exists.
        """
        if self.session_dir.exists():
            raise FileExistsError(f"Session directory already exists: {self.session_dir}")
        self.session_dir.mkdir(parents=True, exist_ok=False)
        self._open_log()
        self.log("INFO", "SessionManager", f"Session {self.session_id} started")
        logger.info("Session directory created: %s", self.session_dir)
        return self.session_dir

    def _open_log(self) -> None:
        """Attach a FileHandler so audit entries go to session.log."""
        self._file_handler = logging.FileHandler(self._log_path, encoding="utf-8")
        fmt = "[%(asctime)s] [%(levelname)s] %(message)s"
        self._file_handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%S"))
        # Attach to the root logger so all app.* loggers also write to the file
        logging.getLogger().addHandler(self._file_handler)

    def close(self) -> None:
        """Flush and detach the session file handler."""
        if self._file_handler:
            logging.getLogger().removeHandler(self._file_handler)
            self._file_handler.close()
            self._file_handler = None

    # ------------------------------------------------------------------
    # Audit log
    # ------------------------------------------------------------------

    def log(self, level: str, component: str, message: str) -> None:
        """Write a structured audit log entry.

        Format: [TIMESTAMP] [LEVEL] [COMPONENT] Message
        (ARCHITECTURE.md §11)
        """
        if level not in _AUDIT_LEVELS:
            level = "INFO"
        ts = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = f"[{ts}] [{level}] [{component}] {message}"
        if self._log_path.exists() or self._file_handler:
            with self._log_path.open("a", encoding="utf-8") as fh:
                fh.write(entry + "\n")
        # Also surface as a standard log message
        std_level = level if level in {"INFO", "WARNING", "ERROR"} else "INFO"
        logging.getLogger(component).log(getattr(logging, std_level), message)

    # ------------------------------------------------------------------
    # JSON artefact helpers
    # ------------------------------------------------------------------

    def write_json(self, filename: str, data: dict | list) -> Path:
        """Serialise *data* to JSON and write to the session directory."""
        dest = self.session_dir / filename
        dest.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.debug("Wrote %s", dest)
        return dest

    def read_json(self, filename: str) -> dict[str, object] | list[object]:
        """Read a JSON artefact from the session directory."""
        src = self.session_dir / filename
        result: dict[str, object] | list[object] = json.loads(src.read_text(encoding="utf-8"))
        return result

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @staticmethod
    def new() -> SessionManager:
        """Create a SessionManager with a fresh timestamp-based session ID."""
        session_id = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S")
        return SessionManager(session_id)
