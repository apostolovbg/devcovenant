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

## Spec compliance checklist
- Configuration: generate a complete `devcovenant/config.yaml` that lists
  every supported knob (even if blank), includes `profiles.generated` data,
  and propagates `version.override` into templated assets before VERSION
  exists.
- Profiles: rebuild `devcovenant/registry/local/profile_catalog.yaml` from
  core/custom manifests, mark active profiles, and ensure assets are listed
  per profile.
- Policy metadata: normalize all selector keys, expose missing keys in
  AGENTS policy blocks without changing values, and enforce the policy block
  as a managed unit separate from other doc blocks.
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
- Packaging: ship tests under top-level `tests/` in sdist only, keep
  `THIRD_PARTY_LICENSES.md`/`licenses/` in sync with dependency changes, and
  enforce Python 3.10+ metadata.
- Tests: treat `new-modules-need-tests` as unit-test-only, keep running
  both `pytest` and `python -m unittest discover`, and convert existing
  policy tests to unit-style suites as part of the migration.
- CLI: verify `refresh-all` exists, `refresh-policies` defaults to preserve,
  and deprecations (`normalize-metadata`, `update-hashes`) are removed or
  redirected as specified.

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
   - Place policy tests in `tests/...` such that the folder hierarchy mirrors
     `devcovenant/` exactly, avoiding additional nested namespaces.
   - Keep profile manifests/assets under `devcovenant/{core,custom}/profiles/<name>/assets/`.
   - Update `MANIFEST.in` and `pyproject.toml` so only the core package tree and
     the top-level `tests/` mirror are bundled.
  - Move the previous `tools/` helpers into `devcovenant/core/` and update
    every reference so the CLI, docs, and managed assets point to the in-package
    tooling instead of an external `tools` directory.
2. **Phase 2 – Profile catalog, config, and overlays**
   - Rebuild `devcovenant/registry/local/profile_catalog.yaml` on every install/update via `profiles.discover_profiles`.
   - Regenerate `devcovenant/config.yaml` so `profiles.active`, `profiles.generated.file_suffixes`, and the `policies` block always reflect the selected profiles.
   - Merge gitignore fragments from global+active profiles into `.gitignore` and ensure profile overlays supply `policy_overlays`, dependencies, required commands, and suffix lists.
   - Propagate the configured `version.override` into template assets and policy generation so generated files (e.g., `pyproject.toml`, policy assets) use the same release version.
   - Describe the new `refresh-all` helper that runs `refresh-policies` in preserve mode, updates the policy registry, and rebuilds the profile catalog without a full install/update.
3. **Phase 3 – Policy lifecycle & registry automation**
   - Split the registry into tracked `devcovenant/registry/global/` (stock policy texts, replacements) and gitignored `devcovenant/registry/local/` (policy_registry, manifest, catalog, assets, test status).
   - Ensure `refresh_policies` + `update-policy-registry` populate every policy entry (active or disabled) with metadata handles, profile scopes, asset hints, script hashes, and core/custom flags.
   - Implement policy replacements/notifications: migrating replaced policies to `custom/` with `custom: true`, removing disabled policies, and logging announcements in `manifest.json` while printing notices on update.
   - Support the `freeze` metadata knob that copies policy code/fixers/assets into `devcovenant/custom/` when true and removes them (and the registry entry) when false, rerunning `devcovenant update-policy-registry` each time.
   - Retire the legacy `devcovenant/registry.json` artifact and remove the
     `update_hashes.py` helper so policy hashes live only in the local
     policy registry.
4. **Phase 4 – CLI, engine, and managed-doc compliance**
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
