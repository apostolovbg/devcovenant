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
5. [Install Profiles and Assets (draft)](#install-profiles-and-assets-draft)
6. [Implementation Plan](#implementation-plan)
7. [Documentation and Templates](#documentation-and-templates)
8. [Release Readiness](#release-readiness)
9. [User Repo Update Path](#user-repo-update-path)
10. [Acceptance Criteria](#acceptance-criteria)
11. [Risks and Backout](#risks-and-backout)
12. [Next Steps](#next-steps)

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
- Keep the default policy set unchanged; use install-time language profiles
  to tailor selector defaults for common stacks (and mixed repos).
- Keep custom overrides stable while core policies evolve.
- Provide a first-class policy replacement workflow (deprecate/migrate/remove)
  when core policies are superseded.
- Notify users when new stock policies become available.
- Delete deprecated core files and folders on update so only
  `devcovenant/custom/` stays user-writable.
- Always back up any merged or overwritten file as `*_old.*`, even when a
  merge succeeds.
- Install prompts for one or more profiles from the available list and
  records the selection in config.
- Add `profile_scopes` metadata to every policy; apply policies when any
  active profile matches; use `profile_scopes: global` for global policies.
- Policy-specific assets are created or updated only when the policy is
  enabled; disabled policies do not touch assets.
- Allow only `--disable-policy` at install (repeatable, no prompts).
- If existing DevCovenant artifacts are detected, install prompts to run
  uninstall first; `--auto-uninstall` bypasses the prompt.
- PATH-installed DevCovenant requires a git repo root, checks for local
  `devcovenant/`, and warns on version mismatches.
- Template coverage expands to language/framework profiles with repo
  system files (requirements, CI, pre-commit, etc.).
- Organize templates into `devcovenant/core/templates/global/`,
  `devcovenant/core/templates/profiles/<profile>/`, and
  `devcovenant/core/templates/policies/<policy>/`; mirror with
  `devcovenant/custom/templates/` for overrides, and avoid template files
  at the package root unless required for packaging.
- Require global applicability via `profile_scopes: global` (no separate
  global key).
- Version discovery order: `VERSION` file, then version fields in
  `pyproject.toml` or profile-specific metadata, then prompt; default to
  `0.0.1` when nothing is found and no prompt is triggered.
- Uninstall removes only DevCovenant-managed assets (per manifest) and
  never deletes user-owned repo files; profile-created files are removed
  only if recorded as DevCovenant-managed.

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


## Install Profiles and Assets (draft)
DevCovenant installs policy assets and repo system files based on active
profiles. Profiles are selected at install time and recorded in config so
future updates can apply the same profile-aware rules.

### Profile selection
Install prompts for one or more profiles from the available catalog. Multiple
profiles are allowed, and the chosen values are stored as `active_profiles`.
This is the only interactive prompt besides auto-uninstall.

Example prompt:
```text
Available profiles (select one or more):
1) python
2) javascript
3) docs
4) data
5) go
6) rust
7) java
8) php
9) ruby
10) dotnet
11) c-cpp
Selection: 1,3,4
```

### Profile catalog (shipped examples)
Profiles are open-ended, lowercase, and user-extendable. The stock catalog
ships with common languages, frameworks, and tooling; any name is valid.

Language profiles (shipped):
```text
python
javascript
typescript
go
rust
java
kotlin
scala
groovy
c
cpp
objective-c
swift
csharp
fsharp
dotnet
php
ruby
elixir
erlang
clojure
haskell
ocaml
lua
pascal
fortran
cobol
dart
r
matlab
julia
perl
bash
powershell
nim
zig
crystal
scheme
lisp
prolog
```

Framework/tooling profiles (shipped):
```text
django
flask
fastapi
rails
laravel
symfony
spring
quarkus
micronaut
express
nestjs
frappe
nextjs
nuxt
react
angular
vue
svelte
flutter
```

Data and ops profiles (shipped):
```text
docs
data
sql
terraform
ansible
docker
kubernetes
```

### Policy applicability via profile_scopes
Every policy block includes `profile_scopes`. A policy applies when any
active profile matches a listed scope. Global policies explicitly set
`profile_scopes: global`. Empty lists are normalized to `global`.

Example metadata (scoped):
```yaml
profile_scopes:
  - python
  - docs
```

Example metadata (global):
```yaml
profile_scopes:
  - global
```

### Policy assets and templates
Policy-required files are created or updated only when the policy is enabled
and its profile scopes match the active profiles. Templates live under
`devcovenant/core/templates/` and are selected by profile.

Examples:
- `dependency-license-sync` (enabled) creates or refreshes
  `THIRD_PARTY_LICENSES.md` and `licenses/`.
- `devflow-run-gates` installs `tools/run_pre_commit.py`,
  `tools/run_tests.py`, and `tools/update_test_status.py`.
- `version-sync` ensures `VERSION` exists and is up to date.
- `changelog-coverage` installs `CHANGELOG.md` from the template.
- `managed-environment` uses metadata only and does not create files.

### Template layout and asset mapping
Templates are grouped by scope to keep installs predictable and to avoid
shipping templates at the package root. Layout:
```text
devcovenant/core/templates/global/
devcovenant/core/templates/profiles/<profile>/
devcovenant/core/templates/policies/<policy>/
devcovenant/custom/templates/global/
devcovenant/custom/templates/profiles/<profile>/
devcovenant/custom/templates/policies/<policy>/
```
Global templates cover shared docs and tooling; profile templates cover
language/framework-specific assets (requirements, CI, pre-commit, etc.),
and policy templates cover assets required by a specific policy. Custom
templates override core templates when the folder names match. A policy
asset map (planned) links policies + profiles to template sets.
Any custom profile or policy template folder is preserved on update.

### Version discovery order
Install checks for version metadata in this order:
1. `VERSION` file at repo root.
2. Version fields in `pyproject.toml` or profile-specific files.
3. Prompt the user (if allowed).
If nothing is found and no prompt is triggered, default to `0.0.1`.

### Merge and backup rules
All template writes back up the current file as `*_old.*`, even when a merge
succeeds. When merge fails, the new template file includes the prior content
with a visible reconciliation banner.

Example banner:
```text
# DEVCOv: MERGE REQUIRED
# Original content appended below from README_old.md.
```

### PATH-installed behavior and version checks
When the `devcovenant` console script is used:
- It must run from a git repo root.
- It checks for `./devcovenant/` in the current repo.
- If a local DevCovenant version is older, the CLI advises using
  `python3 -m devcovenant` from the repo or running `devcovenant update`.
- If a local version is newer, the CLI advises upgrading the system package.

Example warning:
```text
Local DevCovenant (0.2.4) is older than the installed CLI (0.2.6).
Run: python3 -m devcovenant update --target .
```

### Auto-uninstall prompt
If DevCovenant artifacts are detected, install prompts to uninstall first.
Use `--auto-uninstall` to run non-interactively.

Example prompt:
```text
DevCovenant artifacts detected in this repo.
Run uninstall before install? [y/N]
```
## Implementation Plan

### Remaining Phases (in order)


#### Phase J: SemVer scope enforcement
- Rework the semantic version scope policy to validate MAJOR/MINOR/PATCH
  intent (breaking API vs feature vs bugfix).
- Keep the policy present but off by default; document how to enable it
  for public releases (or on demand) and advise against disabling it once
  enabled.
- Reuse normalized metadata fields to declare scope markers and exclusions.
- Update tests and docs to reflect the SemVer rules.

### Policy Scope Map (stock, versioned)
This map is a planning checklist. The authoritative scope list is the
`profile_scopes:` metadata in each policy block. Every stock policy must
list all profiles where it is valid.

Asset precedence when paths collide:
1) profile assets override policy assets
2) custom overrides core (for both assets and catalogs)

Global-only (profile_scopes: global only):
- devcov-self-enforcement
- devcov-structure-guard
- policy-text-presence
- stock-policy-text-sync
- devflow-run-gates
- changelog-coverage
- no-future-dates
- read-only-directories
- managed-environment
- semantic-version-scope (off by default)
- policy-replacements (update-only, no runtime enforcement)

Global + profile overlays (profile_scopes include global + profiles):
- version-sync
  profiles: python,django,flask,fastapi,frappe
  javascript,typescript,express,nestjs,nextjs,nuxt,angular,react,vue,svelte
  php,laravel,symfony
  ruby,rails
  java,kotlin,spring,quarkus,micronaut
  go,rust,csharp,dotnet
  dart,flutter
  swift,scala,clojure,elixir,erlang
- dependency-license-sync
  same profile scopes as version-sync
- last-updated-placement
  profiles: global + docs,data,ansible,docker,kubernetes,terraform,sql
- documentation-growth-tracking
  profiles: global + all user-facing language/framework profiles
- line-length-limit
  profiles: global + all profiles (suffix coverage via profiles)

Profile-scoped (language/framework specific):
- docstring-and-comment-coverage
  profiles: python,django,flask,fastapi,frappe
- name-clarity
  profiles: python,django,flask,fastapi,frappe
- new-modules-need-tests
  profiles: python,django,flask,fastapi,frappe
- security-scanner
  profiles: python,django,flask,fastapi,frappe

Custom profiles and policies:
- Custom profiles define their own assets and policy metadata overlays in
  custom catalogs and templates; matching core entries are overridden.
- Custom policies should list profile_scopes explicitly and may reuse
  overlay files from profile assets when applicable.

Follow-up implementation tasks:
- Add language-specific AST/scanner adapters so the Python-only policies
  can expand to additional languages (name clarity, docstrings, tests,
  security scanning).
- Populate profile assets and metadata overlays so each shipped profile is
  complete (dependency manifests, build files, ignore fragments, and
  profile-specific docs).


### Completed Phases
#### Phase L: Profile-driven config + gitignore assets
- Ship exemplar `devcovenant/custom/profile_catalog.yaml` and
  `devcovenant/custom/policy_assets.yaml` so custom profiles and policy
  assets can override core entries by name.
- Move profile assets into per-profile `profile.yaml` manifests under
  `devcovenant/core/templates/profiles/<profile>/` with optional
  `.gitignore` fragments and profile-scoped assets.
- Add `gitignore_base.txt` and `gitignore_os.txt` under
  `templates/global/`, and assemble `.gitignore` in this order:
  global base → profile fragments → OS fragment → user section.
- Apply profile policy overlays from profile manifests to
  `devcovenant/config.yaml` so profile metadata drives policy scope.
- Update docs/specs to describe profile manifests, overlay merging, and
  gitignore merge behavior.

#### Phase I: Managed environment policy (done)
- Replaced bench/venv policies with `managed-environment`, driven by
  metadata (`expected_paths`, `expected_interpreters`, `required_commands`,
  `command_hints`) and off by default.
- Updated docs and templates to reference the unified policy and the
  managed-environment guidance in the managed AGENTS block.

#### Phase G: Tests and validation (done)
- Added tests for selector-role migration and metadata normalization.
- Added tests for update behavior (append-missing + core refresh).
- Added tests for manifest creation/refresh, structure guard usage, and
  profile-aware asset installation.

#### Phase K: Profile-aware install and asset merges (done)
- Added a profile catalog and interactive profile selection on install,
  recording active profiles in config and the manifest.
- Introduced `profile_scopes` for every policy and normalized legacy entries
  to `profile_scopes: global`; policies now apply when any active profile
  matches.
- Shipped `policy_assets.yaml` to map templates and merge rules by
  policy/profile, and wired the installer to apply those assets.
- Skipped asset creation when a policy is disabled or outside the active
  profiles, including policy-scoped assets.
- Expanded profile templates under `devcovenant/core/templates/profiles/`,
  with shared assets in `devcovenant/core/templates/global/` and overrides
  in `devcovenant/custom/templates/`.
- Enforced repo-root detection and CLI version mismatch warnings for
  PATH-based usage.

#### Phase E: DevCovenant manifest + structure validation (done)
- Defined a non-hidden DevCovenant manifest under `devcovenant/` and
  ensured it is created on install/update or first run when missing.
- Manifest schema now tracks core layout, managed docs, active profiles,
  and policy asset mappings.
- Structure guard validates against the manifest, treating `custom/` as
  allowed user-writable scope.
- Install/update/uninstall refresh the manifest so deprecated core paths
  disappear and new core paths appear.

#### Phase F: Update/install/uninstall convergence (done)
- Share a unified flag schema across install/update/uninstall (single parser
  or shared option registry) so default behavior is consistent.
- Install refuses to run on existing installs and directs users to update or
  uninstall; uninstall remains idempotent and can recover from partial
  installs.
- Add `--disable-policy` and `--auto-uninstall` to the shared option set;
  install prompts for auto-uninstall when artifacts exist.
- Always back up merged or overwritten files as `*_old.*`, even on successful
  merges, and note the backups in install logs.
- Update reuses install defaults when appropriate (force docs/config) and
  writes them into the manifest for future updates.
- Default install behavior replaces `CONTRIBUTING.md` and `CHANGELOG.md`,
  backing up prior files as `*_old.md`; no preserve option is exposed for
  these two docs.
- Version handling: prefer an existing `VERSION`, otherwise read version
  fields from `pyproject.toml` or profile-specific files, otherwise prompt;
  default to `0.0.1` when nothing is found and prompting is skipped.

#### Phase A: Policy metadata schema + normalization (done)
- Defined a canonical metadata schema using template policy blocks, with
  every script-supported key present (empty values preserve defaults).
- Added `devcovenant normalize-metadata` to insert missing keys in order
  without changing existing values.
- Standardize selector roles so `user_visible`, `user_facing`, and
  `doc_quality` are declared via `selector_roles` and stored as role-specific
  globs/files/dirs instead of ad-hoc policy keys.
- Normalization marks changed policies with `updated: true` and preserves
  repo-authored severity/threshold values.

#### Phase B: Safe update modes for policy blocks (done)
- Implemented `--policy-mode` with preserve/append-missing/overwrite.
- Added `--managed-blocks-only` to refresh managed blocks without touching
  policies or metadata (to be removed per target behavior).
- Update/install flows now preserve policy blocks unless overwrite is
  explicitly requested.

#### Phase C: Selector-role migration (normalizer) (done)
- Migrate selector-ish keys into selector-role triplets (for example
  `guarded_paths`, `user_visible_*`, `user_facing_*`, `doc_quality_*`).
- Map legacy selector keys into `selector_roles` so policies remain consistent
  after updates and installs.
- Warn when selector keys appear without declared selector roles.

#### Phase D: Target update behavior alignment (done)
- Remove `--managed-blocks-only` from CLI and update flows.
- Make `append-missing` the default policy-mode for updates.
- Ensure update refreshes core DevCovenant files while preserving custom.
- Delete deprecated core files/folders during update.
- Treat all block-containing files as block-managed.
- Enforce changelog block placement with editable content preserved.
- Ensure metadata normalization runs during default update.

#### Phase H: Policy replacement and deprecation workflow (done)
- Added a replacement map (`devcovenant/core/policy_replacements.yaml`)
  and update logic to migrate or remove replaced policies.
- Replaced policies now move to custom with `custom: true` +
  `status: deprecated` when enabled; disabled ones are removed along with
  their custom scripts/fixers.
- Update notices are printed and stored in the manifest.
- Tests cover replacement migration/removal and notification logging.

## Documentation and Templates
- Update root docs (`README.md`, `SPEC.md`, `PLAN.md`).
- Update nested docs (`devcovenant/README.md`, templates).
- Document safe update flags and policy-mode semantics.
- Document metadata schema, selector roles, and normalization behavior.
- Document policy scope categories (global-only, profile-scoped, language
  scoped) and include the initial scope list for stock policies.
- Document profile metadata overlays for policy files (version sync,
  dependency tracking, doc scopes) and how overlay merging works.
- Document the enforced install/update behavior for
  `CONTRIBUTING.md` and `CHANGELOG.md`, including `_old.md` backups and the
  changelog managed-block marker placement.
- Document the policy replacement workflow, structure manifest behavior, and
  managed-environment policy.
- Document template layout (`core/templates` + `custom/templates`) and how
  profile- and policy-scoped assets are selected during install/update.
- Document the version discovery order and default `0.0.1` fallback.
- Document profile selection prompts, `profile_scopes`, and how mixed
  profiles affect policy applicability and assets.
- Document policy asset templates and the rule that disabled policies do
  not create or update their files.
- Document the `*_old.*` backup rule for every merge or overwrite.
- Document the PATH CLI repo-root checks, local version warnings, and the
  `--auto-uninstall` flow.
- Add a core policy guide in `devcovenant/README.md` describing each stock
  policy: intent, usage, default config, and expected repo impact.
- Document how to enable the SemVer scope policy and why it should stay on
  after public release.
- Document Doc Types (core/optional/custom) in managed blocks, and clarify
  that `CITATION.cff` is custom-only and not installed by default.
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
- Every merge or overwrite creates an `*_old.*` backup.
- Profile selection prompts run at install and are stored in config.
- `profile_scopes` gates policy applicability and asset creation.
- `profile_scopes: global` marks explicit global policies.
- Template layout uses `templates/global` and `templates/profiles`.
- Version discovery follows VERSION → pyproject/profile → prompt → 0.0.1.
- Install respects `--disable-policy` and skips disabled policy assets.
- Install prompts to auto-uninstall when artifacts exist and honors
  `--auto-uninstall`.
- PATH-installed CLI enforces repo-root checks and version mismatch
  guidance.
- Release artifacts build and CI passes.

## Risks and Backout
- Policy replacement automation must be conservative; when unsure, keep the
  old policy and require an explicit user choice.
- If update behavior regresses, revert to `append-missing` plus explicit
  normalization steps until fixed.

## Next Steps
- Phase J: SemVer scope enforcement.
