#!/usr/bin/env python3
"""Refresh DevCovenant-managed content without touching core files."""

from __future__ import annotations

import argparse

from devcovenant.core import cli_options, install


def main(argv=None) -> None:
    """CLI entry point for managed-content updates."""
    parser = argparse.ArgumentParser(
        description=(
            "Update DevCovenant-managed docs/assets/registries without "
            "changing core files."
        )
    )
    cli_options.add_install_update_args(
        parser,
        defaults=cli_options.DEFAULT_UPDATE_DEFAULTS,
    )
    args = parser.parse_args(argv)

    install_args = cli_options.build_install_args(
        args,
        mode="existing",
        allow_existing=True,
    )
    install_args.append("--deploy")
    install_args.append("--skip-core")
    install.main(install_args)


if __name__ == "__main__":
    main()
