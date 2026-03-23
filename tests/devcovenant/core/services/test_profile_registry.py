"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

import yaml

MODULE = "devcovenant.core.services.profile_registry"
REPO_ROOT = Path(__file__).resolve().parents[4]


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_profile_registry_symbol_contract_is_stable() -> None:
    """Profile-registry helpers should remain importable and callable."""
    module = importlib.import_module(MODULE)
    for symbol in [
        "build_profile_registry",
        "discover_profiles",
        "list_profiles",
        "load_profile",
        "load_profile_registry",
        "parse_active_profiles",
        "refresh_profile_registry",
        "resolve_profile_clean_overlays",
        "resolve_profile_ignore_dirs",
        "resolve_profile_suffixes",
        "write_profile_registry",
    ]:
        assert hasattr(module, symbol)
        assert callable(getattr(module, symbol))


def _unit_test_profile_registry_symbol_assertions_cover_public_api() -> None:
    """Profile-registry tests should assert main public helpers directly."""
    module = importlib.import_module(MODULE)
    assert module.build_profile_registry
    assert module.discover_profiles
    assert module.list_profiles
    assert module.load_profile
    assert module.load_profile_registry
    assert module.parse_active_profiles
    assert module.refresh_profile_registry
    assert module.resolve_profile_clean_overlays
    assert module.resolve_profile_ignore_dirs
    assert module.resolve_profile_suffixes
    assert module.write_profile_registry


def _unit_test_profile_registry_resolves_clean_overlays() -> None:
    """Active profiles should expose additive cleanup overlays."""
    module = importlib.import_module(MODULE)
    registry = module.discover_profiles(REPO_ROOT)
    overlays = module.resolve_profile_clean_overlays(
        registry,
        ["global", "python", "typescript"],
    )

    assert "build" in overlays["build_dirs"]
    assert ".pytype" in overlays["cache_dirs"]
    assert ".turbo" in overlays["cache_dirs"]
    assert "*.tsbuildinfo" in overlays["cache_globs"]


