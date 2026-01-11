#!/usr/bin/env python3
"""
Convenience wrapper to run devcovenant checks.

Usage:
    python devcov_check.py              # Normal check
    python devcov_check.py --startup    # Startup (AI)
    python devcov_check.py --lint       # Lint mode
    python devcov_check.py --fix        # Auto-fix
"""

import sys
from pathlib import Path

# Import devcovenant
sys.path.insert(0, str(Path(__file__).parent))

from devcovenant.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
