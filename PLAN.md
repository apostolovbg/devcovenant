# DevCovenant Development Plan
**Last Updated:** 2026-01-27
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** PLAN
**Doc Type:** plan
**Managed By:** DevCovenant
<!-- DEVCOV:END -->

The goal of this plan is to walk through the remaining work required to fully
satisfy the specification in `SPEC.md`. Each phase, trace, and validation step
below directly references one or more SPEC requirements so nothing is left
implicit. The plan also captures the new rule that the policy tests mirror the
`devcovenant/` layout without introducing an extra `tests/devcovenant/`
subtree; this keeps the repo tests manageable while adhering to the spec.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Phase roadmap](#phase-roadmap)
4. [Specification trace](#specification-trace)
5. [Testing and validation](#testing-and-validation)
6. [Release readiness](#release-readiness)

## Overview
- Treat `SPEC.md` as the source of truth and align every phase with the
  documented functional, policy, and installation requirements.
- Mirror the `devcovenant/` structure under `tests/` (no nested
  `tests/devcovenant/`) so policy/engine tests stay outside the installable
  package while still matching the package layout (per SPEC).
- Drive configuration, registries, and managed docs from profile metadata so
  the system auto-updates policy overlays, suffix lists, version knobs, and
  asset catalogs as profiles change.
- Reiterate that install/update obey the self-install/self-refresh workflow:
  when the CLI runs from the source tree, it refreshes that repo in place,
  and when started from a packaged `devcovenant` on `PATH` it updates the
  working repository (including the post-`--no-touch` scenario where the
  repo merely has the `devcovenant/` folder); configs/docs/metadata alone
  are touched rather than overwriting the existing `devcovenant/` folder.
- Mark completed items explicitly by appending “[done]” so the plan remains
  auditable and we do not redo finished work.
- Documentation style: default to `devcovenant ...` examples, and mention the
  `python3 -m devcovenant ...` fallback once per doc to avoid repetition. [done]
- Documentation style: use `python3` (not `python`) everywhere, especially
  for source-based workflows. [done]

## Spec compliance checklist
- Configuration: generate a complete `devcovenant/config.yaml` that lists
  every supported knob (even if blank), includes `profiles.generated` data,
  splits policy overrides into `autogen_metadata_overrides` (generated from
  active profiles) and `user_metadata_overrides` (user-edited), and
  propagates `version.override` into templated assets before VERSION exists.
- Profiles: rebuild `devcovenant/registry/local/profile_catalog.yaml` from
  core/custom manifests, mark active profiles, and ensure assets are listed
  per profile.
- Policy metadata: normalize all selector keys, expose missing keys in
  AGENTS policy blocks without changing values, and enforce the policy block
  as a managed unit separate from other doc blocks.
- Policy ordering: keep AGENTS policy entries alphabetized with no
  enabled/disabled grouping, list all available policies derived from the
  active profiles/config, and ensure custom overrides are listed with
  `custom: true`.
- Documentation generation: treat YAML assets as the full source for managed
  documents (including policy block scaffolding). Inject outside-of-block
  stock text only when the target doc is missing, empty, or a single-line
  placeholder; otherwise refresh managed blocks only, with the policy block
  handled via `<!-- DEVCOV-POLICIES:BEGIN -->` / `<!-- DEVCOV-POLICIES:END -->`. Ensure
  `AGENTS.md` always inserts `# EDITABLE SECTION` above preserved user text.
- README sync: enforce repo-only blocks in `README.md` and auto-sync
  `devcovenant/README.md` by stripping those blocks via the `readme-sync`
  policy. [done]
- Policy registry: make `devcovenant/registry/local/policy_registry.yaml`
  the sole hash store, and delete the legacy `devcovenant/registry.json`
  along with `update_hashes.py`.
- Policy lifecycle: implement replacements from
  `devcovenant/registry/global/policy_replacements.yaml`, and support the
  `freeze` override that copies policies into `devcovenant/custom/`.
- Managed environment: keep the `managed-environment` policy off by
  default, but warn on missing metadata when enabled.
- Install/update: ensure docs/managed blocks behave as specified
  (`AGENTS.md` template with preserved editable section, optional SPEC/PLAN,
  backups to `*_old.*`, `Last Updated` stamping, and doc include/exclude).
- Assets: compile policy assets into
  `devcovenant/registry/local/policy_assets.yaml` and apply only when the
  policy is enabled and profile scopes match.
- Packaging: do not ship tests in packages; create `tests/devcovenant/`
  only when the `new-modules-need-tests` policy is active (do not touch
  user-owned `tests/` content), keep `THIRD_PARTY_LICENSES.md`/`licenses/`
  in sync with dependency changes, and enforce Python 3.10+ metadata.
- Tests: treat `new-modules-need-tests` as unit-test-only, keep running
  both `pytest` and `python -m unittest discover`, and convert existing
  policy tests to unit-style suites as part of the migration.
- CLI: verify `refresh-all` exists, `refresh-policies` defaults to preserve,
  and deprecations (`normalize-metadata`, `update-hashes`) are removed or
  redirected as specified.

## Spec Coverage (Explicit)
Every SPEC bullet is listed here with status. Update to keep PLAN in sync.

### Workflow
- [done] Run the gated workflow for every change: pre-commit start, tests, pre-commit end.
- [done] Run a startup check at session start (`python3 -m devcovenant check --mode startup`).
- [done] When policy text changes, set `updated: true`, update scripts/tests, run `devcovenant update-policy-registry`, then reset `updated: false`.
- [done] Log every change in `CHANGELOG.md` under the current version header.

### Functional Requirements
- [done] Parse policy blocks from `AGENTS.md` and capture the descriptive text that follows each `policy-def` block.
- [done] Hash policy definitions and scripts into `devcovenant/registry/local/policy_registry.yaml`.
- [done] Expose `restore-stock-text` to reset policy prose to canonical wording.
- [done] Support `custom: true/false` metadata to mark custom policy prose that bypasses stock text sync checks.
- [done] Provide an optional semantic-version-scope policy (`apply: false` by default) that requires one SemVer scope tag in the latest changelog entry and matches the bump to major/minor/patch semantics.
- [not done] Maintain a canonical metadata schema that lists all supported keys (common and policy-specific) so every policy block can be normalized on demand.
- [done] Load policy modules from `devcovenant/core/policies/<id>/<id>.py` with custom overrides in `devcovenant/custom/policies/<id>/<id>.py`.
- [done] Load language adapters from `devcovenant/core/policies/<id>/adapters/` with custom overrides in `devcovenant/custom/policies/<id>/adapters/`. Custom adapters override core for the same policy + language.
- [done] When a custom policy module exists, it fully replaces the built-in policy and suppresses core fixers for that policy.
- [done] Respect `apply`, `severity`, `status`, and `enforcement` metadata for each policy.
- [done] Support `startup`, `lint`, `pre-commit`, and `normal` modes.
- [done] Apply auto-fixers when allowed, using fixers located under `devcovenant/core/policies/<id>/fixers/` and any custom fixers under `devcovenant/custom/policies/<id>/fixers/`.
- [done] Fixers are language-aware: policy fixers live in per-policy folders as `fixers/global.py` plus optional language-specific files (for example `fixers/python.py`, `fixers/js.py`). When no language-specific fixer is available, the engine falls back to `global.py`.
- [done] Not every policy ships with a fixer. Some policies will remain fixerless by design and are documented as such in the core policy guide.
- [done] Provide a console entry point (`devcovenant`) and module entry (`python3 -m devcovenant`) that both route to the same CLI. Docs should default to the console entry point and mention the `python3 -m ...` form once as the fallback when the CLI is not on PATH.
- [not done] Documentation should use `python3` (not `python`) for all source-based workflows and command examples.
- [done] Supported commands: `check`, `sync`, `test`, `update-policy-registry`, `restore-stock-text`, `install`, `update`, `uninstall`, `normalize-metadata`.
- [done] `check` exits non-zero when blocking violations or sync issues are present.
- [done] `sync` runs a startup-mode check and reports drift.
- [not done] `test` runs `pytest` against `tests/`, which now hosts the relocated policy and engine suites under `tests/devcovenant/`. That root-level tree mirrors the package layout and sits outside the installable `devcovenant` package, so only source distributions (via `MANIFEST.in`) carry it.
- [done] `install` and `uninstall` delegate to `devcovenant/core/install.py` and `devcovenant/core/uninstall.py`.
- [done] `update` supports managed-block-only refreshes and policy-mode control.
- [done] `normalize-metadata` inserts any missing policy keys with safe placeholders while preserving existing values.
- [done] Every managed doc must include `Last Updated` and `Version` headers.
- [not done] `devcovenant/README.md` also includes `DevCovenant Version`, sourced from the installer package version.
- [done] Every managed doc must include a top-of-file managed block inserted just below the header lines. The block records the `Doc ID`, `Doc Type`, and management ownership, and uses the standard markers: `<!-- DEVCOV:BEGIN -->` and `<!-- DEVCOV:END -->`.
- [done] `AGENTS.md` opens with a concise “operational orientation” outlining the enforced workflow (pre-commit start/tests/pre-commit end) and the managed environment expectations. It points readers to `devcovenant/README.md` for the broader command set so agents know how to interact with the repo before reaching the policy blocks.
- [done] The policy block is the text between `<!-- DEVCOV-POLICIES:BEGIN -->` and `<!-- DEVCOV-POLICIES:END -->` inside `AGENTS.md` and must be treated as a dedicated DevCovenant-managed unit. Policy entries are ordered alphabetically (no enabled/disabled grouping) and list every available policy, including custom overrides (automatically marked with `custom: true`).
- [not done] Managed documents are generated from YAML assets that supply the full document structure, including managed blocks and policy block scaffolding. Outside-of-block stock text is injected only when a target document is missing, empty, or effectively a single-line placeholder; otherwise install/update/refresh only regenerate the managed blocks (with the policy block treated separately per the marker rule above).
- [done] `devcovenant/config.yaml` must support `devcov_core_include` and `devcov_core_paths` for core exclusion.
- [done] Config is generated from global defaults plus active profiles and must include `profiles.generated.file_suffixes` so profile selections are visible to users and tooling.
- [done] Config exposes `version.override` so config-driven installs can declare the project version that templated assets (for example, `pyproject.toml`) should use when no `VERSION` file exists yet.
- [done] The `global` profile is always active. Other shipped defaults (`docs`, `data`, `suffixes`) are enabled by default but can be trimmed from `profiles.active` when a user wants to stop applying their assets or metadata overlays.
- [done] Config should expose global knobs for `paths`, `docs`, `install`, `update`, `engine`, `hooks`, `reporting`, `ignore`, `autogen_metadata_overrides`, and `user_metadata_overrides` so repos can tune behavior without editing core scripts. Every generated config must list every known knob (even if the default value is blank) so the file doubles as an override template that documents every supported option; only the policy overrides sections may remain empty to avoid overwhelming the document.
- [done] The profile catalog is generated into `devcovenant/registry/local/profile_catalog.yaml` by scanning profile manifests. Active profiles are recorded under `profiles.active` in config and extend file suffix coverage through catalog definitions.
- [done] Custom profiles are declared by adding a profile manifest plus assets under `devcovenant/custom/profiles/<name>/`.
- [done] Profile assets live under `devcovenant/core/profiles/<name>/assets/` and `devcovenant/custom/profiles/<name>/assets/`, with `global/assets/` covering shared docs and tooling.
- [done] Policy assets are declared inside policy folders under `devcovenant/core/policies/<policy>/assets/`. Install/update compiles the results into `devcovenant/registry/local/policy_assets.yaml`. Custom overrides live under `devcovenant/custom/policies/<policy>/assets/`. Assets install only when a policy is enabled and its `profile_scopes` match active profiles.
- [done] Template indexes live at `devcovenant/core/profiles/README.md` and `devcovenant/core/policies/README.md`.
- [done] Profile assets and policy overlays live in profile manifests at `devcovenant/core/profiles/<name>/profile.yaml`, with custom overrides under `devcovenant/custom/profiles/<name>/profile.yaml`. Profile assets are applied for active profiles, and profile overlays merge into `config.yaml` under `autogen_metadata_overrides` (with `user_metadata_overrides` taking precedence when set).
- [done] A lightweight check wrapper ships as `devcovenant/core/check.py` and can be invoked with `python3 -m devcovenant.core.check` to run the CLI from source installs.
- [not done] Managed-document templates include stock non-managed text for each devcovenant-managed doc, injected only when the target doc is missing, empty, or a single-line placeholder. Otherwise only managed blocks are refreshed. `AGENTS.md` is a special case: the stock `# EDITABLE SECTION` header is always inserted ahead of preserved user text so the editable notes remain anchored beneath the marker.

### Policy Requirements
- [done] Every policy definition includes descriptive prose immediately after the metadata block.
- [done] Built-in policies have canonical text stored in `devcovenant/registry/global/stock_policy_texts.yaml`.
- [done] Policies declare `profile_scopes` metadata to gate applicability; global policies use `profile_scopes: global`.
- [done] Custom policy `readme-sync` enforces that `devcovenant/README.md` mirrors `README.md` with repository-only blocks removed via `<!-- REPO-ONLY:BEGIN -->` / `<!-- REPO-ONLY:END -->` markers. Its auto-fix rewrites the packaged guide from the repo README.
- [done] The policy list is generated from the active profiles/config and includes every available core/custom policy. Entries are ordered alphabetically and custom overrides are marked with `custom: true`.
- [done] `apply: false` disables enforcement without removing definitions.
- [done] Provide a `managed-environment` policy (off by default) that enforces execution inside the expected environment when `apply: true`. It must warn when `expected_paths` or `expected_interpreters` are empty, warn when `command_hints` are missing, and report missing `required_commands` as warnings.
- [not done] `fiducial` policies remain enforced and always surface their policy text.
- [not done] Selector keys (`include_*`, `exclude_*`, `force_*`, `watch_*`) are supported across policy definitions for consistent scoping.
- [done] Policy metadata normalization must be able to add missing keys without changing existing values or policy text.
- [not done] Support policy replacement metadata via `devcovenant/registry/global/policy_replacements.yaml`. During updates, replaced policies move to custom and are marked deprecated when enabled; disabled policies are removed along with their custom scripts and fixers.
- [not done] Record update notices (replacements and new stock policies) in `devcovenant/registry/local/manifest.json` and print them to stdout.
- [not done] Treat the collective `<!-- DEVCOV-POLICIES:BEGIN -->`/`<!-- DEVCOV-POLICIES:END -->` block as a managed unit that install/update commands refresh from `devcovenant/core/` assets. Provide a per-policy `freeze` override that copies the policy’s modules, descriptors, and assets into `devcovenant/custom/` (with `custom: true`) when true and removes those files when the flag clears, always rerunning `devcovenant update-policy-registry` (and any needed registry fixes) so the registry records the custom copy. Auto-fixers should be devised for every policy and wired through the per-policy adapters so they work across every language/profile combination that the policy supports.
- [done] Generate `devcovenant/registry/local/policy_registry.yaml` dynamically from `refresh_policies` and `update_policy_registry`. The YAML tracks every policy (enabled or disabled) with its metadata handles, asset hints, profile scopes, core/custom source, enabled flag, and script hashes so the registry is the canonical policy map without requiring a separate reference document.
- [not done] The legacy `devcovenant/registry.json` storage and the accompanying `update_hashes.py` helper have been retired so policy hashes live solely inside `devcovenant/registry/local/policy_registry.yaml`.

### Installation Requirements
- [done] Install the full DevCovenant toolchain into the target repo, including the `devcovenant/` tree, `devcovenant/core/run_pre_commit.py`, `devcovenant/core/run_tests.py`, `devcovenant/core/update_lock.py`, and `devcovenant/core/update_test_status.py` helpers, and CI workflow assets.
- [not done] Use packaged assets from `devcovenant/core/profiles/` and `devcovenant/core/policies/` when installed from PyPI; fall back to repo files when running from source.
- [not done] Install modes: `auto`, `empty`; use mode-specific defaults for docs, config, and metadata handling. Use `devcovenant update` for existing repos.
- [not done] When install finds DevCovenant artifacts, it refuses to proceed unless `--auto-uninstall` is supplied or the user confirms the uninstall prompt.
- [done] `--disable-policy` sets `apply: false` for listed policy IDs during install/update.
- [not done] Update mode defaults to preserving policy blocks and metadata; managed blocks can be refreshed independently of policy definitions.
- [not done] Preserve custom policy scripts and fixers by default on existing installs (`--preserve-custom`), with explicit overrides available.
- [not done] `AGENTS.md` is always written from the template; if a prior `AGENTS.md` exists, preserve its editable section under `# EDITABLE SECTION`.
- [not done] `README.md` keeps user content, receives the standard header, and gains a managed block with missing sections (Table of Contents, Overview, Workflow, DevCovenant).
- [not done] `SPEC.md` and `PLAN.md` are optional. Existing files get header refreshes; missing files are created only when `--include-spec` or `--include-plan` are supplied.
- [not done] `CHANGELOG.md` and `CONTRIBUTING.md` are always replaced on install (backing up to `*_old.md`); updates refresh managed blocks only.
- [not done] `VERSION` is created on demand. Prefer an existing VERSION, otherwise read version fields from `pyproject.toml`, otherwise prompt. If prompting is skipped, default to `0.0.1`. The `--version` flag overrides detection and accepts `x.x` or `x.x.x` (normalized to `x.x.0`).
- [not done] If no license exists, install the GPL-3.0 template with a `Project Version` header. Only overwrite licenses when explicitly requested.
- [not done] Regenerate `.gitignore` from global, profile, and OS fragments, then merge existing user entries under a preserved block.
- [not done] Always back up overwritten or merged files as `*_old.*`, even when merges succeed, and report the backups at the end of install.
- [not done] Stamp `Last Updated` values using the UTC install date.
- [not done] Support partial doc overwrites via `--docs-include` / `--docs-exclude`, so only selected docs are replaced when docs mode overwrites.
- [not done] Support policy update modes via `--policy-mode preserve|append-missing|` `overwrite`.
- [not done] Write `devcovenant/registry/local/manifest.json` with the core layout, doc types, installed paths, options, active profiles, policy asset mappings, and the UTC timestamp of the install or update. Profile manifests drive profile assets and overlays, even when not listed as assets.
- [not done] Install and update share a unified self-install/self-refresh workflow. Whatever command runs operates on the host repository: invoking the installed package (on `PATH`) targets the current working repo, while running `python3` inside the DevCovenant source tree updates that repo in place without overwriting the existing `devcovenant/` folder, refreshing only configs, managed docs, and metadata. The optional `devcovenant/config_override` path remains a temporary override for experimentation.
- [not done] Add a `refresh-all` command that runs `refresh-policies` (defaulting to preserve metadata mode), updates `devcovenant/registry/local/policy_registry.yaml`, and rebuilds `devcovenant/registry/local/profile_catalog.yaml` so the profile/catalog state stays current without a full install/update run.

### Packaging Requirements
- [not done] Ship `devcovenant` as a pure-Python package with a console script entry.
- [not done] Include profile assets and policy assets in the sdist and wheel.
- [not done] Require Python 3.10+ and declare runtime dependencies in `requirements.in`, `requirements.lock`, and `pyproject.toml`.
- [not done] Keep `THIRD_PARTY_LICENSES.md` and `licenses/` synchronized with dependency changes so the dependency-license-sync policy passes.
- [not done] DevCovenant's own test suites live under `tests/devcovenant/` in the DevCovenant repo only. Tests are not shipped in packages; `tests/` is created on demand when the `new-modules-need-tests` policy is active. User repos exclude `devcovenant/**` from test enforcement except `devcovenant/custom/**`, which is included. When needed, user repos create `tests/devcovenant/custom/` to cover custom policy/profile code. Policies reuse metadata (for example, `tests_watch_dirs`, `selector_roles`, and policy-specific selector options) so the suite can move without hard-coded paths. Profile or repo overrides set these metadata values when they relocate tests elsewhere.
- [not done] The tests tree mirrors the package layout (core/custom and their profile directories) under `tests/devcovenant/` so interpreter or scanner modules in `devcovenant/core/profiles` or `devcovenant/custom/profiles` can rely on corresponding suites under `tests/devcovenant/core/profiles/` and `tests/devcovenant/custom/profiles/`.
- [not done] The `new-modules-need-tests` policy explicitly requires unit tests. The repository continues to run both `pytest` and `python -m unittest discover`, but newly added coverage must be unit-level and existing policy tests should be converted to unit suites over time.
- [not done] User repos keep an always-on `devcov-exclude` profile that excludes `devcovenant/**` from test enforcement except `devcovenant/custom/**`. When `devcov_core_include` is true, the `devcov-exclude` profile is ignored so the DevCovenant repo can test core code.

### Non-Functional Requirements
- [not done] Checks must be fast enough for pre-commit usage on typical repos.
- [not done] Violations must be clear, actionable, and reference the policy source.
- [not done] Install and uninstall operations must be deterministic and reversible.

### Future Direction
- [not done] Version 0.2.7 moves more stock policies onto a metadata-driven DSL surfaced via `devcovenant/config.yaml`. That lets `AGENTS.md` focus on documentation text while selectors, version boundaries, and runtime paths become configurable knobs.
- [not done] Expect the DSL to replace hard-coded policy metadata (version watching, docs location, selectors) with reusable templates keyed by active profiles, while still allowing true custom policies to live inside `devcovenant/custom/`.

## Outstanding Work (Dependency Order)
Not-done SPEC items ordered by dependency. Keep this list current.

### Functional Requirements
- Maintain a canonical metadata schema that lists all supported keys (common and policy-specific) so every policy block can be normalized on demand.
- Documentation should use `python3` (not `python`) for all source-based workflows and command examples.
- `test` runs `pytest` against `tests/`, which now hosts the relocated policy and engine suites under `tests/devcovenant/`. That root-level tree mirrors the package layout and sits outside the installable `devcovenant` package, so only source distributions (via `MANIFEST.in`) carry it.
- `devcovenant/README.md` also includes `DevCovenant Version`, sourced from the installer package version.
- Managed documents are generated from YAML assets that supply the full document structure, including managed blocks and policy block scaffolding. Outside-of-block stock text is injected only when a target document is missing, empty, or effectively a single-line placeholder; otherwise install/update/refresh only regenerate the managed blocks (with the policy block treated separately per the marker rule above).
- Managed-document templates include stock non-managed text for each devcovenant-managed doc, injected only when the target doc is missing, empty, or a single-line placeholder. Otherwise only managed blocks are refreshed. `AGENTS.md` is a special case: the stock `# EDITABLE SECTION` header is always inserted ahead of preserved user text so the editable notes remain anchored beneath the marker.

### Policy Requirements
- `fiducial` policies remain enforced and always surface their policy text.
- Selector keys (`include_*`, `exclude_*`, `force_*`, `watch_*`) are supported across policy definitions for consistent scoping.
- Support policy replacement metadata via `devcovenant/registry/global/policy_replacements.yaml`. During updates, replaced policies move to custom and are marked deprecated when enabled; disabled policies are removed along with their custom scripts and fixers.
- Record update notices (replacements and new stock policies) in `devcovenant/registry/local/manifest.json` and print them to stdout.
- Treat the collective `<!-- DEVCOV-POLICIES:BEGIN -->`/`<!-- DEVCOV-POLICIES:END -->` block as a managed unit that install/update commands refresh from `devcovenant/core/` assets. Provide a per-policy `freeze` override that copies the policy’s modules, descriptors, and assets into `devcovenant/custom/` (with `custom: true`) when true and removes those files when the flag clears, always rerunning `devcovenant update-policy-registry` (and any needed registry fixes) so the registry records the custom copy. Auto-fixers should be devised for every policy and wired through the per-policy adapters so they work across every language/profile combination that the policy supports.
- The legacy `devcovenant/registry.json` storage and the accompanying `update_hashes.py` helper have been retired so policy hashes live solely inside `devcovenant/registry/local/policy_registry.yaml`.

### Packaging Requirements
- Ship `devcovenant` as a pure-Python package with a console script entry.
- Include profile assets and policy assets in the sdist and wheel.
- Require Python 3.10+ and declare runtime dependencies in `requirements.in`, `requirements.lock`, and `pyproject.toml`.
- Keep `THIRD_PARTY_LICENSES.md` and `licenses/` synchronized with dependency changes so the dependency-license-sync policy passes.
- DevCovenant's own test suites live under `tests/devcovenant/` in the DevCovenant repo only. Tests are not shipped in packages; `tests/` is created on demand when the `new-modules-need-tests` policy is active. User repos exclude `devcovenant/**` from test enforcement except `devcovenant/custom/**`, which is included. When needed, user repos create `tests/devcovenant/custom/` to cover custom policy/profile code. Policies reuse metadata (for example, `tests_watch_dirs`, `selector_roles`, and policy-specific selector options) so the suite can move without hard-coded paths. Profile or repo overrides set these metadata values when they relocate tests elsewhere.
- The tests tree mirrors the package layout (core/custom and their profile directories) under `tests/devcovenant/` so interpreter or scanner modules in `devcovenant/core/profiles` or `devcovenant/custom/profiles` can rely on corresponding suites under `tests/devcovenant/core/profiles/` and `tests/devcovenant/custom/profiles/`.
- The `new-modules-need-tests` policy explicitly requires unit tests. The repository continues to run both `pytest` and `python -m unittest discover`, but newly added coverage must be unit-level and existing policy tests should be converted to unit suites over time.
- User repos keep an always-on `devcov-exclude` profile that excludes `devcovenant/**` from test enforcement except `devcovenant/custom/**`. When `devcov_core_include` is true, the `devcov-exclude` profile is ignored so the DevCovenant repo can test core code.

### Non-Functional Requirements
- Checks must be fast enough for pre-commit usage on typical repos.
- Violations must be clear, actionable, and reference the policy source.
- Install and uninstall operations must be deterministic and reversible.

## Workflow
- [done] Run the gated workflow for every change: pre-commit start, tests, pre-commit end.
- [done] Run a startup check at session start (`python3 -m devcovenant check --mode startup`).
- [done] When policy text changes, set `updated: true`, update scripts/tests, run `devcovenant update-policy-registry`, then reset `updated: false`.
- [done] Log every change in `CHANGELOG.md` under the current version header.

### Functional Requirements
- [done] Parse policy blocks from `AGENTS.md` and capture the descriptive text that follows each `policy-def` block.
- [done] Hash policy definitions and scripts into `devcovenant/registry/local/policy_registry.yaml`.
- [done] Expose `restore-stock-text` to reset policy prose to canonical wording.
- [done] Support `custom: true/false` metadata to mark custom policy prose that bypasses stock text sync checks.
- [done] Provide an optional semantic-version-scope policy (`apply: false` by default) that requires one SemVer scope tag in the latest changelog entry and matches the bump to major/minor/patch semantics.
- [not done] Maintain a canonical metadata schema that lists all supported keys (common and policy-specific) so every policy block can be normalized on demand.
- [done] Load policy modules from `devcovenant/core/policies/<id>/<id>.py` with custom overrides in `devcovenant/custom/policies/<id>/<id>.py`.
- [done] Load language adapters from `devcovenant/core/policies/<id>/adapters/` with custom overrides in `devcovenant/custom/policies/<id>/adapters/`. Custom adapters override core for the same policy + language.
- [done] When a custom policy module exists, it fully replaces the built-in policy and suppresses core fixers for that policy.
- [done] Respect `apply`, `severity`, `status`, and `enforcement` metadata for each policy.
- [done] Support `startup`, `lint`, `pre-commit`, and `normal` modes.
- [done] Apply auto-fixers when allowed, using fixers located under `devcovenant/core/policies/<id>/fixers/` and any custom fixers under `devcovenant/custom/policies/<id>/fixers/`.
- [done] Fixers are language-aware: policy fixers live in per-policy folders as `fixers/global.py` plus optional language-specific files (for example `fixers/python.py`, `fixers/js.py`). When no language-specific fixer is available, the engine falls back to `global.py`.
- [done] Not every policy ships with a fixer. Some policies will remain fixerless by design and are documented as such in the core policy guide.
- [done] Provide a console entry point (`devcovenant`) and module entry (`python3 -m devcovenant`) that both route to the same CLI. Docs should default to the console entry point and mention the `python3 -m ...` form once as the fallback when the CLI is not on PATH.
- [not done] Documentation should use `python3` (not `python`) for all source-based workflows and command examples.
- [done] Supported commands: `check`, `sync`, `test`, `update-policy-registry`, `restore-stock-text`, `install`, `update`, `uninstall`, `normalize-metadata`.
- [not done] `check` exits non-zero when blocking violations or sync issues are present.
- [not done] `sync` runs a startup-mode check and reports drift.
- [not done] `test` runs `pytest` against `tests/`, which now hosts the relocated policy and engine suites under `tests/devcovenant/`. That root-level tree mirrors the package layout and sits outside the installable `devcovenant` package, so only source distributions (via `MANIFEST.in`) carry it.
- [not done] `install` and `uninstall` delegate to `devcovenant/core/install.py` and `devcovenant/core/uninstall.py`.
- [not done] `update` supports managed-block-only refreshes and policy-mode control.
- [not done] `normalize-metadata` inserts any missing policy keys with safe placeholders while preserving existing values.
- [not done] Every managed doc must include `Last Updated` and `Version` headers.
- [not done] `devcovenant/README.md` also includes `DevCovenant Version`, sourced from the installer package version.
- [not done] Every managed doc must include a top-of-file managed block inserted just below the header lines. The block records the `Doc ID`, `Doc Type`, and management ownership, and uses the standard markers: `<!-- DEVCOV:BEGIN -->` and `<!-- DEVCOV:END -->`.
- [not done] `AGENTS.md` opens with a concise “operational orientation” outlining the enforced workflow (pre-commit start/tests/pre-commit end) and the managed environment expectations. It points readers to `devcovenant/README.md` for the broader command set so agents know how to interact with the repo before reaching the policy blocks.
- [not done] The policy block is the text between `<!-- DEVCOV-POLICIES:BEGIN -->` and `<!-- DEVCOV-POLICIES:END -->` inside `AGENTS.md` and must be treated as a dedicated DevCovenant-managed unit. Policy entries are ordered alphabetically (no enabled/disabled grouping) and list every available policy, including custom overrides (automatically marked with `custom: true`).
- [not done] Managed documents are generated from YAML assets that supply the full document structure, including managed blocks and policy block scaffolding. Outside-of-block stock text is injected only when a target document is missing, empty, or effectively a single-line placeholder; otherwise install/update/refresh only regenerate the managed blocks (with the policy block treated separately per the marker rule above).
- [not done] `devcovenant/config.yaml` must support `devcov_core_include` and `devcov_core_paths` for core exclusion.
- [not done] Config is generated from global defaults plus active profiles and must include `profiles.generated.file_suffixes` so profile selections are visible to users and tooling.
- [not done] Config exposes `version.override` so config-driven installs can declare the project version that templated assets (for example, `pyproject.toml`) should use when no `VERSION` file exists yet.
- [not done] The `global` profile is always active. Other shipped defaults (`docs`, `data`, `suffixes`) are enabled by default but can be trimmed from `profiles.active` when a user wants to stop applying their assets or metadata overlays.
- [done] Config should expose global knobs for `paths`, `docs`, `install`, `update`, `engine`, `hooks`, `reporting`, `ignore`, `autogen_metadata_overrides`, and `user_metadata_overrides` so repos can tune behavior without editing core scripts. Every generated config must list every known knob (even if the default value is blank) so the file doubles as an override template that documents every supported option; only the policy overrides sections may remain empty to avoid overwhelming the document.
- [not done] The profile catalog is generated into `devcovenant/registry/local/profile_catalog.yaml` by scanning profile manifests. Active profiles are recorded under `profiles.active` in config and extend file suffix coverage through catalog definitions.
- [not done] Custom profiles are declared by adding a profile manifest plus assets under `devcovenant/custom/profiles/<name>/`.
- [not done] Profile assets live under `devcovenant/core/profiles/<name>/assets/` and `devcovenant/custom/profiles/<name>/assets/`, with `global/assets/` covering shared docs and tooling.
- [not done] Policy assets are declared inside policy folders under `devcovenant/core/policies/<policy>/assets/`. Install/update compiles the results into `devcovenant/registry/local/policy_assets.yaml`. Custom overrides live under `devcovenant/custom/policies/<policy>/assets/`. Assets install only when a policy is enabled and its `profile_scopes` match active profiles.
- [not done] Template indexes live at `devcovenant/core/profiles/README.md` and `devcovenant/core/policies/README.md`.
- [done] Profile assets and policy overlays live in profile manifests at `devcovenant/core/profiles/<name>/profile.yaml`, with custom overrides under `devcovenant/custom/profiles/<name>/profile.yaml`. Profile assets are applied for active profiles, and profile overlays merge into `config.yaml` under `autogen_metadata_overrides` (with `user_metadata_overrides` taking precedence when set).
- [done] A lightweight check wrapper ships as `devcovenant/core/check.py` and can be invoked with `python3 -m devcovenant.core.check` to run the CLI from source installs.
- [not done] Managed-document templates include stock non-managed text for each devcovenant-managed doc, injected only when the target doc is missing, empty, or a single-line placeholder. Otherwise only managed blocks are refreshed. `AGENTS.md` is a special case: the stock `# EDITABLE SECTION` header is always inserted ahead of preserved user text so the editable notes remain anchored beneath the marker.

### Policy Requirements
- [not done] Every policy definition includes descriptive prose immediately after the metadata block.
- [not done] Built-in policies have canonical text stored in `devcovenant/registry/global/stock_policy_texts.yaml`.
- [not done] Policies declare `profile_scopes` metadata to gate applicability; global policies use `profile_scopes: global`.
- [done] Custom policy `readme-sync` enforces that `devcovenant/README.md` mirrors `README.md` with repository-only blocks removed via `<!-- REPO-ONLY:BEGIN -->` / `<!-- REPO-ONLY:END -->` markers. Its auto-fix rewrites the packaged guide from the repo README.
- [not done] The policy list is generated from the active profiles/config and includes every available core/custom policy. Entries are ordered alphabetically and custom overrides are marked with `custom: true`.
- [not done] `apply: false` disables enforcement without removing definitions.
- [not done] Provide a `managed-environment` policy (off by default) that enforces execution inside the expected environment when `apply: true`. It must warn when `expected_paths` or `expected_interpreters` are empty, warn when `command_hints` are missing, and report missing `required_commands` as warnings.
- [not done] `fiducial` policies remain enforced and always surface their policy text.
- [not done] Selector keys (`include_*`, `exclude_*`, `force_*`, `watch_*`) are supported across policy definitions for consistent scoping.
- [not done] Policy metadata normalization must be able to add missing keys without changing existing values or policy text.
- [not done] Support policy replacement metadata via `devcovenant/registry/global/policy_replacements.yaml`. During updates, replaced policies move to custom and are marked deprecated when enabled; disabled policies are removed along with their custom scripts and fixers.
- [not done] Record update notices (replacements and new stock policies) in `devcovenant/registry/local/manifest.json` and print them to stdout.
- [not done] Treat the collective `<!-- DEVCOV-POLICIES:BEGIN -->`/`<!-- DEVCOV-POLICIES:END -->` block as a managed unit that install/update commands refresh from `devcovenant/core/` assets. Provide a per-policy `freeze` override that copies the policy’s modules, descriptors, and assets into `devcovenant/custom/` (with `custom: true`) when true and removes those files when the flag clears, always rerunning `devcovenant update-policy-registry` (and any needed registry fixes) so the registry records the custom copy. Auto-fixers should be devised for every policy and wired through the per-policy adapters so they work across every language/profile combination that the policy supports.
- [not done] Generate `devcovenant/registry/local/policy_registry.yaml` dynamically from `refresh_policies` and `update_policy_registry`. The YAML tracks every policy (enabled or disabled) with its metadata handles, asset hints, profile scopes, core/custom source, enabled flag, and script hashes so the registry is the canonical policy map without requiring a separate reference document.
- [not done] The legacy `devcovenant/registry.json` storage and the accompanying `update_hashes.py` helper have been retired so policy hashes live solely inside `devcovenant/registry/local/policy_registry.yaml`.

### Installation Requirements
- [not done] Install the full DevCovenant toolchain into the target repo, including the `devcovenant/` tree, `devcovenant/core/run_pre_commit.py`, `devcovenant/core/run_tests.py`, `devcovenant/core/update_lock.py`, and `devcovenant/core/update_test_status.py` helpers, and CI workflow assets.
- [not done] Use packaged assets from `devcovenant/core/profiles/` and `devcovenant/core/policies/` when installed from PyPI; fall back to repo files when running from source.
- [not done] Install modes: `auto`, `empty`; use mode-specific defaults for docs, config, and metadata handling. Use `devcovenant update` for existing repos.
- [not done] When install finds DevCovenant artifacts, it refuses to proceed unless `--auto-uninstall` is supplied or the user confirms the uninstall prompt.
- [not done] `--disable-policy` sets `apply: false` for listed policy IDs during install/update.
- [not done] Update mode defaults to preserving policy blocks and metadata; managed blocks can be refreshed independently of policy definitions.
- [not done] Preserve custom policy scripts and fixers by default on existing installs (`--preserve-custom`), with explicit overrides available.
- [not done] `AGENTS.md` is always written from the template; if a prior `AGENTS.md` exists, preserve its editable section under `# EDITABLE SECTION`.
- [not done] `README.md` keeps user content, receives the standard header, and gains a managed block with missing sections (Table of Contents, Overview, Workflow, DevCovenant).
- [not done] `SPEC.md` and `PLAN.md` are optional. Existing files get header refreshes; missing files are created only when `--include-spec` or `--include-plan` are supplied.
- [not done] `CHANGELOG.md` and `CONTRIBUTING.md` are always replaced on install (backing up to `*_old.md`); updates refresh managed blocks only.
- [not done] `VERSION` is created on demand. Prefer an existing VERSION, otherwise read version fields from `pyproject.toml`, otherwise prompt. If prompting is skipped, default to `0.0.1`. The `--version` flag overrides detection and accepts `x.x` or `x.x.x` (normalized to `x.x.0`).
- [not done] If no license exists, install the GPL-3.0 template with a `Project Version` header. Only overwrite licenses when explicitly requested.
- [not done] Regenerate `.gitignore` from global, profile, and OS fragments, then merge existing user entries under a preserved block.
- [not done] Always back up overwritten or merged files as `*_old.*`, even when merges succeed, and report the backups at the end of install.
- [not done] Stamp `Last Updated` values using the UTC install date.
- [not done] Support partial doc overwrites via `--docs-include` / `--docs-exclude`, so only selected docs are replaced when docs mode overwrites.
- [not done] Support policy update modes via `--policy-mode preserve|append-missing|` `overwrite`.
- [not done] Write `devcovenant/registry/local/manifest.json` with the core layout, doc types, installed paths, options, active profiles, policy asset mappings, and the UTC timestamp of the install or update. Profile manifests drive profile assets and overlays, even when not listed as assets.
- [not done] Install and update share a unified self-install/self-refresh workflow. Whatever command runs operates on the host repository: invoking the installed package (on `PATH`) targets the current working repo, while running `python3` inside the DevCovenant source tree updates that repo in place without overwriting the existing `devcovenant/` folder, refreshing only configs, managed docs, and metadata. The optional `devcovenant/config_override` path remains a temporary override for experimentation.
- [not done] Add a `refresh-all` command that runs `refresh-policies` (defaulting to preserve metadata mode), updates `devcovenant/registry/local/policy_registry.yaml`, and rebuilds `devcovenant/registry/local/profile_catalog.yaml` so the profile/catalog state stays current without a full install/update run.

### Packaging Requirements
- [not done] Ship `devcovenant` as a pure-Python package with a console script entry.
- [not done] Include profile assets and policy assets in the sdist and wheel.
- [not done] Require Python 3.10+ and declare runtime dependencies in `requirements.in`, `requirements.lock`, and `pyproject.toml`.
- [not done] Keep `THIRD_PARTY_LICENSES.md` and `licenses/` synchronized with dependency changes so the dependency-license-sync policy passes.
- [not done] DevCovenant's own test suites live under `tests/devcovenant/` in the DevCovenant repo only. Tests are not shipped in packages; `tests/` is created on demand when the `new-modules-need-tests` policy is active. User repos exclude `devcovenant/**` from test enforcement except `devcovenant/custom/**`, which is included. When needed, user repos create `tests/devcovenant/custom/` to cover custom policy/profile code. Policies reuse metadata (for example, `tests_watch_dirs`, `selector_roles`, and policy-specific selector options) so the suite can move without hard-coded paths. Profile or repo overrides set these metadata values when they relocate tests elsewhere.
- [not done] The tests tree mirrors the package layout (core/custom and their profile directories) under `tests/devcovenant/` so interpreter or scanner modules in `devcovenant/core/profiles` or `devcovenant/custom/profiles` can rely on corresponding suites under `tests/devcovenant/core/profiles/` and `tests/devcovenant/custom/profiles/`.
- [not done] The `new-modules-need-tests` policy explicitly requires unit tests. The repository continues to run both `pytest` and `python -m unittest discover`, but newly added coverage must be unit-level and existing policy tests should be converted to unit suites over time.
- [not done] User repos keep an always-on `devcov-exclude` profile that excludes `devcovenant/**` from test enforcement except `devcovenant/custom/**`. When `devcov_core_include` is true, the `devcov-exclude` profile is ignored so the DevCovenant repo can test core code.

### Non-Functional Requirements
- [not done] Checks must be fast enough for pre-commit usage on typical repos.
- [not done] Violations must be clear, actionable, and reference the policy source.
- [not done] Install and uninstall operations must be deterministic and reversible.

### Future Direction
- [not done] Version 0.2.7 moves more stock policies onto a metadata-driven DSL surfaced via `devcovenant/config.yaml`. That lets `AGENTS.md` focus on documentation text while selectors, version boundaries, and runtime paths become configurable knobs.
- [not done] Expect the DSL to replace hard-coded policy metadata (version watching, docs location, selectors) with reusable templates keyed by active profiles, while still allowing true custom policies to live inside `devcovenant/custom/`.

## Workflow
- [done] Run the gated workflow for every change: pre-commit start, tests,
- [done] Run a startup check at session start (`python3 -m devcovenant check --mode
- [done] When policy text changes, set `updated: true`, update scripts/tests, run
- [done] Log every change in `CHANGELOG.md` under the current version header.

### Functional Requirements
- [done] Parse policy blocks from `AGENTS.md` and capture the descriptive text that
- [done] Hash policy definitions and scripts into
- [done] Expose `restore-stock-text` to reset policy prose to canonical wording.
- [done] Support `custom: true/false` metadata to mark custom policy prose that
- [done] Provide an optional semantic-version-scope policy (`apply: false` by
- [not done] Maintain a canonical metadata schema that lists all supported keys (common
- [done] Load policy modules from `devcovenant/core/policies/<id>/<id>.py` with
- [done] Load language adapters from `devcovenant/core/policies/<id>/adapters/`
- [done] When a custom policy module exists, it fully replaces the built-in policy
- [done] Respect `apply`, `severity`, `status`, and `enforcement` metadata for each
- [done] Support `startup`, `lint`, `pre-commit`, and `normal` modes.
- [done] Apply auto-fixers when allowed, using fixers located under
- [done] Fixers are language-aware: policy fixers live in per-policy folders as
- [done] Not every policy ships with a fixer. Some policies will remain fixerless
- [done] Provide a console entry point (`devcovenant`) and module entry
- [not done] Documentation should use `python3` (not `python`) for all source-based
- [not done] Supported commands: `check`, `sync`, `test`, `update-policy-registry`,
- [not done] `check` exits non-zero when blocking violations or sync issues are present.
- [not done] `sync` runs a startup-mode check and reports drift.
- [not done] `test` runs `pytest` against `tests/`, which now hosts the relocated policy
- [not done] `install` and `uninstall` delegate to `devcovenant/core/install.py` and
- [not done] `update` supports managed-block-only refreshes and policy-mode control.
- [not done] `normalize-metadata` inserts any missing policy keys with safe placeholders
- [not done] Every managed doc must include `Last Updated` and `Version` headers.
- [not done] `devcovenant/README.md` also includes `DevCovenant Version`, sourced from
- [not done] Every managed doc must include a top-of-file managed block inserted just
- [not done] `AGENTS.md` opens with a concise “operational orientation” outlining the
- [not done] The policy block is the text between
- [not done] Managed documents are generated from YAML assets that supply the full
- [not done] `devcovenant/config.yaml` must support `devcov_core_include` and
- [not done] Config is generated from global defaults plus active profiles and must
- [not done] Config exposes `version.override` so config-driven installs can declare
- [not done] The `global` profile is always active. Other shipped defaults (`docs`,
- [not done] Config should expose global knobs for `paths`, `docs`, `install`,
- [not done] The profile catalog is generated into
- [not done] Custom profiles are declared by adding a profile manifest plus assets
- [not done] Profile assets live under `devcovenant/core/profiles/<name>/assets/` and
- [not done] Policy assets are declared inside policy folders under
- [not done] Template indexes live at `devcovenant/core/profiles/README.md` and
- [not done] Profile assets and policy overlays live in profile manifests at
- [not done] A lightweight check wrapper ships as `devcovenant/core/check.py` and can
- [not done] Managed-document templates include stock non-managed text for each

### Policy Requirements
- [not done] Every policy definition includes descriptive prose immediately after the
- [not done] Built-in policies have canonical text stored in
- [not done] Policies declare `profile_scopes` metadata to gate applicability;
- [done] Custom policy `readme-sync` enforces that `devcovenant/README.md` mirrors
- [not done] The policy list is generated from the active profiles/config and includes
- [not done] `apply: false` disables enforcement without removing definitions.
- [not done] Provide a `managed-environment` policy (off by default) that
- [not done] `fiducial` policies remain enforced and always surface their policy text.
- [not done] Selector keys (`include_*`, `exclude_*`, `force_*`, `watch_*`) are supported
- [not done] Policy metadata normalization must be able to add missing keys without
- [not done] Support policy replacement metadata via
- [not done] Record update notices (replacements and new stock policies) in
- [not done] Treat the collective `<!-- DEVCOV-POLICIES:BEGIN -->`/`<!-- DEVCOV-POLICIES:END -->` block as a
- [not done] Generate `devcovenant/registry/local/policy_registry.yaml` dynamically from
- [not done] The legacy `devcovenant/registry.json` storage and the accompanying

### Installation Requirements
- [not done] Install the full DevCovenant toolchain into the target repo, including the
- [not done] Use packaged assets from `devcovenant/core/profiles/` and
- [not done] Install modes: `auto`, `empty`; use mode-specific defaults for docs,
- [not done] When install finds DevCovenant artifacts, it refuses to proceed unless
- [not done] `--disable-policy` sets `apply: false` for listed policy IDs during
- [not done] Update mode defaults to preserving policy blocks and metadata; managed blocks
- [not done] Preserve custom policy scripts and fixers by default on existing installs
- [not done] `AGENTS.md` is always written from the template; if a prior `AGENTS.md`
- [not done] `README.md` keeps user content, receives the standard header, and gains a
- [not done] `SPEC.md` and `PLAN.md` are optional. Existing files get header refreshes;
- [not done] `CHANGELOG.md` and `CONTRIBUTING.md` are always replaced on install
- [not done] `VERSION` is created on demand. Prefer an existing VERSION, otherwise
- [not done] If no license exists, install the GPL-3.0 template with a `Project Version`
- [not done] Regenerate `.gitignore` from global, profile, and OS fragments, then
- [not done] Always back up overwritten or merged files as `*_old.*`, even when
- [not done] Stamp `Last Updated` values using the UTC install date.
- [not done] Support partial doc overwrites via `--docs-include` / `--docs-exclude`, so
- [not done] Support policy update modes via `--policy-mode preserve|append-missing|`
- [not done] Write `devcovenant/registry/local/manifest.json` with the core layout, doc types,
- [not done] Install and update share a unified self-install/self-refresh workflow. Whatever
- [not done] Add a `refresh-all` command that runs `refresh-policies` (defaulting to

### Packaging Requirements
- [not done] Ship `devcovenant` as a pure-Python package with a console script entry.
- [not done] Include profile assets and policy assets in the sdist and wheel.
- [not done] Require Python 3.10+ and declare runtime dependencies in
- [not done] Keep `THIRD_PARTY_LICENSES.md` and `licenses/` synchronized with dependency
- [not done] DevCovenant's own test suites live under `tests/devcovenant/` in the
- [not done] The tests tree mirrors the package layout (core/custom and their profile
- [not done] The `new-modules-need-tests` policy explicitly requires unit tests. The
- [not done] User repos keep an always-on `devcov-exclude` profile that excludes

### Non-Functional Requirements
- [not done] Checks must be fast enough for pre-commit usage on typical repos.
- [not done] Violations must be clear, actionable, and reference the policy source.
- [not done] Install and uninstall operations must be deterministic and reversible.

### Future Direction
- [not done] Version 0.2.7 moves more stock policies onto a metadata-driven DSL surfaced
- [not done] Expect the DSL to replace hard-coded policy metadata (version watching, docs

## Workflow
- Run the gated workflow for every change: pre-commit start, tests,
- Run a startup check at session start (`python3 -m devcovenant check --mode
- When policy text changes, set `updated: true`, update scripts/tests, run
- Log every change in `CHANGELOG.md` under the current version header.

### Functional Requirements
- Parse policy blocks from `AGENTS.md` and capture the descriptive text that
- Hash policy definitions and scripts into
- Expose `restore-stock-text` to reset policy prose to canonical wording.
- Support `custom: true/false` metadata to mark custom policy prose that
- Provide an optional semantic-version-scope policy (`apply: false` by
- Maintain a canonical metadata schema that lists all supported keys (common
- Load policy modules from `devcovenant/core/policies/<id>/<id>.py` with
- Load language adapters from `devcovenant/core/policies/<id>/adapters/`
- When a custom policy module exists, it fully replaces the built-in policy
- Respect `apply`, `severity`, `status`, and `enforcement` metadata for each
- Support `startup`, `lint`, `pre-commit`, and `normal` modes.
- Apply auto-fixers when allowed, using fixers located under
- Fixers are language-aware: policy fixers live in per-policy folders as
- Not every policy ships with a fixer. Some policies will remain fixerless
- Provide a console entry point (`devcovenant`) and module entry
- Documentation should use `python3` (not `python`) for all source-based
- Supported commands: `check`, `sync`, `test`, `update-policy-registry`,
- `check` exits non-zero when blocking violations or sync issues are present.
- `sync` runs a startup-mode check and reports drift.
- `test` runs `pytest` against `tests/`, which now hosts the relocated policy
- `install` and `uninstall` delegate to `devcovenant/core/install.py` and
- `update` supports managed-block-only refreshes and policy-mode control.
- `normalize-metadata` inserts any missing policy keys with safe placeholders
- Every managed doc must include `Last Updated` and `Version` headers.
- `devcovenant/README.md` also includes `DevCovenant Version`, sourced from
- Every managed doc must include a top-of-file managed block inserted just
- `AGENTS.md` opens with a concise “operational orientation” outlining the
- The policy block is the text between
- Managed documents are generated from YAML assets that supply the full
- `devcovenant/config.yaml` must support `devcov_core_include` and
- Config is generated from global defaults plus active profiles and must
- Config exposes `version.override` so config-driven installs can declare
- The `global` profile is always active. Other shipped defaults (`docs`,
- Config should expose global knobs for `paths`, `docs`, `install`,
- The profile catalog is generated into
- Custom profiles are declared by adding a profile manifest plus assets
- Profile assets live under `devcovenant/core/profiles/<name>/assets/` and
- Policy assets are declared inside policy folders under
- Template indexes live at `devcovenant/core/profiles/README.md` and
- Profile assets and policy overlays live in profile manifests at
- Managed-document templates include stock non-managed text for each

### Policy Requirements
- Every policy definition includes descriptive prose immediately after the
- Built-in policies have canonical text stored in
- Policies declare `profile_scopes` metadata to gate applicability;
- The policy list is generated from the active profiles/config and includes
- `apply: false` disables enforcement without removing definitions.
- Provide a `managed-environment` policy (off by default) that
- `fiducial` policies remain enforced and always surface their policy text.
- Selector keys (`include_*`, `exclude_*`, `force_*`, `watch_*`) are supported
- Policy metadata normalization must be able to add missing keys without
- Support policy replacement metadata via
- Record update notices (replacements and new stock policies) in
- Treat the collective `<!-- DEVCOV-POLICIES:BEGIN -->`/`<!-- DEVCOV-POLICIES:END -->` block as a
- Generate `devcovenant/registry/local/policy_registry.yaml` dynamically from
- The legacy `devcovenant/registry.json` storage and the accompanying

### Packaging Requirements
- Ship `devcovenant` as a pure-Python package with a console script entry.
- Include profile assets and policy assets in the sdist and wheel.
- Require Python 3.10+ and declare runtime dependencies in
- Keep `THIRD_PARTY_LICENSES.md` and `licenses/` synchronized with dependency
- DevCovenant's own test suites live under `tests/devcovenant/` in the
- The tests tree mirrors the package layout (core/custom and their profile
- The `new-modules-need-tests` policy explicitly requires unit tests. The
- User repos keep an always-on `devcov-exclude` profile that excludes

### Non-Functional Requirements
- Checks must be fast enough for pre-commit usage on typical repos.
- Violations must be clear, actionable, and reference the policy source.
- Install and uninstall operations must be deterministic and reversible.

## Workflow
- [not done] Run the gated workflow for every change: pre-commit start, tests,
- [not done] Run a startup check at session start (`python3 -m devcovenant check --mode
- [not done] When policy text changes, set `updated: true`, update scripts/tests, run
- [not done] Log every change in `CHANGELOG.md` under the current version header.

## Functional Requirements
- [not done] Parse policy blocks from `AGENTS.md` and capture the descriptive text that
- [not done] Hash policy definitions and scripts into
- [not done] Expose `restore-stock-text` to reset policy prose to canonical wording.
- [not done] Support `custom: true/false` metadata to mark custom policy prose that
- [not done] Provide an optional semantic-version-scope policy (`apply: false` by
- [not done] Maintain a canonical metadata schema that lists all supported keys (common
- [not done] Load policy modules from `devcovenant/core/policies/<id>/<id>.py` with
- [not done] Load language adapters from `devcovenant/core/policies/<id>/adapters/`
- [not done] When a custom policy module exists, it fully replaces the built-in policy
- [not done] Respect `apply`, `severity`, `status`, and `enforcement` metadata for each
- [not done] Support `startup`, `lint`, `pre-commit`, and `normal` modes.
- [not done] Apply auto-fixers when allowed, using fixers located under
- [not done] Fixers are language-aware: policy fixers live in per-policy folders as
- [not done] Not every policy ships with a fixer. Some policies will remain fixerless
- [not done] Provide a console entry point (`devcovenant`) and module entry
- [not done] Documentation should use `python3` (not `python`) for all source-based
- [not done] Supported commands: `check`, `sync`, `test`, `update-policy-registry`,
- [not done] `check` exits non-zero when blocking violations or sync issues are present.
- [not done] `sync` runs a startup-mode check and reports drift.
- [not done] `test` runs `pytest` against `tests/`, which now hosts the relocated policy
- [not done] `install` and `uninstall` delegate to `devcovenant/core/install.py` and
- [not done] `update` supports managed-block-only refreshes and policy-mode control.
- [not done] `normalize-metadata` inserts any missing policy keys with safe placeholders
- [not done] Every managed doc must include `Last Updated` and `Version` headers.
- [not done] `devcovenant/README.md` also includes `DevCovenant Version`, sourced from
- [not done] Every managed doc must include a top-of-file managed block inserted just
- [not done] `AGENTS.md` opens with a concise “operational orientation” outlining the
- [not done] The policy block is the text between
- [not done] Managed documents are generated from YAML assets that supply the full
- [not done] `devcovenant/config.yaml` must support `devcov_core_include` and
- [not done] Config is generated from global defaults plus active profiles and must
- [not done] Config exposes `version.override` so config-driven installs can declare
- [not done] The `global` profile is always active. Other shipped defaults (`docs`,
- [not done] Config should expose global knobs for `paths`, `docs`, `install`,
- [not done] The profile catalog is generated into
- [not done] Custom profiles are declared by adding a profile manifest plus assets
- [not done] Profile assets live under `devcovenant/core/profiles/<name>/assets/` and
- [not done] Policy assets are declared inside policy folders under
- [not done] Template indexes live at `devcovenant/core/profiles/README.md` and
- [not done] Profile assets and policy overlays live in profile manifests at
- [done] A lightweight check wrapper ships as `devcovenant/core/check.py` and can
- [not done] Managed-document templates include stock non-managed text for each

## Policy Requirements
- [not done] Every policy definition includes descriptive prose immediately after the
- [not done] Built-in policies have canonical text stored in
- [not done] Policies declare `profile_scopes` metadata to gate applicability;
- [done] Custom policy `readme-sync` enforces that `devcovenant/README.md` mirrors
- [not done] The policy list is generated from the active profiles/config and includes
- [not done] `apply: false` disables enforcement without removing definitions.
- [not done] Provide a `managed-environment` policy (off by default) that
- [not done] `fiducial` policies remain enforced and always surface their policy text.
- [not done] Selector keys (`include_*`, `exclude_*`, `force_*`, `watch_*`) are supported
- [not done] Policy metadata normalization must be able to add missing keys without
- [not done] Support policy replacement metadata via
- [not done] Record update notices (replacements and new stock policies) in
- [not done] Treat the collective `<!-- DEVCOV-POLICIES:BEGIN -->`/`<!-- DEVCOV-POLICIES:END -->` block as a
- [not done] Generate `devcovenant/registry/local/policy_registry.yaml` dynamically from
- [not done] The legacy `devcovenant/registry.json` storage and the accompanying

## Installation Requirements
- [not done] Install the full DevCovenant toolchain into the target repo, including the
- [not done] Use packaged assets from `devcovenant/core/profiles/` and
- [not done] Install modes: `auto`, `empty`; use mode-specific defaults for docs,
- [not done] When install finds DevCovenant artifacts, it refuses to proceed unless
- [not done] `--disable-policy` sets `apply: false` for listed policy IDs during
- [not done] Update mode defaults to preserving policy blocks and metadata; managed blocks
- [not done] Preserve custom policy scripts and fixers by default on existing installs
- [not done] `AGENTS.md` is always written from the template; if a prior `AGENTS.md`
- [not done] `README.md` keeps user content, receives the standard header, and gains a
- [not done] `SPEC.md` and `PLAN.md` are optional. Existing files get header refreshes;
- [not done] `CHANGELOG.md` and `CONTRIBUTING.md` are always replaced on install
- [not done] `VERSION` is created on demand. Prefer an existing VERSION, otherwise
- [not done] If no license exists, install the GPL-3.0 template with a `Project Version`
- [not done] Regenerate `.gitignore` from global, profile, and OS fragments, then
- [not done] Always back up overwritten or merged files as `*_old.*`, even when
- [not done] Stamp `Last Updated` values using the UTC install date.
- [not done] Support partial doc overwrites via `--docs-include` / `--docs-exclude`, so
- [not done] Support policy update modes via `--policy-mode preserve|append-missing|`
- [not done] Write `devcovenant/registry/local/manifest.json` with the core layout, doc types,
- [not done] Install and update share a unified self-install/self-refresh workflow. Whatever
- [not done] Add a `refresh-all` command that runs `refresh-policies` (defaulting to

## Packaging Requirements
- [not done] Ship `devcovenant` as a pure-Python package with a console script entry.
- [not done] Include profile assets and policy assets in the sdist and wheel.
- [not done] Require Python 3.10+ and declare runtime dependencies in
- [not done] Keep `THIRD_PARTY_LICENSES.md` and `licenses/` synchronized with dependency
- [not done] DevCovenant's own test suites live under `tests/devcovenant/` in the
- [not done] The tests tree mirrors the package layout (core/custom and their profile
- [not done] The `new-modules-need-tests` policy explicitly requires unit tests. The
- [not done] User repos keep an always-on `devcov-exclude` profile that excludes

## Non-Functional Requirements
- [not done] Checks must be fast enough for pre-commit usage on typical repos.
- [not done] Violations must be clear, actionable, and reference the policy source.
- [not done] Install and uninstall operations must be deterministic and reversible.

## Future Direction
- [not done] Version 0.2.7 moves more stock policies onto a metadata-driven DSL surfaced
- [not done] Expect the DSL to replace hard-coded policy metadata (version watching, docs

## Workflow
- Always run `python3 devcovenant/core/run_pre_commit.py --phase start` before editing.
- Run `python3 devcovenant/core/run_tests.py` (which in turn runs `pytest` against
  `tests/` with the mirrored structure).
- Finish with `python3 devcovenant/core/run_pre_commit.py --phase end` to satisfy
  `devflow-run-gates`.
- Flag policy text changes with `updated: true`, run `devcovenant update-policy-registry`, then reset the flag.

## Phase roadmap
1. **Phase 1 – Layout & policy/test mirroring**
   - Move every policy module/adapter into `devcovenant/{core,custom}/policies/<id>`
     with the prescribed subfolders (`adapters/`, `fixers/`, `assets/`).
   - Place policy tests in `tests/devcovenant/...` such that the folder
     hierarchy mirrors `devcovenant/` exactly and does not collide with
     user-owned `tests/` content. Do not ship tests in packages; user repos
     exclude `devcovenant/**` from test enforcement except
     `devcovenant/custom/**`, and create `tests/devcovenant/custom/` only
     when the policy is active. [not done]
   - Keep profile manifests/assets under `devcovenant/{core,custom}/profiles/<name>/assets/`.
   - Update `MANIFEST.in` and `pyproject.toml` so only the core package tree and
     the top-level `tests/` mirror are bundled.
   - Move the previous `tools/` helpers into `devcovenant/core/` and update
    every reference so the CLI, docs, and managed assets point to the in-package
    tooling instead of an external `tools` directory. [done]
   - Move `devcov_check.py` into `devcovenant/core/check.py` and document
     `python3 -m devcovenant.core.check` as the wrapper entry point. [done]
2. **Phase 2 – Profile catalog, config, and overlays**
   - Rebuild `devcovenant/registry/local/profile_catalog.yaml` on every install/update via `profiles.discover_profiles`.
   - Regenerate `devcovenant/config.yaml` so `profiles.active`, `profiles.generated.file_suffixes`, and `autogen_metadata_overrides` always reflect the selected profiles, while preserving `user_metadata_overrides`.
   - Merge gitignore fragments from global+active profiles into `.gitignore` and ensure profile overlays supply `policy_overlays`, dependencies, required commands, and suffix lists.
   - Propagate the configured `version.override` into template assets and policy generation so generated files (e.g., `pyproject.toml`, policy assets) use the same release version.
   - Describe the new `refresh-all` helper that runs `refresh-policies` in preserve mode, updates the policy registry, and rebuilds the profile catalog without a full install/update.
   - Add a default always-on `devcov-exclude` profile for user repos that
     excludes `devcovenant/**` from test enforcement except
     `devcovenant/custom/**`. When `devcov_core_include` is true, skip loading
     `devcov-exclude` so this repo can test core code. [not done]
   - Align docs, policy text, and assets to the `tests/devcovenant/` layout and
     update `new-modules-need-tests` metadata so it only creates/uses
     `tests/devcovenant/` when the policy is active. [not done]
3. **Phase 3 – Policy lifecycle & registry automation**
   - Split the registry into tracked `devcovenant/registry/global/` (stock policy texts, replacements) and gitignored `devcovenant/registry/local/` (policy_registry, manifest, catalog, assets, test status).
   - Ensure `refresh_policies` + `update-policy-registry` populate every policy entry (active or disabled) with metadata handles, profile scopes, asset hints, script hashes, and core/custom flags.
   - Remove enabled/disabled grouping in AGENTS policy blocks and sort all
     policies alphabetically; list all available policies (core/custom) as
     derived from the active profiles/config and mark overrides as
     `custom: true`.
   - Implement policy replacements/notifications: migrating replaced policies to `custom/` with `custom: true`, removing disabled policies, and logging announcements in `manifest.json` while printing notices on update.
   - Support the `freeze` metadata knob that copies policy code/fixers/assets into `devcovenant/custom/` when true and removes them (and the registry entry) when false, rerunning `devcovenant update-policy-registry` each time.
   - Retire the legacy `devcovenant/registry.json` artifact and remove the
     `update_hashes.py` helper so policy hashes live only in the local
     policy registry.
4. **Phase 4 – CLI, engine, and managed-doc compliance**
   - Add the custom `readme-sync` policy with auto-fix to keep
     `devcovenant/README.md` mirrored from `README.md` after removing
     `<!-- REPO-ONLY:BEGIN -->` / `<!-- REPO-ONLY:END -->` blocks. [done]
   - Validate CLI commands (`check`, `sync`, `test`, `update-policy-registry`, `restore-stock-text`, `normalize-metadata`, `install`, `update`, `uninstall`) all behave per SPEC, especially around `apply`, `severity`, `status`, fixers, and adapters.
   - Keep policy fixers language-aware (`fixers/global.py` plus optional `<lang>.py`) and let custom fixers override core ones.
   - Enforce the documentation rules (header with `Version`/`Last Updated`, `<!-- DEVCOV:BEGIN-->` blocks, AGENTS policy block special handling). Document the `policy block` as a managed unit distinct from other blocks.
5. **Phase 5 – Packaging/tests/validation**
   - Keep tests outside the package while shipping them via `MANIFEST.in`; confirm the mirrored `tests/` tree is packaged only in source builds.
   - Run `python3 -m devcovenant update --target .` plus `python3 devcovenant/core/run_tests.py` to validate the updated layout, registry automation, config generation, overlays, and metadata normalization.
   - Ensure `.gitignore` covers the auto-generated registry files and profile-specific tmp artifacts.

## Specification trace
Map SPEC requirements to the phases above:
- Layout & tests (Phase 1) cover the SPEC expectation for `devcovenant/core/<policy>` layout, `tests/` mirroring, and `MANIFEST.in` packaging.
- Profile catalog/config/overlays (Phase 2) fulfill the config, profile, and version override requirements from the Configuration and Extension sections.
- Policy lifecycle (Phase 3) implements the registry split, stock texts, replacements, freeze knob, and managed notifications.
- CLI/engine/docs (Phase 4) ensure the commands, fixers, selectors, and managed doc rules are met.
- Packaging/tests/validation (Phase 5) proves the updates by running `update`, `tests`, and packaging checks.

## Testing and validation
- Use the mirrored `tests/` tree for policy engine tests (`pytest tests/...`).
- After each phase run `python3 -m devcovenant update --target .` to ensure installers pick up the new layout/config/registry.
- Regenerate `devcovenant/registry/local/policy_registry.yaml` and `manifest.json` to confirm the automation works end-to-end.
- Whenever managed docs change, rerun the pre-commit workflow (`devcovenant/core/run_pre_commit.py --phase start/end`) and `devcovenant/core/run_tests.py` to keep the policy pipelines happy.

## Release readiness
- Update `CHANGELOG.md` with every net change under the current version header (no future dates).
- Keep `THIRD_PARTY_LICENSES.md`/`licenses/` aligned when dependencies change.
- Always snapshot the managed docs before release (`*_old.*`) and record packages/assets inside `devcovenant/registry/local/manifest.json` so the update guard rails can verify them later.
- Once Phase 5 passes (tests + update), tag the release and confirm `.github/workflows/publish.yml` still publishes with the expected token.
