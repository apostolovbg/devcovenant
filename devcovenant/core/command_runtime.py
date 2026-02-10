"""Shared runtime helpers for root-level DevCovenant commands."""

from __future__ import annotations

import re
from pathlib import Path

from devcovenant import __version__ as package_version


def print_banner(title: str, emoji: str) -> None:
    """Print a readable stage banner."""
    print("\n" + "=" * 70)
    print(f"{emoji} {title}")
    print("=" * 70)


def print_step(message: str, emoji: str = "•") -> None:
    """Print a short, single-line status step."""
    print(f"{emoji} {message}")


def find_git_root(path: Path) -> Path | None:
    """Return the nearest git root for a path."""
    current = path.resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def read_local_version(repo_root: Path) -> str | None:
    """Read the local devcovenant version from repo_root."""
    init_path = repo_root / "devcovenant" / "__init__.py"
    if not init_path.exists():
        return None
    pattern = re.compile(r'__version__\s*=\s*["\']([^"\']+)["\']')
    match = pattern.search(init_path.read_text(encoding="utf-8"))
    if match:
        return match.group(1).strip()
    return None


def warn_version_mismatch(repo_root: Path) -> None:
    """Warn when the local devcovenant version differs from the CLI."""
    local_version = read_local_version(repo_root)
    if not local_version:
        return
    if local_version != package_version:
        message = (
            "⚠️  Local DevCovenant version differs from CLI.\n"
            f"   Local: {local_version}\n"
            f"   CLI:   {package_version}\n"
            "Use the local version via `python3 -m devcovenant` or update."
        )
        print(message)


def resolve_repo_root(path: Path, *, require_install: bool = False) -> Path:
    """Resolve and validate the target git repository root."""
    repo_root = find_git_root(path)
    if repo_root is None:
        raise SystemExit(
            "DevCovenant commands must run inside a git repository."
        )
    if require_install and not (repo_root / "devcovenant").exists():
        raise SystemExit(
            "DevCovenant is not installed in this repo. "
            "Run `devcovenant install --target .` first."
        )
    return repo_root


def run_bootstrap_registry_refresh(repo_root: Path) -> None:
    """Run lightweight registry refresh for command startup."""
    print_step("Refreshing local registry", "🔄")
    try:
        from devcovenant.core.refresh_registry import refresh_registry

        refresh_registry(repo_root, skip_freeze=True)
        print_step("Registry refresh complete", "✅")
    except Exception as exc:  # pragma: no cover - defensive
        print_step(f"Registry refresh skipped ({exc})", "⚠️")
