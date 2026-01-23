#!/usr/bin/env python3
"""Update DevCovenant in a target repository."""

from __future__ import annotations

import argparse
from pathlib import Path

from devcovenant.core import install
from devcovenant.core import metadata_normalizer


def main(argv=None) -> None:
    """CLI entry point for updates."""
    parser = argparse.ArgumentParser(
        description="Update DevCovenant in a target repository."
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Target repository path (default: current directory).",
    )
    parser.add_argument(
        "--docs-mode",
        choices=("preserve", "overwrite"),
        default="preserve",
        help="How to handle docs during update.",
    )
    parser.add_argument(
        "--docs-include",
        default=None,
        help="Comma-separated doc names to target for overwrite.",
    )
    parser.add_argument(
        "--docs-exclude",
        default=None,
        help="Comma-separated doc names to exclude from overwrite.",
    )
    parser.add_argument(
        "--policy-mode",
        choices=("preserve", "append-missing", "overwrite"),
        default="append-missing",
        help="How to handle policy blocks during update.",
    )
    parser.add_argument(
        "--config-mode",
        choices=("preserve", "overwrite"),
        default="preserve",
        help="How to handle config files during update.",
    )
    parser.add_argument(
        "--metadata-mode",
        choices=("preserve", "overwrite", "skip"),
        default="preserve",
        help="How to handle metadata files during update.",
    )
    parser.add_argument(
        "--license-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        default="inherit",
        help="Override the metadata mode for LICENSE.",
    )
    parser.add_argument(
        "--version-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        default="inherit",
        help="Override the metadata mode for VERSION.",
    )
    parser.add_argument(
        "--version",
        dest="version_value",
        default=None,
        help="Version to use when writing VERSION.",
    )
    parser.add_argument(
        "--pyproject-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        default="inherit",
        help="Override the metadata mode for pyproject.toml.",
    )
    parser.add_argument(
        "--ci-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        default="inherit",
        help="Override the config mode for CI workflow files.",
    )
    parser.add_argument(
        "--include-spec",
        action="store_true",
        help="Create SPEC.md when missing.",
    )
    parser.add_argument(
        "--include-plan",
        action="store_true",
        help="Create PLAN.md when missing.",
    )
    parser.add_argument(
        "--preserve-custom",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Preserve custom policy scripts and fixers during update.",
    )
    parser.add_argument(
        "--force-docs",
        action="store_true",
        help="Overwrite docs when updating.",
    )
    parser.add_argument(
        "--force-config",
        action="store_true",
        help="Overwrite config files when updating.",
    )
    args = parser.parse_args(argv)

    install_args = [
        "--allow-existing",
        "--mode",
        "existing",
        "--target",
        str(args.target),
        "--docs-mode",
        args.docs_mode,
        "--config-mode",
        args.config_mode,
        "--metadata-mode",
        args.metadata_mode,
        "--license-mode",
        args.license_mode,
        "--version-mode",
        args.version_mode,
        "--pyproject-mode",
        args.pyproject_mode,
        "--ci-mode",
        args.ci_mode,
        "--policy-mode",
        args.policy_mode,
    ]
    if args.version_value:
        install_args.extend(["--version", args.version_value])
    if args.docs_include:
        install_args.extend(["--docs-include", args.docs_include])
    if args.docs_exclude:
        install_args.extend(["--docs-exclude", args.docs_exclude])
    if args.include_spec:
        install_args.append("--include-spec")
    if args.include_plan:
        install_args.append("--include-plan")
    if args.preserve_custom is not None:
        if args.preserve_custom:
            install_args.append("--preserve-custom")
        else:
            install_args.append("--no-preserve-custom")
    if args.force_docs:
        install_args.append("--force-docs")
    if args.force_config:
        install_args.append("--force-config")

    install.main(install_args)

    schema_path = (
        Path(__file__).resolve().parents[1] / "templates" / "AGENTS.md"
    )
    agents_path = Path(args.target).resolve() / "AGENTS.md"
    metadata_normalizer.normalize_agents_metadata(
        agents_path, schema_path, set_updated=True
    )


if __name__ == "__main__":
    main()
