"""Entry point for `python3 -m devcovenant` (or `python -m devcovenant`)."""

from __future__ import annotations

from devcovenant.launcher_bootstrap import apply_repo_pycache_prefix_from_cwd

apply_repo_pycache_prefix_from_cwd()

from devcovenant.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
