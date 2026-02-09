"""Tests for the refresh-all helper."""

from pathlib import Path

import yaml

from devcovenant.core import deploy, install
from devcovenant.core.refresh_all import refresh_all


def _with_skip_refresh(args: list[str]) -> list[str]:
    """Append the skip-refresh flag to speed up install setup."""
    return [*args, "--skip-refresh"]


def _set_doc_assets(
    target: Path, *, autogen: list[str], user: list[str]
) -> None:
    """Set doc_assets.autogen and doc_assets.user in config.yaml."""
    config_path = target / "devcovenant" / "config.yaml"
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    payload["doc_assets"] = {
        "autogen": list(autogen),
        "user": list(user),
    }
    config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _mark_config_ready(target: Path) -> None:
    """Set install.generic_config to false so deploy can run."""
    config_path = target / "devcovenant" / "config.yaml"
    text = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        text.replace("generic_config: true", "generic_config: false"),
        encoding="utf-8",
    )


def test_refresh_all_syncs_configured_autogen_docs_only(
    tmp_path: Path,
) -> None:
    """refresh-all should sync only docs selected by doc_assets.autogen."""
    target = tmp_path / "repo"
    target.mkdir()
    install.main(
        _with_skip_refresh(
            [
                "--target",
                str(target),
                "--mode",
                "empty",
                "--version",
                "0.9.0",
            ]
        )
    )
    _mark_config_ready(target)
    deploy.main(_with_skip_refresh(["--target", str(target)]))

    readme_path = target / "README.md"
    plan_path = target / "PLAN.md"
    readme_text = "# User README\n\nDo not touch.\n"
    plan_text = "# Plan\n"
    readme_path.write_text(readme_text, encoding="utf-8")
    plan_path.write_text(plan_text, encoding="utf-8")
    _set_doc_assets(target, autogen=["PLAN.md"], user=[])

    result = refresh_all(target)

    assert result == 0
    assert readme_path.read_text(encoding="utf-8") == readme_text
    updated_plan = plan_path.read_text(encoding="utf-8")
    assert install.BLOCK_BEGIN in updated_plan
    assert "**Last Updated:**" in updated_plan
