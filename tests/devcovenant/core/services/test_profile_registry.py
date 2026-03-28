"""Mirrored surface sanity checks."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

import yaml

MODULE = "devcovenant.core.services.profile_registry"
REPO_ROOT = Path(__file__).resolve().parents[4]


def _load_raw_workflow(path: Path) -> dict[str, object]:
    """Load one workflow with string-preserving YAML semantics."""
    payload = yaml.load(
        path.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    assert isinstance(payload, dict)
    return payload


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


def _unit_test_discover_profiles_orders_profiles_deterministically() -> None:
    """Profile discovery order should not depend on filesystem iteration."""
    module = importlib.import_module(MODULE)
    registry = module.discover_profiles(REPO_ROOT)
    discovered_names = list(registry.keys())
    builtin_root = REPO_ROOT / "devcovenant" / "builtin" / "profiles"
    custom_root = REPO_ROOT / "devcovenant" / "custom" / "profiles"
    expected_names = [
        module._normalize_profile_name(entry.name)
        for entry in module._iter_profile_dirs(builtin_root)
    ]
    expected_names.extend(
        module._normalize_profile_name(entry.name)
        for entry in module._iter_profile_dirs(custom_root)
    )
    assert discovered_names == expected_names


def _unit_test_profile_registry_exports_workflow_contract() -> None:
    """Tracked profile registry should expose the workflow contract."""
    module = importlib.import_module(MODULE)
    payload = module.build_profile_registry(REPO_ROOT)
    contract = payload.get("workflow_contract")
    assert isinstance(contract, dict)
    run_ids = contract.get("run_ids")
    assert isinstance(run_ids, list)
    assert "tests" in run_ids
    runs = contract.get("runs")
    assert isinstance(runs, list)
    tests_run = next(
        (
            run
            for run in runs
            if isinstance(run, dict) and run.get("id") == "tests"
        ),
        None,
    )
    assert isinstance(tests_run, dict)
    runner = tests_run.get("runner")
    assert isinstance(runner, dict)
    assert runner.get("kind") == "command_group"


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
    job = jobs.get("ci-and-test")
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
        "Run DevCovenant mid gate",
        "Run DevCovenant workflow runs",
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
        manifest_payload.get("ci_and_test_template") or ""
    ).strip()
    assert template_name

    asset_workflow = global_manifest.parent / "assets" / template_name
    repo_workflow = REPO_ROOT / ".github" / "workflows" / "ci-and-test.yml"

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
        / "ci-and-test.yml"
    )
    payload = yaml.safe_load(asset_workflow.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    jobs = payload.get("jobs")
    assert isinstance(jobs, dict)
    assert payload.get("name") == "CI"
    assert set(jobs) == {"ci-and-test"}
    assert "compatibility-matrix" not in jobs
    assert "assurance" not in jobs
    assert "installed-cli-smoke" not in jobs


def _unit_test_repo_workflow_includes_devcovrepo_jobs() -> None:
    """Repo workflow should include devcovrepo-provided CI jobs."""
    repo_workflow = REPO_ROOT / ".github" / "workflows" / "ci-and-test.yml"
    payload = yaml.safe_load(repo_workflow.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert payload.get("name") == "CI"

    jobs = payload.get("jobs")
    assert isinstance(jobs, dict)
    assert set(jobs) == {"ci-and-test", "build-and-install-test"}
    assert "compatibility-matrix" not in jobs
    assert "assurance" not in jobs
    assert "installed-cli-smoke" not in jobs

    ci_and_test = jobs["ci-and-test"]
    assert isinstance(ci_and_test, dict)
    assert ci_and_test.get("name") == "DevCovenant"
    steps = ci_and_test.get("steps")
    assert isinstance(steps, list)
    step_names = [
        str(step.get("name") or "").strip()
        for step in steps
        if isinstance(step, dict)
    ]
    assert "Install scanner dependencies" in step_names
    assert "Audit locked dependencies" in step_names
    assert "Run Bandit" in step_names
    audit_step = next(
        step
        for step in steps
        if isinstance(step, dict)
        and str(step.get("name") or "").strip() == "Audit locked dependencies"
    )
    audit_run = str(audit_step.get("run") or "").strip()
    assert "--ignore-vuln CVE-2026-4539" in audit_run

    build_and_install = jobs["build-and-install-test"]
    assert isinstance(build_and_install, dict)
    assert build_and_install.get("name") == "Build and Install"
    assert build_and_install.get("needs") == "ci-and-test"
    installed_steps = build_and_install.get("steps")
    assert isinstance(installed_steps, list)
    installed_step_names = [
        str(step.get("name") or "").strip()
        for step in installed_steps
        if isinstance(step, dict)
    ]
    assert "Build package artifacts" in installed_step_names
    assert "Validate built artifacts" in installed_step_names
    assert "Prove wheel artifact lifecycle" in installed_step_names
    assert "Prove sdist artifact lifecycle" in installed_step_names
    assert "Install DevCovenant with pipx" in installed_step_names
    assert "Resolve pipx bin directory" in installed_step_names
    assert "Prove pipx operator lifecycle" in installed_step_names

    lifecycle_run_blocks = "\n".join(
        str(step.get("run") or "").strip()
        for step in installed_steps
        if isinstance(step, dict)
        and str(step.get("name") or "").strip()
        in {
            "Prove wheel artifact lifecycle",
            "Prove sdist artifact lifecycle",
            "Prove pipx operator lifecycle",
        }
    )
    assert 'pushd "$TMPDIR/repo" >/dev/null' in lifecycle_run_blocks
    assert "popd >/dev/null" in lifecycle_run_blocks
    assert '(\n          cd "$TMPDIR/repo"' not in lifecycle_run_blocks


def _unit_test_build_workflow_uploads_provenance_artifact() -> None:
    """Build workflow should emit provenance beside validated dists."""
    workflow = _load_raw_workflow(
        REPO_ROOT / ".github" / "workflows" / "build.yml"
    )
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)
    build_job = jobs.get("build-distributions")
    assert isinstance(build_job, dict)
    steps = build_job.get("steps")
    assert isinstance(steps, list)

    step_names = [
        str(step.get("name") or "").strip()
        for step in steps
        if isinstance(step, dict)
    ]
    assert "Generate build provenance" in step_names
    assert "Upload build provenance" in step_names

    upload_step = next(
        step
        for step in steps
        if isinstance(step, dict)
        and str(step.get("name") or "").strip() == "Upload build provenance"
    )
    upload_with = upload_step.get("with")
    assert isinstance(upload_with, dict)
    assert upload_with.get("name") == "devcovenant-provenance"

    all_run_blocks = "\n".join(
        str(step.get("run") or "").strip()
        for step in steps
        if isinstance(step, dict)
    )
    assert "pushd artifacts/wheel-proof >/dev/null" in all_run_blocks
    assert "pushd artifacts/sdist-proof >/dev/null" in all_run_blocks


def _unit_test_publish_workflow_uses_validated_build_artifacts() -> None:
    """Publish workflow should download one validated Build artifact."""
    workflow = _load_raw_workflow(
        REPO_ROOT / ".github" / "workflows" / "publish.yml"
    )
    triggers = workflow.get("on")
    assert isinstance(triggers, dict)
    workflow_dispatch = triggers.get("workflow_dispatch")
    assert isinstance(workflow_dispatch, dict)
    inputs = workflow_dispatch.get("inputs")
    assert isinstance(inputs, dict)
    build_run_id = inputs.get("build_run_id")
    assert isinstance(build_run_id, dict)
    assert build_run_id.get("required") == "true"

    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)
    assert set(jobs) == {"publish"}
    publish_job = jobs.get("publish")
    assert isinstance(publish_job, dict)

    permissions = publish_job.get("permissions")
    assert isinstance(permissions, dict)
    assert permissions.get("actions") == "read"
    assert permissions.get("id-token") == "write"

    steps = publish_job.get("steps")
    assert isinstance(steps, list)
    step_names = [
        str(step.get("name") or "").strip()
        for step in steps
        if isinstance(step, dict)
    ]
    assert "Validate selected Build run" in step_names
    assert "Download validated distributions" in step_names
    assert "Download build provenance" in step_names
    assert "Verify downloaded provenance" in step_names
    assert "Publish to PyPI with trusted publishing" in step_names

    all_run_blocks = "\n".join(
        str(step.get("run") or "").strip()
        for step in steps
        if isinstance(step, dict)
    )
    assert "python -m build" not in all_run_blocks

    dist_download = next(
        step
        for step in steps
        if isinstance(step, dict)
        and str(step.get("name") or "").strip()
        == "Download validated distributions"
    )
    dist_with = dist_download.get("with")
    assert isinstance(dist_with, dict)
    assert dist_with.get("run-id") == "${{ steps.build-run.outputs.run_id }}"
    assert dist_with.get("name") == "devcovenant-dist"

    provenance_download = next(
        step
        for step in steps
        if isinstance(step, dict)
        and str(step.get("name") or "").strip() == "Download build provenance"
    )
    provenance_with = provenance_download.get("with")
    assert isinstance(provenance_with, dict)
    assert provenance_with.get("run-id") == (
        "${{ steps.build-run.outputs.run_id }}"
    )
    assert provenance_with.get("name") == "devcovenant-provenance"


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

    def test_discover_profiles_orders_profiles_deterministically(self):
        """Run deterministic profile-discovery ordering assertions."""
        _unit_test_discover_profiles_orders_profiles_deterministically()

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

    def test_build_workflow_uploads_provenance_artifact(self):
        """Run build-workflow provenance artifact assertions."""
        _unit_test_build_workflow_uploads_provenance_artifact()

    def test_publish_workflow_uses_validated_build_artifacts(self):
        """Run publish-workflow artifact provenance assertions."""
        _unit_test_publish_workflow_uses_validated_build_artifacts()
