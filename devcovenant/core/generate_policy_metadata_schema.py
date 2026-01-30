"""Generate the policy metadata schema file from descriptors."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import refresh_policies


def main() -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(
        description="Generate the policy metadata schema YAML file."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=("Override the output path (defaults to the registry location)."),
    )
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    output_path = refresh_policies.export_metadata_schema(
        repo_root, output_path=args.output
    )
    print(f"Wrote policy metadata schema to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
