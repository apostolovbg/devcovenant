#!/usr/bin/env python3
"""Thin wrapper to run the DevCovenant uninstall CLI."""

from __future__ import annotations

import sys

from devcovenant.cli import main as devcov_cli

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "uninstall"] + sys.argv[1:]
    devcov_cli()
