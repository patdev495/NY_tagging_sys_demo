import os

import pytest

IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "release",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "coverage",
    ".system_generated",
    ".scratch",
    "outputs",
    ".codegraph",
    ".gemini",
}

IGNORED_FILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "uv.lock",
    "database.db",
    "database.db-wal",
    "database.db-shm",
}

VALID_SOURCE_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".vue",
    ".js",
    ".jsx",
    ".html",
    ".css",
    ".scss",
    ".sql",
    ".json",
    ".yaml",
    ".yml",
}

MAX_ALLOWED_LINES = 500


def get_repo_root() -> str:
    """Find the root directory of the workspace."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up from backend_v2/tests to repository root
    repo_root = os.path.dirname(os.path.dirname(current_dir))
    if os.path.exists(os.path.join(repo_root, "backend_v2")) and os.path.exists(os.path.join(repo_root, "frontend_v2")):
        return repo_root
    return os.path.dirname(current_dir)


class TestCodeQualityAndFileLimits:
    def test_no_source_file_exceeds_500_lines(self):
        """
        Architecture rule: All source code files in the project must remain under 500 lines
        to ensure modularity, maintainability, and clean separation of concerns.
        """
        repo_root = get_repo_root()
        violations = []

        for root, dirs, files in os.walk(repo_root):
            # Prune ignored directories in-place
            dirs[:] = [
                d
                for d in dirs
                if d not in IGNORED_DIRS and not d.startswith(".")
            ]

            for file in files:
                if file in IGNORED_FILES:
                    continue

                _, ext = os.path.splitext(file)
                if ext.lower() not in VALID_SOURCE_EXTENSIONS:
                    continue

                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        line_count = sum(1 for _ in f)
                        if line_count > MAX_ALLOWED_LINES:
                            rel_path = os.path.relpath(filepath, repo_root)
                            violations.append((line_count, rel_path))
                except Exception as e:
                    pytest.fail(f"Could not read file {filepath}: {e}")

        # Format error message if any violations exist
        if violations:
            violations.sort(reverse=True, key=lambda x: x[0])
            violation_summary = "\n".join(
                f"  - {path}: {lines} lines (exceeds {MAX_ALLOWED_LINES})"
                for lines, path in violations
            )
            assert False, (
                f"Found {len(violations)} file(s) exceeding {MAX_ALLOWED_LINES} lines:\n"
                f"{violation_summary}\n"
                f"Please refactor these files to keep them under {MAX_ALLOWED_LINES} lines."
            )
