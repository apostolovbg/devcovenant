"""Shared CLI options for DevCovenant commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import argparse

DOCS_MODE_CHOICES = ("preserve", "overwrite")
POLICY_MODE_CHOICES = ("preserve", "append-missing", "overwrite")
CONFIG_MODE_CHOICES = ("preserve", "overwrite")
METADATA_MODE_CHOICES = ("preserve", "overwrite", "skip")
INHERIT_MODE_CHOICES = ("inherit", "preserve", "overwrite", "skip")


@dataclass(frozen=True)
class InstallUpdateDefaults:
    """Defaults shared across install and update."""

    docs_mode: str | None
    policy_mode: str | None
    config_mode: str | None
    metadata_mode: str | None
    license_mode: str
    version_mode: str
    pyproject_mode: str
    ci_mode: str
    preserve_custom: bool | None


DEFAULT_INSTALL_DEFAULTS = InstallUpdateDefaults(
    docs_mode=None,
    policy_mode=None,
    config_mode=None,
    metadata_mode=None,
    license_mode="inherit",
    version_mode="inherit",
    pyproject_mode="inherit",
    ci_mode="inherit",
    preserve_custom=None,
)

DEFAULT_UPDATE_DEFAULTS = InstallUpdateDefaults(
    docs_mode="preserve",
    policy_mode="append-missing",
    config_mode="preserve",
    metadata_mode="preserve",
    license_mode="inherit",
    version_mode="inherit",
    pyproject_mode="inherit",
    ci_mode="inherit",
    preserve_custom=True,
)


def add_target_arg(parser: argparse.ArgumentParser) -> None:
    """Add the shared target argument."""
    parser.add_argument(
        "--target",
        default=".",
        help="Target repository path (default: current directory).",
    )


def add_install_update_args(
    parser: argparse.ArgumentParser,
    *,
    defaults: InstallUpdateDefaults,
    include_mode: bool = False,
    include_allow_existing: bool = False,
) -> None:
    """Add shared install/update arguments to a parser."""
    add_target_arg(parser)
    if include_mode:
        parser.add_argument(
            "--mode",
            choices=("auto", "empty", "existing"),
            default="auto",
            help="Install mode (auto detects existing installs).",
        )
    parser.add_argument(
        "--docs-mode",
        choices=DOCS_MODE_CHOICES,
        default=defaults.docs_mode,
        help="How to handle docs in existing repos.",
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
        choices=POLICY_MODE_CHOICES,
        default=defaults.policy_mode,
        help="How to handle policy blocks during install/update.",
    )
    parser.add_argument(
        "--config-mode",
        choices=CONFIG_MODE_CHOICES,
        default=defaults.config_mode,
        help="How to handle config files in existing repos.",
    )
    parser.add_argument(
        "--metadata-mode",
        choices=METADATA_MODE_CHOICES,
        default=defaults.metadata_mode,
        help="How to handle metadata files in existing repos.",
    )
    parser.add_argument(
        "--license-mode",
        choices=INHERIT_MODE_CHOICES,
        default=defaults.license_mode,
        help="Override the metadata mode for LICENSE.",
    )
    parser.add_argument(
        "--version-mode",
        choices=INHERIT_MODE_CHOICES,
        default=defaults.version_mode,
        help="Override the metadata mode for VERSION.",
    )
    parser.add_argument(
        "--version",
        dest="version_value",
        default=None,
        help="Version to use when creating VERSION for new installs.",
    )
    parser.add_argument(
        "--pyproject-mode",
        choices=INHERIT_MODE_CHOICES,
        default=defaults.pyproject_mode,
        help="Override the metadata mode for pyproject.toml.",
    )
    parser.add_argument(
        "--ci-mode",
        choices=INHERIT_MODE_CHOICES,
        default=defaults.ci_mode,
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
        default=defaults.preserve_custom,
        help="Preserve custom policy scripts and fixers during install.",
    )
    if include_allow_existing:
        parser.add_argument(
            "--allow-existing",
            action="store_true",
            help=argparse.SUPPRESS,
        )
    parser.add_argument(
        "--force-docs",
        action="store_true",
        help="Overwrite docs and metadata on update.",
    )
    parser.add_argument(
        "--force-config",
        action="store_true",
        help="Overwrite config files on update.",
    )


def build_install_args(
    args: argparse.Namespace,
    *,
    mode: str,
    allow_existing: bool = False,
) -> list[str]:
    """Build the install argument list from parsed args."""
    install_args = ["--target", str(args.target)]
    if mode:
        install_args.extend(["--mode", mode])
    if allow_existing:
        install_args.append("--allow-existing")
    if args.docs_mode is not None:
        install_args.extend(["--docs-mode", args.docs_mode])
    if args.docs_include:
        install_args.extend(["--docs-include", args.docs_include])
    if args.docs_exclude:
        install_args.extend(["--docs-exclude", args.docs_exclude])
    if args.policy_mode is not None:
        install_args.extend(["--policy-mode", args.policy_mode])
    if args.config_mode is not None:
        install_args.extend(["--config-mode", args.config_mode])
    if args.metadata_mode is not None:
        install_args.extend(["--metadata-mode", args.metadata_mode])
    if args.license_mode is not None:
        install_args.extend(["--license-mode", args.license_mode])
    if args.version_mode is not None:
        install_args.extend(["--version-mode", args.version_mode])
    if args.version_value:
        install_args.extend(["--version", args.version_value])
    if args.pyproject_mode is not None:
        install_args.extend(["--pyproject-mode", args.pyproject_mode])
    if args.ci_mode is not None:
        install_args.extend(["--ci-mode", args.ci_mode])
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
    return install_args


def normalize_choice(
    option_value: str | None,
    *,
    fallback: str,
    allowed: Iterable[str] | None = None,
) -> str:
    """Normalize an optional mode value."""
    if option_value in (None, "inherit"):
        return fallback
    if allowed is not None and option_value not in allowed:
        raise ValueError(f"Unsupported option: {option_value}")
    return option_value
