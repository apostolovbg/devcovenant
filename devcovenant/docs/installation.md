# Installation and Lifecycle
**Last Updated:** 2026-03-15
**Project Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Lifecycle Model](#lifecycle-model)
- [Commands](#commands)
- [Workflow](#workflow)
- [First-Time Setup Runbook](#first-time-setup-runbook)
- [Common Lifecycle Scenarios](#common-lifecycle-scenarios)
- [Upgrade and Lock Maintenance](#upgrade-and-lock-maintenance)
- [Package Legal Compliance](#package-legal-compliance)
- [Teardown Commands](#teardown-commands)

## Overview
DevCovenant separates installation from activation on purpose.

`install` copies runtime files and writes a generic config stub.
`deploy` is the activation step and requires explicit operator review of
`devcovenant/config.yaml` before managed artifacts are generated.

That split prevents accidental policy activation with unreviewed defaults.

## Prerequisites
Before lifecycle commands:
- run inside a git repository
- ensure Python and toolchain dependencies used by your profile command chain
  are available
- ensure `devcovenant/config.yaml` is present after `install`
- ensure humans review user-owned config values before first `deploy`

If `devcovenant` is not on PATH, use `python3 -m devcovenant ...`.
On Windows, `py -m devcovenant ...` is a common equivalent launcher form.

## Lifecycle Model
Command contract:
- `install`:
  copy `devcovenant/`, seed generic config, and seed tracked registry
  structure without copying source runtime logs or runtime registry files
- `deploy`:
  require `install.generic_config: false`, then run full refresh
- `clean`:
  remove disposable build/package/cache/runtime-registry/log artifacts from
  resolved profile/config cleanup targets while preserving protected tracked
  files
- `refresh`:
  regenerate the tracked registry, managed blocks, and generated governance
  files; recreate `devcovenant/registry/registry.yaml` when missing without
  fabricating runtime session state
- `upgrade`:
  reconcile core from source on every run, preserve runtime-local
  `devcovenant/registry/runtime/` and `devcovenant/logs/`, then refresh
- `undeploy`:
  remove managed artifacts while preserving core/config
- `uninstall`:
  remove the DevCovenant package footprint

Additional invariants:
- `install` does not deploy managed docs/assets/registries
- `install` is not a preservation path; if DevCovenant already exists it
  exits and points to `upgrade` instead of merging repo-local state
- if DevCovenant already exists, `install` exits and points to `upgrade`
- `upgrade` compares semantic versions with prerelease ordering (and accepts
  normalized `v`-prefixed version strings such as `v1.2`)
- `deploy` validates config shape before activation
- when `devcov_core_include: false`, deploy cleanup removes
  `devcovenant/custom/policies/**`,
  `tests/devcovenant/core/**`, and
  `devcovenant/custom/profiles/**`

## Commands
```bash
devcovenant install
devcovenant deploy
devcovenant clean --all
devcovenant clean --registry
devcovenant clean --logs
devcovenant refresh
devcovenant upgrade
devcovenant undeploy
devcovenant uninstall
devcovenant update_lock
```

Lifecycle plus governance commands are normally paired with:

```bash
devcovenant gate --start
devcovenant gate --mid   # required pre-test mid-session mutating preflight
devcovenant test
devcovenant gate --end
```

## Workflow
Recommended operating sequence:
1. Install (`install`) once.
2. Review config (`devcovenant/config.yaml`).
3. Activate (`deploy`).
4. Do work under start -> mid preflight loop -> test -> end gates.
5. Use `refresh`/`upgrade` when contracts or core content change.
6. Use `clean` when local build/cache residue needs pruning after those runs.

Runtime details that affect operations:
- `devcovenant test` executes
  `devflow-run-gates.required_commands` in metadata order
- `engine.tests_output_mode: normal` consumes verbose command output into
  full run-log artifacts while keeping status output concise and suppressing
  flood-prone test child output with sparse deterministic
  `[n/total] <command>` markers
- `engine.tests_output_mode: verbose` keeps detailed command output visible,
  and both modes now preserve full command output in per-run log artifacts
- `engine.tests_output_mode: quiet` suppresses routine stdout chatter and
  child output while preserving stderr failure surfaces and full run logs
- root CLI commands emit a standard `Run logs:` pointer
  (`devcovenant/logs/...`) on success and failure so troubleshooting can
  start from `summary.txt`/`summary.json`; `uninstall` is the one exception
  because it removes `devcovenant/` itself
- `devcovenant test` in `engine.tests_output_mode: normal` also emits the
  same `Run logs:` pointer when command execution starts so operators can
  inspect logs immediately without waiting for command completion
- `devcovenant clean` resolves active-profile `clean_overlays` plus repo
  `clean.overlays`/`clean.overrides`, requires an explicit `--all`,
  `--build`, `--cache`, `--registry`, or `--logs` scope, records cleanup
  details in `summary.txt`/`summary.json`, and keeps tracked files such as
  `.git`, `.venv`, `devcovenant/registry/registry.yaml`,
  `devcovenant/registry/README.md`, and `devcovenant/logs/README.md`
- repository pytest execution is configured in `pyproject.toml` with
  `--import-mode=importlib` and `pythonpath = ["."]` so mirrored builtin/core
  test names do not collide during collection
- `pyproject.toml` no longer depends on `tqdm`; normal-mode liveness uses
  runtime messages and run-log artifacts instead of progress-bar UI helpers
- `gate --start` is blocking and records no baseline when hooks fail
- `gate --mid` is a required non-lifecycle pre-commit sweep that may apply
  hook/DevCovenant mutations but does not write gate lifecycle fields
- `gate --status` is a short read-only inspection command for session state
  and latest relevant run-log pointers
- `devcovenant check` is a read-only audit command; gate pre-commit phases
  own refresh/autofix orchestration for the shared checking routine
- hidden `check` retired flags are gone; audit behavior is controlled
  only by the command contract itself and gate-owned environment toggles
- `devcovenant check --help` and `devcovenant gate --help` are aligned with
  the same command contract (`check` audit-only, gate session lifecycle
  ownership, required non-lifecycle `gate --mid`, and short read-only
  `gate --status`)
- gate-managed autofix behavior is controlled by
  `engine.auto_fix_enabled: true|false` in `devcovenant/config.yaml`
- when `managed-environment` is active, CLI commands invoked from a
  non-managed interpreter re-exec automatically in the managed interpreter
  before command logic continues, except lifecycle bootstrap/teardown commands
  (`install`, `deploy`, `undeploy`, `uninstall`)
- if the resolved managed interpreter path is not executable, CLI emits an
  explicit managed-environment failure and stops so the interpreter path or
  permissions can be fixed directly
- command-run evidence (`devcovenant/logs/<run-id>/run.json`) records
  interpreter provenance fields (`invoked_python`, `effective_python`,
  `managed_environment_active`, `managed_reexec_applied`) so you can verify
  whether managed re-exec took effect
- unhandled CLI runtime exceptions are normalized into explicit typed errors
  (`devcovenant/core/runtime/errors.py`,
  `devcovenant/core/contracts/errors.py`) instead of leaking raw traceback
  output to console; traceback details remain in run logs
- the CLI top-level normalization boundary uses an explicit
  `DEVCOV_ALLOW_BROAD_ONCE` marker so `no-raw-errors` can enforce broad
  handler discipline without hiding boundary intent
- run-log retention is configured in `devcovenant/config.yaml` via
  `engine.logs_keep_last` (`0` keeps all run folders; positive values keep
  the latest N folders)
- managed-environment bootstrap/stage commands honor runtime output mode:
  normal mode suppresses managed bootstrap bursts, quiet mode keeps routine
  stdout hidden, and verbose mode keeps full child streams visible
- managed command stages support `start|test|end|command|all`; non-start
  invocations can reuse `start=>...` bootstrap commands once when the
  interpreter does not exist yet
- repositories can treat `devcovenant/**/__pycache__/` and `*.py[cod]` as
  guardrail violations and set `engine.pycache_prefix_enabled: true` so
  DevCovenant-managed child Python commands route bytecode caches via
  `PYTHONPYCACHEPREFIX`
- boundary truth for source-checkout alternate launcher runs
  (`python3 -m devcovenant ...`): Python may still write bytecode for
  `devcovenant/__init__.py` or the first launcher module before DevCovenant
  runtime code gains control; this launcher form is supported, but its
  pre-import bytecode boundary still belongs to shell or CI environment
  setup
- if you need zero repo-local launcher-process bytecode drift while
  preserving bytecode generation, set `PYTHONPYCACHEPREFIX` in the shell/CI
  environment before Python starts; example shell helper:
  ```bash
  devcov-local() {
    PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/devcovenant-pycache" \
      python3 -m devcovenant "$@"
  }
  ```

## First-Time Setup Runbook
1. Run:
   ```bash
   devcovenant install
   ```
2. Open `devcovenant/config.yaml` and review:
   - `profiles.active`
   - `policy_state`
   - `engine.fail_threshold`
   - `engine.output_mode`
   - `engine.tests_output_mode`
3. Set:
   ```yaml
   install:
     generic_config: false
   ```
4. Activate:
   ```bash
   devcovenant deploy
   ```
5. Validate baseline workflow:
   ```bash
   devcovenant gate --start
   # pre-test mutating preflight; rerun until clean
   devcovenant gate --mid
   devcovenant test
   devcovenant gate --end
   ```

If `deploy` fails, fix config shape errors first. Deploy should not be forced
through malformed config.

## Common Lifecycle Scenarios
Scenario: update policy descriptors or profile manifests
1. edit descriptors/profiles
2. run `devcovenant refresh`
3. run `devcovenant test`
4. run `devcovenant gate --end`

Scenario: move from generic install to active governance
1. set `install.generic_config: false`
2. confirm profile stack and policy activation booleans
3. run `devcovenant deploy`
4. run full gate sequence (`gate --mid` before `test`)

Scenario: operator wants concise command output
1. set:
   ```yaml
   engine:
      output_mode: normal
      tests_output_mode: normal
   ```
2. run `devcovenant test` and confirm sparse normal-mode output plus the
   printed run-log pointer

Scenario: repository should stop including DevCovenant-core internals
1. set:
   ```yaml
   devcov_core_include: false
   ```
2. run `devcovenant deploy`
3. review cleanup output and rerun tests/gates

## Upgrade and Lock Maintenance
Use `upgrade` when core files should be reconciled from the installed CLI
package source.
Use `refresh` when generated runtime state must be rebuilt.

Upgrade replacement preserves repo-local runtime state under:
- `devcovenant/registry/runtime/`
- `devcovenant/logs/`
- `devcovenant/config.yaml`

Upgrade also preserves user payload directories under:
- `devcovenant/custom/policies/<policy-id>/`
- `devcovenant/custom/profiles/<profile-id>/`

Upgrade prunes known repository-only custom payload paths leaked by older
installs before refresh:
- `devcovenant/custom/policies/devcov_raw_string_escapes`
- `devcovenant/custom/policies/managed_doc_assets`
- `devcovenant/custom/policies/readme_sync`
- `devcovenant/custom/profiles/<repo-only-profile-id>`

Package distribution excludes repository-owned custom payloads by design;
user repository custom payloads remain preserved by upgrade replacement.

If a custom policy script is present but its descriptor file is missing or
invalid, refresh/upgrade behavior is explicit:
- fail the command with the same descriptor error contract as core policies
- require descriptor fix before rerunning refresh/upgrade
Upgrade reconciles the full `devcovenant/` package from source on every run
(including `devcovenant/*.py`, `core/`, and `builtin/`) regardless of version
direction, so stale or missing shipped files are always restored.
When `devcovenant` is run inside a repo that already contains
`devcovenant/`, upgrade resolves source from the installed package
distribution to avoid local-import shadowing.

Install remains a cold bootstrap command and does not provide preservation or
merge behavior for existing `devcovenant/` trees.

Use `update_lock` when dependency/lock metadata changed and license artifacts
must be synchronized:
- lock handlers are selected from resolved metadata
- lock orchestration runs through dependency-license-sync policy runtime
  action dispatch (`PolicyCheck.run_runtime_action(...)`)
- license artifacts are refreshed through configured targets
- metadata paths must stay repo-relative

Refresh regenerates:
- local policy/profile registries and manifest
- AGENTS managed policy block
- generated config sections
- generated `.pre-commit-config.yaml`
- generated `.gitignore`
- tracked `devcovenant/logs/README.md` remains visible while generated
  `.gitignore` ignores runtime artifacts under `devcovenant/logs/*`
- generated `.github/workflows/governance-and-test.yml`
- managed docs/managed blocks

DevCovenant-repo workflow ownership note:
- this repository also tracks the global workflow asset source at
  `devcovenant/builtin/profiles/global/assets/governance-and-test.yml`
- tracked `.github/workflows/governance-and-test.yml` is refresh-generated
  output from that source; update profile/config inputs, then refresh
- profile-registry integrity checks validate the referenced
  `governance_template` file exists under the profile asset root
- repository tests compare the tracked
  `.github/workflows/governance-and-test.yml`
  against the global asset on critical CI contract fields (job env and
  DevCovenant gate/test command sequence) to catch drift early
- `.github/workflows/build.yml` and `.github/workflows/publish.yml` are
  repository-maintained workflows and are intentionally not regenerated by
  refresh

## Package Legal Compliance
DevCovenant distribution contracts follow PEP 639-compatible metadata:
- `pyproject.toml` declares SPDX `license = "MIT"`
- `pyproject.toml` declares `license-files`:
  - `LICENSE`
  - `licenses/THIRD_PARTY_LICENSES.md`
  - `licenses/*.txt`
- `pyproject.toml` constrains package discovery to `devcovenant` package roots
  and excludes package bytecode/cache payloads plus retired tree names from
  wheel discovery so stale local build artifacts cannot leak
- `MANIFEST.in` includes license-source artifacts for sdist inputs
- `MANIFEST.in` excludes retired tree names so stale build artifacts
  cannot leak into sdists
- `MANIFEST.in` excludes runtime log payloads under `devcovenant/logs/*`
  while re-including `devcovenant/logs/README.md`
- `MANIFEST.in` excludes tracked/runtime registry payload generation outputs
  (`devcovenant/registry/registry.yaml`,
  `devcovenant/registry/runtime/*`) while keeping
  `devcovenant/registry/README.md`
- `MANIFEST.in` prunes `build/`, `dist/`, `*.egg-info`, and cache artifacts

Build-time checks in `tests/devcovenant/test_install.py` validate:
- SPDX and `license-files` metadata
- manifest license inclusion
- wheel legal artifacts under `*.dist-info/licenses/`
- wheel exclusions for `__pycache__/`, `*.py[cod]`, and retired tree names
- wheel exclusions for runtime logs under `devcovenant/logs/` while keeping
  the tracked `devcovenant/logs/README.md` skeleton
- wheel exclusions for tracked/runtime registry payloads while keeping
  `devcovenant/registry/README.md`
- dirty-build validation where stale `build/lib/*` artifacts must not leak

CI artifact-installability checks validate:
- `.github/workflows/build.yml` smoke-installs wheel and sdist artifacts in
  isolated virtual environments and runs `python -m devcovenant --help`
- `.github/workflows/build.yml` clears `build/`, `dist/`, `*.egg-info`,
  `.pytest_cache/`, and `.ruff_cache/` before `python -m build`
- `.github/workflows/publish.yml` mirrors the same smoke-install contract in
  its build job before upload/publish steps
- `.github/workflows/publish.yml` runs the same pre-build cleanup contract

This package contract is separate from repository-change policy
`dependency-license-sync`.

## Teardown Commands
Teardown contract:
- `undeploy`:
  remove managed runtime outputs and keep core/config
- `uninstall`:
  remove DevCovenant package footprint

Both commands include recovery behavior for malformed config so teardown can
continue when parse errors exist.

Use `undeploy` when reconfiguring.
Use `uninstall` when removing DevCovenant entirely.