def _unit_test_discover_profiles_validates_missing_asset_template() -> None:
    """Profile discovery should fail when an asset template is missing."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        builtin_root = repo_root / "devcovenant" / "builtin" / "profiles"
        custom_root = repo_root / "devcovenant" / "custom" / "profiles"
        profile_dir = builtin_root / "demo"
        (profile_dir / "assets").mkdir(parents=True, exist_ok=True)
        (profile_dir / "assets" / "README.md").write_text(
            "demo\n",
            encoding="utf-8",
        )
        manifest_path = profile_dir / "demo.yaml"
        manifest_path.write_text(
            yaml.safe_dump(
                {
                    "version": 1,
                    "profile": "demo",
                    "category": "framework",
                    "assets": [
                        {"path": "README.md", "template": "README.md"},
                        {"path": "pubspec.lock", "template": "pubspec.lock"},
                    ],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        custom_root.mkdir(parents=True, exist_ok=True)

        try:
            module.discover_profiles(
                repo_root,
                builtin_root=builtin_root,
                custom_root=custom_root,
            )
        except ValueError as error:
            message = str(error)
            assert "pubspec.lock" in message
            assert "missing template" in message
        else:
            raise AssertionError("Expected ValueError for missing template.")


def _unit_test_discover_profiles_accepts_flutter_lock_template() -> None:
    """Flutter profile should ship the declared pubspec.lock template."""
    module = importlib.import_module(MODULE)
    registry = module.discover_profiles(REPO_ROOT)
    flutter = registry.get("flutter", {})
    assert flutter
    assets_available = set(flutter.get("assets_available", []))
    assert (
        "devcovenant/builtin/profiles/flutter/assets/pubspec.lock"
        in assets_available
    )


def _workflow_step_signature(step: dict[str, object]) -> dict[str, object]:
    """Return the comparable subset of a workflow step."""
    signature: dict[str, object] = {}
    name = str(step.get("name") or "").strip()
    if name:
        signature["name"] = name
    uses = str(step.get("uses") or "").strip()
    if uses:
        signature["uses"] = uses
    run_text = str(step.get("run") or "").strip()
    if run_text:
        signature["run"] = "\n".join(
            line.rstrip() for line in run_text.splitlines()
        ).strip()
    raw_with = step.get("with")
    if isinstance(raw_with, dict):
        normalized_with = {str(key): value for key, value in raw_with.items()}
        if normalized_with:
            signature["with"] = normalized_with
    return signature


def _governance_workflow_signature(
    payload: dict[str, object],
) -> dict[str, object]:
    """Extract a minimal workflow contract signature for CI alignment."""
    jobs = payload.get("jobs")
    assert isinstance(jobs, dict)
    job = jobs.get("governance-and-test")
    assert isinstance(job, dict)
    env = job.get("env")
    assert isinstance(env, dict)
    steps = job.get("steps")
    assert isinstance(steps, list)

    interesting_names = {
        "Checkout",
        "Set up Python",
        "Install tooling and dependencies",
        "Run DevCovenant start gate",
        "Run DevCovenant tests",
        "Run DevCovenant end gate",
    }
    selected_steps: list[dict[str, object]] = []
    for raw_step in steps:
        if not isinstance(raw_step, dict):
            continue
        name = str(raw_step.get("name") or "").strip()
        if name not in interesting_names:
            continue
        selected_steps.append(_workflow_step_signature(raw_step))
    return {
        "workflow_name": str(payload.get("name") or "").strip(),
        "runs-on": str(job.get("runs-on") or "").strip(),
        "job_name": str(job.get("name") or "").strip(),
        "pycacheprefix": str(env.get("PYTHONPYCACHEPREFIX") or "").strip(),
        "steps": selected_steps,
    }


def _unit_test_governance_workflow_asset_matches_repo_contract() -> None:
    """Repo workflow should stay aligned with the global asset baseline."""
    global_manifest = REPO_ROOT / "devcovenant" / "builtin" / "profiles"
    global_manifest = global_manifest / "global" / "global.yaml"
    manifest_payload = yaml.safe_load(
        global_manifest.read_text(encoding="utf-8")
    )
    assert isinstance(manifest_payload, dict)
    template_name = str(
        manifest_payload.get("governance_template") or ""
    ).strip()
    assert template_name

    asset_workflow = global_manifest.parent / "assets" / template_name
    repo_workflow = (
        REPO_ROOT / ".github" / "workflows" / "governance-and-test.yml"
    )

    asset_payload = yaml.safe_load(asset_workflow.read_text(encoding="utf-8"))
    repo_payload = yaml.safe_load(repo_workflow.read_text(encoding="utf-8"))
    assert isinstance(asset_payload, dict)
    assert isinstance(repo_payload, dict)

    assert _governance_workflow_signature(repo_payload) == (
        _governance_workflow_signature(asset_payload)
    )


def _unit_test_global_governance_workflow_asset_stays_generic() -> None:
    """Global workflow asset should not absorb repo-specific jobs."""
    asset_workflow = (
        REPO_ROOT
        / "devcovenant"
        / "builtin"
        / "profiles"
        / "global"
        / "assets"
        / "governance-and-test.yml"
    )
    payload = yaml.safe_load(asset_workflow.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    jobs = payload.get("jobs")
    assert isinstance(jobs, dict)
    assert payload.get("name") == "CI and Tests"
    assert set(jobs) == {"governance-and-test"}
    assert "compatibility-matrix" not in jobs
    assert "assurance" not in jobs


def _unit_test_repo_workflow_includes_devcovrepo_jobs() -> None:
    """Repo workflow should include devcovrepo-provided CI jobs."""
    repo_workflow = (
        REPO_ROOT / ".github" / "workflows" / "governance-and-test.yml"
    )
    payload = yaml.safe_load(repo_workflow.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert payload.get("name") == "CI and Tests"

    jobs = payload.get("jobs")
    assert isinstance(jobs, dict)
    assert "governance-and-test" in jobs
    assert "compatibility-matrix" in jobs
    assert "assurance" in jobs

    compatibility = jobs["compatibility-matrix"]
    assert isinstance(compatibility, dict)
    steps = compatibility.get("steps")
    assert isinstance(steps, list)
    step_names = [
        str(step.get("name") or "").strip()
        for step in steps
        if isinstance(step, dict)
    ]
    assert "Prime managed environment" in step_names
    assert "Run compatibility contract tests" in step_names


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_profile_registry_symbol_contract_is_stable(self):
        """Run profile-registry helper surface assertions."""
        _unit_test_profile_registry_symbol_contract_is_stable()

    def test_profile_registry_symbol_assertions_cover_public_api(self):
        """Run explicit profile-registry symbol assertions."""
        _unit_test_profile_registry_symbol_assertions_cover_public_api()

    def test_discover_profiles_validates_missing_asset_template(self):
        """Run missing asset-template manifest validation assertions."""
        _unit_test_discover_profiles_validates_missing_asset_template()

    def test_discover_profiles_accepts_flutter_lock_template(self):
        """Run flutter pubspec.lock template integrity regression."""
        _unit_test_discover_profiles_accepts_flutter_lock_template()

    def test_profile_registry_resolves_clean_overlays(self):
        """Run cleanup overlay resolution regression coverage."""
        _unit_test_profile_registry_resolves_clean_overlays()

    def test_governance_workflow_asset_matches_repo_contract(self):
        """Run global workflow asset vs repo workflow contract assertions."""
        _unit_test_governance_workflow_asset_matches_repo_contract()

    def test_global_governance_workflow_asset_stays_generic(self):
        """Run global workflow generic-boundary assertions."""
        _unit_test_global_governance_workflow_asset_stays_generic()

    def test_repo_workflow_includes_devcovrepo_jobs(self):
        """Run repo workflow extra-job assertions."""
        _unit_test_repo_workflow_includes_devcovrepo_jobs()
