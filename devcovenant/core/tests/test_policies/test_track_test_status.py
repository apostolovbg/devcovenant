"""Tests for the track test status policy."""

import json
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policy_scripts.track_test_status import (
    STATUS_RELATIVE,
    TrackTestStatusCheck,
)


def _write(path: Path, content: str) -> Path:
    """Write file content and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _policy() -> TrackTestStatusCheck:
    """Return a policy instance configured for sample paths."""
    policy = TrackTestStatusCheck()
    policy.set_options(
        {
            "watch_dirs": [
                "project_lib",
                "engines",
                "tests",
                "tools",
                "scripts",
            ],
            "watch_files": ["project.py", "pyproject.toml"],
        },
        {},
    )
    return policy


def test_flags_missing_status_update(tmp_path: Path):
    """Code changes without status updates should be rejected."""
    code_path = _write(
        tmp_path / "project_lib" / "module.py",
        "def demo():\n    return 1\n",
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[code_path, tmp_path / "scripts" / "run_tests.sh"],
    )
    violations = _policy().check(context)
    assert violations
    assert "test status" in violations[0].message.lower()


def test_accepts_recent_status(tmp_path: Path):
    """Fresh test status payloads should pass."""
    code_path = _write(
        tmp_path / "project_lib" / "module.py",
        "def demo():\n    return 1\n",
    )
    status_path = tmp_path / STATUS_RELATIVE
    payload = {
        "last_run": "2025-12-24T12:00:00+00:00",
        "command": "pytest && python -m unittest discover",
        "sha": "a" * 40,
        "notes": "",
    }
    _write(status_path, json.dumps(payload))
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[code_path, status_path],
    )
    assert _policy().check(context) == []


def test_rejects_invalid_payload(tmp_path: Path):
    """Malformed payloads should be rejected."""
    code_path = _write(
        tmp_path / "project_lib" / "module.py",
        "def demo():\n    return 1\n",
    )
    status_path = _write(
        tmp_path / STATUS_RELATIVE,
        '{"last_run": "", "sha": ""}',
    )
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[code_path, status_path],
    )
    violations = _policy().check(context)
    assert violations
    assert "invalid" in violations[0].message.lower()
