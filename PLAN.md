# DevCovenant Development Plan
**Last Updated:** 2026-01-28
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
- [done] Startup check (`python3 -m devcovenant check --mode startup`).
- [done] Policy edits set `updated: true`.
  Run `devcovenant update-policy-registry`.
  Then reset the flag.
- [done] Every change gets logged into `CHANGELOG.md`.
  Record it under the current version entry.

### Functional requirements
- [not done] Maintain a canonical metadata schema that enumerates every
  selector/metadata key so policy normalization can add missing keys without
  changing existing values.
- [not done] Document every supported policy (including true custom policies)
  so the normalized block lists every policy alphabetically and reports custom
  overrides without mutating user-specified metadata or policy text.
- [done] Follow the policy module/adapters/fixer loading rules described
  in SPEC.
- [done] Respect `apply`, `severity`, `status`, and `enforcement` metadata.
  Apply those settings across all policies.
- [done] Support `startup`, `lint`, `pre-commit`, and `normal` modes along with
  the available fixers.
- [done] Provide both `devcovenant` console entry and `python3 -m devcovenant`
  module entry, with docs defaulting to the console path.
- [not done] `test` runs `pytest` + `python3 -m unittest discover` while
  respecting the `tests/devcovenant/` layout and keeping those suites out of
  packages.
- [not done] `check` exits non-zero when blocking violations exist.
- [not done] `sync` runs a startup-mode check and reports drift.
- [not done] `normalize-metadata` inserts all supported keys safely.
  Leave existing text untouched.
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
- [not done] Policy metadata normalization must add missing keys while
  preserving existing text and values.
- [done] Built-in policies have canonical text in
  `devcovenant/registry/global/stock_policy_texts.yaml`.
- [done] Custom policy `readme-sync` enforces the README mirroring
  and repo-only block stripping.
- [not done] Policy replacement metadata from
  `devcovenant/registry/global/policy_replacements.yaml` is applied.
  Replaced policies move to `custom/` with `custom: true` and are marked
  deprecated when enabled.
- [not done] The collective `<!-- DEVCOV-POLICIES:BEGIN -->`/
  `<!-- DEVCOV-POLICIES:END -->` block is treated as a managed unit and
  refreshed from assets. A per-policy `freeze` override copies scripts to
  `devcovenant/custom/` and reruns `devcovenant update-policy-registry` when
  toggled.
- [not done] `devcovenant/registry/local/policy_registry.yaml` is the sole
  hash store; the legacy `registry.json` and `update_hashes` helper have been
  removed. The YAML tracks every policy (enabled or disabled) with hashes,
  asset hints, profile scopes, and core/custom origin.
- [not done] Record update notices (replacements/new stock policies) inside
  `devcovenant/registry/local/manifest.json` and print them during updates.
- [not done] `managed-environment` remains off by default.
  Warn when required metadata or command hints are absent.

### Policy metadata redesign
- [not done] Define per-policy YAML descriptors that include the canonical
  text, selector metadata, and defaults derived from the policy metadata schema
  (`devcovenant/registry/global/policy_metadata_schema.yaml`).
- [not done] Remove `status`/`updated` keys from metadata; use provenance
  (core vs. frozen/custom path) to determine `custom`/`apply` behavior while
  exposing `freeze`, `enforcement`, `profile_scopes`, and other switches via
  `config.yaml` overlays.
- [not done] Introduce config keys `do_not_apply_policies` and
  `freeze_core_policies` under `config.yaml` so the active profile can flip
  `apply`/`freeze` across many policies without touching AGENTS. Removing a
  policy from `freeze_core_policies` unfreezes it, while adding a custom policy
  to that list triggers a reminder that custom policies are not touched by the
  generator.
- [not done] Allow `policy_overrides` in `config.yaml` to tweak metadata such
  as `enforcement`, `severity`, and selector filters; DevCovenant merges these
  overrides on top of the YAML defaults before regenerating AGENTS/registry.
- [not done] Autogenerate `AGENTS.md` and the registry from the same YAML files
  so the policy engine checks scripts/text against the loaded definitions and
  the AGENTS block is never edited manually.

### Installation & documentation
- [not done] Install modes `auto`/`empty`.
- Refuse install when DevCovenant already exists unless `--auto-uninstall`.
- Share an install/update workflow touching only configs, docs, and metadata.
- Leave the `devcovenant/` tree intact.
- [not done] `update` preserves policy blocks and metadata.
  Provide independent doc refresh controls (`--docs-include/exclude`).
