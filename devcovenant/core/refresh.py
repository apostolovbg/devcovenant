#!/usr/bin/env python3
"""Registry-only refresh for DevCovenant."""

from __future__ import annotations

import argparse
from pathlib import Path

from devcovenant.core import cli_options
from devcovenant.core.refresh_all import refresh_registry


def main(argv=None) -> None:
    """CLI entry point for registry-only refresh."""
    parser = argparse.ArgumentParser(
        description="Refresh DevCovenant registry metadata only."
    )
    cli_options.add_target_arg(parser)
    args = parser.parse_args(argv)
    target_root = Path(args.target).resolve()
    result = refresh_registry(target_root)
    raise SystemExit(result)


if __name__ == "__main__":
    main()
