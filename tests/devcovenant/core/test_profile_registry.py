"""Tests for devcovenant.core.profile_registry."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

import yaml

MODULE = "devcovenant.core.profile_registry"
REPO_ROOT = Path(__file__).resolve().parents[3]


def _profile_registry_load_raw_workflow(path: Path) -> dict[str, object]:
    """Load one workflow with string-preserving YAML semantics."""
    payload = yaml.load(
        path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    assert isinstance(payload, dict)
    return payload


def _profile_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _profile_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _profile_profile_registry_symbol_contract_is_stable() -> None:
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


def _profile_profile_registry_symbol_assertions_cover_public_api() -> None:
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


def _profile_profile_registry_resolves_clean_overlays() -> None:
    """Active profiles should expose additive cleanup overlays."""
    module = importlib.import_module(MODULE)
    registry = module.discover_profiles(REPO_ROOT)
    overlays = module.resolve_profile_clean_overlays(
        registry, ["global", "python", "typescript"]
    )
    assert "build" in overlays["build_dirs"]
    assert ".pytype" in overlays["cache_dirs"]
    assert ".turbo" in overlays["cache_dirs"]
    assert "*.tsbuildinfo" in overlays["cache_globs"]


def _profile_discover_profiles_validates_missing_asset_template() -> None:
    """Profile discovery should fail when an asset template is missing."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        builtin_root = repo_root / "devcovenant" / "builtin" / "profiles"
        custom_root = repo_root / "devcovenant" / "custom" / "profiles"
        profile_dir = builtin_root / "demo"
        (profile_dir / "assets").mkdir(parents=True, exist_ok=True)
        (profile_dir / "assets" / "README.md").write_text(
            "demo\n", encoding="utf-8"
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
                repo_root, builtin_root=builtin_root, custom_root=custom_root
            )
        except ValueError as error:
            message = str(error)
            assert "pubspec.lock" in message
            assert "missing template" in message
        else:
            raise AssertionError("Expected ValueError for missing template.")


def _profile_discover_profiles_accepts_flutter_lock_template() -> None:
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