- [not done] `refresh-all` regenerates registries/policies without writing
  managed docs.
  Default to preserve metadata mode.
- [not done] `AGENTS.md` always uses the template.
  Preserve the `# EDITABLE SECTION` text when it already exists.
- [not done] `README.md`, `SPEC.md`, `PLAN.md`, `CHANGELOG.md`, and
  `CONTRIBUTING.md` sync from YAML assets with new managed blocks.
- [not done] `SPEC.md`/`PLAN.md` rebuild when missing.
  Keep user edits otherwise.
- [not done] `VERSION` creation prefers existing file, then `pyproject.toml`.
  Prompt (default `0.0.1`). `--version` overrides detection.
- [not done] `LICENSE` falls back to the GPL-3.0 template when missing.
- [not done] `.gitignore` is rebuilt from fragments while merging user entries.
- [not done] Every managed doc gets its `Last Updated` header stamped in UTC.
- [not done] Config exposes `devcov_core_include`, `devcov_core_paths`, and
  `doc_assets` with `profiles.generated.file_suffixes`.
- [not done] Profile and policy assets live under `core/` and `custom/`.
  Catalog entries go to `devcovenant/registry/local/profile_catalog.yaml`.
  Asset metadata lands in `policy_assets.yaml`.
- [not done] Profile-driven pre-commit config turns metadata into hooks and
  documents the “Pre-commit config refactor” phase.

### Packaging & testing
- [not done] Ship DevCovenant as a pure-Python package with a console script
  entry.
- [not done] Keep `requirements.*` aligned with `THIRD_PARTY_LICENSES.md`.
  Sync `licenses/` accordingly.
- [not done] Run `pytest` and `python3 -m unittest discover`, mirroring the
  `tests/devcovenant/` layout unless `devcov_core_include` unblocks core.

## Outstanding work (dependency order)
Below is every missing SPEC requirement, ordered by dependency.

1. **Canonical metadata schema & normalization.**
   Build the metadata schema and normalize AGENTS blocks.
2. **Policy registry + replacements + `freeze`.**
   Move hashes into `policy_registry.yaml`, drop `registry.json`, and add
   replacements plus the `freeze` toggle.
3. **Managed document asset generation.**
   Let YAML assets rebuild doc templates and preserve non-policy text.
4. **Doc asset stamping & last-updated auto-fixer.**
   Hook `last-updated-placement` to stamp UTC headers consistently.
5. **Documentation sync & readme-sync policy.**
   Keep `devcovenant/README.md` mirroring `/README.md` with auto-fixes.
6. **Install/update/refresher command matrix.**
   Implement `install`, `update`, `refresh-all`, and `reset-to-stock`.
   Include policy and docs overrides plus CLI mode distinctions.
7. **Config & profile asset generation.**
   Generate `devcovenant/config.yaml` with knobs, doc assets, and catalogs.
8. **Profile-driven pre-commit config.**
   Store hook fragments, merge them with overrides, and record metadata.
9. **CLI command placement cleanup.**
   Keep CLI helpers inside `devcovenant/`, expose the standard commands.
10. **Testing infrastructure.**
   Mirror `tests/devcovenant/` to the package layout and respect the
   `new-modules-need-tests` policy exclusions.
11. **Packaging & licensing guardrails.**
   Build artifacts with assets, enforce GPL-3.0 when needed, and sync licenses.

## Execution notes
- Move completed SPEC bullets to `[done]` with a short note.
- List remaining work in “Outstanding work” by dependency.
- Keep README/AGENTS/SPEC docs current and let the fixer bump “Last Updated”.

## Testing and validation
- Run `devcovenant.run_pre_commit --phase start`, `devcovenant.run_tests`,
  and `devcovenant.run_pre_commit --phase end` for every change.
- Write `.devcov-state/test_status.json` before the final pre-commit phase.
- Run `python3 -m devcovenant check --fix` when doc assets or `last-updated`
  are modified.

## Release readiness
- Confirm `manifest.json` logs layout, docs, and UTC timestamp before release.
- Verify `CHANGELOG.md` reflects the current version.
  Ensure `no-future-dates` passes.
- Build artifacts (`python -m build`, `twine check dist/*`) and publish with
  `PYPI_API_TOKEN` once prerequisites are met.
