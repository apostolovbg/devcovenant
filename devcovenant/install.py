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

import devcovenant.core.services.registry as manifest_module
from devcovenant.core.runtime.execution import (
    build_command_parser,
    print_banner,
    print_step,
    resolve_repo_root,
)


def _source_package_dir() -> Path:
    """Return the packaged devcovenant source directory."""
    return Path(__file__).resolve().parent


def _target_package_dir(repo_root: Path) -> Path:
    """Return the destination devcovenant directory for a repo."""
    return repo_root / "devcovenant"


_CUSTOM_SCAFFOLD_FILES = {"README.md", "__init__.py"}


def _copy_ignore_builder(source_dir: Path):
    """Return copy ignore callback scoped to one source directory."""

    def _copy_ignore(directory: str, names: list[str]) -> set[str]:
        """Ignore runtime caches/local state and package-owned payload."""
        ignored = set()
        current = Path(directory)
        try:
            rel_path = current.relative_to(source_dir).as_posix()
        except ValueError:
            rel_path = current.name

        if rel_path == "registry" and "local" in names:
            ignored.add("local")

        if rel_path in {"custom/policies", "custom/profiles"}:
            for name in names:
                if name in _CUSTOM_SCAFFOLD_FILES:
                    continue
                ignored.add(name)

        for name in names:
            if name == "__pycache__":
                ignored.add(name)
            if name.endswith(".pyc"):
                ignored.add(name)
        return ignored

    return _copy_ignore


def _collect_custom_payload_dirs(custom_dir: Path) -> list[tuple[Path, Path]]:
    """Collect user custom payload dirs to preserve across replacement."""
    collected: list[tuple[Path, Path]] = []
    sections = (
        "policies",
        "profiles",
    )
    for section in sections:
        section_root = custom_dir / section
        if not section_root.exists():
            continue
        for entry in sorted(section_root.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith(".") or entry.name == "__pycache__":
                continue
            rel = Path("custom") / section / entry.name
            collected.append((entry, rel))
    return collected


def replace_core_package(
    repo_root: Path,
    source_dir: Path | None = None,
) -> None:
    """Replace repo-root devcovenant package with packaged source."""
    source_dir = (source_dir or _source_package_dir()).resolve()
    target_dir = _target_package_dir(repo_root).resolve()
    if source_dir == target_dir:
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        preserved_payload_root = temp_path / "custom_payload"
        custom_dir = target_dir / "custom"

        if custom_dir.exists():
            for payload_dir, rel_path in _collect_custom_payload_dirs(
                custom_dir
            ):
                destination = preserved_payload_root / rel_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(payload_dir, destination, dirs_exist_ok=True)

        if target_dir.exists():
            shutil.rmtree(target_dir)

        shutil.copytree(
            source_dir,
            target_dir,
            ignore=_copy_ignore_builder(source_dir),
        )

        if preserved_payload_root.exists():
            for preserved_dir in sorted(preserved_payload_root.rglob("*")):
                if not preserved_dir.is_dir():
                    continue
                rel_path = preserved_dir.relative_to(preserved_payload_root)
                if len(rel_path.parts) != 3:
                    continue
                destination = target_dir / rel_path
                if destination.exists():
                    shutil.rmtree(destination)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(preserved_dir, destination)


def _ensure_generic_config(repo_root: Path) -> None:
    """Write/install a generic config stub for post-install editing."""
    template_path = (
        repo_root
        / "devcovenant"
        / "builtin"
        / "profiles"
        / "global"
        / "assets"
        / "config.yaml"
    )
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not template_path.exists():
        raise FileNotFoundError(
            "Missing global config template: "
            "devcovenant/builtin/profiles/global/assets/config.yaml"
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
    return build_command_parser(
        "install",
        "Install DevCovenant into the current repository.",
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
