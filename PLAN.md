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
- [done] Gated workflow: `pre-commit start`, tests (`pytest` + `python3 -m unittest discover`), `pre-commit end` is required for every change.
- [done] Startup check (`python3 -m devcovenant check --mode startup`).
- [done] Policy edits set `updated: true`, run `devcovenant update-policy-registry`, then reset the flag.
- [done] Every change gets logged into `CHANGELOG.md` under the current version.

### Functional requirements
- [not done] Maintain a canonical metadata schema enumerating every selector/metadata key so policy normalization can add missing keys without changing existing values.
- [done] Follow the policy module/adapters/fixer loading rules described in SPEC.
- [done] Respect `apply`, `severity`, `status`, and `enforcement` metadata across all policies.
- [done] Support `startup`, `lint`, `pre-commit`, and `normal` modes along with the available fixers.
- [done] Provide both `devcovenant` console entry and `python3 -m devcovenant` module entry, with docs defaulting to the console path.
- [not done] `test` runs `pytest` + `python3 -m unittest discover` while respecting the `tests/devcovenant/` layout and keeping those suites out of packages.
- [not done] `check` exits non-zero when blocking violations exist.
- [not done] `sync` runs a startup-mode check and reports drift.
- [not done] `normalize-metadata` inserts all supported keys safely while leaving existing text untouched.
- [not done] Every managed doc must include `Last Updated`/`Version` headers and top-of-file managed blocks with `Doc ID`, `Doc Type`, and owner metadata.
- [not done] Documentation examples and running instructions always use `python3` when referring to source-based usage.
- [not done] `devcovenant/README.md` includes the packaged `DevCovenant Version` value.
- [not done] Managed documents are generated from YAML assets, injecting stock non-managed text only when the target doc is missing/empty/placeholder. Otherwise install/update commands refresh just the managed blocks while handling the `<!-- DEVCOV-POLICIES -->` block separately.

### Policy requirements
- [not done] Policy metadata normalization must be able to add missing keys while preserving existing text and values.
- [done] Built-in policies have canonical text (`devcovenant/registry/global/stock_policy_texts.yaml`).
- [done] Custom policy `readme-sync` enforces the README mirroring and repo-only block stripping.
- [not done] Policy replacement metadata from `devcovenant/registry/global/policy_replacements.yaml` is applied, moving replaced policies to `custom/` with `custom: true` and marking them deprecated when enabled.
- [not done] The collective `<!-- DEVCOV-POLICIES:BEGIN -->`/`<!-- DEVCOV-POLICIES:END -->` block is treated as a managed unit and refreshed from assets. A per-policy `freeze` override copies scripts to `devcovenant/custom/` and reruns `devcovenant update-policy-registry` when toggled.
- [not done] `devcovenant/registry/local/policy_registry.yaml` is the sole hash store; the legacy `registry.json` and `update_hashes` helper have been removed, and the YAML tracks every policy (enabled or disabled) with hashes, asset hints, profile scopes, and core/custom origin.
- [not done] Record update notices (replacements/new stock policies) inside `devcovenant/registry/local/manifest.json` and print them during updates.
- [not done] `managed-environment` remains off by default but warns when required metadata is missing or command hints are absent.

### Installation & documentation
- [not done] Install modes `auto`/`empty`, `install` refusal when DevCovenant already exists (unless `--auto-uninstall`), and shared install/update workflow that touches only configs/docs/metadata while leaving the `devcovenant/` tree intact.
- [not done] `update` preserves policy blocks/metadata and has independent doc refresh controls (`--docs-include/exclude`).
- [not done] `refresh-all` regenerates registries/policies (defaulting to preserve metadata) without writing managed docs.
- [not done] `AGENTS.md` always uses the template, preserving the `# EDITABLE SECTION` text when it already exists.
- [not done] `README.md`, `SPEC.md`, `PLAN.md`, `CHANGELOG.md`, and `CONTRIBUTING.md` are delivered or refreshed from YAML assets with the new managed-block scaffolding; `CHANGELOG`/`CONTRIBUTING` are replaced on install with `_old.*` backups.
- [not done] `SPEC.md`/`PLAN.md` default to being provisioned by the global profile; missing docs are rebuilt, while existing files retain user content.
- [not done] `VERSION` creation follows the order: existing file → `pyproject.toml` → prompt (default `0.0.1`); `--version` overrides detection.
- [not done] `LICENSE` is the GPL-3.0 template when absent and overwritten only when requested.
- [not done] `.gitignore` is rebuilt from global/profile/OS fragments, merging user entries under a preserved section with backups recorded.
- [not done] Every managed doc gets `Last Updated` stamped with UTC install/update time.
- [not done] Config exposes `devcov_core_include`, `devcov_core_paths`, `doc_assets` (with `autogen`/`user`), and `profiles.generated.file_suffixes`; every known knob is listed so the file molecules as an override template.
- [not done] Profile and policy assets live under their respective `core/` and `custom/` directories, with catalog generation in `devcovenant/registry/local/profile_catalog.yaml` and asset application metadata in `devcovenant/registry/local/policy_assets.yaml`.

