#!/usr/bin/env python3
"""
Convenience wrapper to run DevCovenant checks.

Usage:
    python -m devcovenant.core.check check                 # Auto-fix check
    python -m devcovenant.core.check check --nofix         # Audit-only check
    python -m devcovenant.core.check check --start         # Start gate
    python -m devcovenant.core.check check --end           # End gate
"""

from devcovenant.cli import main

if __name__ == "__main__":
    main()
