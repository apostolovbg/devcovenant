# DevCovenant Development Plan
**Last Updated:** 2026-02-03
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
- Install/update obey the self-install/self-refresh workflow: running the
  CLI from a source checkout updates that repo in place while running the
  packaged command refreshes whatever repo the user pointed at. Config/
  docs/metadata alone are touched during an update so we never overwrite the
  existing `devcovenant/` tree.
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
- [done] Policy edits set `updated: true`.
  Run `devcovenant update-policy-registry`.
  Then reset the flag.
- [done] Every change gets logged into `CHANGELOG.md`.
  Record it under the current version entry.

### Functional requirements
- [done] Maintain a canonical metadata schema that enumerates every
  selector/metadata key so policy normalization can add missing keys without
  changing existing values.
- [not done] Document every supported policy (including true custom policies)
  so the normalized block lists every policy alphabetically and reports custom
  overrides without mutating user-specified metadata or policy text.
- [done] Follow the policy module/adapters/fixer loading rules described
  in SPEC.
- [done] Respect `apply`, `severity`, `status`, and `enforcement` metadata.
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
- [not done] Every managed doc must include `Last Updated`/`Version` headers.
  Ensure each file also has top-of-file managed blocks.
  Include `Doc ID`, `Doc Type`, and owner metadata in those blocks.
- [not done] Documentation examples and running instructions mention `python3`.
  Mention the module entry whenever you discuss source-based usage.
- [not done] `devcovenant/README.md` includes the packaged
  `DevCovenant Version` value.
- [not done] Managed documents are generated from YAML assets.
  Inject stock non-managed text only when the target doc is missing, empty, or
  a single-line placeholder.
  Otherwise install/update commands refresh just the managed blocks while
  handling the `<!-- DEVCOV-POLICIES -->` block separately.

### Policy requirements
- [done] Policy metadata normalization now emits schema + value blocks
  while keeping existing text values intact.
- [done] Built-in policies have canonical text in
  `devcovenant/registry/global/stock_policy_texts.yaml`.
- [done] Custom policy `readme-sync` enforces the README mirroring
  and repo-only block stripping.
- [done] `devcov-parity-guard` replaces the old stock-policy text check and
  compares AGENTS policy text to descriptor YAML prose for core and custom
  policies.
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
  hints, profile scopes, and core/custom origins.
- [done] Record update notices (replacements/new stock policies) inside
  `devcovenant/registry/local/manifest.json` and print them during updates.
- [not done] `managed-environment` remains off by default.
  Warn when required metadata or command hints are absent.
- [done] Dogfood-only policies (`patches-txt-sync`, `gcv-script-naming`,
  `security-compliance-notes`) are removed from the DevCovenant repo.
- [done] Reduced the stock profile catalog to a slim, maintained set
  (global, docs, data, suffixes, python, javascript, typescript, java, go,
  rust, php, ruby, csharp, sql, docker, terraform, kubernetes, fastapi,
  frappe, dart, flutter, swift, objective-c) and updated
  PROFILE_MAP/POLICY_MAP/SPEC to describe the change. Retired stacks are to be
  reintroduced only as custom profiles.
- [done] Materialize expanded POLICY_MAP/PROFILE_MAP expectations: ensure
  profiles/policies/assets/adapters/fixers match the reference maps and keep
  the maps authoritative for future additions.
- [done] Align POLICY_MAP scopes with retained profiles: add fastapi,
  frappe, objective-c, and sql where supported (dependency-license-sync,
  docstring-and-comment-coverage, name-clarity, new-modules-need-tests,
  security-scanner, documentation-growth-tracking, line-length-limit,
  version-sync) and trim deprecated stacks (kotlin/scala/groovy/dotnet/
  fsharp/elixir/erlang/haskell/clojure/julia/ocaml/crystal/ansible).
- [done] Per-profile descriptors (`<profile>.yaml`) must be populated manually
  (maps are reference only); stubs have been fleshed out with real assets and
  overlays for the retained catalog.
- [done] Profile-first scoping: policies run only when a profile lists them
  (including `global`, which now activates all global policies explicitly).
  Policy `profile_scopes` stay as documentation only. Profiles are
  explicit—no inheritance; each profile lists its own assets, suffixes,
  policies, and overlays. Custom policies remain opt-in via custom profiles
  or config overrides (not implicitly active in `global`).

