"""Command dispatcher for DevCovenant."""

from __future__ import annotations

import argparse
import importlib
import sys
from types import ModuleType

_COMMAND_MODULES = {
    "check": "devcovenant.check",
    "gate": "devcovenant.gate",
    "test": "devcovenant.test",
    "install": "devcovenant.install",
    "deploy": "devcovenant.deploy",
    "upgrade": "devcovenant.upgrade",
    "refresh": "devcovenant.refresh",
    "uninstall": "devcovenant.uninstall",
    "undeploy": "devcovenant.undeploy",
    "update_lock": "devcovenant.update_lock",
}


def _build_parser() -> argparse.ArgumentParser:
    """Build the root dispatcher parser."""
    parser = argparse.ArgumentParser(
        description="DevCovenant - Self-enforcing policy system"
    )
    parser.add_argument(
        "command",
        choices=sorted(_COMMAND_MODULES.keys()),
        help="Command to run",
    )
    return parser


def _load_command_module(command: str) -> ModuleType:
    """Import and return command module for a command id."""
    module_path = _COMMAND_MODULES[command]
    return importlib.import_module(module_path)


def main(argv: list[str] | None = None) -> None:
    """Main CLI entry point."""
    parser = _build_parser()
    command_args = list(sys.argv[1:] if argv is None else argv)
    if not command_args:
        parser.print_help()
        raise SystemExit(0)

    first = command_args[0]
    if first in {"-h", "--help"}:
        parser.print_help()
        raise SystemExit(0)
    if first not in _COMMAND_MODULES:
        parser.error(
            f"argument command: invalid choice: '{first}' "
            f"(choose from {', '.join(sorted(_COMMAND_MODULES))})"
        )
    module = _load_command_module(first)

    if not hasattr(module, "main"):
        raise SystemExit(
            f"Command module '{module.__name__}' is missing main()."
        )

    module.main(command_args[1:])


if __name__ == "__main__":
    main()
