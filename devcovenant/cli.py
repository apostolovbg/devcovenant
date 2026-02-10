"""Command-line interface for DevCovenant."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from devcovenant import __version__ as package_version
from devcovenant.core.engine import DevCovenantEngine

_TARGET_COMMANDS = {
    "install",
    "deploy",
    "upgrade",
    "refresh",
    "uninstall",
    "undeploy",
}
_INSTALLED_REQUIRED_COMMANDS = {
    "check",
    "test",
    "deploy",
    "upgrade",
    "refresh",
    "undeploy",
    "update_lock",
}
_BOOTSTRAP_REFRESH_COMMANDS = {"check", "test", "update_lock"}


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


def _run_pre_commit_gate(repo_root: Path, phase: str) -> int:
    """Run the start/end gate through the root command module."""
    command = [
        sys.executable,
        "-m",
        "devcovenant.run_pre_commit",
        "--phase",
        phase,
    ]
    result = subprocess.run(command, cwd=repo_root, check=False)
    return int(result.returncode)


def _add_repo_arg(parser: argparse.ArgumentParser) -> None:
    """Add --repo argument for repo-scoped commands."""
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current directory)",
    )


def _add_target_arg(parser: argparse.ArgumentParser) -> None:
    """Add --target argument for lifecycle commands."""
    parser.add_argument(
        "--target",
        type=Path,
        default=Path("."),
        help="Target repository (default: current directory)",
    )


def _add_lifecycle_options(
    parser: argparse.ArgumentParser,
    *,
    include_install_mode: bool,
) -> None:
    """Add shared lifecycle options for install/deploy/upgrade."""
    _add_target_arg(parser)
    if include_install_mode:
        parser.add_argument(
            "--install-mode",
            choices=("auto", "empty", "existing"),
            help="Install mode for install command (default: auto).",
        )
    parser.add_argument(
        "--skip-policy-refresh",
        action="store_true",
        help="Skip policy metadata refresh during lifecycle command.",
    )
    parser.add_argument(
        "--backup-existing",
        action="store_true",
        help="Create *_old backups before overwriting files.",
    )
    parser.add_argument(
        "--docs-mode",
        choices=("preserve", "overwrite"),
        help="Docs mode override.",
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
        choices=("preserve", "overwrite"),
        default=None,
        help="How to handle policy blocks during lifecycle command.",
    )
    parser.add_argument(
        "--config-mode",
        choices=("preserve", "overwrite"),
        help="Config mode override.",
    )
    parser.add_argument(
        "--license-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        help="License mode override.",
    )
    parser.add_argument(
        "--version-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        help="Version mode override.",
    )
    parser.add_argument(
        "--version",
        dest="version_value",
        help="Version override value.",
    )
    parser.add_argument(
        "--pyproject-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        help="Pyproject mode override.",
    )
    parser.add_argument(
        "--ci-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        help="CI workflow mode override.",
    )
    parser.add_argument(
        "--preserve-custom",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Preserve custom policy scripts and fixers.",
    )
    parser.add_argument(
        "--force-docs",
        action="store_true",
        help="Force overwriting docs.",
    )
    parser.add_argument(
        "--force-config",
        action="store_true",
        help="Force overwriting configs.",
    )


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser with command-specific argument sets."""
    parser = argparse.ArgumentParser(
        description="DevCovenant - Self-enforcing policy system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check",
        help="Run policy checks.",
    )
    check_parser.add_argument(
        "--nofix",
        action="store_true",
        help="Disable auto-fixes for check.",
    )
    gate_group = check_parser.add_mutually_exclusive_group()
    gate_group.add_argument(
        "--start",
        action="store_true",
        help="Run full pre-commit and record the start gate.",
    )
    gate_group.add_argument(
        "--end",
        action="store_true",
        help="Run full pre-commit and record the end gate.",
    )
    check_parser.add_argument(
        "--mode",
        choices=["startup", "lint", "pre-commit", "normal"],
        default="normal",
        help=argparse.SUPPRESS,
    )
    _add_repo_arg(check_parser)

    test_parser = subparsers.add_parser(
        "test",
        help="Run required test suites.",
    )
    _add_repo_arg(test_parser)

    install_parser = subparsers.add_parser(
        "install",
        help="Install DevCovenant into a repository.",
    )
    _add_lifecycle_options(install_parser, include_install_mode=True)

    deploy_parser = subparsers.add_parser(
        "deploy",
        help="Deploy managed docs/assets into a repository.",
    )
    _add_lifecycle_options(deploy_parser, include_install_mode=False)

    upgrade_parser = subparsers.add_parser(
        "upgrade",
        help="Upgrade DevCovenant core in a repository.",
    )
    _add_lifecycle_options(upgrade_parser, include_install_mode=False)

    refresh_parser = subparsers.add_parser(
        "refresh",
        help="Run full refresh for registry/docs/assets.",
    )
    _add_target_arg(refresh_parser)
    refresh_parser.add_argument(
        "--backup-existing",
        action="store_true",
        help="Create *_old backups before overwriting files.",
    )

    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Remove DevCovenant from a repository.",
    )
    _add_target_arg(uninstall_parser)
    uninstall_parser.add_argument(
        "--remove-docs",
        action="store_true",
        help="Remove docs when uninstalling.",
    )

    undeploy_parser = subparsers.add_parser(
        "undeploy",
        help="Remove deployed managed blocks and generated runtime files.",
    )
    _add_target_arg(undeploy_parser)

    update_lock_parser = subparsers.add_parser(
        "update_lock",
        help="Regenerate lockfiles.",
    )
    _add_repo_arg(update_lock_parser)

    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args()

    if (
        args.command == "check"
        and (args.start or args.end)
        and args.mode != "normal"
    ):
        parser.error("--mode cannot be combined with --start or --end.")

    repo_target = (
        args.target if args.command in _TARGET_COMMANDS else args.repo
    )
    repo_root = _find_git_root(repo_target)
    if repo_root is None:
        print("DevCovenant commands must run inside a git repository.")
        sys.exit(1)

    if args.command in _TARGET_COMMANDS:
        args.target = repo_root
    else:
        args.repo = repo_root

    if args.command in _INSTALLED_REQUIRED_COMMANDS:
        if not (repo_root / "devcovenant").exists():
            print(
                "DevCovenant is not installed in this repo. "
                "Run `devcovenant install --target .` first."
            )
            sys.exit(1)

    if args.command == "check" and (args.start or args.end):
        phase = "start" if args.start else "end"
        _print_banner("Devflow gate", "🚦")
        _print_step(f"Running `{phase}` pre-commit gate", "▶️")
        exit_code = _run_pre_commit_gate(repo_root, phase)
        if exit_code == 0:
            _print_step(f"{phase.capitalize()} gate recorded", "✅")
        sys.exit(exit_code)

    _print_banner("DevCovenant run", "🚀")
    _print_step(f"Command: {args.command}", "🧭")

    if args.command == "check":
        _print_step(f"Mode: {args.mode}", "🔧")
        _print_step(
            f"Auto-fix: {'disabled' if args.nofix else 'enabled'}",
            "🛠️",
        )

    if args.command in _BOOTSTRAP_REFRESH_COMMANDS:
        _print_step("Refreshing local registry", "🔄")
        try:
            from devcovenant.core.refresh_registry import refresh_registry

            refresh_registry(repo_root, skip_freeze=True)
            _print_step("Registry refresh complete", "✅")
        except Exception as exc:  # pragma: no cover - defensive
            _print_step(f"Registry refresh skipped ({exc})", "⚠️")

    _warn_version_mismatch(repo_root)

    if args.command == "check":
        _print_step("Initializing engine", "🧠")
        engine = DevCovenantEngine(repo_root=args.repo)
        _print_step("Engine ready", "✅")
        _print_banner("Policy checks", "🔍")
        _print_step("Running policy checks", "▶️")
        result = engine.check(mode=args.mode, apply_fixes=not args.nofix)
        _print_step("Policy checks complete", "🏁")
        if result.should_block or result.has_sync_issues():
            sys.exit(1)
        sys.exit(0)

    if args.command == "test":
        _print_banner("DevCovenant tests", "🧪")
        _print_step("Running pytest + unittest discover", "▶️")
        cmd = [sys.executable, "-m", "devcovenant.run_tests"]
        try:
            result = subprocess.run(cmd, cwd=args.repo, check=True)
            sys.exit(result.returncode)
        except Exception as exc:  # pragma: no cover - subprocess failure path
            print(f"❌ Test execution failed: {exc}")
            sys.exit(1)

    if args.command == "refresh":
        _print_banner("Full refresh", "🔄")
        from devcovenant.core.refresh_all import refresh_all

        result = refresh_all(
            args.target,
            registry_only=False,
            backup_existing=args.backup_existing,
        )
        sys.exit(result)

    if args.command == "install":
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
            install_args.append(
                "--preserve-custom"
                if args.preserve_custom
                else "--no-preserve-custom"
            )
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

    if args.command == "deploy":
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
            deploy_args.append(
                "--preserve-custom"
                if args.preserve_custom
                else "--no-preserve-custom"
            )
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

    if args.command == "upgrade":
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
            upgrade_args.append(
                "--preserve-custom"
                if args.preserve_custom
                else "--no-preserve-custom"
            )
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

    if args.command == "uninstall":
        _print_banner("Uninstall DevCovenant", "🧹")
        uninstall_args = ["--target", str(args.target)]
        if args.remove_docs:
            uninstall_args.append("--remove-docs")
        from devcovenant.core.uninstall import main as uninstall_main

        uninstall_main(argv=uninstall_args)
        sys.exit(0)

    if args.command == "undeploy":
        _print_banner("Undeploy DevCovenant", "🧽")
        from devcovenant.core.undeploy import main as undeploy_main

        undeploy_main(argv=["--target", str(args.target)])
        sys.exit(0)

    if args.command == "update_lock":
        _print_banner("Update lockfiles", "🔐")
        result = subprocess.run(
            [sys.executable, "-m", "devcovenant.update_lock"],
            cwd=args.repo,
            check=False,
        )
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
