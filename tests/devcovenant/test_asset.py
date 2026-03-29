"""Unit tests for the asset command behavior."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from devcovenant import asset as asset_command


def _unit_test_asset_module_symbol_contract_is_stable() -> None:
    """asset module should expose its public command entrypoints."""
    assert asset_command._build_parser
    assert asset_command.run
    assert asset_command.main


def _unit_test_asset_materializes_named_asset() -> None:
    """run() should delegate asset materialization through the service."""
    repo_root = Path("/repo")
    args = SimpleNamespace(
        asset_name="SPEC.md",
        output_name="OTHERNAME.md",
        overwrite=True,
    )
    result_payload = SimpleNamespace(
        candidate=SimpleNamespace(
            kind="managed_doc",
            target_path="SPEC.md",
            profile_name="global",
        ),
        output_path=Path("/Desktop/OTHERNAME.md"),
    )

    with patch("devcovenant.asset.resolve_repo_root", return_value=repo_root):
        with patch("devcovenant.asset.warn_version_mismatch") as mismatch:
            with patch("devcovenant.asset.print_banner") as print_banner:
                with patch("devcovenant.asset.print_step") as print_step:
                    with patch(
                        (
                            "devcovenant.asset.asset_service."
                            "materialize_named_asset"
                        ),
                        return_value=result_payload,
                    ) as materialize:
                        exit_code = asset_command.run(args)

    assert exit_code == 0
    mismatch.assert_called_once_with(repo_root)
    print_banner.assert_called_once_with("DevCovenant asset", "🧰")
    materialize.assert_called_once_with(
        repo_root,
        "SPEC.md",
        output_name="OTHERNAME.md",
        overwrite=True,
    )
    assert print_step.call_count >= 3


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for asset-command checks."""

    def test_asset_module_symbol_contract_is_stable(self):
        """Run asset-module symbol assertions."""
        _unit_test_asset_module_symbol_contract_is_stable()

    def test_asset_materializes_named_asset(self):
        """Run asset-command delegation assertions."""
        _unit_test_asset_materializes_named_asset()
