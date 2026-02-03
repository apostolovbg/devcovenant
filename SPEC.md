# DevCovenant Specification
**Last Updated:** 2026-02-03
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** SPEC
**Doc Type:** specification
**Managed By:** DevCovenant
<!-- DEVCOV:END -->

This specification defines the required behavior for the DevCovenant engine,
CLI, installer, and managed documentation. The codebase is the source of
truth; this document must stay aligned with `devcovenant/core/` and the
installer scripts.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Functional Requirements](#functional-requirements)
4. [Policy Requirements](#policy-requirements)
5. [Installation Requirements](#installation-requirements)
6. [Packaging Requirements](#packaging-requirements)
7. [Non-Functional Requirements](#non-functional-requirements)

## Overview
DevCovenant turns policy documentation into executable checks. Policies are
written in `AGENTS.md`, parsed into structured metadata, and enforced by the
engine. The system must keep documentation, enforcement logic, and registry
hashes synchronized so drift is detectable and reversible.

## Workflow
- Run the gated workflow for every change: pre-commit start, tests,
  pre-commit end.
- `pre-commit --phase start` must run before edits but is not required to leave
  the tree clean; it simply captures a gate snapshot and identifies existing
  issues. Later phases still rerun hooks/tests until the workspace is clean.
- If start is recorded after edits, the gate issues a warning and brief
  pause instead of blocking, but a clean `start → tests → end` run is still
  required to pass.
- If end-phase hooks or DevCovenant autofixers change the working tree, rerun
  the required tests (and rerun hooks if needed) until the repo is clean, then
  record only that final successful pass in `.devcov-state/test_status.json`.
Devflow gate status is stored in `.devcov-state/test_status.json`, created
  on demand, and treated as gitignored state.
- Run a startup check at session start (`python3 -m devcovenant check --mode
  startup`).
- When policy text changes, set `updated: true`, update scripts/tests, run
  `devcovenant update-policy-registry`, then reset `updated: false`.
- Log every change in `CHANGELOG.md` under the current version header.

## Functional Requirements
### Policy definitions and registry
- Parse policy blocks from `AGENTS.md` and capture the descriptive text that
  follows each `policy-def` block.
- Hash policy definitions and scripts into
  `devcovenant/registry/local/policy_registry.yaml`.
- Expose `restore-stock-text` to reset policy prose to canonical wording.
- Support `custom: true/false` metadata to mark custom policy prose that
  bypasses stock text sync checks.
- Provide an optional semantic-version-scope policy (`apply: false` by
  default) that requires one SemVer scope tag in the latest changelog
  entry and matches the bump to major/minor/patch semantics.
- Maintain a canonical metadata schema that lists all supported keys (common
  and policy-specific) as well as every available policy ID (core and
  custom) so normalization can add missing keys, keep the alphabetic policy
  list intact, and signal the presence of custom policies without mutating
  user-supplied metadata or policy text. The schema lives under
  `devcovenant/registry/local/policy_metadata_schema.yaml`, is ignored by VCS,
  and is regenerated automatically at engine startup and during policy
  refresh/update so CI and users never rely on a packaged copy.

### Engine behavior
- Load policy modules from `devcovenant/core/policies/<id>/<id>.py` with
  custom overrides in `devcovenant/custom/policies/<id>/<id>.py`.
- Load language adapters from `devcovenant/core/policies/<id>/adapters/`
  with custom overrides in `devcovenant/custom/policies/<id>/adapters/`.
  Custom adapters override core for the same policy + language.
- When a custom policy module exists, it fully replaces the built-in policy
  and suppresses core fixers for that policy.
- Respect `apply`, `severity`, `status`, and `enforcement` metadata for each
  policy.
- Support `startup`, `lint`, `pre-commit`, and `normal` modes.
- Apply auto-fixers when allowed, using fixers located under
  `devcovenant/core/policies/<id>/fixers/` and any custom fixers under
  `devcovenant/custom/policies/<id>/fixers/`.
- Fixers are language-aware: policy fixers live in per-policy folders as
  `fixers/global.py` plus optional language-specific files (for example
  `fixers/python.py`, `fixers/js.py`). When no language-specific fixer is
  available, the engine falls back to `global.py`.
- Not every policy ships with a fixer. Some policies will remain fixerless
  by design and are documented as such in the core policy guide.

### CLI commands
- Provide a console entry point (`devcovenant`) and module entry
  (`python3 -m devcovenant`) that both route to the same CLI. Docs should
  default to the console entry point and mention the `python3 -m ...` form
  once as the fallback when the CLI is not on PATH.
- Documentation should use `python3` (not `python`) for all source-based
  workflows and command examples.
- Supported commands: `check`, `test`, `update-policy-registry`,
  `restore-stock-text`, `install`, `update`, `uninstall`.
- `check` runs in two modes:
  - `audit` (default): no auto-fixes; exits non-zero on blocking violations or
    sync issues.
  - `fix`: allows policy fixers; still exits non-zero if blocking issues
    remain.
- `test` runs `pytest` plus `python3 -m unittest discover` against `tests/`
  (mirrors the package layout under `tests/devcovenant/` but stays outside the
  installable package).
- `install` and `uninstall` delegate to `devcovenant/core/install.py` and
  `devcovenant/core/uninstall.py`.
- `update` supports managed-block-only refreshes and policy-mode control.
- Explicit normalize-metadata command is unnecessary; refresh/update already
  normalize metadata via descriptors + overrides + schema.

### Install, update, refresh model
- `install` bootstraps DevCovenant into a repo. It must detect existing
  DevCovenant artifacts and refuse to proceed (or redirect to `update`)
  unless the user explicitly confirms or supplies `--auto-uninstall`.
- `update` refreshes DevCovenant-managed content without changing user
  metadata: refresh managed blocks, regenerate registries, update bundled
  assets, and leave user overrides intact. It must not overwrite an existing
  `devcovenant/` folder with itself.
- `refresh` (via `refresh-all`) rebuilds registries and policy metadata from
  the current config/profile state without forcing stock defaults. It is the
  explicit “regenerate from existing config” command.
- “Restore to stock metadata/profile configuration” is a separate command
  (planned) and must not be conflated with `update` or `refresh`.
- Source-based usage must use `python3 -m devcovenant ...` when invoking
  from a repo checkout; the installed CLI is the default for packaged usage.

#### Install/update scenarios
1. Empty repo: `install` lays down default config, managed docs, and policy
   scaffolding.
2. Non-empty repo: `install` injects managed blocks and default docs only
   when missing/empty/placeholder; preserved user content stays intact.
3. Existing DevCovenant: `install` routes to `update`/`refresh` and avoids
   mangling user config or custom policies.

#### Command matrix (behavioral intent)
- `install`: bootstrap DevCovenant in a repo.
  It makes no config changes beyond defaults, refreshes managed docs, and
  rebuilds registries.
- `update`: refresh DevCovenant-managed content without changing config.
  It refreshes managed docs and rebuilds registries.
- `refresh-all`: rebuild registries/metadata from the current config without
  touching managed docs.
- `reset-to-stock` (planned): restore stock metadata/profile config, updating
  config, docs, and registries.

### Command/script placement
- User-facing, runnable commands live at the `devcovenant/` root and are
  exposed through the CLI (and callable via `python3 -m devcovenant`).
- Implementation logic lives under `devcovenant/core/` as internal modules.
- `devcovenant/core/tools/` is not a public entrypoint surface; any helper
  meant for users must have a CLI command and a top-level module.
- CLI-exposed command modules include (non-exhaustive): `check.py`,
  `sync.py`, `test.py`, `install.py`, `update.py`, `uninstall.py`,
  `refresh_all.py`, `refresh_policies.py`, `update_policy_registry.py`,
  `update_lock.py`, `update_test_status.py`, `run_pre_commit.py`,
  `run_tests.py`, and `restore_stock_text.py`. `run_tests.py` executes the
  merged `devflow-run-gates.required_commands` list resolved from profiles
  and config (defaults remain pytest + unittest) and records the exact command
  string to `update_test_status`. The corresponding implementations live under
  `devcovenant/core/`. Language-aware policies delegate parsing/checking to
  per-language adapters under `devcovenant/core/policies/<policy>/adapters/
  <lang>.py`; core policy modules remain language-agnostic.

### Documentation management
- Every managed doc must include `Last Updated` and `Version` headers.
- `devcovenant/README.md` also includes `DevCovenant Version`, sourced from
  the installer package version.
- Every managed doc must include a top-of-file managed block inserted just
  below the header lines. The block records the `Doc ID`, `Doc Type`, and
  management ownership, and uses the standard markers:
  `<!-- DEVCOV:BEGIN -->` and `<!-- DEVCOV:END -->`.
- `AGENTS.md` opens with a concise “operational orientation” outlining the
  enforced workflow (pre-commit start/tests/pre-commit end) and the managed
  environment expectations. It points readers to `devcovenant/README.md` for
  the broader command set so agents know how to interact with the repo before
  reaching the policy blocks.
- The policy block is the text between `<!-- DEVCOV-POLICIES:BEGIN -->` and
  `<!-- DEVCOV-POLICIES:END -->` inside `AGENTS.md` and must be treated as a
  dedicated DevCovenant-managed unit. Policy entries are ordered
  alphabetically (no enabled/disabled grouping) and list every available
  policy, including custom overrides (automatically marked with
  `custom: true`).
- Managed documents (AGENTS.md, README.md, SPEC.md, PLAN.md, CHANGELOG.md,
  CONTRIBUTING.md, and devcovenant/README.md) are generated from YAML assets
  that supply the full document structure, header metadata, and managed
  block scaffolding. Outside-of-block stock text is injected only when a
  target document is missing, empty, or effectively a single-line placeholder;
  otherwise install/update/refresh regenerate only the managed blocks.
- The `last-updated-placement` policy runs with auto-fix enabled so touched
  managed docs receive a UTC `Last Updated` header update during each run
  (`python3 devcovenant check --fix`), keeping the timestamp aligned with the
  latest change.
- To capture the deep knowledge we accumulate while evolving DevCovenant, the
  custom `devcovrepo` profile must extend `documentation-growth-tracking` so
  it explicitly monitors `devcovenant/docs` alongside the usual docs.
  `README.md` remains the quick-start/priority logic surface, but the policy
  keeps `devcovenant/docs` healthy—full of constructive narratives,
  overrides, custom-profile pointers, and advanced workflows—without
  drifting into noise. List the folder in the profile overlay so the policy
  treats it like any other managed doc target.

### Configuration and extension
- `devcovenant/config.yaml` must support `devcov_core_include` and
  `devcov_core_paths` for core exclusion.
- Config is generated from global defaults plus active profiles and must
  include `profiles.generated.file_suffixes` so profile selections are
  visible to users and tooling.
- Config exposes `version.override` so config-driven installs can declare
  the project version that templated assets (for example, `pyproject.toml`)
  should use when no `VERSION` file exists yet.
- Provide the dedicated `devcovrepo`/`devcovuser` profiles so the DevCovenant
  repository can opt into its own test overrides while user repositories keep
  `devcovenant/**` out of enforcement while still keeping
  `devcovenant/custom/**` monitored.
- The `global` profile is always active. Other shipped defaults (`docs`,
  `data`, `suffixes`) are enabled by default but can be trimmed from
  `profiles.active` when a user wants to stop applying their assets or
  metadata overlays.
- Config should expose global knobs for `paths`, `docs`, `install`,
  `update`, `engine`, `hooks`, `reporting`, `ignore`,
  `autogen_metadata_overrides`, and `user_metadata_overrides` so repos can
  tune behavior without editing core scripts. Every generated config must
  list every known knob (even if the default value is blank) so the file
  doubles as an override template that documents every supported option;
  only the policy overrides sections may remain empty to avoid
  overwhelming the document.
- Config also exposes `doc_assets` (with `autogen` and `user` lists).
  Repositories can drive which managed docs the active profiles (for example,
  `global`, `docs`, `devcovenant`) synthesize versus which remain purely
  user-maintained.
- This mirrors the policy override structure (`autogen_metadata_overrides` and
  `user_metadata_overrides`) so teams can lift the default curated assets into
  their own configs when needed.
- The profile catalog is generated into
  `devcovenant/registry/local/profile_catalog.yaml` by scanning
  profile manifests.
- Active profiles are recorded under `profiles.active` in config and extend
  file suffix coverage through catalog definitions.
- Custom profiles are declared by adding a profile manifest plus assets
  under `devcovenant/custom/profiles/<name>/`.
- Profile assets live under `devcovenant/core/profiles/<name>/assets/` and
  `devcovenant/custom/profiles/<name>/assets/`, with `global/assets/`
  covering shared docs and tooling.
- Policy assets are declared inside policy folders under
  `devcovenant/core/policies/<policy>/assets/`. Install/update compiles
  the results into `devcovenant/registry/local/policy_assets.yaml`. Custom
  overrides live under `devcovenant/custom/policies/<policy>/assets/`.

### Pre-commit configuration by profile
- Each profile can declare a `precommit` fragment describing the repos
  and hooks it requires; the fragments are cataloged inside
  `devcovenant/registry/local/profile_catalog.yaml` under the profile
  manifest metadata so installs can regenerate `.pre-commit-config.yaml`
  whenever profile selections change.
- The merge order for `.pre-commit-config.yaml` is:
-  1. global profile defaults and the shared base fragment managed by
-     DevCovenant, ensuring a consistent baseline.
-  2. active profile fragments (in the order listed in `profiles.active`).
-  3. overrides supplied via `config.yaml`.
-     They follow the existing metadata override pattern.
-  4. a user-provided `.pre-commit-config.yaml` that may exist at the repo
     root, allowing manual overrides without touching generated assets.
- The CLI merges the fragments into `.pre-commit-config.yaml` before running
  the hooks. `devcovenant/registry/local/manifest.json` records the resolved
  hook set so commands such as `run_pre_commit.py` know which config to
  execute and can rerun the merge if profiles change during a session.
- Include a “Pre-commit config refactor” phase in `PLAN.md` that references
  this SPEC section and clarifies the merge metadata keys.
- Add tests verifying the generated config matches the manifest for sample
  profile combinations.
- Assets install only when a policy is enabled and its `profile_scopes`
  match active profiles.
- Template indexes live at `devcovenant/core/profiles/README.md` and
  `devcovenant/core/policies/README.md`.
- Profile assets and policy overlays live in profile manifests at
  `devcovenant/core/profiles/<name>/profile.yaml`, with custom overrides
  under `devcovenant/custom/profiles/<name>/profile.yaml`. Profile assets
  are applied for active profiles, and profile overlays merge into
  `config.yaml` under `autogen_metadata_overrides` (with
  `user_metadata_overrides` taking precedence when set).
- A lightweight check wrapper ships as `devcovenant/core/check.py` and can
  be invoked with `python3 -m devcovenant.core.check` to run the CLI from
  source installs.
- Managed-document templates include stock non-managed text for each
  devcovenant-managed doc, injected only when the target doc is missing,
  empty, or a single-line placeholder. Otherwise only managed blocks are
  refreshed. `AGENTS.md` is a special case: the stock `# EDITABLE SECTION`
  header is always inserted ahead of preserved user text so the editable
  notes remain anchored beneath the marker.

## Policy Requirements
- Every policy definition includes descriptive prose immediately after the
  metadata block.
- Built-in policies have canonical text stored in
  `devcovenant/registry/global/stock_policy_texts.yaml`.
- Policies are activated by profiles: a policy is in scope only when a profile
  lists it (or config overlays add it). There is no implicit execution; the
  `global` profile must be active and must list every global policy. Core
  policy YAMLs retain `profile_scopes` as documentation; effective scopes are
  derived from profiles plus config overlays during registry generation.
  Custom policies are activated only via custom profiles or config overrides,
  not by the `global` profile. POLICY_MAP.md and PROFILE_MAP.md are the
  authoritative references for required assets, adapters, policies, and
  overlays; keep them aligned with the manifests and code.
Profiles are explicit—no inheritance or family defaults; each profile lists
its own assets, suffixes, policies, and overlays.
- Custom policy `readme-sync` enforces that `devcovenant/README.md` mirrors
  `README.md` with repository-only blocks removed via
  `<!-- REPO-ONLY:BEGIN -->` / `<!-- REPO-ONLY:END -->` markers. Its auto-fix
  rewrites the packaged guide from the repo README.
- The policy list is generated from the active profiles/config and includes
  every available core/custom policy. Entries are ordered alphabetically and
  custom overrides are marked with `custom: true`.
- `apply: false` disables enforcement without removing definitions.
- Provide a `managed-environment` policy (off by default) that
  enforces execution inside the expected environment when
  `apply: true`. It must warn when `expected_paths` or
  `expected_interpreters` are empty, warn when `command_hints`
  are missing, and report missing `required_commands` as warnings.
- `fiducial` policies remain enforced and always surface their policy text.
- Selector keys (`include_*`, `exclude_*`, `force_*`, `watch_*`) are supported
  across policy definitions for consistent scoping.
- Policy metadata normalization must be able to add missing keys without
  changing existing values or policy text. Move broad suffix/prefix/glob
  defaults out of base policies into profile overlays (python/docs/lang-
  specific, devcovrepo) so policy YAMLs carry only minimal/common scope.
  Audit all policies and relocate hard-coded metadata into profiles where
  appropriate.
- `devcov-parity-guard` replaces the legacy stock-text policy and compares
  AGENTS policy prose to descriptor YAML text for both core and custom
  policies.
- Dogfood-only policies (`patches-txt-sync`, `gcv-script-naming`,
  `security-compliance-notes`) are not shipped in the DevCovenant repo.
- Support policy replacement metadata via
  `devcovenant/registry/global/policy_replacements.yaml`.
  During updates, replaced policies move to custom and are marked deprecated
  when enabled; disabled policies are removed along with their custom scripts
  and fixers.
- Record update notices (replacements and new stock policies) in
  `devcovenant/registry/local/manifest.json` and print them to stdout.
- Treat the collective `<!-- DEVCOV-POLICIES:BEGIN -->` /
  `<!-- DEVCOV-POLICIES:END -->` block as a managed unit that install/update
  commands refresh from `devcovenant/core/` assets.
  Provide a per-policy `freeze`
  override that copies the policy’s modules, descriptors, and assets into
  `devcovenant/custom/` (with `custom: true`) when true and removes those files
  when the flag clears.
  Always rerun `devcovenant update-policy-registry` (and any needed registry
  fixes) so the registry records the custom copy. Auto-fixers should be devised
  for every policy and wired through the per-policy adapters.
  They work across every language/profile combination that the policy supports.
- Generate `devcovenant/registry/local/policy_registry.yaml` dynamically from
  `refresh_policies` and `update_policy_registry`. The YAML tracks every
  policy (enabled or disabled) with its metadata schema (from the policy YAML
  `metadata` keys), resolved metadata values (merged defaults/overrides,
  apply/freeze, selectors, severity, hashes, asset hints, provenance), profile
  scopes, and enabled flag so the registry is the canonical policy map.
- The legacy `devcovenant/registry.json` storage and the accompanying
- `update_hashes.py` helper were retired and removed, leaving
- `devcovenant/registry/local/policy_registry.yaml` as the single
- canonical hash store. Any residual legacy artifacts in the tree
- should be deleted during the cleanup phase (registry.json,
- config_old.yaml, GPL license template) and removed from manifests,
- schemas, and policy references so refresh/install no longer expect
- them.


-### Policy definition YAML
- Each policy (core, frozen, or custom) ships with a `<policy>.yaml` that
- contains:
  ```
  id: changelog-coverage
  text: |
    Every substantive change must be recorded ...
  metadata:
    severity: error
    profile_scopes: [global]
    include_suffixes: [.md]
    selectors:
      include_files: [...]
    overrules: [...]
    enforcement: active
  ```
- Metadata keys double as the canonical schema for that policy:
- whatever appears under `metadata` automatically becomes part of the
- `metadata_schema` block inside
  `devcovenant/registry/local/policy_registry.yaml` and is consumed by
  generators and overrides. The resolved metadata (merged defaults, overrides,
  apply/freeze, selectors, severity, hashes, and asset hints) lives in the
  companion `metadata_values` block so downstream tooling can read both schema
  and values from the same entry. No separate `status`/`updated` flags are
  required because provenance (core vs. frozen/custom loading path)
  determines whether the generated entry is marked `custom` and whether
  future updates automatically refresh the stock text.
- Loader logic synthesizes policy entries directly from these YAML files,
- merges `config.yaml` overrides on top of `metadata`, and regenerates
- both `AGENTS.md` and `policy_registry.yaml` from the same source so policy
- truth lives in YAML instead of ad-hoc hand-editing.
- When DevCovenant removes a core policy, the updater copies it to
- `devcovenant/custom/policies/` (or a frozen overlay defined in config),
- marks the new copy as `custom`, and reruns `update-policy-registry` so the
- management docs, notices, and registry reflect the deprecated version.
- `config.yaml` exposes:
  - `autogen_do_not_apply`: multi-line list whose entries become
    `apply: false` in the resolved metadata block (profile-driven defaults).
  - `manual_force_apply`: manual override list that flips `apply: true`
    even when `autogen_do_not_apply` disables a policy.
  - `freeze_core_policies`: list whose IDs toggle `freeze: true`; when a
    custom policy appears here, the generator drops it and reports that
    custom texts do not need freezing.
  - `policy_overrides`: a keyed map (policy ID → overrides) that reconfigures
    `severity`, `enforcement`, selectors, or any other inferred schema key
    without touching the YAML text. Overrides merge before AGENTS/registry
    generation so user edits stay declarative.
  - `manual_force_apply` overrides `autogen_do_not_apply` during registry
    generation so the resolved `apply` flag is always derived from the active
    config lists rather than hand-edited policy metadata.
- Config-defined metadata overlays merge with the existing metadata
  values, deduplicating any repeats, so the generators do not repeat
  identical entries when the overrides merely augment the base schema.
- Core profiles stay immutable; to attach a custom policy to a core profile,
  use `profile_overlays.<profile>.custom_policies` in config. Registry
  generation adds those policy IDs to the profile’s scope; profile-specific
  metadata for custom policies should live in custom profiles, not in config.
- Generated configs must list every supported key, even when empty, including
  the `profile_overlays` section, so users see all available hooks.
- `policy_registry.yaml` only records the `profile_scopes` matching the current
  `profiles.active` list (plus `global`). The normalization pipeline
  trims scope values before writing the `metadata_values` block so the
  canonical registry reflects the active profile surface.
- `raw-string-escapes` remains a core policy, but it is scoped to `python`
  metadata only and defaults to `apply: false` via the python profile’s
  `autogen_do_not_apply` overlay. Users can enable it via
  `manual_force_apply`.
- Add a repo-specific `devcov-raw-string-escapes` custom policy for the
  DevCovenant repo only; do not ship that custom policy in user installs.

## Installation Requirements
- Install the full DevCovenant toolchain into the target repo, including the
  `devcovenant/` tree, `devcovenant/run_pre_commit.py`,
  `devcovenant/run_tests.py`, `devcovenant/update_lock.py`, and
  `devcovenant/update_test_status.py` helpers, and CI workflow assets.
- Use packaged assets from `devcovenant/core/profiles/` and
  `devcovenant/core/policies/` when installed from PyPI; fall back to repo
  files when running from source.
- Install modes: `auto`, `empty`; use mode-specific defaults for docs,
  config, and metadata handling. Use `devcovenant update` for existing repos.
- When install finds DevCovenant artifacts, it refuses to proceed unless
  `--auto-uninstall` is supplied or the user confirms the uninstall prompt.
- `--disable-policy` sets `apply: false` for listed policy IDs during
  install/update.
- Managed docs (AGENTS/README/PLAN/SPEC/CHANGELOG) refresh their headers and
  managed blocks on install/update/refresh with UTC timestamps. Installs
  create missing files while preserving any existing user content; updates
  and refreshes always preserve user content outside managed blocks.
- Update mode defaults to preserving policy blocks and metadata; managed blocks
  can be refreshed independently of policy definitions.
- Preserve custom policy scripts and fixers by default on existing installs
  (`--preserve-custom`), with explicit overrides available.
- `devcovenant/config.yaml` is generated only when missing. Autogen sections
  are clearly marked and may be updated; user-controlled settings and
  overrides are preserved to allow installs from an existing config.
- When an install/update runs, it deletes any `devcovrepo`-prefixed custom
  policies or profiles inside `devcovenant/custom` unless `devcov_core_include`
  is set to true. The refresh/installer regenerates `devcovenant/custom` and
  `tests/devcovenant` from the global asset, and recreates the default config
  by materializing the `devcovuser` profile descriptor (the YAML asset that
  describes the metadata schema—actual values are filled by profile-driven
  overlays during install). That keeps repo-only overrides local while giving
  downstream installs a clean baseline they can edit.
- User repositories (and this repo when treated as a user repo) must maintain
  the mirror tree under `tests/devcovenant/**`. When `devcov_core_include` is
  false the `devcovuser` profile mirrors just `devcovenant/custom/**` so only
  custom extensions are tracked, leaving `tests/**` for project tests. When
  `devcov_core_include` is true, the `devcovrepo` profile adds overlays so the
  entire `devcovenant/**` tree (including core scripts) is mirrored under
  `tests/devcovenant/`. Install/update/refresh only touch
  `tests/devcovenant/**`, leaving all other `tests/**` entries intact.
- Runtime-required artifacts (
  `devcovenant/registry/local/policy_registry.yaml`,
  `devcovenant/registry/local/manifest.json`,
  and `.devcov-state/test_status.json`
) are generated from `devcovuser` assets during install/update/refresh. They
  are generated from `devcovuser` assets during install/update/refresh. They
  are tracked in this repo for CI/builds, excluded from packages, and
  regenerated when missing.
- `AGENTS.md` is always written from the template; if a prior `AGENTS.md`
  exists, preserve its editable section under `# EDITABLE SECTION`.
- `README.md` keeps user content, receives the standard header, and gains a
  managed block with missing sections (Table of Contents, Overview, Workflow,
  DevCovenant).
- `SPEC.md` and `PLAN.md` are always part of the profile-driven doc assets.
  Existing files receive header refreshes; missing files are created during
  each install/update run without extra CLI toggles.
- `CHANGELOG.md` and `CONTRIBUTING.md` are always replaced on install
  (backing up to `*_old.md`); updates refresh managed blocks only.
- `VERSION` is created on demand. Prefer an existing VERSION, otherwise
  read version fields from `pyproject.toml`, otherwise prompt. If prompting
  is skipped, default to `0.0.1`. The `--version` flag overrides detection
  and accepts `x.x` or `x.x.x` (normalized to `x.x.0`).
- If no license exists, install the MIT template with a `Project Version`
  header. Only overwrite licenses when explicitly requested.
- Regenerate `.gitignore` from global, profile, and OS fragments, then
  merge existing user entries under a preserved block.
- Always back up overwritten or merged files as `*_old.*`, even when
  merges succeed, and report the backups at the end of install.
- Stamp `Last Updated` values using the UTC install date.
- Support partial doc overwrites via `--docs-include` / `--docs-exclude`, so
  only selected docs are replaced when docs mode overwrites.
- Support policy update modes via `--policy-mode preserve|append-missing|`
  `overwrite`.
- Write `devcovenant/registry/local/manifest.json` with the core layout,
  doc types, installed paths, options, active profiles, and policy asset
- Record the UTC timestamp of the install or update.
- Core profile manifests (`devcovenant/core/profiles/<profile>/<profile>.yaml`)
  are shipped as static, authoritative descriptors. `devcovenant update`
  keeps user repos on the latest shipped descriptors, but `refresh-*` commands
  do not rewrite them. `PROFILE_MAP.md` and `POLICY_MAP.md` are reference
  tables only—authors consult them when manually populating profile YAMLs;
  they are not a source-of-truth that is materialized into the manifests.
  Generic `profile.yaml` stubs are still invalid once normalization runs.
- The stock catalog is intentionally slim: global, docs, data, suffixes,
  python, javascript, typescript, java, go, rust, php, ruby, csharp, sql,
  docker, terraform, kubernetes, fastapi, frappe, dart, flutter, swift,
  objective-c. Retired stacks should be added back as custom profiles.
- Install and update share a unified self-install/self-refresh workflow.
  Whatever command runs operates on the host repository: invoking the installed
  package (on `PATH`) targets the current working repo.
  Running `python3` inside the DevCovenant source tree updates that repo in
  place without overwriting the existing `devcovenant/` folder, refreshing only
  configs, managed docs, and metadata. The optional
  `devcovenant/config_override` path remains a temporary override for
  experimentation.
- Add a `refresh-all` command that runs `refresh-policies`.
  It defaults to preserve metadata mode, updates
  `devcovenant/registry/local/policy_registry.yaml`, and rebuilds
  `devcovenant/registry/local/profile_catalog.yaml`.
  That keeps the profile/catalog state current without a full
  install/update run.

## Packaging Requirements
- Ship `devcovenant` as a pure-Python package with a console script entry.
- Include profile assets and policy assets in the sdist and wheel.
- Include `CITATION.cff` in sdists/wheels so citation metadata is available to
  consumers (MIT license; authors Black Epsilon Ltd. and Apostol Apostolov).
- Require Python 3.10+ and declare runtime dependencies in
  `requirements.in`, `requirements.lock`, and `pyproject.toml`; publish
  classifiers through Python 3.14.
- Publish with MIT license metadata (`license = { file = "LICENSE" }`,
  `License :: OSI Approved :: MIT License` classifier) and ensure CITATION
  authors/license/version stay aligned; version-sync enforces this under the
  `devcovrepo` profile.
- Keep `THIRD_PARTY_LICENSES.md` and `licenses/` synchronized with dependency
  changes so the dependency-license-sync policy passes.
- DevCovenant's own test suites live under `tests/devcovenant/` in the
  DevCovenant repo only. Tests are not shipped in packages; `tests/` is
  created on demand when the `new-modules-need-tests` policy is active.
  User repos exclude `devcovenant/**` from test enforcement except
  `devcovenant/custom/**`, which is included. When needed, user repos create
  `tests/devcovenant/custom/` to cover custom policy/profile code. Policies
  reuse metadata (for example,
  `tests_watch_dirs`, `selector_roles`, and policy-specific selector options)
  so the suite can move without hard-coded paths. Profile or repo overrides
  set these metadata values when they relocate tests elsewhere.
- The tests tree mirrors the package layout (core/custom and their profile
  directories) under `tests/devcovenant/` so interpreter or scanner modules
  in `devcovenant/core/profiles` or `devcovenant/custom/profiles` can rely on
  corresponding suites under `tests/devcovenant/core/profiles/` and
  `tests/devcovenant/custom/profiles/`.
- The `new-modules-need-tests` policy explicitly requires unit tests. The
  repository continues to run both `pytest` and `python3 -m unittest discover`,
  but newly added coverage must be unit-level and existing policy tests
  should be converted to unit suites over time.
- User repos keep a default-on `devcovuser` profile that excludes
  `devcovenant/**` from test enforcement except `devcovenant/custom/**`.
  When `devcov_core_include` is true (DevCovenant’s own repo), disable
  `devcovuser` and enable `devcovrepo` so the full `devcovenant/**` tree
  (code and tests) is mirrored and enforced.

## Non-Functional Requirements
- Checks must be fast enough for pre-commit usage on typical repos.
- Violations must be clear, actionable, and reference the policy source.
- Install and uninstall operations must be deterministic and reversible.

## Future Direction
- Version 0.2.7 moves more stock policies onto a metadata-driven DSL surfaced
  via `devcovenant/config.yaml`. That lets `AGENTS.md` focus on documentation
  text while selectors, version boundaries, and runtime paths become
  configurable knobs.
- Expect the DSL to replace hard-coded policy metadata (version watching, docs
  location, selectors) with reusable templates keyed by active profiles, while
  still allowing true custom policies to live inside `devcovenant/custom/`.
