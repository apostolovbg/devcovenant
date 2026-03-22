# Profiles
**Last Updated:** 2026-03-22
**Project Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Responsibilities](#responsibilities)
- [Repository Custom Profiles](#repository-custom-profiles)
- [Metadata Population](#metadata-population)
- [Baseline Defaults Profile](#baseline-defaults-profile)
- [Dependency Selector Overlays](#dependency-selector-overlays)
- [Version And Project Governance \
  Overlays](#version-and-project-governance-overlays)
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

The practical way to think about profiles is:
- profiles describe what kind of repo you have
- config decides which of those profile-provided behaviors are active
- policies enforce the resulting contract

Most users do not need to author a custom profile on day one.
For many repos, choosing the right `profiles.active` stack is enough.
This is the primary home for profile shape, assets, hooks, and translator
ownership. Use `devcovenant/docs/config.md` for selecting the active stack
in one repository and `devcovenant/docs/policies.md` for policy behavior.

## Responsibilities
Profiles may provide:
- policy metadata overlays
- selector scopes
- file assets and templates
- pre-commit fragments
- translator declarations (language profiles)

Profile assets should stay reusable.
When an asset needs repository identity, prefer placeholders resolved from
`project-governance` (for example `{{ PROJECT_NAME }}` and
`{{ PROJECT_DESCRIPTION }}`) instead of repo-specific duplicate templates.

Shipped builtin language profiles include:
- `python`, `javascript`, `typescript`, `java`, `go`, `rust`, `opencl`,
  `csharp`, `php`, `ruby`, `dart`, `swift`, `objective_c`, `sql`
Builtin profiles are the only shipped profile authority in `1.0.0+`.
Profile manifests, assets, and translators now live only under
`devcovenant/builtin/profiles/**` plus repo-owned `devcovenant/custom/**`.

Any profile category may contribute policy metadata overlays, including
`devflow-run-gates` test command metadata
(`required_commands`).
Repository profiles can also provide managed-environment metadata
(`expected_paths`, `expected_interpreters`, `manual_commands`,
`managed_commands`).
Global profile overlays own shared runtime-path defaults for gate/session
policies (`gate_status_file`, policy-definition/registry paths, and
pre-commit command metadata).
The global profile also ships managed workflow text assets (for example the
AGENTS workflow contract) so output/polling guidance stays refresh-managed
and consistent across generated docs, including concise operator-update
communication discipline.
The same global asset stack also seeds the initial install baseline in
`devcovenant/config.yaml`, including `developer_mode: false` for normal
user-repo scope and `install.config_reviewed: false` so `deploy` stays
blocked until a human completes the first config review.
Those shipped config comments are meant to explain the first integration
story in practical terms: empty-repo install, seeded-doc install, and
existing-repo install all stop at the same human config-review checkpoint
before `deploy` activates the reviewed contract.
That baseline is meant for ordinary repos using DevCovenant as a tool; this
repository flips `developer_mode` to `true` because it is used to develop
DevCovenant itself.
That same AGENTS asset now also carries the question-only prompt stop rule in
both `THE DEV COVENANT` and `Execution Order`, so repos inherit the `?`
branch explicitly instead of relying on buried workflow prose.
It also owns the universal ignore/gitignore baseline for editor, packaging,
coverage, and DevCovenant runtime artifacts so repos do not need to rediscover
common exclusions such as `.vscode/**`, `.idea/**`, `*.egg-info/**`,
`pip-wheel-metadata/**`, `.coverage*`, `devcovenant/logs/**`, and
`devcovenant/registry/runtime/**`.

Profiles should not embed unrelated business logic.

## Repository Custom Profiles
This repository includes custom profiles for dogfooding and reusable examples.
Those payload directories are repository-owned and are not packaged as
distribution inventory for user repositories.

Create a custom profile when you need repo-specific reusable behavior such as:
- custom managed docs
- recurring path selectors
- custom policy metadata overlays
- repo-specific pre-commit fragments or assets

Do not create a custom profile just to flip one boolean once; simple
repository-local changes usually belong in `devcovenant/config.yaml`.

Current repo-local example:
- `restapi`: API (application programming interface) governance overlays for
  endpoint-heavy repositories.
  It tightens `documentation-growth-tracking` with API/OpenAPI
  (OpenAPI Specification) `doc_routes`,
  hardens `security-scanner` and test policies with API path force-includes,
  keeps `no-raw-errors` broad-handler control explicit through
  `DEVCOV_ALLOW_BROAD_ONCE`, and can seed `docs/api.md`, `docs/auth.md`,
  and `docs/errors.md` through profile assets.

## Metadata Population
Profiles are the preferred source of operational metadata values when policy
behavior depends on project stack or tooling shape.

Guidelines:
- keep policy descriptor metadata minimal
- put ubiquitous filesystem noise in the `global` baseline (`ignore.patterns`
  and generated `.gitignore`), not in repo-local overlays
- put disposable build/cache defaults in profile `clean_overlays`, not in
  policy descriptors
- let profile `clean_overlays` declare runtime-registry and log cleanup
  targets too, so `clean --registry` and `clean --logs` stay profile-driven
- keep generated `clean.overrides` defaults empty (`{}`) and use explicit
  per-key `[]` overrides only when you intentionally want to clear inherited
  cleanup lists for that one key
- reserve repo-local overlays/config for genuinely repository-specific
  exclusions
- define runtime-specific values through `policy_overlays`
- define stack-specific cleanup targets through `clean_overlays`
- keep value types explicit (`''`, `[]`, `{}` for empty placeholders)
- prefer typed empties; do not use sentinel pseudo-empty tokens such as
  `__none__` in overlays
- profile overlays may use YAML (YAML Ain't Markup Language)
  scalar/list/bool values directly; metadata resolution preserves a stable
  string-map form for AGENTS/registry output and runtime code consumes the
  shared typed decoder/view when it needs bool/list/number semantics
- use config overlays/overrides only for repository-specific deltas
- treat config overrides as destructive replacement, not additive merge;
  refresh records override-replacement warnings and per-key resolution trace
  in `devcovenant/registry/registry.yaml` so repos can audit why one value won
- when overlays define `documentation-growth-tracking.doc_routes`, ensure
  route-target docs are also included in `user_visible_files` and
  `doc_quality_files`
- route tracked registry changes explicitly (for example
  `devcovenant/registry/registry.yaml => devcovenant/docs/registry.md`) so
  the tracked registry contract stays documented when registry structure
  changes
- route custom policy descriptors explicitly (for example
  `devcovenant/custom/policies/**/*.yaml => devcovenant/docs/policies.md`)
  so documentation-growth checks stay deterministic
- prefer one primary-home route per code area; touch a second doc only when
  the behavior genuinely spans both surfaces instead of using doc routes to
  enforce duplicate explanation

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
- repository profiles may exclude internal non-user-facing helper surfaces
  from `tests-coverage` and `documentation-growth-tracking` while still
  keeping those files inside `modules-need-tests` structural mirror
  enforcement.

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
  Current shipped defaults set `allow_long_url_lines: true` and
  `allow_long_lines: true` so marker-based escape hatches work without
  per-repo override boilerplate.
- test-watch root defaults
- tests-coverage assertion-signal behavior defaults (fixture marker contract)
- generic dependency-license-sync output defaults
- documentation-growth-tracking user-facing suffix defaults (non-doc suffixes)
- generic selector excludes for scope-style policies
  (`docstring-and-comment-coverage`, `name-clarity`, `security-scanner`,
  `no-raw-errors`)
- no-raw-errors strict defaults for broad handlers with explicit waiver
  channels (`forbid_broad_exception_handlers`,
  `broad_exception_waiver_markers`, `broad_exception_waiver_between`)
- managed-environment bootstrap defaults
  (`expected_paths`, `expected_interpreters`, and baseline `manual_commands`)

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

## Version And Project Governance Overlays
Versioning metadata stays policy-driven, while project-governance defaults are
profile-driven through the dedicated config section:
- `global` seeds the top-level `project-governance` config block with a
  generic unversioned baseline (`prototype`, `experimental`, `unversioned`)
  so fresh installs do not invent fake numbered versions
- `global` seeds `policy_state.version-governance: false` in the generated
  config template so version-governance stays an explicit opt-in.
- `global` doc assets also define the managed-doc adoption contract used
  during first install/deploy, where compatible pre-authored docs such as
  `SPEC.md`, `README.md`, and `PLAN.md` can be imported as seed content
  instead of being overwritten.
- the shipped README assets should also document the project-governance
  service and point operators at `devcovenant/docs/project_governance.md`
  when lifecycle metadata behavior changes.
- in this repository, the authored README source remains `README.md`, while
  `readme-sync` derives `devcovenant/README.md` by removing repo-only blocks
  for the packaged guide.
- `defaults` seeds `version-governance` with shared path, ordering, and
  scheme-governance controls: `version_file`, `changelog_file`,
  `changelog_header_prefix`, `enforce_bumping`,
  `canonical_versions_required`, and the default
  PEP (Python Enhancement Proposal) 440 marker toggles.
- repositories should choose `version-governance.scheme` explicitly in an
  active profile or repo config; repo-specific profiles may also add
  scheme-specific keys such as `semver_scope_tags_required`.
- repositories that want Python-package-native versioning may set
  `version-governance.scheme` to `pep440` without changing the surrounding
  framework contract.
- repositories with format-only custom version strings may switch to
  `scheme: custom_regex`, provide `custom_regex_pattern`, and keep
  `enforce_bumping: false`.
- repositories with fully custom ordering rules may switch to
  `scheme: custom_adapter` and point `custom_adapter_path` at one
  repo-relative Python module exporting `SCHEME`.
- `defaults` also seeds `project-governance` with allowed stage/stance
  vocabularies plus the generic unversioned display defaults
  (`Unversioned`, `## Unreleased`)
- repositories may configure `project-governance` with or without
  `version-governance`; the service is about lifecycle state, not version
  parsing
- managed-doc descriptors can opt into richer governance header lines with
  `project_governance_headers: true`; AGENTS still gets its dedicated
  post-workflow governance section from the AGENTS-specific refresh path,
  while ordinary managed docs stay on the compact header set
- repository profiles may redirect only the repo-specific surfaces they own;
  for example, a repository profile may override
  `version-governance.version_file` to a package-scoped path such as
  `devcovenant/VERSION`.

`version-sync` metadata is also profile-driven:
- target surfaces are role-based (`target_roles`,
  `target_role_files|globs|dirs` with `role=>selector` entries)
- extractors are mapped per role via `role_extractors`
- optional ecosystem legality is mapped per role via
  `role_legality_schemes`
- docs roles, and any repo that opts legal text into version-sync, should
  usually use `project_version_line`
- `manifest_project_version` is format-aware and should be used for manifest
  roles that may include TOML (Tom's Obvious, Minimal Language)/JSON
  (JavaScript Object Notation)/YAML (YAML Ain't Markup Language) files in
  mixed repositories
- Python profiles now also seed `package_manifest=>pep440` legality so
  `pyproject.toml` stays packaging-legal even when repo-level equality runs
  under another governed scheme
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
1. keep `defaults` for baseline `version-governance` and `version-sync`
   metadata
2. add language profile overlays (for example python package manifests)
3. apply repository-profile overlays for repo-owned paths such as custom
   `version_file` locations
4. apply user overrides only when you need repo-specific replacement of the
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
- optional `clean_overlays`
- `clean_overlays` may contribute build, cache, runtime-registry, and log
  cleanup selectors while leaving tracked files protected
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
- managed-doc descriptors must follow an explicit key schema in order:
  `title`, `target_path`, `doc_id`, `doc_type`, `project_version`,
  `last_updated`, `devcovenant_version`, optional managed-doc booleans,
  optional `legacy_generic_body_fingerprints`, `managed_block`, `body`,
  optional `workflow_block`
- `project_version`, `last_updated`, and `devcovenant_version` must be
  booleans; `devcovenant_version` must be `true`
- managed-doc booleans currently cover shared doc-engine behavior such as
  `project_governance_headers`, `import_seed`, and `authoritative_source`
- `legacy_generic_body_fingerprints` is optional and lists exact body-only
  SHA-256 fingerprints for known old generic scaffolds that refresh may
  replace during upgrade or refresh
- descriptors may live under the global asset root or an active profile
  `assets/` tree; add the document path to `doc_assets.autogen` to activate
  that managed doc for one repo
- omitting a builtin doc from `doc_assets.autogen` turns that managed doc off
  for the repo while leaving `AGENTS.md` mandatory
- AGENTS multi-block workflow/policy rendering is intentionally not a generic
  managed-doc descriptor feature
- generic-scaffold replacement is exact, not heuristic: refresh strips the
  generated headers and first managed block, fingerprints the remaining body,
  and replaces the doc only when that body fingerprint matches one of the
  descriptor's declared legacy generic fingerprints
- multiline `managed_block`, `body`, and `workflow_block` values must use
  YAML literal block style (`|-`/`|`), not quoted multiline scalars
- descriptor schema/style violations fail refresh explicitly with file+field
  guidance
- `<!-- DEVCOV-USER-PRESERVE:BEGIN -->` /
  `<!-- DEVCOV-USER-PRESERVE:END -->` blocks are preserved during refresh
  anywhere in managed docs (including top-of-file and inside managed blocks)
- profile `assets:` manifest entries still describe ordinary materialized
  files; managed-doc descriptors under `assets/` are discovered by the
  managed-doc service instead of the profile asset-copy path
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
- global managed-doc assets under
  `devcovenant/builtin/profiles/global/assets/` now use doc-type-specific
  DevCovenant intro text instead of one generic "Read first" message
- `CONTRIBUTING.yaml` keeps the standard DevCovenant workflow inside the
  managed block and leaves repository notes below `<!-- DEVCOV:END -->`
- repository profiles can treat `README.md` as the authored docs-map/start-
  here entrypoint and `devcovenant/README.md` as the packaged projection when
  they want one maintained README source plus a repo-only-pruned user guide
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
- global config template comments include the required edit-session gate flow
  (`gate --start` -> `gate --mid` -> `test` -> `gate --end`) and concise mode
  semantics for `engine.output_mode` and `engine.tests_output_mode`
- global config template defines `engine.output_mode` as human-owned runtime
  output selector (`normal|quiet|verbose`, default `verbose`)
- global config template defines `engine.tests_output_mode` as a separate
  human-owned selector for test-command progress/log output
- global config template defines `engine.pycache_prefix_enabled` and
  `engine.pycache_prefix` for Python bytecode-cache routing via
  `PYTHONPYCACHEPREFIX`; refresh can seed explicit
  `engine.pycache_prefix_enabled: true` for repo profiles that require it
- refresh-generated governance workflow and repo-maintained
  `build.yml`/`publish.yml` workflows can set `PYTHONPYCACHEPREFIX` at job
  scope (DevCovenant uses `.gha-pycache`) for managed child commands and
  stable CI (continuous integration) behavior; source-checkout
  `python -m devcovenant ...` launches
  now suppress Python cache-file writes for the launcher process directly and
  clean the package-import cache on exit so source repos stay free of
  `__pycache__/` drift
- the global `README.yaml` asset intentionally leaves the root `README.md`
  managed note blank; repo-specific authored README content remains outside
  managed regions unless the file is missing, empty, or one line only
- the global `PLAN.yaml` and `SPEC.yaml` assets keep explicit managed
  identity blocks; only the root `README.md` intentionally uses an empty
  managed block

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
- when resolved managed interpreter paths are non-executable, runtime surfaces
  an explicit managed-environment error and stops so the environment
  contract can be fixed directly
- valid managed command stages are:
  `start`, `test`, `end`, `command`, and `all`
- command placeholders may use:
  `{repo_root}`, `{managed_python}`, `{managed_bin}`, and `{managed_root}`
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
- `defaults` profile also seeds managed-environment path defaults
  (`.venv`, `.venv/bin/python`, `.venv/Scripts/python.exe`) so enabling
  `managed-environment` starts from explicit path ownership instead of empty
  metadata
- `devcovuser` narrows force-include selectors for
  `docstring-and-comment-coverage`, `name-clarity`, `security-scanner`,
  `no-raw-errors`, and `modules-need-tests` to custom Python files
  (`devcovenant/custom/**/*.py`) so custom README docs are not misclassified
  as code modules

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
There is no hidden generic adapter path in runtime anymore. If a repo
wants generic command coverage, a profile must declare
`devcovenant.core.services.event:generic_test_event_adapter_factory`
explicitly; otherwise unmatched test commands are skipped.

## Builtin vs Custom
Builtin profiles are shipped defaults.
Custom profiles are repository-owned and override same-name builtin profiles.
Package builds ship custom scaffolding files (`README.md`, `__init__.py`)
but do not ship repository-owned custom payload directories.
Upgrade/install replacement preserves existing repository custom payload
directories under `devcovenant/custom/profiles/*` and
`devcovenant/custom/policies/*`.

Custom profile precedence is path-based and deterministic.

## Workflow
Use this document when the change is about profile-supplied metadata, assets,
hooks, or custom profile structure.
For the exact gate sequence, use `devcovenant/docs/workflow.md`.

Profile-change loop:
1. Update profile manifest/assets.
2. Refresh to rebuild generated state.
3. Update tests for behavior changes.
4. Update `PROFILE_MAP.md` when inventory or contracts change.
5. Run the normal gate workflow from `devcovenant/docs/workflow.md`.
