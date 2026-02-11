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

import yaml

from devcovenant.core import manifest as manifest_module
from devcovenant.core.execution import (
    print_banner,
    print_step,
    resolve_repo_root,
)

DEFAULT_ACTIVE_PROFILES = [
    "global",
    "docs",
    "data",
    "suffixes",
    "devcovuser",
    "python",
]

DEFAULT_MANAGED_DOCS = [
    "AGENTS.md",
    "README.md",
    "CONTRIBUTING.md",
    "SPEC.md",
    "PLAN.md",
    "CHANGELOG.md",
    "devcovenant/README.md",
]


def _source_package_dir() -> Path:
    """Return the packaged devcovenant source directory."""
    return Path(__file__).resolve().parent


def _target_package_dir(repo_root: Path) -> Path:
    """Return the destination devcovenant directory for a repo."""
    return repo_root / "devcovenant"


def _read_yaml(path: Path) -> dict[str, object]:
    """Load YAML mapping payload from disk."""
    if not path.exists():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    """Write YAML mapping payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


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


def _ensure_profiles_block(payload: dict[str, object]) -> None:
    """Ensure active profile defaults exist."""
    profiles_block = payload.get("profiles")
    if not isinstance(profiles_block, dict):
        profiles_block = {}

    active = profiles_block.get("active")
    if isinstance(active, list) and active:
        profiles_block["active"] = [str(item) for item in active if str(item)]
    else:
        profiles_block["active"] = list(DEFAULT_ACTIVE_PROFILES)

    payload["profiles"] = profiles_block


def _ensure_doc_assets_block(payload: dict[str, object]) -> None:
    """Ensure managed doc asset defaults exist."""
    doc_assets = payload.get("doc_assets")
    if not isinstance(doc_assets, dict):
        doc_assets = {}

    autogen = doc_assets.get("autogen")
    if isinstance(autogen, list) and autogen:
        doc_assets["autogen"] = [str(item) for item in autogen if str(item)]
    else:
        doc_assets["autogen"] = list(DEFAULT_MANAGED_DOCS)

    user_docs = doc_assets.get("user")
    if isinstance(user_docs, list):
        doc_assets["user"] = [str(item) for item in user_docs if str(item)]
    else:
        doc_assets["user"] = []

    payload["doc_assets"] = doc_assets


def _ensure_generic_config(repo_root: Path) -> None:
    """Write/install a generic config stub for post-install editing."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    payload = _read_yaml(config_path)

    install_block = payload.get("install")
    if not isinstance(install_block, dict):
        install_block = {}

    install_block["generic_config"] = True
    payload["install"] = install_block

    if "devcov_core_include" not in payload:
        payload["devcov_core_include"] = False

    _ensure_profiles_block(payload)
    _ensure_doc_assets_block(payload)
    _write_yaml(config_path, payload)


def install_repo(repo_root: Path) -> int:
    """Install DevCovenant core and generic config in a repository."""
    replace_core_package(repo_root)
    _ensure_generic_config(repo_root)
    manifest_module.ensure_manifest(repo_root)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for install command."""
    return argparse.ArgumentParser(
        description="Install DevCovenant into the current repository."
    )


def run(args: argparse.Namespace) -> int:
    """Execute install command."""
    del args
    repo_root = resolve_repo_root(Path.cwd(), require_install=False)

    print_banner("DevCovenant run", "🚀")
    print_step("Command: install", "🧭")
    print_banner("Install", "📦")

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