### Packaging & testing
- [not done] Ship DevCovenant as a pure-Python package with a console script entry and include all profile/policy assets in sdist/wheel.
- [not done] Require Python 3.10+ and keep `requirements.in`, `requirements.lock`, and `pyproject.toml` synchronized with `THIRD_PARTY_LICENSES.md`/`licenses/`.
- [not done] The `new-modules-need-tests` policy explicitly requires unit tests, the repo runs both `pytest` and `python3 -m unittest discover`, and the tests tree mirrors `devcovenant/` layout under `tests/devcovenant/` on demand (devcov-core code is excluded unless `devcov_core_include` is true).

## Outstanding work (dependency order)
Below is every SPEC requirement that remains unimplemented, ordered by the dependencies the task must satisfy.

1. **Canonical metadata schema & normalization.** Build the schema that lists every supported selector and metadata key, normalize AGENTS policy blocks so they expose each field (even when blank), and feed that schema into `refresh-policies` so it can rehydrate the policy block automatically.
2. **Policy registry + replacements + `freeze`.** Finish migrating all policy hashes into `devcovenant/registry/local/policy_registry.yaml`, drop `registry.json`, implement replacements from `policy_replacements.yaml` (with notices in `manifest.json`), and provide a `freeze` toggle that copies reassigned policies into `custom/` while re-running `update-policy-registry`.
3. **Managed document asset generation.** Wire the YAML assets under `devcovenant/core/profiles/global/assets/` to regenerate AGENTS/README/SPEC/PLAN/CHANGELOG/CONTRIBUTING/devcovenant/README/etc., injecting non-managed text only for missing/empty sources, and ensure AGENTS always retains `# EDITABLE SECTION`. The policy block needs to be handled via the `<!-- DEVCOV-POLICIES -->` markers so updates never shuffle non-policy text.
4. **Doc asset stamping & last-updated auto-fixer.** Hook `last-updated-placement` to stamp UTC `Last Updated` headers for every managed doc touched, keeping the plan updated when docs change.
5. **Documentation sync & readme-sync policy.** Ensure `devcovenant/README.md` mirrors `/README.md`, repository-only text is preserved in the repo README, and the readme-sync policy auto-fixes mismatches.
6. **Install/update/refresher command matrix.** Implement the install/update/refresh modes (`install`, `update`, `refresh-all`, planned `reset-to-stock`), `--policy-mode`/`--docs-*` controls, `--disable-policy`, `--preserve-custom`, `--auto-uninstall`, and the distinction between source-based (`python3 -m devcovenant …`) and packaged CLI paths.
7. **Config & profile asset generation.** Generate `devcovenant/config.yaml` with every knob listed, include `profiles.generated`/`doc_assets` sections, and rebuild `profile_catalog.yaml` + `policy_assets.yaml` whenever profiles change.
8. **CLI command placement cleanup.** Keep CLI entrypoints at `devcovenant/` root, move helper logic into `devcovenant/core/`, and expose commands like `refresh-all`, `refresh-policies`, `update-policy-registry`, `install`, `update`, `uninstall`, `restore-stock-text`, `update_lock`, and `update_test_status`.
9. **Testing infrastructure.** Ensure `tests/devcovenant/` mirrors the package layout and is created automatically when `new-modules-need-tests` is active; keep DevCovenant core excluded in user repos unless `devcov_core_include` overrides the `devcov-exclude` profile.
10. **Packaging & licensing guardrails.** Build the release artifacts (sdist/wheel) with all assets, include GPL-3.0 when missing, regenerate `.gitignore` fragments, and keep dependency docs/test licenses synchronized while requiring Python 3.10+.

## Execution notes
- When completing a SPEC item, move the `[not done]` bullet to a category marked `[done]` and include a short note describing how the implementation satisfies the requirement.
- Remaining work should be listed under “Outstanding work” in dependency order so every phase knows what to tackle next.
- Documented instructions in README/AGENTS/SPEC should reflect the current behavior after each change, and any doc-only adjustments bump the “Last Updated” header via the fixer.

## Testing and validation
- Continue running `python3 -m devcovenant.run_pre_commit --phase start`, `python3 -m devcovenant.run_tests`, and `python3 -m devcovenant.run_pre_commit --phase end` for every change.
- Keep `devflow-run-gates` satisfied by ensuring `.devcov-state/test_status.json` is written before the final pre-commit phase.
- Run `python3 -m devcovenant check --fix` when the `last-updated-placement` or doc assets touched.

## Release readiness
- Confirm `devcovenant/registry/local/manifest.json` records the install/update layout, doc coverage, options, active profiles, policy assets, and UTC timestamp before tagging a release.
- Verify `CHANGELOG.md` contains the current version section with the latest edits; `no-future-dates` should never fail.
- Build artifacts (`python -m build`, `twine check dist/*`) and ensure `.github/workflows/publish.yml` publishes using `PYPI_API_TOKEN` once the preceding work is complete.
