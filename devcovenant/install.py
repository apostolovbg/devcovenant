#!/usr/bin/env python3
"""Install DevCovenant into the current repository."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import shutil
import tempfile
from pathlib import Path

from devcovenant.core import registry_runtime as manifest_module
from devcovenant.core.execution_runtime import (
    print_banner,
    print_step,
    resolve_repo_root,
)

DEFAULT_ACTIVE_PROFILES = [
    "global",
    "devcovuser",
    "python",
    "docs",
]


def _source_package_dir() -> Path:
    """Return the packaged devcovenant source directory."""
    return Path(__file__).resolve().parent


def _target_package_dir(repo_root: Path) -> Path:
    """Return the destination devcovenant directory for a repo."""
    return repo_root / "devcovenant"


def _copy_ignore(directory: str, names: list[str]) -> set[str]:
    """Ignore runtime caches and local registry state during copy."""
    ignored = set()
    if Path(directory).name == "registry" and "local" in names:
        ignored.add("local")
    for name in names:
        if name == "__pycache__":
            ignored.add(name)
        if name.endswith(".pyc"):
            ignored.add(name)
    return ignored


def replace_core_package(repo_root: Path) -> None:
    """Replace repo-root devcovenant package with packaged source."""
    source_dir = _source_package_dir().resolve()
    target_dir = _target_package_dir(repo_root).resolve()
    if source_dir == target_dir:
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        preserved_custom = temp_path / "custom"
        custom_dir = target_dir / "custom"

        if custom_dir.exists():
            shutil.copytree(custom_dir, preserved_custom, dirs_exist_ok=True)

        if target_dir.exists():
            shutil.rmtree(target_dir)

        shutil.copytree(source_dir, target_dir, ignore=_copy_ignore)

        if preserved_custom.exists():
            restored_custom = target_dir / "custom"
            if restored_custom.exists():
                shutil.rmtree(restored_custom)
            shutil.copytree(preserved_custom, restored_custom)


def _ensure_generic_config(repo_root: Path) -> None:
    """Write/install a generic config stub for post-install editing."""
    template_path = (
        repo_root
        / "devcovenant"
        / "core"
        / "profiles"
        / "global"
        / "assets"
        / "config.yaml"
    )
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not template_path.exists():
        raise FileNotFoundError(
            "Missing global config template: "
            "devcovenant/core/profiles/global/assets/config.yaml"
        )
    config_path.write_text(
        template_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def install_repo(repo_root: Path) -> int:
    """Install DevCovenant core and generic config in a repository."""
    replace_core_package(repo_root)

    local_registry = repo_root / "devcovenant" / "registry" / "local"
    if local_registry.exists():
        shutil.rmtree(local_registry)

    _ensure_generic_config(repo_root)
    manifest_module.ensure_manifest(repo_root)
    return 0


def _is_existing_install(repo_root: Path) -> bool:
    """Return True when DevCovenant is already present in repo_root."""
    target_dir = _target_package_dir(repo_root)
    if not target_dir.exists():
        return False
    return (target_dir / "__init__.py").exists() or (
        target_dir / "VERSION"
    ).exists()


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for install command."""
    return argparse.ArgumentParser(
        description="Install DevCovenant into the current repository."
    )


def run(args: argparse.Namespace) -> int:
    """Execute install command."""
    del args
    repo_root = resolve_repo_root(require_install=False)

    print_banner("DevCovenant run", "🚀")
    print_step("Command: install", "🧭")
    print_banner("Install", "📦")

    if _is_existing_install(repo_root):
        print_step("DevCovenant is already present in this repository.", "ℹ️")
        print_step("Run `devcovenant upgrade` to replace core files.", "ℹ️")
        return 1

    result = install_repo(repo_root)
    if result != 0:
        return result

    print_step("Installed devcovenant/ core package", "✅")
    print_step(
        (
            "Config reset to generic stub. Edit devcovenant/config.yaml, "
            "then run `devcovenant deploy`."
        ),
        "ℹ️",
    )
    return 0


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
