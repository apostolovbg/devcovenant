# DevCovenant Development Plan
**Last Updated:** 2026-01-23
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** PLAN
**Doc Type:** plan
**Managed By:** DevCovenant
<!-- DEVCOV:END -->

This plan focuses on making DevCovenant updates safe, predictable, and
metadata-driven across user repos. The near-term goal is a stable core that
can evolve without breaking downstream policies, while keeping policy blocks
complete and easy to fill in.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Goals for 0.2.6](#goals-for-026)
4. [Target Update Behavior](#target-update-behavior)
5. [Implementation Plan](#implementation-plan)
6. [Documentation and Templates](#documentation-and-templates)
7. [Release Readiness](#release-readiness)
8. [User Repo Update Path](#user-repo-update-path)
9. [Acceptance Criteria](#acceptance-criteria)
10. [Risks and Backout](#risks-and-backout)
11. [Next Steps](#next-steps)

## Overview
DevCovenant already supports core policies, custom overrides, and an update
command. The remaining gaps are a consistent update path that refreshes
managed blocks, updates DevCovenant core safely, and normalizes metadata so
core policy changes never break user repos. Policy metadata must be complete:
all supported keys appear in blocks (even when empty), and keys can be added
or renamed through normalization without overriding user values.

A full refresh of DevCovenant (core + docs + templates) should be achievable
by uninstalling and reinstalling with the intended installer arguments.

## Workflow
- Run `python3 tools/run_pre_commit.py --phase start` before edits.
- Run `python3 tools/run_tests.py` after edits.
- Finish with `python3 tools/run_pre_commit.py --phase end`.
- When policy text changes, set `updated: true`, run
  `devcovenant update-hashes`, then reset the flag.

## Goals for 0.2.6
- Safe updates: refresh managed blocks without altering policy values.
- Metadata stability: ensure every policy block includes all supported keys.
- Metadata completeness: insert new keys and rename keys without changing
  existing values.
- Selector role completeness: use `selector_roles` to declare which selector
  roles a policy supports, then insert the globs/files/dirs triplets for those
  roles (empty when unused). Custom selector roles are supported.
- Streamlined install defaults: `CONTRIBUTING.md` and `CHANGELOG.md` are
  always replaced on install, with `*_old.md` backups.
- Deterministic version bootstrap: use existing `VERSION`, otherwise create
  `VERSION` with `0.0.1` when no version argument is supplied.
- Standardize doc headers and managed blocks: every DevCovenant-managed doc
  includes a header block (title/last updated/version) and a small DevCovenant
  block directly below it, both refreshed by update routines.
- Remove citation support from core install/update flows and documentation;
  treat `CITATION.cff` as a custom (user-managed) doc type only.
- Replace repo-specific environment policies with a unified
  `managed-environment` policy.
- Clarify SemVer scope enforcement to align with MAJOR/MINOR/PATCH semantics
  (API-breaking, feature-level, and bugfix releases), while shipping the
  policy disabled by default.
- Keep custom overrides stable while core policies evolve.
- Provide a first-class policy replacement workflow (deprecate/migrate/remove)
  when core policies are superseded.
- Notify users when new stock policies become available.
- Delete deprecated core files and folders on update so only
  `devcovenant/custom/` stays user-writable.

## Target Update Behavior
- Default update runs metadata normalization. If a key is added or renamed,
  user policy blocks are updated accordingly; existing values are preserved.
- Policy-mode default is `append-missing`: existing policy blocks are kept,
  missing stock policies are appended.
- Core DevCovenant files (everything under `devcovenant/` except `custom/`)
  are refreshed on update; deprecated core paths are removed.
- Any file containing `DEVCOV` blocks is treated as block-managed: managed
  blocks refresh from templates, non-block content is preserved.
- DevCovenant-managed docs must include a standard header block (title, last
  updated, version) followed immediately by a small `DEVCOV` block. Updates
  must merge existing `DEVCOV` blocks (add missing fields, refresh values)
  without overwriting header lines.
- Managed blocks record `Doc ID`, `Doc Type`, and `Managed By` metadata.
  Doc classification (core/optional/custom) lives in the manifest; optional
  docs follow the same managed-block rules when present, while custom docs
  remain user-managed unless explicitly configured.
  updated, version) followed immediately by a small `DEVCOV` block. Updates
  must merge existing `DEVCOV` blocks (add missing fields, refresh values)
  without overwriting header lines.
- `CHANGELOG.md` and `CONTRIBUTING.md` refresh managed blocks on update;
  editable content remains intact. `DEVCOV:END` sits directly above
  `# Log changes here` in `CHANGELOG.md`.
- Deprecated policies: if enabled, they move to custom with `custom: true` and
  their fixers migrate; if disabled, they are deleted. Users are notified
  either way and told which policy replaces them.
- New stock policies added in updates trigger a user notification that the
  policy is available.
- `devcov-structure-guard` validates against an update-shipped structure
  manifest instead of hard-coded globs.
- A persistent DevCovenant manifest file under `devcovenant/` records the
  installed core layout, managed docs, optional docs, and allowed custom
  directories; install/update/uninstall all read and update the same manifest
  so structure validation and cleanup are consistent.
- Update/install/uninstall share the same flag schema; update reuses install
  defaults when appropriate, and uninstall uses the manifest to remove only
  managed assets while preserving user content.

## Implementation Plan
### Phase A: Policy metadata schema + normalization (done)
- Defined a canonical metadata schema using template policy blocks, with
  every script-supported key present (empty values preserve defaults).
- Added `devcovenant normalize-metadata` to insert missing keys in order
  without changing existing values.
- Standardize selector roles so `user_visible`, `user_facing`, and
  `doc_quality` are declared via `selector_roles` and stored as role-specific
  globs/files/dirs instead of ad-hoc policy keys.
- Normalization marks changed policies with `updated: true` and preserves
  repo-authored severity/threshold values.

### Phase B: Safe update modes for policy blocks (done)
- Implemented `--policy-mode` with preserve/append-missing/overwrite.
- Added `--managed-blocks-only` to refresh managed blocks without touching
  policies or metadata (to be removed per target behavior).
- Update/install flows now preserve policy blocks unless overwrite is
  explicitly requested.

### Phase C: Selector-role migration (normalizer) (done)
- Migrate selector-ish keys into selector-role triplets (for example
  `guarded_paths`, `user_visible_*`, `user_facing_*`, `doc_quality_*`).
- Map legacy selector keys into `selector_roles` so policies remain consistent
  after updates and installs.
- Warn when selector keys appear without declared selector roles.

### Phase D: Target update behavior alignment (done)
- Remove `--managed-blocks-only` from CLI and update flows.
- Make `append-missing` the default policy-mode for updates.
- Ensure update refreshes core DevCovenant files while preserving custom.
- Delete deprecated core files/folders during update.
- Treat all block-containing files as block-managed.
- Enforce changelog block placement with editable content preserved.
- Ensure metadata normalization runs during default update.

### Phase E: DevCovenant manifest + structure validation (done)
- Define a non-hidden DevCovenant manifest under `devcovenant/` (for example
  `devcovenant/manifest.json`) and create it on install/update or first run
  if missing.
- Manifest schema includes: core directories/files (required), managed docs
  (required), optional docs (allowed), custom directories (allowed), generated
  files (registry/test status), and recorded installer defaults (flags).
- Make `devcov-structure-guard` validate against the manifest (core + managed
  docs) and treat `custom/` as allowed user-writable scope.
- Update the manifest during install/update/uninstall so deprecated core
  paths disappear, new core paths appear, and manual migrations self-heal on
  first DevCovenant run.

### Phase F: Update/install/uninstall convergence (done)
- Share a unified flag schema across install/update/uninstall (single parser
  or shared option registry) so default behavior is consistent.
- Install refuses to run on existing installs and directs users to update or
  uninstall; uninstall remains idempotent and can recover from partial
  installs.
- Update reuses install defaults when appropriate (force docs/config) and
  writes them into the manifest for future updates.
- Default install behavior replaces `CONTRIBUTING.md` and `CHANGELOG.md`,
  backing up prior files as `*_old.md`; no preserve option is exposed for
  these two docs.
- Version handling: reuse existing `VERSION`, otherwise create `VERSION` with
  `0.0.1` when no version argument is supplied.

### Phase G: Tests and validation (in progress)
- Added tests for selector-role migration and key renaming.
- Added tests for update behavior (append-missing + core refresh).
- Added tests for manifest creation/refresh and structure guard usage.
- Verify update behavior against at least two real repos. (pending)

### Phase H: Policy replacement and deprecation workflow (done)
- Added a replacement map (`devcovenant/core/policy_replacements.yaml`)
  and update logic to migrate or remove replaced policies.
- Replaced policies now move to custom with `custom: true` +
  `status: deprecated` when enabled; disabled ones are removed along with
  their custom scripts/fixers.
- Update notices are printed and stored in the manifest.
- Tests cover replacement migration/removal and notification logging.

### Phase I: Managed environment policy
- Introduce a single `managed-environment` policy that replaces
  repo-specific variants (bench/venv).
- Drive behavior via metadata so each repo describes its required environment
  without custom policy text.
- Update docs and templates to reference the unified policy, and ensure the
  standard managed block above policy sections references the unified name.

### Phase J: SemVer scope enforcement
- Rework the semantic version scope policy to validate MAJOR/MINOR/PATCH
  intent (breaking API vs feature vs bugfix).
- Keep the policy present but off by default; document how to enable it
  for public releases (or on demand) and advise against disabling it once
  enabled.
- Reuse normalized metadata fields to declare scope markers and exclusions.
- Update tests and docs to reflect the SemVer rules.

## Documentation and Templates
- Update root docs (`README.md`, `SPEC.md`, `PLAN.md`).
- Update nested docs (`devcovenant/README.md`, templates).
- Document safe update flags and policy-mode semantics.
- Document metadata schema, selector roles, and normalization behavior.
- Document the enforced install/update behavior for
  `CONTRIBUTING.md` and `CHANGELOG.md`, including `_old.md` backups and the
  changelog managed-block marker placement.
- Document the policy replacement workflow, structure manifest behavior, and
  managed-environment policy.
- Document how to enable the SemVer scope policy and why it should stay on
  after public release.
- Document Doc Types (core/optional/custom) in managed blocks, and clarify
  that `CITATION.cff` is custom-only and not installed by default.
  after public release.
- Draft and publish the standard managed doc header and DevCovenant block.

### Managed Doc Header and Block (draft)
Required header for every DevCovenant-managed doc:
```md
# <Title>
```

DevCovenant block (immediately below the header):
```md
<!-- DEVCOV:BEGIN -->
**Doc ID:** PLAN
**Doc Type:** plan
**Managed By:** DevCovenant
<!-- DEVCOV:END -->

```

## Release Readiness
- Run `python -m build` and `twine check dist/*`.
- Confirm console entry points work with `python3 -m devcovenant`.
- Validate `MANIFEST.in` includes updated templates and assets.
- Ensure dependency manifests + `THIRD_PARTY_LICENSES.md` stay aligned.
- Confirm policy replacement notifications appear before release tags.
- Confirm structure manifest updates ship with core updates.

## User Repo Update Path
1. Run `devcovenant update` (default behavior includes normalization).
2. Review policy notices for deprecated or newly available policies.
3. Run `devcovenant update-hashes` if policy text changes were applied.
4. Re-run pre-commit and tests.
5. Log changes in the repo changelog.
6. For a full refresh, run `devcovenant uninstall` and reinstall with the
   intended installer arguments.

## Acceptance Criteria
- Managed blocks refresh without altering policy values by default.
- Metadata normalization inserts/renames keys without overriding values.
- Selector roles are declared per policy; only declared roles are inserted.
- Default update uses `append-missing` for policies.
- Core DevCovenant updates replace core files while preserving custom.
- Deprecated policies migrate or delete with user notification.
- New stock policies trigger user notifications.
- Structure guard validates against the update-shipped manifest.
- Release artifacts build and CI passes.

## Risks and Backout
- Policy replacement automation must be conservative; when unsure, keep the
  old policy and require an explicit user choice.
- If update behavior regresses, revert to `append-missing` plus explicit
  normalization steps until fixed.

## Next Steps
- Complete Phase G validation by verifying updates in two real repos.
- Implement Phase I managed-environment policy.
- Implement Phase J SemVer scope enforcement.
