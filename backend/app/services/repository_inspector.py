"""
Repository Inspector.

Reads the target repository, categorises its files, detects the primary
language and test framework, and produces a ProjectContext.

Constraints (ARCHITECTURE.md §3):
- Reads files only; never modifies.
- Files exceeding MAX_FILE_BYTES are flagged but not read.
- Unreadable files are logged as warnings, not errors.
"""
from __future__ import annotations

from pathlib import Path

from app.core.logging import get_logger
from app.models.workflow import FileEntry, ProjectContext

logger = get_logger(__name__)

# Files larger than this are listed but their content is not read.
MAX_FILE_BYTES = 100_000  # 100 KB

# Directories to skip entirely
_SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".mypy_cache",
    ".ruff_cache", ".pytest_cache", "node_modules", "dist", "build",
    ".devflow",
}

# Extension → category mappings
_SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".go", ".java", ".rb", ".rs", ".cs"}
_DOC_EXTENSIONS    = {".md", ".rst", ".txt"}
_MANIFEST_NAMES    = {
    "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg",
    "package.json", "Pipfile", "poetry.lock", "Cargo.toml", "go.mod",
}
_DOC_NAMES = {"readme", "architecture", "api", "changelog", "contributing", "license"}

# Test file heuristics
_TEST_PREFIXES = {"test_", "tests_"}
_TEST_SUFFIXES = {"_test", "_spec"}


def _is_test_file(rel_path: str) -> bool:
    stem = Path(rel_path).stem.lower()
    name = Path(rel_path).name.lower()
    parts = Path(rel_path).parts
    if any(p.lower() in {"test", "tests", "spec", "specs"} for p in parts[:-1]):
        return True
    return (
        any(stem.startswith(p) for p in _TEST_PREFIXES)
        or any(stem.endswith(s) for s in _TEST_SUFFIXES)
        or name.startswith("test")
    )


def _is_doc_file(rel_path: str) -> bool:
    p = Path(rel_path)
    if p.suffix.lower() not in _DOC_EXTENSIONS:
        return False
    return any(token in p.stem.lower() for token in _DOC_NAMES) or p.suffix.lower() == ".md"


def _detect_language(source_files: list[FileEntry]) -> str:
    counts: dict[str, int] = {}
    for f in source_files:
        ext = Path(f.path).suffix.lower()
        counts[ext] = counts.get(ext, 0) + 1
    if not counts:
        return "unknown"
    dominant_ext = max(counts, key=lambda e: counts[e])
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".java": "java",
        ".rb": "ruby",
        ".rs": "rust",
        ".cs": "csharp",
    }.get(dominant_ext, "unknown")


def _detect_test_framework(
    detected_language: str,
    manifest_contents: dict[str, str],
    test_files: list[FileEntry],
    file_contents: dict[str, str],
) -> str:
    if detected_language == "python":
        # Check manifests
        for content in manifest_contents.values():
            if "pytest" in content:
                return "pytest"
            if "unittest" in content:
                return "unittest"
        # Check test file imports
        for path, content in file_contents.items():
            if not _is_test_file(path):
                continue
            if "import pytest" in content or "from pytest" in content:
                return "pytest"
            if "import unittest" in content or "from unittest" in content:
                return "unittest"
        if test_files:
            return "pytest"  # default for Python when tests exist
    return "unknown"


class RepositoryInspector:
    """Reads a repository and produces a ProjectContext."""

    def inspect(self, repository_path: str) -> ProjectContext:
        """Inspect *repository_path* and return a populated ProjectContext.

        Args:
            repository_path: Absolute or relative path to the repository root.

        Returns:
            A ProjectContext with all discovered files categorised and
            small-enough files' contents loaded.
        """
        root = Path(repository_path).resolve()
        if not root.exists():
            raise FileNotFoundError(f"Repository path does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Repository path is not a directory: {root}")

        logger.info("Inspecting repository: %s", root)

        source_files: list[FileEntry] = []
        test_files: list[FileEntry] = []
        doc_files: list[FileEntry] = []
        manifest_files: list[FileEntry] = []
        other_files: list[FileEntry] = []
        file_contents: dict[str, str] = {}
        unreadable: list[str] = []

        for abs_path in sorted(root.rglob("*")):
            if not abs_path.is_file():
                continue

            # Skip unwanted directories
            rel = abs_path.relative_to(root)
            if any(part in _SKIP_DIRS for part in rel.parts):
                continue

            rel_str = rel.as_posix()
            try:
                size = abs_path.stat().st_size
            except OSError as exc:
                logger.warning("Cannot stat %s: %s", rel_str, exc)
                unreadable.append(rel_str)
                continue

            skipped_reason: str | None = None
            if size > MAX_FILE_BYTES:
                skipped_reason = f"exceeds size limit ({size} bytes > {MAX_FILE_BYTES})"
                logger.warning("Skipping content of %s: %s", rel_str, skipped_reason)
            else:
                try:
                    file_contents[rel_str] = abs_path.read_text(encoding="utf-8", errors="replace")
                except OSError as exc:
                    logger.warning("Cannot read %s: %s", rel_str, exc)
                    unreadable.append(rel_str)
                    skipped_reason = str(exc)

            entry = FileEntry(path=rel_str, size_bytes=size, skipped_reason=skipped_reason)

            name_lower = abs_path.name.lower()
            ext_lower  = abs_path.suffix.lower()

            if name_lower in _MANIFEST_NAMES:
                manifest_files.append(entry)
            elif _is_test_file(rel_str) and ext_lower in _SOURCE_EXTENSIONS:
                test_files.append(entry)
            elif ext_lower in _SOURCE_EXTENSIONS:
                source_files.append(entry)
            elif _is_doc_file(rel_str):
                doc_files.append(entry)
            else:
                other_files.append(entry)

        # Detect language and test framework
        detected_language = _detect_language(source_files)
        manifest_contents = {
            f.path: file_contents[f.path]
            for f in manifest_files
            if f.path in file_contents
        }
        detected_test_framework = _detect_test_framework(
            detected_language, manifest_contents, test_files, file_contents
        )

        logger.info(
            "Inspection complete: %d source, %d test, %d doc, %d manifest | lang=%s fw=%s",
            len(source_files), len(test_files), len(doc_files), len(manifest_files),
            detected_language, detected_test_framework,
        )

        return ProjectContext(
            repository_path=str(root),
            detected_language=detected_language,
            detected_test_framework=detected_test_framework,
            source_files=source_files,
            test_files=test_files,
            doc_files=doc_files,
            manifest_files=manifest_files,
            other_files=other_files,
            file_contents=file_contents,
            unreadable_files=unreadable,
        )
