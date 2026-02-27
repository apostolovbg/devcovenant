# Profiles
**Last Updated:** 2026-02-27
**Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Responsibilities](#responsibilities)
- [Metadata Population](#metadata-population)
- [Baseline Defaults Profile](#baseline-defaults-profile)
- [Dependency Selector Overlays](#dependency-selector-overlays)
- [Version Sync Overlays](#version-sync-overlays)
- [Manifest Model](#manifest-model)
- [Assets and Hooks](#assets-and-hooks)
- [Translator Ownership](#translator-ownership)
- [Core vs Custom](#core-vs-custom)
- [Workflow](#workflow)

## Overview
Profiles model repository stack shape.
They define metadata overlays, selectors, assets, hook fragments, and optional
translator declarations for language profiles.

Policies are not activated by profiles.
Activation remains config-driven via `policy_state`, with critical-severity
enforcement immunity handled by runtime (not by profiles).

## Responsibilities
Profiles may provide:
- policy metadata overlays
- selector scopes
- file assets and templates
- pre-commit fragments
- translator declarations (language profiles)

Any profile category may contribute policy metadata overlays, including
`devflow-run-gates` test command metadata
(`required_commands`).
Repository profiles can also provide managed-environment metadata
(`expected_paths`, `expected_interpreters`, `manual_commands`,
`managed_commands`, `managed_rerun_commands`).
Global profile overlays own shared runtime-path defaults for gate/session
policies (`gate_status_file`, policy-definition/registry paths, and
pre-commit command metadata).
The global profile also ships managed workflow text assets (for example the
AGENTS workflow contract) so output/polling guidance stays refresh-managed
and consistent across generated docs, including concise operator-update
communication discipline.

Profiles should not embed unrelated business logic.

## Metadata Population
Profiles are the preferred source of operational metadata values when policy
behavior depends on project stack or tooling shape.

Guidelines:
- keep policy descriptor metadata minimal
- define runtime-specific values through `policy_overlays`
- keep value types explicit (`''`, `[]`, `{}` for empty placeholders)
- prefer typed empties; do not use sentinel pseudo-empty tokens such as
  `__none__` in overlays
- profile overlays may use YAML scalar/list/bool values directly; metadata
  resolution preserves a stable string-map form for AGENTS/registry output and
  runtime code consumes the shared typed decoder/view when it needs bool/list/
  number semantics
- use config overlays/overrides only for repository-specific deltas
- when overlays define `documentation-growth-tracking.doc_routes`, ensure
  route-target docs are also included in `user_visible_files` and
  `doc_quality_files`
- route custom policy descriptors explicitly (for example
  `devcovenant/custom/policies/**/*.yaml => devcovenant/docs/policies.md`)
  so documentation-growth checks stay deterministic

Output-sink governance pattern:
- language profiles own sink inventories for
  `no-print-outside-output-runtime` via `sink_call_targets`,
  `sink_attr_targets`, and `sink_macro_targets`.
- repository profiles own enforcement scope and boundary allowances through
  selectors plus `allowed_file_globs`, `allowed_symbol_targets`, and
  `allow_waiver_comment`.

Test-fidelity governance pattern:
- language profiles own `tests-coverage` assertion semantics through
  `assertion_signal_patterns`, `tautology_patterns`, and optional
  `fixture_marker_pattern`.
- language profiles may tune symbol-fidelity controls through
  `symbol_kinds`, `symbol_name_min_length`, `symbol_assertion_window`, and
  `enforce_symbol_fidelity`.
- language profiles own `modules-need-tests` mirror templates via
  `mirror_test_name_templates`; repository profiles own `mirror_roots`.

## Baseline Defaults Profile
`defaults` is the shipped baseline repo-layout profile.
It carries common operational metadata defaults that are useful for many repos,
while `global` stays focused on universal baseline hooks/assets.

Typical `defaults` metadata includes:
- changelog routing/header-window defaults
- version/changelog target defaults
- last-updated document scope defaults
- line-length baseline defaults (`max_length`, URL-prefix escape hatches,
  and generic repo include/exclude selectors)
- test-watch root defaults
- tests-coverage assertion-signal behavior defaults (fixture marker contract)
- generic dependency-license-sync output defaults
- documentation-growth-tracking user-facing suffix defaults (non-doc suffixes)
- generic selector excludes for scope-style policies
  (`docstring-and-comment-coverage`, `name-clarity`, `security-scanner`)

Custom layout patterns:
1. Keep `defaults` active and add local deltas through config overlays.
2. Deactivate `defaults`, copy its manifest into
   `devcovenant/custom/profiles/<name>/<name>.yaml`, rename it, and activate
   your custom profile instead.
3. Keep `defaults` active and add a higher-priority custom profile after it in
   `profiles.active` for additive/replace behavior.

## Dependency Selector Overlays
Dependency metadata is profile-driven:
- `defaults` provides generic output targets for dependency licensing
  (`third_party_file`, `licenses_dir`, `report_heading`).
- language/framework profiles contribute dependency selectors only when those
  profiles are active.
- role selectors are the primary selector contract:
  `dependency_role_files`, `dependency_role_globs`,
  `dependency_role_dirs` using `role=>selector` tokens.
- canonical role names are:
  - `intent`
  - `resolved`
  - `package_manifest`
- selector values may include both manifests and lock/resolution files.
- custom profiles can add repository-specific selectors when needed.
- package-manifest route coverage (for example `pyproject.toml`,
  `MANIFEST.in`, or ecosystem equivalents) should be declared through
  profile-driven `documentation-growth-tracking.doc_routes`.
- for core runtime-contract files such as
  `devcovenant/core/contracts/policy.py`, add explicit `doc_routes`
  mappings to architecture docs.

Custom layout patterns for dependency selectors:
1. Keep `defaults` and active language profiles, then add config overlays.
2. Disable `defaults` and use a custom baseline profile.
3. Add a custom profile later in `profiles.active` to extend/replace selector
   values without changing builtin profiles.

## Version Sync Overlays
`version-sync` metadata is also profile-driven:
- target surfaces are role-based (`target_roles`,
  `target_role_files|globs|dirs` with `role=>selector` entries)
- extractors are mapped per role via `role_extractors`
- `manifest_project_version` is format-aware and should be used for manifest
  roles that may include TOML/JSON/YAML files in mixed repositories
- language profiles should set extractor mappings explicitly instead of
  encoding file-format assumptions in role names

Resolution precedence for version-sync metadata follows the standard metadata
stack:
1. policy descriptor defaults
2. active profile overlays in `profiles.active` order
3. config overlays (`autogen_metadata_overlays`, then
   `user_metadata_overlays`)
4. config overrides (`autogen_metadata_overrides`, then
   `user_metadata_overrides`)

Practical pattern:
1. keep `defaults` for baseline docs/changelog/legal roles
2. add language profile overlays (for example python package manifests)
3. apply user overrides only when you need repo-specific replacement of the
   composed target set

## Manifest Model
Manifest files:
- `devcovenant/builtin/profiles/<name>/<name>.yaml`
- `devcovenant/custom/profiles/<name>/<name>.yaml`

Typical keys:
- `profile`
- `category`
- `suffixes`
- `ignore_dirs`
- optional `gitignore_fragments`
- optional `gitignore_template` (global baseline template)
- optional `governance_template` (global workflow template)
- optional `governance_and_test` (workflow fragment overlay)
- `policy_overlays`
- `assets`
- `pre_commit`
- optional `translators`

Profile-registry validation rules:
- `discover_profiles()` validates manifest template references before profile
  metadata is accepted into the registry
- `assets[*].template`, `gitignore_template`, and `governance_template`
  must resolve to real files under that profile's `assets/` directory
- missing templates fail profile registry build/refresh explicitly instead of
  deferring to later materialization paths

## Assets and Hooks
Asset materialization rules:
- create file when missing
- preserve existing non-one-line file content
- refresh managed blocks where descriptors require
- profile assets do not use per-asset mode flags
- target/template paths must stay inside repo/profile asset roots
- root `.gitignore` is generated, not shipped as profile assets
- `.gitignore` combines global template fragments, per-profile manifest
  fragments (`gitignore_fragments` or `ignore_dirs`), config overlays, and
  preserved user entries
- global template source is
  `devcovenant/builtin/profiles/global/assets/gitignore.yaml`
- global managed-doc assets (for example `AGENTS.yaml` and
  `devcovenant/README.yaml`) carry workflow/help text contract updates such as
  the read-only `check` guidance, required non-lifecycle `gate --mid`
  pre-test workflow wording, gate-owned refresh/autofix wording, and
  artifact-first output/log inspection workflow guidance
- repository profiles can treat `README.md` / `devcovenant/README.md` as
  canonical docs map/start-here entrypoints and avoid materializing
  `devcovenant/docs/README.md`
- AGENTS workflow wording should prefer artifact summaries/tails/logs for
  debugging and caution against verbose streaming token overhead without
  forbidding concise normal-mode streaming
- AGENTS workflow wording should treat concise normal-mode streaming as
  acceptable for progress visibility while keeping official run logs as the
  canonical debug source
- global config template seeds `engine.auto_fix_enabled: false`; repositories
  may override it and profile overlays can seed `true` where desired
- global template includes `.ruff_cache/` to keep Ruff cache noise out of
  managed repositories
- global template ignores `devcovenant/logs/**` runtime artifacts while
  re-including `devcovenant/logs/` and `devcovenant/logs/README.md` so the
  tracked logs skeleton remains visible
- global config template source is
  `devcovenant/builtin/profiles/global/assets/config.yaml`
- config template comments are part of the operator contract and should be
  updated whenever ownership/merge/runtime behavior changes
- global config template defines `engine.output_mode` as human-owned runtime
  output selector (`normal|quiet|verbose`, default `verbose`)
- global config template defines `engine.tests_output_mode` as a separate
  human-owned selector for test-command progress/log output
- global config template defines `engine.pycache_prefix_enabled` and
  `engine.pycache_prefix` for Python bytecode-cache routing via
  `PYTHONPYCACHEPREFIX`; profiles can seed
  `engine.pycache_prefix_enabled: true` when the key is absent
- refresh-generated governance workflow and repo-maintained
  `build.yml`/`publish.yml` workflows can set `PYTHONPYCACHEPREFIX` at job
  scope so fallback `python -m devcovenant ...` launches avoid repo-local
  `__pycache__` drift in CI

Hook rules:
- pre-commit fragments merge into generated `.pre-commit-config.yaml`
- global baseline comes from active profile set and config overrides
- merge order is deterministic:
  1) global baseline
  2) active profiles in `profiles.active` order
  3) `pre_commit.overlays` from config
  4) `pre_commit.overrides` from config (replacement when non-empty)
- the global local `devcovenant` hook uses `language: system` so it executes
  in the caller environment (including managed-environment interpreter reruns)
  instead of an isolated pre-commit hook virtualenv

Governance workflow rules:
- `governance-and-test.yml` is generated on refresh
- global baseline comes from `governance_template`
- active profile `governance_and_test` fragments are merged in activation order
- config applies `governance_and_test.overlays`, then
  `governance_and_test.overrides` as full replacement when non-empty
- in the DevCovenant repository, the tracked
  `.github/workflows/governance-and-test.yml` is refresh-generated output
  derived from the global asset baseline and must stay aligned on critical CI
  contract behavior (for example `PYTHONPYCACHEPREFIX` job env and the
  `gate --start` -> `test` -> `gate --end` command sequence)

Test-command metadata rules:
- profiles may add command chains under `devflow-run-gates` using
  `required_commands`
- resolved command list is consumed by `devcovenant test`
- command order is preserved from resolved metadata
- profiles may provide `managed-environment` stage commands using
  `managed_commands` entries (`stage=>command`) and human guidance through
  `manual_commands`
- profiles may provide wrapper rerun adapters through
  `managed_rerun_commands` (`stage=>command`) for bench/xenv launchers
- valid managed command stages are:
  `start`, `test`, `end`, `command`, and `all`
- command placeholders may use:
  `{repo_root}`, `{managed_python}`, `{managed_bin}`, `{managed_root}`,
  `{command}`, `{command_name}`, `{command_args}`, `{command_argv}`,
  `{command_string}`
- profile metadata can target bench-style environments by setting
  `expected_paths`/`expected_interpreters` to bench env locations and using
  stage commands for bench-specific bootstrap/install flows
- `global` profile metadata excludes `devcovenant/config.yaml` from
  changelog-coverage file requirements and documentation-growth trigger scope
  so human config edits can be made without changelog/doc-route formalities
- `global` config template seeds `ignore.patterns` with
  `devcovenant/config.yaml` so gate-session scope and unsessioned-edit checks
  ignore config-only edits by default
- `global` config template also seeds `engine.logs_keep_last: 0`
  (unlimited run-log retention) unless a repository sets a positive keep
  count in its local `devcovenant/config.yaml`
- `defaults` profile seeds a broad `changelog-coverage.summary_verbs`
  vocabulary so changelog entries can use natural action wording (for example
  `make`/`made`, `review`/`reviewed`, `complete`/`completed`) without ad-hoc
  profile customization

Documentation profile scope rule:
- `docs` profile provides docs-focused line-length includes
- `docs` profile does not mark `.md`, `.rst`, or `.txt` as
  documentation-growth-tracking user-facing scope by default

## Translator Ownership
Only language profiles may declare translators.
Framework/ops/tooling profiles do not select translators directly.
Documentation routes for translators may use
`devcovenant/*/profiles/*/*_translator.py` to cover both builtin and custom
language profile translators with one selector.

Translator runtime resolves candidates by extension from active language
profiles and enforces no-match / ambiguous-match behavior.

### Test Event Adapters
Language profiles can register test-event adapters through the `test_events`
metadata block. Each entry must provide:
- `id`: normalized identifier for the adapter
- `entrypoint`: `<module>:<callable>` factory that returns a
  `TestEventAdapter` instance
- `config`: optional mapping passed to the adapter factory for runtime
  configuration

Adapters load through `devcovenant/core/services/event.py`, so any command
run by `devcovenant test` can emit schema-version `1.0` events (from
`EVENT_SCHEMA_VERSION`) and record them into `gate_status.json` for tooling
that consumes the normalized lifecycle.

The builtin Python profile ships with a `test_events` entry that points to
`devcovenant.core.services.event:python_test_event_adapter_factory`.

## Builtin vs Custom
Builtin profiles are shipped defaults.
Custom profiles are repository-owned and override same-name builtin profiles.

Custom profile precedence is path-based and deterministic.

## Workflow
1. Update profile manifest/assets.
2. Refresh to rebuild generated state.
3. Update tests for behavior changes.
4. Update `PROFILE_MAP.md` when inventory or contracts change.
5. Run full gate sequence.
6. Respect AGENTS hard-stop flow: run start before edits and clear
   DevCovenant complaints before continuing implementation.
