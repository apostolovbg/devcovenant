#!/usr/bin/env python3
"""Upgrade DevCovenant core in the current repository."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import re
import shutil
import tempfile
from pathlib import Path

import semver

from devcovenant import install
from devcovenant.core.flow.refresh import refresh_repo
from devcovenant.core.runtime.execution import (
    print_banner,
    print_step,
    resolve_repo_root,
)

_UPGRADE_RUNTIME_PRESERVE_DIRS = (
    Path("devcovenant/registry/local"),
    Path("devcovenant/logs"),
)
_SEMVER_COMPARE_RE = re.compile(
    r"^(?P<core>\d+(?:\.\d+){0,2})"
    r"(?:-(?P<prerelease>[0-9A-Za-z.-]+))?"
    r"(?:\+(?P<build>[0-9A-Za-z.-]+))?$"
)


def _read_version(path: Path) -> str:
    """Read version text from a file, falling back to 0.0.0."""
    if not path.exists():
        return "0.0.0"
    version_text = path.read_text(encoding="utf-8").strip()
    return version_text or "0.0.0"


def _normalize_version_for_compare(raw: str) -> str:
    """Normalize repo version text into parseable SemVer for comparison."""
    token = str(raw or "").strip()
    if not token:
        return "0.0.0"
    if token[:1] in {"v", "V"}:
        token = token[1:].strip()
    match = _SEMVER_COMPARE_RE.fullmatch(token)
    if match is None:
        raise ValueError(
            f"Invalid semantic version string `{raw}` for upgrade compare."
        )
    core_parts = [part.strip() for part in match.group("core").split(".")]
    if any(not part.isdigit() for part in core_parts):
        raise ValueError(
            f"Invalid semantic version string `{raw}` for upgrade compare."
        )
    while len(core_parts) < 3:
        core_parts.append("0")
    normalized = ".".join(core_parts[:3])
    prerelease = str(match.group("prerelease") or "").strip()
    build = str(match.group("build") or "").strip()
    if prerelease:
        normalized = f"{normalized}-{prerelease}"
    if build:
        normalized = f"{normalized}+{build}"
    try:
        semver.Version.parse(normalized)
    except ValueError as exc:
        raise ValueError(
            f"Invalid semantic version string `{raw}` for upgrade compare."
        ) from exc
    return normalized


def _parse_version_for_compare(raw: str) -> semver.Version:
    """Parse a version string into a SemVer object for upgrade ordering."""
    return semver.Version.parse(_normalize_version_for_compare(raw))


def _preserve_upgrade_runtime_state(repo_root: Path, temp_root: Path) -> None:
    """Copy runtime-local state that should survive core replacement."""
    for rel_path in _UPGRADE_RUNTIME_PRESERVE_DIRS:
        source_path = repo_root / rel_path
        if not source_path.exists():
            continue
        if not source_path.is_dir():
            continue
        preserved_path = temp_root / rel_path
        preserved_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_path, preserved_path)


def _restore_upgrade_runtime_state(repo_root: Path, temp_root: Path) -> None:
    """Restore runtime-local state after core replacement during upgrade."""
    local_registry_rel = Path("devcovenant/registry/local")
    logs_rel = Path("devcovenant/logs")
    preserved_local = temp_root / local_registry_rel
    preserved_logs = temp_root / logs_rel

    if preserved_local.exists():
        target_local = repo_root / local_registry_rel
        if target_local.exists():
            shutil.rmtree(target_local)
        target_local.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(preserved_local, target_local)

    if preserved_logs.exists():
        target_logs = repo_root / logs_rel
        target_logs.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(preserved_logs, target_logs, dirs_exist_ok=True)


def _replace_core_package_for_upgrade(repo_root: Path) -> None:
    """Replace core package while preserving upgrade-owned runtime state."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        _preserve_upgrade_runtime_state(repo_root, temp_root)
        install.replace_core_package(repo_root)
        _restore_upgrade_runtime_state(repo_root, temp_root)


def upgrade_repo(repo_root: Path) -> int:
    """Upgrade DevCovenant core and run full refresh."""
    source_version_path = Path(__file__).resolve().parent / "VERSION"
    target_version_path = repo_root / "devcovenant" / "VERSION"

    source_version = _read_version(source_version_path)
    target_version = _read_version(target_version_path)
    try:
        source_key = _parse_version_for_compare(source_version)
        target_key = _parse_version_for_compare(target_version)
    except ValueError as error:
        raise SystemExit(f"Upgrade blocked: {error}") from error
    if source_key > target_key:
        _replace_core_package_for_upgrade(repo_root)
        target_version_path.write_text(f"{source_version}\n", encoding="utf-8")
        print_step("Core package replaced with newer version", "✅")
    else:
        print_step("Core already up to date", "ℹ️")

    return refresh_repo(repo_root)


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for upgrade command."""
    return argparse.ArgumentParser(
        description="Upgrade DevCovenant core in the current repository."
    )


def run(args: argparse.Namespace) -> int:
    """Execute upgrade command."""
    del args
    repo_root = resolve_repo_root(require_install=True)

    print_banner("DevCovenant run", "🚀")
    print_step("Command: upgrade", "🧭")
    print_banner("Upgrade", "⬆️")

    return upgrade_repo(repo_root)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
