#!/usr/bin/env python3
"""Deploy DevCovenant managed artifacts for the current repository."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from pathlib import Path

import yaml

from devcovenant.core.execution import (
    print_banner,
    print_step,
    resolve_repo_root,
)
from devcovenant.core.repo_refresh import refresh_repo


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


def _is_generic_config(config: dict[str, object]) -> bool:
    """Return True when install.generic_config is still enabled."""
    install_block = config.get("install")
    if not isinstance(install_block, dict):
        return True
    return bool(install_block.get("generic_config", True))


def deploy_repo(repo_root: Path) -> int:
    """Deploy managed DevCovenant docs/assets to a repo."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    config = _read_yaml(config_path)
    if _is_generic_config(config):
        raise SystemExit(
            "Deploy blocked: config is still generic. Set "
            "`install.generic_config: false` first."
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
    repo_root = resolve_repo_root(Path.cwd(), require_install=True)

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
