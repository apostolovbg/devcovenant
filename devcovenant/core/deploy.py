#!/usr/bin/env python3
"""Deploy DevCovenant-managed docs/assets into a target repository."""

from __future__ import annotations

import argparse

from devcovenant.core import cli_options, install


def main(argv=None) -> None:
    """CLI entry point for deploy."""
    parser = argparse.ArgumentParser(
        description=(
            "Deploy DevCovenant-managed docs/assets using the existing core."
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
    install_args.append("--require-non-generic")
    install_args.append("--skip-core")
    install.main(install_args)


if __name__ == "__main__":
    main()
