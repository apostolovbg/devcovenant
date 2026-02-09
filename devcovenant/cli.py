"""
Command-line interface for devcovenant.
"""

import argparse
import re
import sys
from pathlib import Path

from devcovenant import __version__ as package_version
from devcovenant.core.engine import DevCovenantEngine


def _print_banner(title: str, emoji: str) -> None:
    """Print a readable stage banner."""
    print("\n" + "=" * 70)
    print(f"{emoji} {title}")
    print("=" * 70)


def _print_step(message: str, emoji: str = "•") -> None:
    """Print a short, single-line status step."""
    print(f"{emoji} {message}")


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
            "refresh_registry",
            "refresh-policies",
            "refresh-all",
            "normalize-metadata",
            "install",
            "deploy",
            "update",
            "upgrade",
            "refresh",
            "uninstall",
            "undeploy",
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
        "--agents",
        default="AGENTS.md",
        help="Relative path to AGENTS.md (default: AGENTS.md).",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help=(
            "Schema source for refresh-policies (default: "
            "devcovenant/core/profiles/global/assets/AGENTS.md)."
        ),
    )
    parser.add_argument(
        "--skip-policy-refresh",
        action="store_true",
        help="Skip refresh-policies during install/update.",
    )
    parser.add_argument(
        "--backup-existing",
        action="store_true",
        help="Create *_old backups before overwriting files.",
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
        "--registry-only",
        action="store_true",
        help=(
            "Registry-only refresh (skip AGENTS/docs) when running"
            " refresh-all."
        ),
    )
    parser.add_argument(
        "--policy-mode",
        choices=("preserve", "overwrite"),
        default=None,
        help="How to handle policy blocks during install/update.",
    )
    parser.add_argument(
        "--config-mode",
        choices=("preserve", "overwrite"),
        help="Config mode for install command.",
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
        help="Version to use when creating devcovenant/VERSION for install.",
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
    if args.command in {
        "install",
        "deploy",
        "update",
        "upgrade",
        "refresh",
        "uninstall",
        "undeploy",
    }:
        repo_target = args.target
    repo_root = _find_git_root(repo_target)
    if repo_root is None:
        print("DevCovenant commands must run inside a git repository.")
        sys.exit(1)
    args.repo = repo_root
    if args.command in {
        "install",
        "deploy",
        "update",
        "upgrade",
        "refresh",
        "uninstall",
        "undeploy",
    }:
        args.target = repo_root
    if args.command in {
        "check",
        "sync",
        "test",
        "refresh_registry",
        "normalize-metadata",
        "deploy",
        "update",
        "upgrade",
        "refresh",
        "undeploy",
    }:
        if not (repo_root / "devcovenant").exists():
            print(
                "DevCovenant is not installed in this repo. "
                "Run `devcovenant install --target .` first."
            )
            sys.exit(1)

    # Lightweight registry refresh (no AGENTS/docs writes) on every invocation
    _print_banner("DevCovenant run", "🚀")
    _print_step(f"Command: {args.command}", "🧭")
    if args.command == "check":
        _print_step(f"Mode: {args.mode}", "🔧")
        _print_step(f"Auto-fix: {'enabled' if args.fix else 'disabled'}", "🛠️")
    _print_step("Refreshing local registry", "🔄")
    try:
        from devcovenant.core.refresh_registry import refresh_registry

        refresh_registry(args.repo, skip_freeze=True)
        _print_step("Registry refresh complete", "✅")
    except Exception as exc:
        _print_step(f"Registry refresh skipped ({exc})", "⚠️")

    _warn_version_mismatch(repo_root)

    # Initialize engine
    _print_step("Initializing engine", "🧠")
    engine = DevCovenantEngine(repo_root=args.repo)
    _print_step("Engine ready", "✅")

    # Execute command
    if args.command == "check":
        _print_banner("Policy checks", "🔍")
        _print_step("Running policy checks", "▶️")
        result = engine.check(mode=args.mode, apply_fixes=args.fix)
        _print_step("Policy checks complete", "🏁")

        # Exit with error code if blocked
        if result.should_block or result.has_sync_issues():
            sys.exit(1)
        else:
            sys.exit(0)

    elif args.command == "sync":
        _print_banner("Policy sync", "🔗")
        _print_step("Running startup sync check", "▶️")
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
        _print_banner("DevCovenant tests", "🧪")
        _print_step("Running pytest + unittest discover", "▶️")
        # Run devcovenant's own tests (pytest + unittest) and record status
        import subprocess

        cmd = [sys.executable, "-m", "devcovenant.run_tests"]
        try:
            result = subprocess.run(cmd, cwd=args.repo, check=True)
            sys.exit(result.returncode)
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            sys.exit(1)

    elif args.command == "refresh_registry":
        from devcovenant.core.refresh_all import refresh_registry

        _print_banner("Policy registry refresh", "🧾")
        result = refresh_registry(args.repo)
        sys.exit(result)

    elif args.command in ("refresh-policies", "normalize-metadata"):
        from devcovenant.core.refresh_policies import refresh_policies

        _print_banner("Policy metadata refresh", "🧩")
        if args.schema is None:
            schema_path = None
        else:
            schema_path = Path(args.schema)
            if not schema_path.is_absolute():
                schema_path = args.repo / schema_path
            if not schema_path.exists():
                print(f"Schema file not found: {schema_path}")
                sys.exit(1)
        agents_path = args.repo / args.agents

        result = refresh_policies(
            agents_path,
            schema_path,
        )
        if args.command == "normalize-metadata":
            print(
                "normalize-metadata is now deprecated. "
                "Use refresh-policies instead."
            )
        if result.skipped_policies:
            print("Skipped policies with missing ids:")
            for policy_id in result.skipped_policies:
                print(f"- {policy_id}")
        if result.changed_policies:
            joined = ", ".join(result.changed_policies)
            print(f"Updated metadata for: {joined}")

    elif args.command == "refresh-all":
        from devcovenant.core.refresh_all import refresh_all

        _print_banner("Refresh all", "🔄")
        result = refresh_all(
            args.repo,
            registry_only=args.registry_only,
            backup_existing=args.backup_existing,
        )
        sys.exit(result)

    elif args.command == "refresh":
        _print_banner("Registry refresh", "🔄")
        from devcovenant.core.refresh import main as refresh_main

        refresh_main(argv=["--target", str(args.target)])
        sys.exit(0)

    elif args.command == "install":
        _print_banner("Install DevCovenant", "📦")
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
        if args.backup_existing:
            install_args.append("--backup-existing")

        from devcovenant.core.install import main as install_main

        install_main(argv=install_args)
        sys.exit(0)

    elif args.command == "deploy":
        _print_banner("Deploy DevCovenant", "🚀")
        deploy_args = ["--target", str(args.target)]
        if args.docs_mode:
            deploy_args.extend(["--docs-mode", args.docs_mode])
        if args.docs_include:
            deploy_args.extend(["--docs-include", args.docs_include])
        if args.docs_exclude:
            deploy_args.extend(["--docs-exclude", args.docs_exclude])
        if args.policy_mode:
            deploy_args.extend(["--policy-mode", args.policy_mode])
        if args.config_mode:
            deploy_args.extend(["--config-mode", args.config_mode])
        if args.license_mode:
            deploy_args.extend(["--license-mode", args.license_mode])
        if args.version_mode:
            deploy_args.extend(["--version-mode", args.version_mode])
        if args.version_value:
            deploy_args.extend(["--version", args.version_value])
        if args.pyproject_mode:
            deploy_args.extend(["--pyproject-mode", args.pyproject_mode])
        if args.ci_mode:
            deploy_args.extend(["--ci-mode", args.ci_mode])
        if args.preserve_custom is not None:
            if args.preserve_custom:
                deploy_args.append("--preserve-custom")
            else:
                deploy_args.append("--no-preserve-custom")
        if args.force_docs:
            deploy_args.append("--force-docs")
        if args.force_config:
            deploy_args.append("--force-config")
        if args.skip_policy_refresh:
            deploy_args.append("--skip-policy-refresh")
        if args.backup_existing:
            deploy_args.append("--backup-existing")

        from devcovenant.core.deploy import main as deploy_main

        deploy_main(argv=deploy_args)
        sys.exit(0)

    elif args.command == "update":
        _print_banner("Update DevCovenant", "🔁")
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
        if args.backup_existing:
            update_args.append("--backup-existing")

        from devcovenant.core.update import main as update_main

        update_main(argv=update_args)
        sys.exit(0)

    elif args.command == "upgrade":
        _print_banner("Upgrade DevCovenant", "⬆️")
        upgrade_args = ["--target", str(args.target)]
        if args.docs_mode:
            upgrade_args.extend(["--docs-mode", args.docs_mode])
        if args.docs_include:
            upgrade_args.extend(["--docs-include", args.docs_include])
        if args.docs_exclude:
            upgrade_args.extend(["--docs-exclude", args.docs_exclude])
        if args.policy_mode:
            upgrade_args.extend(["--policy-mode", args.policy_mode])
        if args.config_mode:
            upgrade_args.extend(["--config-mode", args.config_mode])
        if args.license_mode:
            upgrade_args.extend(["--license-mode", args.license_mode])
        if args.version_mode:
            upgrade_args.extend(["--version-mode", args.version_mode])
        if args.version_value:
            upgrade_args.extend(["--version", args.version_value])
        if args.pyproject_mode:
            upgrade_args.extend(["--pyproject-mode", args.pyproject_mode])
        if args.ci_mode:
            upgrade_args.extend(["--ci-mode", args.ci_mode])
        if args.preserve_custom is not None:
            if args.preserve_custom:
                upgrade_args.append("--preserve-custom")
            else:
                upgrade_args.append("--no-preserve-custom")
        if args.force_docs:
            upgrade_args.append("--force-docs")
        if args.force_config:
            upgrade_args.append("--force-config")
        if args.skip_policy_refresh:
            upgrade_args.append("--skip-policy-refresh")
        if args.backup_existing:
            upgrade_args.append("--backup-existing")

        from devcovenant.core.upgrade import main as upgrade_main

        upgrade_main(argv=upgrade_args)
        sys.exit(0)

    elif args.command == "uninstall":
        _print_banner("Uninstall DevCovenant", "🧹")
        uninstall_args = ["--target", str(args.target)]
        if args.remove_docs:
            uninstall_args.append("--remove-docs")
        from devcovenant.core.uninstall import main as uninstall_main

        uninstall_main(argv=uninstall_args)
        sys.exit(0)

    elif args.command == "undeploy":
        _print_banner("Undeploy DevCovenant", "🧽")
        from devcovenant.core.undeploy import main as undeploy_main

        undeploy_main(argv=["--target", str(args.target)])
        sys.exit(0)


if __name__ == "__main__":
    main()
