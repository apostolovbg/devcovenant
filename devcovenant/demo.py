#!/usr/bin/env python3
"""Run a disposable DevCovenant evaluation demo."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import os
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path

import devcovenant.core.cli_support as cli_args_module


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for the demo command."""
    return cli_args_module.build_command_parser(
        "demo",
        "Run a disposable evaluation demo for DevCovenant.",
    )


def _write_text(path: Path, content: str) -> None:
    """Write one UTF-8 text file and create parents when needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_demo_repo(repo_root: Path) -> None:
    """Create one disposable git repo for the demo lifecycle."""
    repo_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(  # nosec B603 B607
        ["git", "init", "-q"], cwd=repo_root, check=True
    )
    _write_text(
        repo_root / "README.md",
        "# Demo repository\n\n"
        "## Overview\n"
        "This disposable repository shows DevCovenant as a governed repo\n"
        "lifecycle rather than a one-off checker. It starts as a normal\n"
        "repository, then introduces install, deploy, customization, and\n"
        "workflow commands in a fixed sequence. The goal is to make the\n"
        "repository contract visible quickly so a new reader can see what\n"
        "DevCovenant does without first learning the whole internal model.\n\n"
        "## How It Works\n"
        "DevCovenant keeps repository rules, generated assets, and policy\n"
        "metadata in sync. The demo repo uses a tiny test package, then\n"
        "walks through the standard lifecycle. That makes the repo feel\n"
        "like a real project instead of a marketing sample. You can see\n"
        "where install ends, where reviewed deployment begins, and how the\n"
        "gate cycle protects the repo after a change.\n\n"
        "## Why It Matters\n"
        "A repo that owns its own governance is easier to understand and\n"
        "harder to drift. Humans, AI helpers, and CI all see the same\n"
        "contract. That is useful for evaluation, for onboarding, and for\n"
        "selling the idea to teams that want better repo discipline.\n\n"
        "## Next Steps\n"
        "Run `devcovenant demo` to watch the flow end to end, then open the\n"
        "installation and workflow docs if you want the operator version of\n"
        "the same story.\n",
    )
    _write_text(
        repo_root / "CHANGELOG.md",
        "# CHANGELOG\n\n"
        "## Unreleased\n\n"
        "- 2026-04-16:\n"
        "  Change: Seeded the demo repository with a governed baseline.\n"
        "  Why: Give the disposable repo a valid changelog shape before the\n"
        "  guided lifecycle adds its own session entry.\n"
        "  Impact: Later demo edits can prepend a fresh top entry without\n"
        "  rebuilding the file structure.\n"
        "  Files:\n"
        "  README.md\n"
        "  CHANGELOG.md\n",
    )


def _mark_config_reviewed(repo_root: Path) -> None:
    """Set install.config_reviewed to true in the demo repo."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    lines = config_path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "config_reviewed: false":
            indent = line[: len(line) - len(line.lstrip())]
            lines[index] = f"{indent}config_reviewed: true"
            config_path.write_text(
                "\n".join(lines) + "\n",
                encoding="utf-8",
            )
            return
    raise SystemExit("config_reviewed field line not found in config.yaml")


def _write_smoke_test(repo_root: Path) -> None:
    """Write the demo smoke test plus evaluation docs into the repo."""
    _write_text(
        repo_root / "tests" / "__init__.py",
        '"""Demo test package."""\n',
    )
    _write_text(
        repo_root / "tests" / "test_smoke.py",
        '"""Demo smoke tests for the workflow run."""\n\n'
        "import unittest\n\n\n"
        "class SmokeTest(unittest.TestCase):\n"
        '    """Keep the demo workflow run non-empty."""\n\n'
        "    def test_truth(self) -> None:\n"
        '        """Demonstrate a passing governed test."""\n'
        "        self.assertTrue(True)\n\n\n"
        'if __name__ == "__main__":\n'
        "    unittest.main()\n",
    )
    _write_text(
        repo_root / "CHANGELOG.md",
        "# CHANGELOG\n\n"
        "## Unreleased\n\n"
        "- 2026-04-17:\n"
        "  Change: Added a disposable demo repository with a smoke test,\n"
        "  a richer README, and a session changelog entry.\n"
        "  Why: Keep the evaluation repo aligned with documentation-growth\n"
        "  and changelog-coverage during the guided workflow.\n"
        "  Impact: The demo can open, verify, run, and close without\n"
        "  policy complaints.\n"
        "  Files:\n"
        "  CHANGELOG.md\n"
        "  tests/__init__.py\n"
        "  tests/test_smoke.py\n\n"
        "- 2026-04-16:\n"
        "  Change: Seeded the demo repository with a governed baseline.\n"
        "  Why: Give the disposable repo a valid changelog shape before the\n"
        "  guided lifecycle adds its own session entry.\n"
        "  Impact: Later demo edits can prepend a fresh top entry without\n"
        "  rebuilding the file structure.\n"
        "  Files:\n"
        "  README.md\n"
        "  CHANGELOG.md\n",
    )