### Policy metadata redesign
- [done] Define per-policy YAML descriptors that include the managed
  prose, selector metadata, and a `metadata` block whose keys describe the
  schema while also supplying the baseline values that feed into AGENTS and
  the registry. The canonical schema no longer lives in a separate
  hand-written file; it is inferred from the keys declared inside each
  policy’s `metadata`.
- [not done] Use provenance (core vs. frozen/custom loading path) to derive
  `custom`/`apply`/`freeze` in the generated metadata instead of retaining
  explicit `status` or `updated` keys. `metadata` may still expose knobs such
  as `profile_scopes`, `selector_roles`, or `enforcement`, while the generator
  records the final `apply`/`freeze`/`severity` values after applying
  overrides.
- [done] Introduce config keys `autogen_do_not_apply`,
  `manual_force_apply`, `freeze_core_policies`, and `policy_overrides` so the
  active profile can flip `apply`/`freeze` and mutate `enforcement`,
  `severity`, selectors, or any schema value without editing the policy YAMLs.
  The refresh command merges those lists/maps before emitting AGENTS and
  registry entries so docs remain declarative.
- [done] Record every policy in
  `devcovenant/registry/local/policy_registry.yaml` with two blocks per entry:
  `metadata_schema` (keys declared under `metadata`)
  and `metadata_values` (resolved defaults plus merged overrides, apply/freeze,
  hashes, asset hints, and custom/core origins). The generator and AGENTS
  templating read from that unified source so enforcement always matches the
  registry.
- [done] When DevCovenant removes a core policy, copy it into
  `devcovenant/custom/policies/` (or a frozen overlay prescribed in config),
  mark the new entry as `custom`, and rerun `update-policy-registry` so all
  downstream artifacts report the deprecation rather than leaving dangling IDs.
- [done] Scope `raw-string-escapes` to the python profile and default it to
  `apply: false` via the python profile’s `autogen_do_not_apply` list.
  Add the repo-only `devcov-raw-string-escapes` custom policy for
  DevCovenant’s own enforcement.

### Installation & documentation
- [not done] Install modes `auto`/`empty`.
- Refuse install when DevCovenant already exists unless `--auto-uninstall`.
- Share an install/update workflow touching only configs, docs, and metadata.
- Leave the `devcovenant/` tree intact.
- [not done] `update` preserves policy blocks and metadata.
  Provide independent doc refresh controls (`--docs-include/exclude`).
- [done] Introduce a registry-only refresh mode that regenerates
  `devcovenant/registry/local/*` (hashes, manifest, metadata schema) and
  re-materializes `config.yaml` only when missing, while skipping AGENTS and
  managed docs. Run this registry-only refresh automatically at the start of
  every devcovenant invocation (including CI) so state is rebuilt without
  dirtying working trees. Default to preserve metadata mode.
- [not done] `AGENTS.md` always uses the template.
  Preserve the `# EDITABLE SECTION` text when it already exists.
- [not done] `README.md`, `SPEC.md`, `PLAN.md`, `CHANGELOG.md`, and
  `CONTRIBUTING.md` sync from YAML assets with new managed blocks.
- [not done] `SPEC.md`/`PLAN.md` rebuild when missing.
  Keep user edits otherwise.
- [not done] Install/update/refresh regenerate only managed doc headers and
  managed blocks (UTC dates) while preserving user content outside those
  blocks; installs create missing docs without discarding existing content.
- [not done] `VERSION` creation prefers existing file, then `pyproject.toml`.
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
  Catalog entries go to `devcovenant/registry/local/profile_catalog.yaml`.
  Asset metadata lands in `policy_assets.yaml`.
- [not done] Profile-driven pre-commit config turns metadata into hooks and
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
- [not done] Runtime-required artifacts (`devcovenant/registry/local/` entries
  and `.devcov-state/test_status.json`) are generated from `devcovuser` assets,
  tracked in this repo for CI/builds, excluded from packages, and recreated
  during install/update/refresh when missing.

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

1. **Canonical metadata schema & normalization.**
   [done] Build the metadata schema, normalize AGENTS blocks, and ensure
   metadata overlays dedupe existing values when configuration or profile
   fragments merge during normalization.
