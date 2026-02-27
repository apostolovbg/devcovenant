#!/usr/bin/env python3
"""Deploy DevCovenant managed artifacts for the current repository."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import shutil
from pathlib import Path

import yaml

from devcovenant.core.flow.refresh import refresh_repo
from devcovenant.core.runtime.execution import (
    print_banner,
    print_step,
    resolve_repo_root,
)

USER_MODE_CLEANUP_PATHS = (
    Path("devcovenant/custom/policies"),
    Path("tests/devcovenant/core"),
    Path("devcovenant/custom/profiles/devcovrepo"),
)


def _read_yaml(path: Path) -> dict[str, object]:
    """Load YAML mapping payload from disk."""
    if not path.exists():
        raise SystemExit(
            f"Deploy blocked: missing required config file: {path}."
        )
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SystemExit(
            f"Deploy blocked: invalid YAML in {path}: {exc}"
        ) from exc
    except OSError as exc:
        raise SystemExit(
            f"Deploy blocked: unable to read {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise SystemExit(
            f"Deploy blocked: {path} must contain a YAML mapping."
        )
    return payload


def _is_generic_config(config: dict[str, object]) -> bool:
    """Return True when install.generic_config is still enabled."""
    install_block = config.get("install")
    if not isinstance(install_block, dict):
        raise SystemExit(
            "Deploy blocked: `install` must be present as a mapping in "
            "devcovenant/config.yaml."
        )
    generic_config = install_block.get("generic_config")
    if not isinstance(generic_config, bool):
        raise SystemExit(
            "Deploy blocked: `install.generic_config` must be boolean."
        )
    return generic_config


def _include_core_content(config: dict[str, object]) -> bool:
    """Return True when deploy should keep devcovrepo/core overlays."""
    include_core = config.get("devcov_core_include")
    if not isinstance(include_core, bool):
        raise SystemExit(
            "Deploy blocked: `devcov_core_include` must be boolean."
        )
    return include_core


def _remove_path(target: Path) -> bool:
    """Delete a file or directory if it exists."""
    if not target.exists():
        return False
    if target.is_file() or target.is_symlink():
        target.unlink()
        return True
    shutil.rmtree(target)
    return True


def _cleanup_user_mode_paths(repo_root: Path) -> list[str]:
    """Delete deploy-only user-mode paths before full refresh."""
    removed: list[str] = []
    for relative_path in USER_MODE_CLEANUP_PATHS:
        target = repo_root / relative_path
        if _remove_path(target):
            removed.append(str(relative_path))
    return removed


def deploy_repo(repo_root: Path) -> int:
    """Deploy managed DevCovenant docs/assets to a repo."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    config = _read_yaml(config_path)
    if _is_generic_config(config):
        raise SystemExit(
            "Deploy blocked: config is still generic. Set "
            "`install.generic_config: false` first."
        )

    if not _include_core_content(config):
        removed = _cleanup_user_mode_paths(repo_root)
        if removed:
            print_step(
                "Deploy cleanup removed: " + ", ".join(removed),
                "🧹",
            )

    return refresh_repo(repo_root)


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for deploy command."""
    return argparse.ArgumentParser(
        description="Deploy managed docs/assets in the current repository."
    )


def run(args: argparse.Namespace) -> int:
    """Execute deploy command."""
    del args
    repo_root = resolve_repo_root(require_install=True)

    print_banner("DevCovenant run", "🚀")
    print_step("Command: deploy", "🧭")
    print_banner("Deploy", "📤")

    return deploy_repo(repo_root)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
