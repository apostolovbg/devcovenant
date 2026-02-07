# DevCovenant Development Plan
**Last Updated:** 2026-02-07
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** PLAN
**Doc Type:** plan
**Managed By:** DevCovenant
<!-- DEVCOV:END -->

The goal of this plan is to walk through the remaining work required to
fully satisfy the specification in `SPEC.md`. The specification itself is
our single source of truth; this plan tracks every outstanding SPEC item,
orders them by dependency, and highlights what is already done so we do not
duplicate effort.

Every completed item is explicitly marked with `[done]` in the section where
it appears. Items that remain work-in-progress keep the `[not done]` marker
so reviewers immediately see what still blocks a release. When a bullet
moves to `[done]`, update the description so the plan stays an accurate
trace.

## Table of Contents
1. [Overview](#overview)
2. [Spec compliance summary](#spec-compliance-summary)
3. [Outstanding work (dependency order)](#outstanding-work-dependency-order)
4. [Execution notes](#execution-notes)
5. [Testing and validation](#testing-and-validation)
6. [Release readiness](#release-readiness)

## Overview
- Treat `SPEC.md` as the authoritative specification and keep this plan in
  sync with every SPEC requirement.
- Mirror the `devcovenant/` structure under `tests/` as mandated by SPEC, but
  keep the runtime suites under `tests/devcovenant/` so they can remain
  outside the installable package.
- Drive configuration, registries, and managed docs from profile metadata so
  all knobs, selectors, and assets flow from the active profiles.
- Install/deploy/update/upgrade/refresh follow the lifecycle model: `install`
  writes a generic config stub, `deploy` activates docs/assets, `update`
  refreshes managed content without touching core files, `upgrade` explicitly
  replaces core files, and `refresh` is registry-only. `undeploy` removes
  managed blocks while keeping core + config; `uninstall` removes everything.
- Documentation defaults to `devcovenant --help` examples while mentioning
  `python3 -m devcovenant --help` once per doc as the fallback.

## Spec compliance summary
This section enumerates each major SPEC chapter with its completion status.
It is the checklist we consult before declaring the spec satisfied.

### Workflow
- [done] Gated workflow: `pre-commit start`, tests (`pytest` +
  `python3 -m unittest discover`), and `pre-commit end` are required for every
  change.
- Clarify that the start gate only needs to execute before edits; it may detect
  outstanding violations and does not have to leave a clean tree.
- Start recorded after edits now yields a warning (with a brief pause) instead
  of blocking, but a clean `start → tests → end` run is still required to
  clear the gate.
- [done] Startup check (`python3 -m devcovenant check --mode startup`).
- [done] Policy edits run `devcovenant update-policy-registry` after updating
  scripts/tests so hashes stay aligned.
- [done] Every change gets logged into `CHANGELOG.md`.
  Record it under the current version entry.

### Functional requirements
- [done] Emit resolved policy metadata (policy defaults → profile overlays
  → config overrides) into AGENTS and the policy registry for every policy.
  Include every common key and policy-specific key (even when empty), keep the
  policy list alphabetical, and manage the policy block so users never edit it
  directly.
- [done] Follow the policy module/adapters/fixer loading rules described
  in SPEC.
- [done] Respect `enabled`, `severity`, `status`, and `enforcement` metadata.
  Apply those settings across all policies.
- [done] Collapse execution into two modes: `audit` (no auto-fix) and `fix`
  (auto-fix permitted). Both share the same policy set and exit non-zero on
  blocking violations or sync issues.
- [done] Provide both `devcovenant` console entry and `python3 -m devcovenant`
  module entry, with docs defaulting to the console path.
- [done] `test` runs `pytest` + `python3 -m unittest discover` while respecting
  the `tests/devcovenant/` layout and keeping those suites out of packages.
- [done] `check` exits non-zero when blocking violations exist (audit/fix
  modes).
- [done] Metadata normalization handled by refresh/update; no separate
  `normalize-metadata` command needed.
- [done] `refresh-all` regenerates `.gitignore` from profile fragments while
  preserving any user-provided entries.
- [done] `refresh-all` rebuilds registries/metadata without touching managed
  docs; doc syncing moves to install/update or a docs refresh path.
- [done] CLI emits stage banners and status steps (registry refresh, engine
  init, command execution) for traceable runs without flooding output.
- [done] Lifecycle commands match SPEC: `install` writes a generic config
  stub (guarded by `install.generic_config`), `deploy` activates docs/assets,
  `update` refreshes managed content without core changes, `upgrade`
  replaces core explicitly, `refresh` is registry-only, `undeploy` removes
  managed blocks, and `uninstall` removes the core footprint.
- [done] Backups are opt-in via `--backup-existing`; default runs overwrite
  files in-place without creating `*_old.*` copies.
- [done] Version tracking defaults live in profiles: `global` points at
  `VERSION` plus the core doc set, while `devcovrepo` overrides the
  version file to `devcovenant/VERSION`.
- [not done] Every managed doc must include `Last Updated`/`Version` headers.
  Ensure each file also has top-of-file managed blocks.
  Include `Doc ID`, `Doc Type`, and owner metadata in those blocks.
- [not done] Documentation examples and running instructions mention `python3`.
  Mention the module entry whenever you discuss source-based usage.
- [not done] `devcovenant/README.md` includes the packaged
  `DevCovenant Version` value.
- [done] Managed documents are generated from YAML assets.
  Inject stock non-managed text only when the target doc is missing, empty, or
  a single-line placeholder.
  Otherwise install/update commands refresh just the managed blocks while
  handling the `<!-- DEVCOV-POLICIES -->` block separately.

### Policy requirements
- [done] Policy metadata normalization emits a single resolved metadata
  map (no schema/value split) while keeping existing policy text intact.
- [done] `changelog-coverage` enforces one fresh entry per change (dated
  today, Change/Why/Impact summary lines each containing an action verb,
  `Files:` block listing only touched paths) and keeps entries newest-first.
- [done] Runtime state lives under `devcovenant/registry/local`; the legacy
  `.devcov-state` directory is removed.
- [done] Ship `devcovenant/docs/` as user-facing guides in the package.
- [done] `dependency-license-sync` uses profile/config overlays to supply
  dependency manifests; the core policy metadata stays general and the
  devcovrepo profile declares DevCovenant’s dependency files.
- [done] Built-in policies have canonical text in
  `devcovenant/registry/global/stock_policy_texts.yaml`.
- [done] Custom policy `readme-sync` enforces the README mirroring
  and repo-only block stripping.
- [done] Consolidated `devcov-parity-guard`, `devcov-self-enforcement`,
  `policy-text-presence`, and `track-test-status` into
  `devcov-integrity-guard`, which now owns policy prose checks, descriptor
  parity, registry sync, and optional watched-file status validation.
- [done] Policy replacement metadata from
  `devcovenant/registry/global/policy_replacements.yaml` is applied.
  Replaced policies move to `custom/` with `custom: true` and are marked
  deprecated when enabled.
- [not done] The collective `<!-- DEVCOV-POLICIES:BEGIN -->`/
  `<!-- DEVCOV-POLICIES:END -->` block is treated as a managed unit and
  refreshed from assets. A per-policy `freeze` override copies scripts to
  `devcovenant/custom/` and reruns `devcovenant update-policy-registry` when
  toggled.
- [done] `devcovenant/registry/local/policy_registry.yaml` is the
  sole hash store. The legacy `registry.json` and `update_hashes.py` helper
  have been retired and removed; the registry now records hashes, asset
  hints, profile scopes, core/custom origins, and resolved metadata.
- [done] Record update notices (replacements/new stock policies) inside
  `devcovenant/registry/local/manifest.json` and print them during updates.
- [done] `managed-environment` remains off by default via policy metadata
  (`enabled: false`). When enabled, it warns if required metadata or
  command hints are absent.
- [done] Dogfood-only policies (`patches-txt-sync`, `gcv-script-naming`,
  `security-compliance-notes`) are removed from the DevCovenant repo.
- [done] Reduced the stock profile registry to a slim, maintained set
  (global, docs, data, suffixes, python, javascript, typescript, java, go,
  rust, php, ruby, csharp, sql, docker, terraform, kubernetes, fastapi,
  frappe, dart, flutter, swift, objective-c) and updated
  PROFILE_MAP/POLICY_MAP/SPEC to describe the change. Retired stacks are to be
  reintroduced only as custom profiles.
- [done] Materialize expanded POLICY_MAP/PROFILE_MAP expectations: ensure
  profiles/policies/assets/adapters/fixers match the reference maps and keep
  the maps authoritative for future additions.
- [done] Align POLICY_MAP coverage with retained profiles: add fastapi,
  frappe, objective-c, and sql where supported (dependency-license-sync,
  docstring-and-comment-coverage, name-clarity, new-modules-need-tests,
  security-scanner, documentation-growth-tracking, line-length-limit,
  version-sync) and trim deprecated stacks (kotlin/scala/groovy/dotnet/
  fsharp/elixir/erlang/haskell/clojure/julia/ocaml/crystal/ansible).
- [done] Per-profile descriptors (`<profile>.yaml`) must be populated manually
  (maps are reference only); stubs have been fleshed out with real assets and
  overlays for the retained registry.
- [not done] Remove profile-first policy activation and scope semantics.
  Policies must activate from config-only `policy_state`, while profiles stay
  explicit metadata/assets providers (no inheritance, no activation logic).

### Policy metadata redesign
- [not done] Immediate redesign: remove policy/profile scope keys entirely,
  make config activation authoritative via `policy_state`, and keep metadata
  resolution as policy defaults -> profile overlays -> user overrides.
  During migration, preserve current enabled/disabled outcomes in the
  generated config state map.
- [done] Define per-policy YAML descriptors that include the managed
  prose, selector metadata, and a `metadata` block whose keys describe the
  schema while also supplying the baseline values that feed into AGENTS and
  the registry. The canonical schema no longer lives in a separate
  hand-written file; it is inferred from the keys declared inside each
  policy’s `metadata`.
- [not done] Keep provenance (`core` vs. `custom`) for origin reporting only.
  Remove scope keys entirely and derive `enabled` strictly from config
  `policy_state`; generator still records final `enabled`/`freeze`/`severity`
  after metadata overrides resolve.
- [not done] Replace `autogen_disable` and `manual_force_enable` with a single
  config activation map (`policy_state`) that controls all core/custom
  policies uniformly. Keep `freeze_core_policies` and
  `user_metadata_overrides`; metadata merge remains policy defaults -> profile
  overlays -> user overrides.
- [done] Record every policy in
  `devcovenant/registry/local/policy_registry.yaml` with a single resolved
  metadata map (no schema/value split). The generator and AGENTS templating
  read from that unified source so enforcement always matches the registry.
- [done] Render resolved policy metadata in AGENTS using vertical YAML-style
  key/value lines, with multi-value metadata emitted on continuation lines.
- [done] When DevCovenant removes a core policy, copy it into
  `devcovenant/custom/policies/` (or a frozen overlay prescribed in config),
  mark the new entry as `custom`, and rerun `update-policy-registry` so all
  downstream artifacts report the deprecation rather than leaving dangling IDs.
- [not done] Keep `raw-string-escapes` and `devcov-raw-string-escapes`, but
  control both via config `policy_state` (no scope keys, no autogen disable
  list).

### Installation & documentation
- [done] Implement the lifecycle commands per SPEC: `install`, `deploy`,
  `update`, `upgrade`, `refresh`, `undeploy`, and `uninstall`.
- [done] `install` always runs, writes a generic config stub (flagged by
  `install.generic_config`), and prompts to `upgrade` when a newer core
  exists (never deploys docs/assets).
- [done] `deploy` requires a non-generic config and materializes managed
  docs/assets/registries, then runs `refresh`.
- [done] `update` refreshes managed content without touching core files.
- [done] `upgrade` replaces core files and applies policy replacements,
  then runs `update`.
- [done] `refresh` is registry-only and runs inside deploy/update.
- [done] `undeploy` removes managed blocks/registries while keeping core.
- [done] `uninstall` removes DevCovenant core plus managed blocks.
- [not done] `reset-to-stock` restores stock metadata/profile configuration
  after the lifecycle work stabilizes.
- [not done] `update` regenerates policy blocks from descriptors plus
  overrides (no manual edits) without requiring extra CLI flags.
- [done] Introduce a registry-only refresh mode that regenerates
  `devcovenant/registry/local/*` (hashes, manifest, resolved metadata) and
  re-materializes `config.yaml` only when missing, while skipping AGENTS and
  managed docs. Run this registry-only refresh automatically at the start of
  every devcovenant invocation (including CI) so state is rebuilt without
  dirtying working trees. Policy blocks are fully managed by refresh.
- [done] `refresh-all` now refreshes config autogen sections (profiles block,
  core paths, and metadata overlays) while preserving user overrides.
- [not done] `AGENTS.md` always regenerates from the managed template and
  resolved metadata. Preserve the `# EDITABLE SECTION` text when it already
  exists; never allow manual edits in the policy block.
- [not done] `README.md`, `SPEC.md`, `PLAN.md`, `CHANGELOG.md`, and
  `CONTRIBUTING.md` sync from YAML assets with new managed blocks.
- [not done] `SPEC.md`/`PLAN.md` rebuild when missing.
  Keep user edits otherwise.
- [not done] `deploy`/`update` regenerate only managed doc headers and
  managed blocks (UTC dates) while preserving user content outside those
  blocks; `refresh` skips docs entirely.
- [not done] Version file creation prefers an existing configured version
  file (default `VERSION`, devcovrepo override), then `pyproject.toml`.
  Prompt (default `0.0.1`). `--version` overrides detection.
- [not done] `LICENSE` falls back to the GPL-3.0 template when missing.
- [not done] `.gitignore` is rebuilt from fragments while merging user entries.
- [not done] Every managed doc gets its `Last Updated` header stamped in UTC.
- [done] `devcovenant/config.yaml` is generated only when missing; autogen
  sections are marked and refreshed while user overrides stay intact so
  installs from existing configs remain possible. Keep the repo’s tracked
  config available for CI, but exclude it from built artifacts via
  `MANIFEST.in` so packages do not ship the repo config.
- [not done] Config exposes `devcov_core_include`, `devcov_core_paths`, and
  `doc_assets` with `profiles.generated.file_suffixes`.
- [not done] Profile and policy assets live under `core/` and `custom/`.
  Registry entries go to `devcovenant/registry/local/profile_registry.yaml`.
  Policy asset entries are read directly from policy descriptors.
- [done] Profile-driven pre-commit config turns profile YAML fragments into
  the generated hook set (global owns the DevCovenant hook baseline, no
  user-managed `.pre-commit-config.yaml`), applies profile exclusions, and
  documents the “Pre-commit config refactor” phase.
- [done] Ensure the custom `devcovrepo` profile treats `devcovenant/docs`
  as part of the documentation growth tracking surface and ships a
  starter doc (`devcovenant/docs/README.md`) via profile assets so the
  folder grows with useful content and documents how to use overrides and
  custom policies.
- [not done] Describe how `devcovuser`/`devcovrepo` metadata control the
  `tests/devcovenant/**` mirror: `devcovuser` (user installs) mirrors only
  `devcovenant/custom/**`; when `devcov_core_include` is true (DevCovenant’s
  own repo), disable `devcovuser` entirely and let `devcovrepo` mirror the
  full `devcovenant/**` tree.
- [done] Exclude vendored code from `devcovuser` by default (`vendor`,
  `third_party`, `node_modules`) so user installs avoid scanning bundled
  dependencies.
- [done] Honor profile `ignore_dirs` in the engine and skip DevCovenant core
  paths in changelog-coverage for `devcovuser` so vendored DevCovenant code
  stays out of user changelog requirements.
- [not done] Expand `devcovuser` overlays to exclude `devcovenant/**` from
  noise-prone policies (changelog-coverage, version-sync,
  last-updated-placement, documentation-growth-tracking, line-length-limit)
  while explicitly keeping `devcovenant/custom/**` and
  `tests/devcovenant/custom/**` enforced by code-style/security policies.
- [not done] Test mirroring rules: with `devcovuser` active, mirror only
  `devcovenant/custom/**` into `tests/devcovenant/custom/**`; when
  `devcov_core_include` enables `devcovrepo`, mirror the full
  `devcovenant/**` tree into `tests/devcovenant/**` (no extra
  `tests/devcovenant/tests/` level). Document how refresh/update rebuild these
  mirrors so it’s clear which suites belong to DevCovenant versus the host
  project.
- [not done] Define how install/update/refresh regenerate `devcovenant/custom`
  and `tests/devcovenant` from core assets while deleting any `devcovrepo`
  prefixed folders/policies and recreating the user-facing `devcovuser` profile
  so repo-specific overrides never ship.
- [done] Runtime-required artifacts (`devcovenant/registry/local/` entries
  and `devcovenant/registry/local/test_status.json`) are generated from the
  global profile assets, tracked in this repo for CI/builds, excluded from
  packages, and recreated during install/update/refresh when missing.

- [done] Describe the `devcovuser`/`devcovrepo` profiles and wiring so user
  repos keep `devcovenant/**` out of enforcement while still covering
  `devcovenant/custom/**`.
- [done] Describe how install/update/refresh regenerate `devcovenant/custom`
  and `tests/devcovenant` while pruning `devcovrepo`-prefixed overrides when
  `devcov_core_include` is false.
- [done] Document how the `devcovrepo` profile adds `devcovenant/docs` to
  documentation-growth-tracking and how `devcovuser` controls the
  `tests/devcovenant/**` mirror.

### Packaging & testing
- [not done] Ship DevCovenant as a pure-Python package with a console script
  entry.
- [done] Keep `requirements.*` aligned with `THIRD_PARTY_LICENSES.md` and sync
  `licenses/` (license report + AUTO_LICENSE_SYNC marker) whenever manifests
  change.
- [done] Publish PyPI classifiers through Python 3.14 (runtime still
  `requires-python >=3.10`).
- [not done] Run `pytest` and `python3 -m unittest discover`, mirroring the
  `tests/devcovenant/` layout unless `devcov_core_include` unblocks core.

## Outstanding work (dependency order)
Below is every missing SPEC requirement, ordered by dependency.

1. **Activation + scope simplification (immediate).** [not done]
   Remove policy/profile scope keys from policy/profile metadata and generated
   artifacts, switch activation to config-only `policy_state`, and preserve the
   current enabled/disabled state during migration.
2. **Config/schema coverage and registries.** [not done]
   Expose `devcov_core_include`, `devcov_core_paths`, `doc_assets`, and
   `profiles.generated.file_suffixes`; ensure profile/policy assets live under
   `core/` and `custom/` with registries emitted to
   `profile_registry.yaml`.
3. **Managed policy block regeneration.** [not done]
   Treat the `<!-- DEVCOV-POLICIES -->` block as a managed unit, have `update`
   regenerate policy blocks from descriptors + overrides without extra flags,
   and always regenerate AGENTS from the managed template while preserving the
   editable section.
4. **Managed docs pipeline completion.** [not done]
   Ensure all managed docs include `Last Updated`/`Version` headers and
   top-of-file managed blocks; update docs to mention `python3` usage; ensure
   `devcovenant/README.md` includes the packaged DevCovenant Version; and
   sync `README.md`, `SPEC.md`, `PLAN.md`, `CHANGELOG.md`, and
   `CONTRIBUTING.md` from YAML assets (rebuild SPEC/PLAN when missing) while
   deploy/update refresh only managed blocks + headers.
5. **Gitignore regeneration.** [not done]
   Rebuild `.gitignore` from profile fragments while preserving user entries.
6. **Noise control + mirrors for devcovuser/devcovrepo.** [not done]
   Expand `devcovuser` overlays to exclude `devcovenant/**` from noise-prone
   policies while keeping `devcovenant/custom/**` and
   `tests/devcovenant/custom/**` enforced; define mirror rules for
   devcovuser vs devcovrepo and how install/update/refresh regenerate
   `devcovenant/custom` and `tests/devcovenant/**` while pruning devcovrepo
   overrides when `devcov_core_include` is false; document the mirror
   behavior.
7. **Lifecycle extras and environment gating.** [not done]
   Implement `reset-to-stock`, keep `managed-environment` off by default with
   warnings when metadata is missing, and define version-file fallback and
   license fallback behaviors.
8. **Packaging & test execution.** [not done]
   Ship a pure-Python package with a console script entry and ensure
   `run_tests` executes the required command list for mixed stacks.
9. **CLI command placement cleanup.** [not done]
   Keep CLI helpers inside `devcovenant/` and expose the standard commands.
10. **Legacy debris cleanup.** [not done]
   Remove obsolete artifacts (e.g., `devcovenant/registry.json` and the GPL
   template) from manifests/install lists and policy references.
11. **Adapter expansion.** [not done]
   Extract language-specific logic into adapters for the core policies and
   build adapters for languages listed in POLICY_MAP (or trim scopes).

## Execution notes
- Move completed SPEC bullets to `[done]` with a short note.
- List remaining work in “Outstanding work” by dependency.
- Keep README/AGENTS/SPEC docs current and let the fixer bump “Last
  Updated”.

## Testing and validation
- Run `devcovenant.run_pre_commit --phase start`, `devcovenant.run_tests`,
  and `devcovenant.run_pre_commit --phase end` for every change.
- `run_tests` should execute the active `devflow-run-gates.required_commands`
  (from profiles/config) so mixed stacks get all required suites recorded.
- Write `devcovenant/registry/local/test_status.json` before the final
  pre-commit phase.
- Run `python3 -m devcovenant check --fix` when doc assets or `last-updated`
  are modified.

## Release readiness
- Confirm `manifest.json` logs layout, docs, and UTC timestamp before release.
- Verify `CHANGELOG.md` reflects the current version.
  Ensure `no-future-dates` passes.
- Build artifacts (`python -m build`, `twine check dist/*`) and publish with
  `PYPI_API_TOKEN` once prerequisites are met.