def _profile_discover_profiles_ignores_repo_bytecode_assets() -> None:
    """Profile discovery should ignore transient repo bytecode assets."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        builtin_root = repo_root / "devcovenant" / "builtin" / "profiles"
        custom_root = repo_root / "devcovenant" / "custom" / "profiles"
        profile_dir = builtin_root / "demo"
        assets_dir = profile_dir / "assets"
        pycache_dir = assets_dir / "__pycache__"
        pycache_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / "main.py").write_text(
            "print('demo')\n", encoding="utf-8"
        )
        (pycache_dir / "main.cpython-314.pyc").write_bytes(b"x")
        (profile_dir / "demo.yaml").write_text(
            yaml.safe_dump(
                {
                    "version": 1,
                    "profile": "demo",
                    "category": "framework",
                    "assets": [{"path": "main.py", "template": "main.py"}],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        custom_root.mkdir(parents=True, exist_ok=True)
        registry = module.discover_profiles(
            repo_root, builtin_root=builtin_root, custom_root=custom_root
        )
    demo = registry.get("demo", {})
    assets_available = set(demo.get("assets_available", []))
    assert (
        "devcovenant/builtin/profiles/demo/assets/main.py" in assets_available
    )
    assert not any(("__pycache__" in entry for entry in assets_available))
    assert not any((entry.endswith(".pyc") for entry in assets_available))


def _profile_discover_profiles_orders_profiles_deterministically() -> None:
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
        (
            module._normalize_profile_name(entry.name)
            for entry in module._iter_profile_dirs(custom_root)
        )
    )
    assert discovered_names == expected_names


def _profile_profile_registry_exports_workflow_contract() -> None:
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


def _profile_registry_workflow_step_signature(
    step: dict[str, object],
) -> dict[str, object]:
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
            (line.rstrip() for line in run_text.splitlines())
        ).strip()
    raw_with = step.get("with")
    if isinstance(raw_with, dict):
        normalized_with = {str(key): value for key, value in raw_with.items()}
        if normalized_with:
            signature["with"] = normalized_with
    return signature


def _profile_registry_governance_workflow_signature(
    payload: dict[str, object],
) -> dict[str, object]:
    """Extract a minimal workflow contract signature for CI alignment."""
    jobs = payload.get("jobs")
    assert isinstance(jobs, dict)
    job = jobs.get("governance")
    assert isinstance(job, dict)
    steps = job.get("steps")
    assert isinstance(steps, list)
    interesting_names = {
        "Checkout",
        "Set up Python",
        "Configure Python cache root",
        "Install DevCovenant runtime dependencies",
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
        selected_steps.append(
            _profile_registry_workflow_step_signature(raw_step)
        )
    return {
        "workflow_name": str(payload.get("name") or "").strip(),
        "runs-on": str(job.get("runs-on") or "").strip(),
        "job_name": str(job.get("name") or "").strip(),
        "steps": selected_steps,
    }


def _profile_governance_workflow_asset_matches_repo_contract() -> None:
    """Repo workflow should stay aligned with the github asset baseline."""
    global_manifest = REPO_ROOT / "devcovenant" / "builtin" / "profiles"
    global_manifest = global_manifest / "github" / "github.yaml"
    manifest_payload = yaml.safe_load(
        global_manifest.read_text(encoding="utf-8")
    )
    assert isinstance(manifest_payload, dict)
    template_name = str(
        manifest_payload.get("ci_and_test_template") or ""
    ).strip()
    assert template_name
    asset_workflow = global_manifest.parent / "assets" / template_name
    repo_workflow = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    asset_payload = yaml.safe_load(asset_workflow.read_text(encoding="utf-8"))
    repo_payload = yaml.safe_load(repo_workflow.read_text(encoding="utf-8"))
    assert isinstance(asset_payload, dict)
    assert isinstance(repo_payload, dict)
    assert _profile_registry_governance_workflow_signature(
        repo_payload
    ) == _profile_registry_governance_workflow_signature(asset_payload)


def _profile_global_governance_workflow_asset_stays_generic() -> None:
    """Github workflow asset should not absorb repo-specific jobs."""
    asset_workflow = (
        REPO_ROOT
        / "devcovenant"
        / "builtin"
        / "profiles"
        / "github"
        / "assets"
        / "ci.yml"
    )
    payload = yaml.safe_load(asset_workflow.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    jobs = payload.get("jobs")
    assert isinstance(jobs, dict)
    assert payload.get("name") == "CI"
    assert set(jobs) == {"governance"}
    assert "compatibility-matrix" not in jobs
    assert "assurance" not in jobs
    assert "installed-cli-smoke" not in jobs
    governance = jobs["governance"]
    assert isinstance(governance, dict)
    steps = governance.get("steps")
    assert isinstance(steps, list)
    install_step = next(
        (
            step
            for step in steps
            if isinstance(step, dict)
            and str(step.get("name") or "").strip()
            == "Install DevCovenant runtime dependencies"
        )
    )
    install_run = str(install_step.get("run") or "").strip()
    assert "devcovenant/runtime-requirements.lock" in install_run
    assert "python -m pip install --upgrade pip" not in install_run
    assert "python -m pip install -r requirements.lock" not in install_run


def _profile_global_profile_no_longer_owns_ci_template() -> None:
    """Global profile should not own the CI template after the split."""
    manifest_path = (
        REPO_ROOT
        / "devcovenant"
        / "builtin"
        / "profiles"
        / "global"
        / "global.yaml"
    )
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert "ci_and_test_template" not in payload


def _profile_repo_workflow_includes_devcovrepo_jobs() -> None:
    """Repo workflow should include devcovrepo-provided CI jobs."""
    repo_workflow = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    payload = yaml.safe_load(repo_workflow.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert payload.get("name") == "CI"
    jobs = payload.get("jobs")
    assert isinstance(jobs, dict)
    assert set(jobs) == {"governance", "build"}
    assert "compatibility-matrix" not in jobs
    assert "assurance" not in jobs
    assert "installed-cli-smoke" not in jobs
    ci_and_test = jobs["governance"]
    assert isinstance(ci_and_test, dict)
    assert ci_and_test.get("name") == "Governance"
    steps = ci_and_test.get("steps")
    assert isinstance(steps, list)
    step_names = [
        str(step.get("name") or "").strip()
        for step in steps
        if isinstance(step, dict)
    ]
    assert "Install governance tooling" in step_names
    assert "Audit locked dependencies" in step_names
    assert "Run Bandit" in step_names
    audit_step = next(
        (
            step
            for step in steps
            if isinstance(step, dict)
            and str(step.get("name") or "").strip()
            == "Audit locked dependencies"
        )
    )
    audit_run = str(audit_step.get("run") or "").strip()
    assert "--ignore-vuln CVE-2026-4539" in audit_run


def _profile_ci_workflow_contains_build_job_artifact_proof() -> None:
    """CI workflow should include the repo-specific Build artifact proof."""
    workflow = _profile_registry_load_raw_workflow(
        REPO_ROOT / ".github" / "workflows" / "ci.yml"
    )
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)
    governance_job = jobs.get("governance")
    assert isinstance(governance_job, dict)
    governance_steps = governance_job.get("steps")
    assert isinstance(governance_steps, list)
    governance_uses = [
        str(step.get("uses") or "").strip()
        for step in governance_steps
        if isinstance(step, dict)
    ]
    assert (
        "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd"
        in governance_uses
    )
    assert (
        "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405"
        in governance_uses
    )
    build_job = jobs.get("build")
    assert isinstance(build_job, dict)
    assert build_job.get("name") == "Build"
    assert build_job.get("needs") == "governance"
    steps = build_job.get("steps")
    assert isinstance(steps, list)
    build_uses = [
        str(step.get("uses") or "").strip()
        for step in steps
        if isinstance(step, dict)
    ]
    assert (
        "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd"
        in build_uses
    )
    assert (
        "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405"
        in build_uses
    )
    assert (
        "actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f"
        in build_uses
    )
    step_names = [
        str(step.get("name") or "").strip()
        for step in steps
        if isinstance(step, dict)
    ]
    assert "Generate build provenance" in step_names
    assert "Upload build provenance" in step_names
    assert "Install DevCovenant with pipx" in step_names
    assert "Resolve pipx bin directory" in step_names
    assert "Prove pipx operator lifecycle" in step_names
    assert "Set up Python support floor" in step_names
    assert "Prove Python 3.10 support floor" in step_names
    assert "Configure Python cache root" in step_names
    upload_step = next(
        (
            step
            for step in steps
            if isinstance(step, dict)
            and str(step.get("name") or "").strip()
            == "Upload build provenance"
        )
    )
    upload_with = upload_step.get("with")
    assert isinstance(upload_with, dict)
    assert upload_with.get("name") == "devcovenant-provenance"
    all_run_blocks = "\n".join(
        (
            str(step.get("run") or "").strip()
            for step in steps
            if isinstance(step, dict)
        )
    )
    assert "$RUNNER_TEMP/devcovenant-pycache" in all_run_blocks
    assert "${{ runner.temp }}" not in all_run_blocks
    assert "python -m pip install -r requirements.lock" in all_run_blocks
    assert "python -m pip install --upgrade pip" not in all_run_blocks
    assert "python -m pip install build twine pipx" not in all_run_blocks
    assert "pushd artifacts/wheel-proof >/dev/null" in all_run_blocks
    assert "pushd artifacts/sdist-proof >/dev/null" in all_run_blocks
    assert "pushd artifacts/pipx-proof >/dev/null" in all_run_blocks
    for command in (
        "python -m devcovenant gate --start",
        "python -m devcovenant gate --mid",
        "python -m devcovenant run",
        "python -m devcovenant gate --end",
    ):
        assert command in all_run_blocks
    assert "cat > tests/__init__.py <<'PY'" in all_run_blocks
    assert "cat > tests/test_smoke.py <<'PY'" in all_run_blocks
    assert "python -m devcovenant refresh" in all_run_blocks
    assert 'git commit -m "bootstrap installed repo"' in all_run_blocks
    assert 'git commit -m "bootstrap pipx repo"' in all_run_blocks
    assert (
        ".venv/bin/python -m pip install -r requirements.lock"
        in all_run_blocks
    )
    assert "WHEEL_PATH=\"$(python - <<'PY'" in all_run_blocks
    assert (
        '.venv/bin/python -m pip install --no-deps "$WHEEL_PATH"'
        in all_run_blocks
    )
    assert (
        '.venv/bin/python -m pip install --no-deps "$SDIST_PATH"'
        in all_run_blocks
    )
    assert ".venv/bin/python -m devcovenant gate --start" in all_run_blocks
    assert '"$PIPX_BIN_DIR/devcovenant" install' in all_run_blocks
    assert '"$PIPX_BIN_DIR/devcovenant" deploy' in all_run_blocks
    assert '"$PIPX_BIN_DIR/devcovenant" refresh' in all_run_blocks
    assert '"$PIPX_BIN_DIR/devcovenant" gate --start' in all_run_blocks
    assert '"$PIPX_BIN_DIR/devcovenant" gate --mid' in all_run_blocks
    assert '"$PIPX_BIN_DIR/devcovenant" run' in all_run_blocks
    assert '"$PIPX_BIN_DIR/devcovenant" gate --end' in all_run_blocks
    assert '"$PIPX_BIN_DIR/devcovenant" check' in all_run_blocks
    assert "python -m devcovenant --version" in all_run_blocks
    assert (
        "from devcovenant.builtin.policies.version_sync import ("
        in all_run_blocks
    )
    provenance_step = next(
        (
            step
            for step in steps
            if isinstance(step, dict)
            and str(step.get("name") or "").strip()
            == "Generate build provenance"
        )
    )
    provenance_env = provenance_step.get("env")
    assert isinstance(provenance_env, dict)
    assert provenance_env.get("CI_RUN_ID") == "${{ github.run_id }}"
    assert provenance_env.get("CI_RUN_ATTEMPT") == "${{ github.run_attempt }}"
    assert provenance_env.get("CI_HEAD_SHA") == "${{ github.sha }}"
    provenance_run = str(provenance_step.get("run") or "").strip()
    assert '"ci_run_id": os.environ["CI_RUN_ID"]' in provenance_run
    assert '"ci_run_attempt": os.environ["CI_RUN_ATTEMPT"]' in provenance_run
    assert '"head_sha": os.environ["CI_HEAD_SHA"]' in provenance_run
    assert '"build_run_id"' not in provenance_run


def _profile_publish_workflow_uses_validated_build_artifacts() -> None:
    """Publish workflow should download one validated CI artifact."""
    workflow = _profile_registry_load_raw_workflow(
        REPO_ROOT / ".github" / "workflows" / "publish.yml"
    )
    triggers = workflow.get("on")
    assert isinstance(triggers, dict)
    workflow_dispatch = triggers.get("workflow_dispatch")
    assert isinstance(workflow_dispatch, dict)
    inputs = workflow_dispatch.get("inputs")
    assert isinstance(inputs, dict)
    ci_run_id = inputs.get("ci_run_id")
    assert isinstance(ci_run_id, dict)
    assert ci_run_id.get("required") == "true"
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
    assert "Validate selected CI run" in step_names
    assert "Set up Python" in step_names
    assert "Configure Python cache root" in step_names
    assert "Download validated distributions" in step_names
    assert "Download build provenance" in step_names
    assert "Verify downloaded provenance" in step_names
    assert "Publish to PyPI with trusted publishing" in step_names
    all_run_blocks = "\n".join(
        (
            str(step.get("run") or "").strip()
            for step in steps
            if isinstance(step, dict)
        )
    )
    assert "$RUNNER_TEMP/devcovenant-pycache" in all_run_blocks
    assert "${{ runner.temp }}" not in all_run_blocks
    assert "python -m build" not in all_run_blocks
    dist_download = next(
        (
            step
            for step in steps
            if isinstance(step, dict)
            and str(step.get("name") or "").strip()
            == "Download validated distributions"
        )
    )
    assert (
        dist_download.get("uses")
        == "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c"
    )
    dist_with = dist_download.get("with")
    assert isinstance(dist_with, dict)
    assert dist_with.get("run-id") == "${{ steps.ci-run.outputs.run_id }}"
    assert dist_with.get("name") == "devcovenant-dist"
    provenance_download = next(
        (
            step
            for step in steps
            if isinstance(step, dict)
            and str(step.get("name") or "").strip()
            == "Download build provenance"
        )
    )
    assert (
        provenance_download.get("uses")
        == "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c"
    )
    provenance_with = provenance_download.get("with")
    assert isinstance(provenance_with, dict)
    assert (
        provenance_with.get("run-id") == "${{ steps.ci-run.outputs.run_id }}"
    )
    assert provenance_with.get("name") == "devcovenant-provenance"
    assert 'payload.get("ci_run_id")' in all_run_blocks
    assert 'payload.get("ci_run_attempt")' in all_run_blocks
    assert "EXPECTED_CI_RUN_ID" in all_run_blocks
    assert "EXPECTED_CI_RUN_ATTEMPT" in all_run_blocks
    assert "build_run_id" not in all_run_blocks
    validate_step = next(
        (
            step
            for step in steps
            if isinstance(step, dict)
            and str(step.get("name") or "").strip()
            == "Validate selected CI run"
        )
    )
    assert (
        validate_step.get("uses")
        == "actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd"
    )
    setup_python_step = next(
        (
            step
            for step in steps
            if isinstance(step, dict)
            and str(step.get("name") or "").strip() == "Set up Python"
        )
    )
    assert (
        setup_python_step.get("uses")
        == "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405"
    )
    setup_python_with = setup_python_step.get("with")
    assert isinstance(setup_python_with, dict)
    assert setup_python_with.get("python-version") == "3.11"
    publish_step = next(
        (
            step
            for step in steps
            if isinstance(step, dict)
            and str(step.get("name") or "").strip()
            == "Publish to PyPI with trusted publishing"
        )
    )
    assert publish_step.get("uses") == (
        "pypa/gh-action-pypi-publish@"
        "ed0c53931b1dc9bd32cbe73a98c7f6766f8a527e"
    )


def _profile_python_family_profiles_do_not_double_run_pytest() -> None:
    """Python-family tests runs should not launch pytest beside unittest."""
    profile_root = REPO_ROOT / "devcovenant" / "builtin" / "profiles"
    manifest_paths = [
        profile_root / "python" / "python.yaml",
        profile_root / "fastapi" / "fastapi.yaml",
        profile_root / "frappe" / "frappe.yaml",
    ]
    for manifest_path in manifest_paths:
        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        workflow_runs = payload.get("workflow_runs")
        assert isinstance(workflow_runs, list)
        tests_run = next(
            (
                run
                for run in workflow_runs
                if isinstance(run, dict)
                and str(run.get("id") or "") == "tests"
            )
        )
        runner = tests_run.get("runner")
        assert isinstance(runner, dict)
        commands = runner.get("commands")
        assert isinstance(commands, list)
        command_text = [str(command).strip() for command in commands]
        assert "python3 -m unittest discover -v" in command_text
        assert "pytest" not in command_text


def _profile_devcovrepo_managed_env_requires_runtime_tools() -> None:
    """Repo managed-env contract should require gate/runtime tools."""
    manifest_path = (
        REPO_ROOT
        / "devcovenant"
        / "custom"
        / "profiles"
        / "devcovrepo"
        / "devcovrepo.yaml"
    )
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    policy_overlays = payload.get("policy_overlays")
    assert isinstance(policy_overlays, dict)
    managed_environment = policy_overlays.get("managed-environment")
    assert isinstance(managed_environment, dict)
    required_commands = managed_environment.get("required_commands")
    assert isinstance(required_commands, list)
    command_text = [str(command).strip() for command in required_commands]
    assert command_text == ["pre-commit", "pytest"]


def _profile_devcovuser_tests_scope_matches_normal_repo_contract() -> None:
    """Normal user profile should keep only custom modules in scope."""
    module = importlib.import_module(MODULE)
    registry = module.discover_profiles(REPO_ROOT)
    devcovuser = registry.get("devcovuser", {})
    assert isinstance(devcovuser, dict)
    policy_overlays = devcovuser.get("policy_overlays")
    assert isinstance(policy_overlays, dict)

    modules_policy = policy_overlays.get("modules-need-tests")
    assert isinstance(modules_policy, dict)
    assert modules_policy.get("exclude_prefixes") == [
        "build",
        "dist",
        "node_modules",
        "tests",
        "devcovenant",
    ]
    assert modules_policy.get("force_include_globs") == [
        "devcovenant/custom/**/*.py"
    ]
    assert modules_policy.get("mirror_roots") == [
        "devcovenant/custom=>tests/devcovenant/custom"
    ]

    coverage_policy = policy_overlays.get("tests-coverage")
    assert isinstance(coverage_policy, dict)
    assert coverage_policy.get("exclude_prefixes") == [
        "build",
        "dist",
        "node_modules",
        "tests",
        "devcovenant",
    ]
    assert coverage_policy.get("force_include_globs") == [
        "devcovenant/custom/**/*.py"
    ]


class ProfileRegistryTests(unittest.TestCase):
    """unittest wrappers for layered module sanity checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _profile_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _profile_module_has_public_symbols()

    def test_profile_registry_symbol_contract_is_stable(self):
        """Run profile-registry helper surface assertions."""
        _profile_profile_registry_symbol_contract_is_stable()

    def test_profile_registry_symbol_assertions_cover_public_api(self):
        """Run explicit profile-registry symbol assertions."""
        _profile_profile_registry_symbol_assertions_cover_public_api()

    def test_discover_profiles_validates_missing_asset_template(self):
        """Run missing asset-template manifest validation assertions."""
        _profile_discover_profiles_validates_missing_asset_template()

    def test_discover_profiles_accepts_flutter_lock_template(self):
        """Run flutter pubspec.lock template integrity regression."""
        _profile_discover_profiles_accepts_flutter_lock_template()

    def test_discover_profiles_ignores_repo_bytecode_assets(self):
        """Run profile-asset bytecode exclusion assertions."""
        _profile_discover_profiles_ignores_repo_bytecode_assets()

    def test_discover_profiles_orders_profiles_deterministically(self):
        """Run deterministic profile-discovery ordering assertions."""
        _profile_discover_profiles_orders_profiles_deterministically()

    def test_profile_registry_resolves_clean_overlays(self):
        """Run cleanup overlay resolution regression coverage."""
        _profile_profile_registry_resolves_clean_overlays()

    def test_governance_workflow_asset_matches_repo_contract(self):
        """Run github workflow asset vs repo workflow contract assertions."""
        _profile_governance_workflow_asset_matches_repo_contract()

    def test_global_governance_workflow_asset_stays_generic(self):
        """Run github workflow generic-boundary assertions."""
        _profile_global_governance_workflow_asset_stays_generic()

    def test_global_profile_no_longer_owns_ci_template(self):
        """Run global-profile CI ownership split assertions."""
        _profile_global_profile_no_longer_owns_ci_template()

    def test_repo_workflow_includes_devcovrepo_jobs(self):
        """Run repo workflow extra-job assertions."""
        _profile_repo_workflow_includes_devcovrepo_jobs()

    def test_ci_workflow_contains_build_job_artifact_proof(self):
        """Run CI build-job provenance artifact assertions."""
        _profile_ci_workflow_contains_build_job_artifact_proof()

    def test_publish_workflow_uses_validated_build_artifacts(self):
        """Run publish-workflow artifact provenance assertions."""
        _profile_publish_workflow_uses_validated_build_artifacts()

    def test_python_family_profiles_do_not_double_run_pytest(self):
        """Run Python-family workflow command assertions."""
        _profile_python_family_profiles_do_not_double_run_pytest()

    def test_devcovrepo_managed_env_requires_runtime_tools(self):
        """Run repo managed-env runtime-tool assertions."""
        _profile_devcovrepo_managed_env_requires_runtime_tools()

    def test_devcovuser_tests_scope_matches_normal_repo_contract(self):
        """Run normal user profile test-scope assertions."""
        _profile_devcovuser_tests_scope_matches_normal_repo_contract()
