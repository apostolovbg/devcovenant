#!/usr/bin/env python3
"""
Convenience wrapper to run DevCovenant checks.

Usage:
    python -m devcovenant.core.check check                 # Normal check
    python -m devcovenant.core.check check --mode startup  # Startup mode
    python -m devcovenant.core.check check --mode lint     # Lint mode
    python -m devcovenant.core.check check --fix           # Auto-fix
"""

from devcovenant.cli import main

if __name__ == "__main__":
    main()