2. **Policy registry + replacements + `freeze`.**
   [done] Metadata_schema/metadata_values blocks are emitted, config overrides
   propagate to apply/freeze, replacements/freeze copies rerun the registry
   refresh, and the registry records only the profile scopes matching the
   active configuration surface. The canonical map then reflects what is
   actually applied.
3. **End-phase rerun guarantees.**
   Implement the new workflow from SPEC: detect when end-phase hooks or
   DevCovenant autofixers change files.
   Rerun the tests (and hooks if necessary) until the tree is clean.
   Record `pre_commit_end_*` only when that final pass succeeds so the devflow
   gates reflect a real clean run.
4. **Managed document asset generation.**
   Let YAML assets rebuild doc templates and preserve non-policy text.
5. **Doc asset stamping & last-updated auto-fixer.**
   Hook `last-updated-placement` to stamp UTC headers consistently.
6. **Documentation sync & readme-sync policy.**
   Keep `devcovenant/README.md` mirroring `/README.md` with auto-fixes.
7. **Install/update/refresher command matrix.**
   Implement `install`, `update`, `refresh-all`, and `reset-to-stock`.
   Include policy and docs overrides plus CLI mode distinctions.
8. **Config & profile asset generation.**
   Generate `devcovenant/config.yaml` with knobs, doc assets, and catalogs,
   and codify how install/update/refresh recreate `devcovenant/custom`, rebuild
   `tests/devcovenant/custom` (mirroring the policy/profile overlays), delete
   `devcovrepo`-prefixed overrides unless `devcov_core_include` is true, and
   note the default config is materialized from the `devcovuser` profile
   descriptor asset while profile overlays fill in autogen metadata during
   install.
9. **Profile-driven pre-commit config.**
   Store hook fragments, merge them with overrides, and record metadata.
10. **CLI command placement cleanup.**
   Keep CLI helpers inside `devcovenant/`, expose the standard commands.
11. **Testing infrastructure.**
   Mirror `tests/devcovenant/` to the package layout and respect the
   `new-modules-need-tests` policy exclusions.
12. **Packaging & licensing guardrails.**
   [done] Switch DevCovenant to MIT (assets, docs, PyPI metadata) and sync
   CITATION.
   [done] Ship CITATION.cff in sdists/wheels.
   Build artifacts with assets, enforce MIT when needed, and sync
   licenses/CITATION.
13. **Legacy debris cleanup.**
   Remove obsolete artifacts (e.g., `devcovenant/registry.json`,
   `devcovenant/config_old.yaml`, and the unused GPL license asset) from the
   tree, update manifests/install lists, and drop policy/schema references so
   refresh/install no longer expect them.
14. **Profile maps → profile descriptors.**
    Keep core profile YAMLs as the shipped source of truth; `PROFILE_MAP.md`
    / `POLICY_MAP.md` are reference tables for authors to manually populate
    policies, suffixes, assets, and overlays. Descriptors stay named
    `<profile>.yaml`; refresh does not re-materialize maps into manifests.
15. **Registry/metadata cleanup.**
    Drop `metadata_handles` from the policy registry (schema already comes
    from policy YAMLs) and move broad suffix/prefix/glob defaults out of base
    policies into profile overlays (python/docs/lang-specific and devcovrepo).
    Audit remaining policies for hard-coded metadata that should live in
    profiles instead.

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
- Write `.devcov-state/test_status.json` before the final pre-commit phase.
- Run `python3 -m devcovenant check --fix` when doc assets or `last-updated`
  are modified.

## Outstanding work
- Extract language-specific logic from docstring-and-comment-coverage,
  name-clarity, new-modules-need-tests, and security-scanner into adapters
  (`devcovenant/core/policies/<policy>/adapters/<lang>.py`) and keep core
  policy modules language-agnostic.
- Build adapters for other languages listed in POLICY_MAP scopes (beyond
  python) or trim scopes to the languages we actually support to avoid false
  coverage claims.

## Release readiness
- Confirm `manifest.json` logs layout, docs, and UTC timestamp before release.
- Verify `CHANGELOG.md` reflects the current version.
  Ensure `no-future-dates` passes.
- Build artifacts (`python -m build`, `twine check dist/*`) and publish with
  `PYPI_API_TOKEN` once prerequisites are met.
