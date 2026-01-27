"""
Command-line interface for devcovenant.
"""

import argparse
import re
import sys
from pathlib import Path

from devcovenant import __version__ as package_version
from devcovenant.core.engine import DevCovenantEngine


def _find_git_root(path: Path) -> Path | None:
    """Return the nearest git root for a path."""
    current = path.resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _read_local_version(repo_root: Path) -> str | None:
    """Read the local devcovenant version from repo_root."""
    init_path = repo_root / "devcovenant" / "__init__.py"
    if not init_path.exists():
        return None
    pattern = re.compile(r'__version__\s*=\s*["\']([^"\']+)["\']')
    match = pattern.search(init_path.read_text(encoding="utf-8"))
    if match:
        return match.group(1).strip()
    return None


def _warn_version_mismatch(repo_root: Path) -> None:
    """Warn when the local devcovenant version differs from the CLI."""
    local_version = _read_local_version(repo_root)
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


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DevCovenant - Self-enforcing policy system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "command",
        choices=[
            "check",
            "sync",
            "test",
            "update-policy-registry",
            "update-policy-registry",
            "restore-stock-text",
            "refresh-policies",
            "normalize-metadata",
            "install",
            "update",
            "uninstall",
        ],
        help="Command to run",
    )

    parser.add_argument(
        "--mode",
        choices=["startup", "lint", "pre-commit", "normal"],
        default="normal",
        help="Check mode (default: normal)",
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix violations when possible",
    )

    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current directory)",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=Path("."),
        help="Target repository for install/uninstall commands.",
    )
    parser.add_argument(
        "--policy",
        help="Policy id to restore stock text for (restore-stock-text only).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Restore stock text for all built-in policies.",
    )
    parser.add_argument(
        "--agents",
        default="AGENTS.md",
        help="Relative path to AGENTS.md (default: AGENTS.md).",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help=(
            "Schema source for normalize-metadata (default: "
            "devcovenant/core/profiles/global/assets/AGENTS.md)."
        ),
    )
    parser.add_argument(
        "--no-set-updated",
        action="store_true",
        help="Do not set updated: true when metadata changes.",
    )
    parser.add_argument(
        "--metadata",
        choices=("stock", "preserve"),
        default=None,
        help="Metadata strategy used by refresh-policies (stock/preserve).",
    )
    parser.add_argument(
        "--skip-policy-refresh",
        action="store_true",
        help="Skip refresh-policies during install/update.",
    )
    parser.add_argument(
        "--install-mode",
        choices=("auto", "empty", "existing"),
        help="Install mode for install command (default: auto).",
    )
    parser.add_argument(
        "--docs-mode",
        choices=("preserve", "overwrite"),
        help="Docs mode for install command.",
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
        default=None,
        help="How to handle policy blocks during install/update.",
    )
    parser.add_argument(
        "--config-mode",
        choices=("preserve", "overwrite"),
        help="Config mode for install command.",
    )
    parser.add_argument(
        "--metadata-mode",
        choices=("preserve", "overwrite", "skip"),
        help="Metadata mode for install command.",
    )
    parser.add_argument(
        "--license-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        help="License mode override for install command.",
    )
    parser.add_argument(
        "--version-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        help="Version mode override for install command.",
    )
    parser.add_argument(
        "--version",
        dest="version_value",
        help="Version to use when creating VERSION for install.",
    )
    parser.add_argument(
        "--pyproject-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        help="Pyproject mode override for install command.",
    )
    parser.add_argument(
        "--ci-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        help="CI workflow mode override for install command.",
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
        default=None,
        help="Preserve custom policy scripts and fixers during install.",
    )
    parser.add_argument(
        "--force-docs",
        action="store_true",
        help="Force overwriting docs when installing.",
    )
    parser.add_argument(
        "--force-config",
        action="store_true",
        help="Force overwriting configs when installing.",
    )
    parser.add_argument(
        "--remove-docs",
        action="store_true",
        help="Remove docs when uninstalling.",
    )

    args = parser.parse_args()

    repo_target = args.repo
    if args.command in {"install", "update", "uninstall"}:
        repo_target = args.target
    repo_root = _find_git_root(repo_target)
    if repo_root is None:
        print("DevCovenant commands must run inside a git repository.")
        sys.exit(1)
    args.repo = repo_root
    if args.command in {"install", "update", "uninstall"}:
        args.target = repo_root
    if args.command in {
        "check",
        "sync",
        "test",
        "update-policy-registry",
        "normalize-metadata",
        "restore-stock-text",
    }:
        if not (repo_root / "devcovenant").exists():
            print(
                "DevCovenant is not installed in this repo. "
                "Run `devcovenant install --target .` first."
            )
            sys.exit(1)
    _warn_version_mismatch(repo_root)

    # Initialize engine
    engine = DevCovenantEngine(repo_root=args.repo)

    # Execute command
    if args.command == "check":
        result = engine.check(mode=args.mode, apply_fixes=args.fix)

        # Exit with error code if blocked
        if result.should_block or result.has_sync_issues():
            sys.exit(1)
        else:
            sys.exit(0)

    elif args.command == "sync":
        # Force a sync check
        result = engine.check(mode="startup")
        if result.has_sync_issues():
            print(
                "\n⚠️  Policy sync issues detected. "
                "Please update policy scripts."
            )
            sys.exit(1)
        else:
            print("\n✅ All policies are in sync!")
            sys.exit(0)

    elif args.command == "test":
        # Run devcovenant's own tests
        import subprocess

        try:
            result = subprocess.run(
                ["pytest", "tests/", "-v"],
                cwd=args.repo,
                check=True,
            )
            sys.exit(result.returncode)
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            sys.exit(1)

        sys.exit(0)

    elif args.command in ("update-policy-registry", "update-hashes"):
        from devcovenant.core.update_policy_registry import (
            update_policy_registry,
        )

        if args.command == "update-hashes":
            print(
                "The update-hashes command is deprecated. "
                "Use update-policy-registry instead."
            )
        result = update_policy_registry(args.repo)
        sys.exit(result)

    elif args.command in ("refresh-policies", "normalize-metadata"):
        from devcovenant.core.refresh_policies import refresh_policies

        if args.schema is None:
            schema_path = (
                Path(__file__).resolve().parent
                / "core"
                / "profiles"
                / "global"
                / "assets"
                / "AGENTS.md"
            )
        else:
            schema_path = Path(args.schema)
            if not schema_path.is_absolute():
                schema_path = args.repo / schema_path
        agents_path = args.repo / args.agents
        if not schema_path.exists():
            print(f"Schema file not found: {schema_path}")
            sys.exit(1)

        metadata_mode = args.metadata or (
            "stock" if args.command == "normalize-metadata" else "preserve"
        )
        result = refresh_policies(
            agents_path,
            schema_path,
            metadata_mode=metadata_mode,
            set_updated=not args.no_set_updated,
        )
        if args.command == "normalize-metadata":
            print(
                "normalize-metadata is now deprecated. "
                "Use refresh-policies (defaulting to preserve mode)."
            )
        if result.skipped_policies:
            print("Skipped policies with missing ids:")
            for policy_id in result.skipped_policies:
                print(f"- {policy_id}")
        if result.changed_policies:
            joined = ", ".join(result.changed_policies)
            print(
                f"Updated metadata for: {joined} "
                f"({result.metadata_mode} mode)"
            )
            print(
                "Run `devcovenant update-policy-registry` "
                "to refresh the registry."
            )
        else:
            print("Policy metadata already matched the requested layout.")
        sys.exit(0)

    elif args.command == "restore-stock-text":
        from devcovenant.core.policy_texts import restore_stock_texts

        if not args.policy and not args.all:
            print("Provide --policy <id> or --all.")
            sys.exit(1)

        policy_ids = None if args.all else [args.policy]
        restored = restore_stock_texts(
            args.repo,
            policy_ids=policy_ids,
            agents_rel=args.agents,
        )
        if not restored:
            print("No stock policy text restored.")
            sys.exit(1)
        restored_list = ", ".join(restored)
        print(f"Restored stock policy text for: {restored_list}")
        sys.exit(0)
    elif args.command == "install":
        install_args = ["--target", str(args.target)]
        if args.install_mode:
            install_args.extend(["--mode", args.install_mode])
        if args.docs_mode:
            install_args.extend(["--docs-mode", args.docs_mode])
        if args.docs_include:
            install_args.extend(["--docs-include", args.docs_include])
        if args.docs_exclude:
            install_args.extend(["--docs-exclude", args.docs_exclude])
        if args.policy_mode:
            install_args.extend(["--policy-mode", args.policy_mode])
        if args.config_mode:
            install_args.extend(["--config-mode", args.config_mode])
        if args.metadata_mode:
            install_args.extend(["--metadata-mode", args.metadata_mode])
        if args.license_mode:
            install_args.extend(["--license-mode", args.license_mode])
        if args.version_mode:
            install_args.extend(["--version-mode", args.version_mode])
        if args.version_value:
            install_args.extend(["--version", args.version_value])
        if args.pyproject_mode:
            install_args.extend(["--pyproject-mode", args.pyproject_mode])
        if args.ci_mode:
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
        if args.skip_policy_refresh:
            install_args.append("--skip-policy-refresh")

        from devcovenant.core.install import main as install_main

        install_main(argv=install_args)
        sys.exit(0)

    elif args.command == "update":
        update_args = ["--target", str(args.target)]
        if args.docs_mode:
            update_args.extend(["--docs-mode", args.docs_mode])
        if args.docs_include:
            update_args.extend(["--docs-include", args.docs_include])
        if args.docs_exclude:
            update_args.extend(["--docs-exclude", args.docs_exclude])
        if args.policy_mode:
            update_args.extend(["--policy-mode", args.policy_mode])
        if args.config_mode:
            update_args.extend(["--config-mode", args.config_mode])
        if args.metadata_mode:
            update_args.extend(["--metadata-mode", args.metadata_mode])
        if args.license_mode:
            update_args.extend(["--license-mode", args.license_mode])
        if args.version_mode:
            update_args.extend(["--version-mode", args.version_mode])
        if args.version_value:
            update_args.extend(["--version", args.version_value])
        if args.pyproject_mode:
            update_args.extend(["--pyproject-mode", args.pyproject_mode])
        if args.ci_mode:
            update_args.extend(["--ci-mode", args.ci_mode])
        if args.include_spec:
            update_args.append("--include-spec")
        if args.include_plan:
            update_args.append("--include-plan")
        if args.preserve_custom is not None:
            if args.preserve_custom:
                update_args.append("--preserve-custom")
            else:
                update_args.append("--no-preserve-custom")
        if args.force_docs:
            update_args.append("--force-docs")
        if args.force_config:
            update_args.append("--force-config")
        if args.skip_policy_refresh:
            update_args.append("--skip-policy-refresh")

        from devcovenant.core.update import main as update_main

        update_main(argv=update_args)
        sys.exit(0)

    elif args.command == "uninstall":
        uninstall_args = ["--target", str(args.target)]
        if args.remove_docs:
            uninstall_args.append("--remove-docs")
        from devcovenant.core.uninstall import main as uninstall_main

        uninstall_main(argv=uninstall_args)
        sys.exit(0)


if __name__ == "__main__":
    main()