def _run_install(repo_root: Path) -> int:
    """Run install against the disposable demo repo."""
    return _run_demo_command(repo_root, "install")


def _run_deploy(repo_root: Path) -> int:
    """Run deploy against the disposable demo repo."""
    return _run_demo_command(repo_root, "deploy")


def _run_custom_teaser(repo_root: Path) -> int:
    """Run the custom-governance teaser against the demo repo."""
    return _run_demo_command(
        repo_root,
        "custom",
        "--profile",
        "userproject",
        "--do",
    )


def _run_gate_stage(repo_root: Path, stage: str) -> int:
    """Run one gate stage against the disposable demo repo."""
    return _run_demo_command(repo_root, "gate", f"--{stage}")


def _run_workflow_runs(repo_root: Path) -> int:
    """Run the configured workflow runs against the demo repo."""
    return _run_demo_command(repo_root, "run")


def _run_demo_command(repo_root: Path, *command: str) -> int:
    """Run one DevCovenant command inside the disposable demo repo."""
    env = dict(os.environ)
    package_root = Path(__file__).resolve().parents[1]
    pythonpath_entries = [str(package_root)]
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_entries.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
    completed = subprocess.run(
        [sys.executable, "-m", "devcovenant", *command],
        cwd=repo_root,
        check=False,
        env=env,
    )  # nosec B603
    return completed.returncode


def run(_args: argparse.Namespace) -> int:
    """Execute the disposable demo."""
    from devcovenant.core.execution import (
        devcovenant_banner_title,
        print_banner,
        print_step,
    )

    del _args
    with tempfile.TemporaryDirectory(prefix="devcovenant-demo-") as temp_dir:
        repo_root = Path(temp_dir) / "repo"
        _seed_demo_repo(repo_root)

        print_banner("DevCovenant demo", "🎬")
        print_step("Command: demo", "🧭")
        print_step(f"Disposable repo: {repo_root}", "📁")
        print_step("Install the packaged core", "1️⃣")
        if _run_install(repo_root) != 0:
            return 1
        _mark_config_reviewed(repo_root)
        print_step("Review config and deploy managed docs", "2️⃣")
        if _run_deploy(repo_root) != 0:
            return 1
        print_step("Materialize the userproject customization teaser", "3️⃣")
        if _run_custom_teaser(repo_root) != 0:
            return 1
        print_step("Open the gate before making a governed change", "4️⃣")
        if _run_gate_stage(repo_root, "open") != 0:
            return 1
        _write_smoke_test(repo_root)
        print_step("Verify, run, and close the workflow cycle", "5️⃣")
        verify_result = _run_gate_stage(repo_root, "verify")
        if verify_result != 0:
            print_step("Re-run verify after hook-induced changes", "🔁")
            verify_result = _run_gate_stage(repo_root, "verify")
        if verify_result != 0:
            return 1
        if _run_workflow_runs(repo_root) != 0:
            return 1
        if _run_gate_stage(repo_root, "close") != 0:
            return 1

        print_banner(devcovenant_banner_title(), "✅")
        print_step("Demo complete", "🏁")
        print_step("Disposable repo cleaned up automatically", "🧹")
        return 0


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    cli_args_module.apply_output_mode_override_from_namespace(args)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
