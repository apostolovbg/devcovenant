#!/usr/bin/env python3
"""Print the canonical DevCovenant first-use guide."""

from __future__ import annotations

if __package__ in {None, ""}:  # pragma: no cover
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse

import devcovenant.core.cli_support as cli_args_module


def _build_parser() -> argparse.ArgumentParser:
    """Build parser for the quickstart command."""
    return cli_args_module.build_command_parser(
        "quickstart",
        "Print the canonical first-use guide.",
    )


def _render_quickstart() -> str:
    """Return the fixed quickstart guide text."""
    lines = [
        "DevCovenant quickstart",
        "",
        "1. Install the CLI in an isolated machine environment.",
        "   pipx install devcovenant",
        "   devcovenant --version",
        "",
        "2. Install DevCovenant into the repository you want to govern.",
        "   cd your-repo",
        "   devcovenant install",
        "",
        "3. Review devcovenant/config.yaml before you deploy.",
        "   Start with project-governance, developer_mode,",
        "   and profiles.active.",
        "   Builtin devcovuser is intentionally thin.",
        "   In most downstream repositories, customize devcovuser with",
        "   repo-owned values and, when needed, customize the python",
        "   profile too.",
        "   The copy-ready bootstrap template starts at",
        "   devcovenant/builtin/profiles/userproject/ and becomes repo-owned",
        "   when copied to devcovenant/custom/profiles/userproject/.",
        "",
        "4. Activate the reviewed setup.",
        "   devcovenant deploy",
        "",
        "5. Prepare the environment declared by the active profile stack.",
        "   That might be a local .venv, a system interpreter, a container-",
        "   managed environment, or another declared layout.",
        "",
        "6. Run the first gate cycle.",
        "   devcovenant gate --open",
        "   # make your edits",
        "   devcovenant gate --verify",
        "   devcovenant run",
        "   devcovenant gate --close",
        "",
        "7. Read the deeper docs next.",
        "   installation.md, workflow.md, config.md, policies.md, profiles.md",
        "   For a disposable guided evaluation repo, run `devcovenant demo`.",
    ]
    return "\n".join(lines) + "\n"


def run(_args: argparse.Namespace) -> int:
    """Print the fixed quickstart guide."""
    from devcovenant.core.cli_support import write_console_text

    del _args
    write_console_text(_render_quickstart(), flush=True)
    return 0


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    cli_args_module.apply_output_mode_override_from_namespace(args)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
