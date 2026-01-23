"""
Command-line interface for devcovenant.
"""

import argparse
import sys
from pathlib import Path

from devcovenant.core.engine import DevCovenantEngine


def main():
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
            "update-hashes",
            "restore-stock-text",
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
            "devcovenant/templates/AGENTS.md)."
        ),
    )
    parser.add_argument(
        "--no-set-updated",
        action="store_true",
        help="Do not set updated: true when metadata changes.",
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
                ["pytest", "devcovenant/core/tests/", "-v"],
                cwd=args.repo,
                check=True,
            )
            sys.exit(result.returncode)
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            sys.exit(1)

    elif args.command == "update-hashes":
        # Update policy script hashes in registry.json
        from devcovenant.core.update_hashes import update_registry_hashes

        result = update_registry_hashes(args.repo)
        sys.exit(result)

    elif args.command == "normalize-metadata":
        from devcovenant.core.metadata_normalizer import (
            normalize_agents_metadata,
        )

        agents_path = args.repo / args.agents
        if args.schema is None:
            schema_path = (
                Path(__file__).resolve().parent / "templates" / "AGENTS.md"
            )
        else:
            schema_path = Path(args.schema)
            if not schema_path.is_absolute():
                schema_path = args.repo / schema_path
        if not schema_path.exists():
            print(f"Schema file not found: {schema_path}")
            sys.exit(1)

        result = normalize_agents_metadata(
            agents_path,
            schema_path,
            set_updated=not args.no_set_updated,
        )
        if result.skipped_policies:
            print("Skipped policies with missing ids:")
            for policy_id in result.skipped_policies:
                print(f"- {policy_id}")
        if result.changed_policies:
            joined = ", ".join(result.changed_policies)
            print(f"Updated metadata for: {joined}")
            print("Run `devcovenant update-hashes` to refresh the registry.")
        else:
            print("No metadata updates were required.")
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
