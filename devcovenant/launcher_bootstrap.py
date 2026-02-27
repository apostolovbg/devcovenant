"""Lightweight launcher bootstrap for repo bytecode-cache routing.

This module is intentionally stdlib-only and import-light so
`devcovenant/cli.py` and `devcovenant/__main__.py` can apply
`PYTHONPYCACHEPREFIX` before importing runtime-heavy modules.

Boundary truth:
- this code runs after Python has already loaded the initial launcher module
  path, so shell/CI launcher environment variables still own "zero drift"
  guarantees for fallback launcher runs
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
import tempfile
from pathlib import Path

_TRUE_TOKENS = {"true", "1", "yes", "on", "enabled"}
_FALSE_TOKENS = {"false", "0", "no", "off", "disabled"}
_PYCACHE_PREFIX_ENABLED_RE = re.compile(
    r"(?m)^\s*pycache_prefix_enabled:\s*(\S+)\s*$"
)
_PYCACHE_PREFIX_RE = re.compile(r"(?m)^\s*pycache_prefix:\s*(.*?)\s*$")


def find_git_root_for_launcher_bootstrap(start: Path) -> Path | None:
    """Return the nearest parent directory that contains a `.git` entry."""
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def default_repo_pycache_prefix(repo_root: Path) -> str:
    """Return a stable temp pycache prefix path for one repo checkout."""
    try:
        repo_token = str(repo_root.resolve())
    except OSError:
        repo_token = str(repo_root)
    suffix = hashlib.sha256(repo_token.encode("utf-8")).hexdigest()[:12]
    return str(Path(tempfile.gettempdir()) / "devcovenant-pycache" / suffix)


def resolve_repo_pycache_prefix_from_config(
    repo_root: Path,
) -> tuple[bool, str | None]:
    """Return lightweight `(enabled, prefix)` config for launcher bootstrap."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.is_file():
        return False, None
    try:
        payload = config_path.read_text(encoding="utf-8")
    except OSError:
        return False, None

    default_enabled = "- devcovrepo" in payload
    enabled = default_enabled
    match_enabled = _PYCACHE_PREFIX_ENABLED_RE.search(payload)
    if match_enabled:
        token = match_enabled.group(1).strip().strip("\"'").lower()
        if token in _TRUE_TOKENS:
            enabled = True
        elif token in _FALSE_TOKENS:
            enabled = False

    prefix: str | None = None
    match_prefix = _PYCACHE_PREFIX_RE.search(payload)
    if match_prefix:
        raw = match_prefix.group(1).strip()
        if raw in {"''", '""'}:
            prefix = default_repo_pycache_prefix(repo_root)
        elif raw:
            token = raw.strip("\"'")
            path = Path(token).expanduser()
            if not path.is_absolute():
                path = repo_root / path
            prefix = str(path)
        else:
            prefix = default_repo_pycache_prefix(repo_root)
    elif enabled:
        prefix = default_repo_pycache_prefix(repo_root)

    return enabled, prefix


def apply_repo_pycache_prefix_from_start_path(start: Path) -> bool:
    """Best-effort launcher bootstrap for repo-scoped pycache routing."""
    repo_root = find_git_root_for_launcher_bootstrap(start)
    if repo_root is None:
        return False
    enabled, prefix = resolve_repo_pycache_prefix_from_config(repo_root)
    if not enabled or not prefix:
        return False
    try:
        Path(prefix).mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    os.environ["PYTHONPYCACHEPREFIX"] = prefix
    try:
        sys.pycache_prefix = prefix
    except Exception:
        pass
    return True


def apply_repo_pycache_prefix_from_cwd() -> bool:
    """Best-effort launcher bootstrap using the current working directory."""
    return apply_repo_pycache_prefix_from_start_path(Path.cwd())


__all__ = [
    "apply_repo_pycache_prefix_from_cwd",
    "apply_repo_pycache_prefix_from_start_path",
    "default_repo_pycache_prefix",
    "find_git_root_for_launcher_bootstrap",
    "resolve_repo_pycache_prefix_from_config",
]
