# DevCovenant Specification
**Last Updated:** 2026-02-10
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
defined in descriptors, resolved into registry metadata, and emitted into
`AGENTS.md` for human-readable policy documentation. The system must keep
enforcement logic, registry state, and rendered documentation synchronized so
drift is detectable and reversible.

## Workflow
- Run the gated workflow for every change: pre-commit start, tests,
  pre-commit end.
- `devcovenant check --start` must run before edits but is not required to
  leave
  the tree clean; it simply captures a gate snapshot and identifies existing
  issues. Later phases still rerun hooks/tests until the workspace is clean.
- If start is recorded after edits, the gate issues a warning and brief
  pause instead of blocking, but a clean `start → tests → end` run is still
  required to pass.
- If end-phase hooks or DevCovenant autofixers change the working tree, rerun
  the required tests (and rerun hooks if needed) until the repo is clean, then
  record only that final successful pass in
  `devcovenant/registry/local/test_status.json`. Devflow gate status is
  stored in `devcovenant/registry/local/test_status.json`, created on demand,
  and treated as gitignored state. Do not create `.devcov-state`; keep all
  runtime state under `devcovenant/registry/local`.
- When policy text changes, update scripts/tests and run
  `devcovenant refresh` so hashes stay aligned.
- Log every change in `CHANGELOG.md` under the current version header.

## Functional Requirements
### Policy definitions and registry
- Build policy records from discovered core/custom policy scripts and their
  descriptor YAML files.
- Hash policy definitions and scripts into
  `devcovenant/registry/local/policy_registry.yaml`.
- Treat policy descriptor `text` fields as the canonical policy prose source.
- Remove legacy stock-text restore infrastructure (`stock_policy_texts.*`
  and `restore-stock-text`) now that policy text is descriptor-driven.
- `refresh` must skip policies with missing descriptor text and emit
  notices; no stock-text fallback is allowed.
- Support `custom: true/false` metadata to mark custom policy prose that
  bypasses stock text sync checks.
- Provide an optional semantic-version-scope policy (disabled by default in
  config `policy_state`) that requires one SemVer scope tag in the latest
  changelog entry and matches the bump to major/minor/patch semantics.
- Resolve policy metadata from policy YAML defaults, active profile overlays,
  and user config overrides. The resolved metadata is written first into the
  policy registry, then rendered into `AGENTS.md`, which always lists every
  policy (core + custom) and shows the repo’s working values. Common metadata
  keys must appear in every policy block, and policy-specific keys from YAML
  are included even when empty so the schema is visible without a separate
  metadata schema file. The policy block is fully managed; users must not edit
  it directly.

### Engine behavior
- Load policy modules from `devcovenant/core/policies/<id>/<id>.py` with
  custom overrides in `devcovenant/custom/policies/<id>/<id>.py`.
- Load language adapters from `devcovenant/core/policies/<id>/adapters/`
  with custom overrides in `devcovenant/custom/policies/<id>/adapters/`.
  Custom adapters override core for the same policy + language.
- When a custom policy module exists, it fully replaces the built-in policy
  and suppresses core fixers for that policy.
- Respect `enabled`, `severity`, `status`, and `enforcement` metadata for each
  policy.
- Support one check flow with auto-fix enabled by default and a `--nofix`
  audit switch.
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
- Supported commands: `check`, `test`, `install`, `deploy`, `upgrade`,
  `refresh`, `undeploy`, `uninstall`, and `update_lock`.
- CLI parsing is command-scoped (subparsers). `devcovenant <command> --help`
  must show only options for that command and must not leak unrelated
  lifecycle flags.
- `check` defaults to auto-fix and exits non-zero on blocking violations or
  sync issues.
- `check --nofix` runs an audit-only pass.
- `check --start` runs full pre-commit
  (`python3 -m pre_commit run --all-files`) and records start-gate metadata in
  `devcovenant/registry/local/test_status.json`.
- `check --end` runs full pre-commit, reruns tests/hooks until clean when
  fixers modify files, then records end-gate metadata.
- `test` runs `pytest` plus `python3 -m unittest discover` against `tests/`
  (mirrors the package layout under `tests/devcovenant/` but stays outside the
  installable package).
- CLI output emits stage banners and short status steps (registry refresh,
  engine init, command execution) so runs are traceable without flooding.
- `install` and `uninstall` delegate to `devcovenant/core/install.py` and
  `devcovenant/core/uninstall.py`.
- Explicit metadata-normalization commands are unnecessary; refresh already
  resolves metadata via descriptors + profile overlays + config overrides.

### Install, deploy, upgrade, refresh model
- `install` places DevCovenant into a repo and writes a generic,
  devcovrepo-enabled config stub (sets `install.generic_config: true`). It
  never deploys managed docs/assets and exists to force a user config edit
  before activation. If DevCovenant is already present and a newer core is
  available, `install` must prompt to run `upgrade` first, then continue.
  `install` is always allowed (even when DevCovenant already exists).
- `deploy` is the activation step. It requires a non-generic config
  (`install.generic_config: false`), materializes managed
  docs/assets/registries, regenerates `.gitignore`, and runs `refresh`
  internally. This is the only command that makes the repo fully “live.”
- `upgrade` explicitly replaces the DevCovenant core when the source version
  is newer than the target repo’s core. It applies `policy_replacements.yaml`
  and then runs `refresh`. `upgrade` is a direct command, and is also reachable
  by the `install` prompt when a newer core is detected.
- `refresh` is a full refresh command. It rebuilds registries and policy
  metadata, regenerates the AGENTS policy block from registry entries,
  refreshes managed docs/assets selected by `doc_assets`, and refreshes config
  autogen sections (profiles.generated, core paths, and metadata overlays)
  while preserving user overrides.
- `undeploy` removes managed blocks, registries, and generated `.gitignore`
  fragments while keeping `devcovenant/` and config intact so users can edit
  config and redeploy.
- `uninstall` removes DevCovenant from a repo: deletes `devcovenant/`,
  removes managed blocks from documents, and cleans out generated registries.
- Source-based usage must use `python3 -m devcovenant ...` when invoking
  from a repo checkout; the installed CLI is the default for packaged usage.

#### Install/deploy scenarios
1. Any repo: `install` always succeeds and writes only a generic config
   stub (no docs/assets). If a newer core exists, it prompts to `upgrade`
   first.
2. Deploy-ready repo: `deploy` requires a non-generic config and writes
   managed docs/assets/registries, then runs `refresh`.
3. Existing DevCovenant: `install` still runs (after upgrade prompt) and
   leaves the repo in a pre-deploy state unless the user explicitly runs
   `deploy`.

#### Command matrix (behavioral intent)
- `check`: policy checks with default auto-fix; `--nofix` disables fixing;
  `--start`/`--end` run start/end gate pre-commit workflows.
- `test`: run `pytest` and `python3 -m unittest discover` against `tests/`.
- `install`: place core + generic config stub only. Prompt to `upgrade` if a
  newer core is detected. No managed doc deployment.
- `deploy`: materialize managed docs/assets/registries from config, refresh
  `.gitignore`, and run `refresh` internally.
- `upgrade`: copy newer core into the repo and apply policy replacements,
  then run `refresh`.
- `refresh`: full refresh for registries, AGENTS policy block, managed
  docs/assets, and config autogen sections.
- `undeploy`: remove managed blocks/registries and revert generated
  `.gitignore` fragments while keeping core + config.
- `uninstall`: remove the entire DevCovenant footprint and managed blocks.
- `update_lock`: refresh lockfiles and related license material.

### Command/script placement
- User-facing, runnable commands live at the `devcovenant/` root and are
  exposed through the CLI (and callable via `python3 -m devcovenant`).
- File-path command usage is a supported interface and must continue to work
  (`python3 devcovenant/run_pre_commit.py ...` and
  `python3 devcovenant/run_tests.py`).
- Shared policy and engine logic lives under `devcovenant/core/` as internal
  modules; command entrypoints remain rooted at `devcovenant/`.
- `devcovenant/core/tools/` is not a public entrypoint surface; any helper
  meant for users must have a CLI command and a top-level module.
- CLI-exposed modules at `devcovenant/` root are real implementations,
  not forwarding wrappers.
- Avoid duplicate same-name command modules across `devcovenant/` and
  `devcovenant/core/`.
- Do not duplicate CLI helper command sources under profile assets.
  `run_pre_commit.py`, `run_tests.py`, `update_lock.py`, and
  `update_test_status.py` are sourced from the package root modules only.
- CLI-exposed command modules include (non-exhaustive): `cli.py`,
  `run_pre_commit.py`, `run_tests.py`, `update_lock.py`,
  and `update_test_status.py`.
  `run_tests.py` executes the merged
  `devflow-run-gates.required_commands` list resolved from profiles and
  config (defaults remain pytest + unittest) and records the exact command
  string to `update_test_status`. Language-aware policies delegate
  parsing/checking to per-language adapters under
  `devcovenant/core/policies/<policy>/adapters/<lang>.py`; core policy modules
  remain language-agnostic.

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
  otherwise deploy/refresh regenerate only the managed blocks.
- Managed-doc templates are YAML-only. Do not keep duplicate markdown template
  files for managed docs under `devcovenant/core/profiles/global/assets/`;
  descriptors are the sole template source.
- The `last-updated-placement` policy runs with auto-fix enabled so touched
  managed docs receive a UTC `Last Updated` header update during each run
  (`python3 devcovenant check`), keeping the timestamp aligned with the
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
- Config is seeded from the `global` profile asset (generic stub) and
  then refreshed with global defaults plus active profiles. It must include
  `profiles.generated.file_suffixes` so profile selections are visible to
  users and tooling.
- Config exposes `version.override` so config-driven installs can declare
  the project version that templated assets (for example, `pyproject.toml`)
  should use when no version file exists yet.
- Provide the dedicated `devcovrepo`/`devcovuser` profiles so the DevCovenant
  repository can opt into its own test overrides while user repositories keep
  `devcovenant/**` out of enforcement while still keeping
  `devcovenant/custom/**` monitored.
- The `global` profile is always active. Other shipped defaults (`docs`,
  `data`, `suffixes`) are enabled by default but can be trimmed from
  `profiles.active` when a user wants to stop applying their assets or
  metadata overlays.
- Config should expose global knobs for `paths`, `docs`, `install`,
  `deploy`, `upgrade`, `refresh`, `engine`, `hooks`, `reporting`, `ignore`,
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
- Managed-doc targets resolve as `doc_assets.autogen` minus `doc_assets.user`.
  Deploy/refresh sync only those docs from descriptors; AGENTS
  policy content remains generated from the policy registry.
- This mirrors the policy override structure (`autogen_metadata_overrides` and
  `user_metadata_overrides`) so teams can lift the default curated assets into
  their own configs when needed.
- The profile registry is generated into
  `devcovenant/registry/local/profile_registry.yaml` by scanning
  profile manifests.
- Active profiles are recorded under `profiles.active` in config and extend
  file suffix coverage through registry definitions.
- Custom profiles are declared by adding a profile manifest plus assets
  under `devcovenant/custom/profiles/<name>/`.
- Profile assets live under `devcovenant/core/profiles/<name>/assets/` and
  `devcovenant/custom/profiles/<name>/assets/`, with `global/assets/`
  covering shared docs and tooling.
- Policy assets are declared in policy descriptors and live under
  `devcovenant/core/policies/<policy>/assets/`. Deploy/refresh reads the
  descriptor assets directly. Custom overrides live under
  `devcovenant/custom/policies/<policy>/assets/`.

### Pre-commit configuration by profile
- Each profile declares a `pre_commit` fragment describing the repos and hooks
  it requires; fragments are registered inside
  `devcovenant/registry/local/profile_registry.yaml` under the profile
  manifest metadata so installs can regenerate `.pre-commit-config.yaml`
  whenever profile selections change.
- The global profile owns the DevCovenant hook baseline and shared defaults.
- The merge order for `.pre-commit-config.yaml` is:
  1. global profile defaults and the shared DevCovenant fragment,
     ensuring a consistent baseline.
  2. active profile fragments (in the order listed in `profiles.active`).
  3. overrides supplied via `config.yaml` under a dedicated `pre_commit`
     block (no direct edits to `.pre-commit-config.yaml`).
- The generated `.pre-commit-config.yaml` is authoritative and refreshed on
  `deploy`, `upgrade`, and `refresh`.
- Profile exclusions (for example, `devcovuser` vendor/build ignores) are
  translated into pre-commit `exclude`/`files` settings so pre-commit and
  policy scans skip the same paths.
- The CLI merges the fragments into `.pre-commit-config.yaml` before running
  the hooks. `devcovenant/registry/local/manifest.json` records the resolved
  hook set so commands such as `run_pre_commit.py` know which config to
  execute and can rerun the merge if profiles change during a session.
- Include a “Pre-commit config refactor” phase in `PLAN.md` that references
  this SPEC section and clarifies the merge metadata keys.
- Add tests verifying the generated config matches the manifest for sample
  profile combinations.
- Assets install only when a policy is enabled in config. Scope keys are
  removed; applicability is driven by resolved metadata and adapter support.
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
- Built-in policy prose is canonical in descriptor YAML `text` fields
  (`devcovenant/core/policies/<policy>/<policy>.yaml`).
- Policies are activated only by config (`policy_state`), not by policy/profile
  scopes. `AGENTS.md` still lists every policy (core + custom); the resolved
  `enabled` flag reflects config state.
- Runtime checks apply `policy_state` overrides before sync and execution, so
  AGENTS policy metadata remains downstream from config activation.
- Policy and profile scope keys are removed. Profiles still contribute metadata
  overlays and assets; policy YAML still carries defaults. Descriptors,
  manifests, and registry outputs remain authoritative for activation and
  enforcement behavior.
- Policy descriptors and profile manifests must not define retired activation
  scope keys (`profile_scopes`, `policy_scopes`).
- Install/upgrade planning and policy asset application must resolve `enabled`
  from descriptor metadata defaults overridden by config `policy_state`; AGENTS
  `enabled` metadata is downstream and not authoritative for activation.
- Stock policy assets are profile-owned (`global` and active profile manifests)
  and are not installed directly from core policy descriptors.
- Custom policy descriptors may declare fallback assets under
  `devcovenant/custom/policies/<policy>/<policy>.yaml`; fallback is controlled
  by `install.allow_custom_policy_asset_fallback` (default `true`) and remains
  gated by resolved policy `enabled`.
- `dependency-license-sync` must be manifest-agnostic: profiles or config
  overlays provide `dependency_files`, while the core policy metadata remains
  general. The devcovrepo profile sets DevCovenant’s own dependency
  manifests.
- A lightweight registry refresh runs at the start of every devcovenant
  invocation, regenerating `devcovenant/registry/local/*` (hashes, manifest)
  and only materializing `config.yaml` when missing; it skips AGENTS and
  managed docs to keep the worktree clean during CI and local runs.
- Profiles are explicit—no inheritance or family defaults; each profile lists
  its own assets, suffixes, policies, and overlays.
- Custom policy `readme-sync` enforces that `devcovenant/README.md` mirrors
  `README.md` with repository-only blocks removed via
  `<!-- REPO-ONLY:BEGIN -->` / `<!-- REPO-ONLY:END -->` markers. Its auto-fix
  rewrites the packaged guide from the repo README.
- The policy list is generated from the registered policy definitions and
  includes every available core/custom policy. Entries are ordered
  alphabetically; active profiles and config only affect the resolved
  `enabled` flag. Custom overrides are marked with `custom: true`.
- `devcovenant/registry/local/policy_registry.yaml` must stay aligned with
  descriptor inventory. Unknown or missing policy IDs in that inventory are
  invalid.
- `changelog-coverage` requires a fresh topmost entry per change. The newest
  entry must be dated today, include labeled Change/Why/Impact summary lines
  that each contain an action verb from the configured list, and contain a
  `Files:` block listing exactly the touched paths. Changelog entries remain
  newest-first (descending dates).
- `changelog-coverage` ignores AGENTS and other managed-doc file changes only
  when the file diff is confined to `<!-- DEVCOV:BEGIN -->` /
  `<!-- DEVCOV:END -->` or `<!-- DEVCOV-POLICIES:BEGIN -->` /
  `<!-- DEVCOV-POLICIES:END -->` blocks.
- `enabled: false` disables enforcement without removing definitions.
- Provide a `managed-environment` policy (off by default via config
  `policy_state`) that enforces execution inside the expected
  environment when `enabled: true`. It must warn when `expected_paths` or
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
- `devcov-integrity-guard` is the unified integrity policy that validates
  policy prose presence, descriptor parity, policy-registry synchronization,
  and test-status metadata checks when watch selectors are configured.
- Dogfood-only policies (`patches-txt-sync`, `gcv-script-naming`,
  `security-compliance-notes`) are not shipped in the DevCovenant repo.
- Keep `devcovenant/config.yaml` tracked for CI use, but exclude it from
  built artifacts via `MANIFEST.in` so packages do not ship the repo config;
  user installs still auto-generate config when missing and preserve user
  overrides when present.
- Support policy replacement metadata via
  `devcovenant/registry/global/policy_replacements.yaml`.
  During upgrades, replaced policies move to custom and are marked deprecated
  when enabled; disabled policies are removed along with their custom scripts
  and fixers.
- Record upgrade notices (replacements and new policies) in
  `devcovenant/registry/local/manifest.json` and print them to stdout.
- Treat the collective `<!-- DEVCOV-POLICIES:BEGIN -->` /
  `<!-- DEVCOV-POLICIES:END -->` block as a managed unit rendered from
  registry policy entries.
  Provide a per-policy `freeze`
  override that copies the policy’s modules, descriptors, and assets into
  `devcovenant/custom/` (with `custom: true`) when true and removes those files
  when the flag clears.
  Always rerun `devcovenant refresh` (and any needed registry
  fixes) so the registry records the custom copy. Auto-fixers should be devised
  for every policy and wired through the per-policy adapters.
  They work across every language/profile combination that the policy supports.
- Generate `devcovenant/registry/local/policy_registry.yaml` dynamically from
  policy descriptors, script discovery, and metadata resolution. The registry
  is the canonical resolved policy state: it stores hashes, script paths,
  assets, and resolved metadata for every policy (enabled or disabled).
  `AGENTS.md` policy sections are downstream render output from this registry.
- The legacy `devcovenant/registry.json` storage and the accompanying
  `update_hashes.py` helper were retired and removed, leaving
  `devcovenant/registry/local/policy_registry.yaml` as the single
  canonical hash store. Any residual legacy artifacts in the tree should be
  deleted (registry.json, prior `*_old` backups, GPL license template) and
  removed from manifests, schemas, and policy references so refresh/install
  no longer expect them. Backups are opt-in via `--backup-existing`.


### Policy definition YAML
- Each policy (core, frozen, or custom) ships with a `<policy>.yaml` that
  contains:
  ```
  id: changelog-coverage
  text: |
    Every substantive change must be recorded ...
  metadata:
    severity: error
    include_suffixes: [.md]
    selectors:
      include_files: [...]
    enforcement: active
  ```
- Metadata keys under `metadata` are the schema for that policy. Common keys
  appear in every policy block; policy-specific keys are emitted even when
  empty.
- Metadata resolution order is policy defaults → profile overlays → user
  overrides. If no profile declares a metadata key, the policy default is kept.
  The resolved metadata is written first into the policy registry, then
  rendered into `AGENTS.md` for every policy (active or not), with `enabled`
  reflecting config activation. Metadata is rendered in vertical YAML-style
  lines (lists continue on indented lines) rather than comma-joined horizontal
  values.
- When DevCovenant removes a core policy, the updater copies it to
  `devcovenant/custom/policies/` (or a frozen overlay defined in config),
  marks the new copy as `custom`, and reruns `refresh` so the
  management docs, notices, and registry reflect the deprecated version.
- `config.yaml` exposes:
  - `policy_state`: policy ID → `true|false` activation map (authoritative).
  - `freeze_core_policies`: list whose IDs toggle `freeze: true`.
  - `user_metadata_overrides`: policy ID → override map applied last.
- Config-defined overrides replace the targeted keys (no implicit append).
- Core profiles stay immutable; attach custom policy metadata via custom
  profiles and overlays rather than editing core profile YAML.
- `raw-string-escapes` remains a core policy and defaults to `enabled: false`
  via `policy_state` in config; users enable it by setting
  `policy_state.raw-string-escapes: true`.
- Add a repo-specific `devcov-raw-string-escapes` custom policy for the
  DevCovenant repo only; do not ship that custom policy in user installs.

## Installation Requirements
- Install the full DevCovenant toolchain into the target repo, including the
  `devcovenant/` tree, `devcovenant/run_pre_commit.py`,
  `devcovenant/run_tests.py`, `devcovenant/update_lock.py`, and
  `devcovenant/update_test_status.py` helpers, and CI workflow assets.
- Lifecycle installs copy helper command scripts from the package-root
  modules as part of the `devcovenant/` tree; profile assets must not carry
  duplicate helper-script source files.
- Use packaged assets from `devcovenant/core/profiles/` and
  `devcovenant/core/policies/` when installed from PyPI; fall back to repo
  files when running from source.
- Install modes: `auto`, `empty`; use mode-specific defaults for docs,
  config, and metadata handling. Use `devcovenant deploy` for first activation
  and `devcovenant refresh` for ongoing regeneration.
- When install finds DevCovenant artifacts, it refuses to proceed unless
  `--auto-uninstall` is supplied or the user confirms the uninstall prompt.
- `--disable-policy` sets `enabled: false` for listed policy IDs during
  install/deploy/upgrade.
- Managed docs (AGENTS/README/PLAN/SPEC/CHANGELOG) refresh their headers and
  managed blocks on deploy/upgrade/refresh with UTC timestamps. Installs
  create missing files while preserving any existing user content; deploy,
  upgrade, and refresh always preserve user content outside managed blocks.
- Deploy/upgrade defaults preserve policy blocks and metadata; managed blocks
  can be refreshed independently of policy definitions.
- Preserve custom policy scripts and fixers by default on existing installs
  (`--preserve-custom`), with explicit overrides available.
- `devcovenant/config.yaml` is generated only when missing. Autogen sections
  are clearly marked and may be updated; user-controlled settings and
  overrides are preserved to allow installs from an existing config.
- When an install/deploy/upgrade runs, it deletes any
  `devcovrepo`-prefixed custom
  policies or profiles inside `devcovenant/custom` unless `devcov_core_include`
  is set to true. The refresh/installer regenerates `devcovenant/custom` and
  `tests/devcovenant` from the global asset, and recreates the default config
  by materializing the global `config.yaml` asset. The asset seeds default
  settings and overlay lists; resolved metadata is still computed from policy
  defaults, profile overlays, and user overrides during refresh. That keeps
  repo-only overrides local while giving downstream installs a clean baseline
  they can edit.
- User repositories (and this repo when treated as a user repo) must maintain
  the mirror tree under `tests/devcovenant/**`. When `devcov_core_include` is
  false the `devcovuser` profile mirrors just `devcovenant/custom/**` so only
  custom extensions are tracked, leaving `tests/**` for project tests. When
  `devcov_core_include` is true, the `devcovrepo` profile adds overlays so the
  entire `devcovenant/**` tree (including core scripts) is mirrored under
  `tests/devcovenant/`. Install/deploy/upgrade/refresh only touch
  `tests/devcovenant/**`, leaving all other `tests/**` entries intact.
- Runtime-required artifacts (
  `devcovenant/registry/local/policy_registry.yaml`,
  `devcovenant/registry/local/manifest.json`,
  and `devcovenant/registry/local/test_status.json`
) are generated from the global profile assets during
  install/deploy/upgrade/refresh.
  They are local runtime state, excluded from packages, and regenerated when
  missing. Repositories may gitignore these files by default, while CI/builds
  regenerate them on demand.
- `AGENTS.md` is regenerated from the managed template plus policy sections
  rendered from registry metadata/state. Preserve the editable section under
  `# EDITABLE SECTION`, and never allow users to edit the policy block.
- `README.md` keeps user content, receives the standard header, and gains a
  managed block with missing sections (Table of Contents, Overview, Workflow,
  DevCovenant).
- `SPEC.md` and `PLAN.md` are always part of the profile-driven doc assets.
  Existing files receive header refreshes; missing files are created during
  each deploy/refresh run without extra CLI toggles.
- `CHANGELOG.md` and `CONTRIBUTING.md` are replaced on install; backups are
  created only when `--backup-existing` is set. Deploy/refresh regenerate
  managed blocks.
- The configured version file (default `VERSION`, overridden by profile
  overlays like `devcovrepo`) is created on demand. Resolve the target
  version in this order: CLI `--version`, config `version.override`, existing
  valid version file, `pyproject.toml` version, interactive prompt, then
  `0.0.1` when prompting is unavailable. The `--version` flag accepts `x.x`
  or `x.x.x` (normalized to `x.x.0`).
- Invalid existing version values are treated as missing and must continue
  down the fallback chain instead of blocking updates.
- Metadata mode defaults for version/license are command-lifecycle based:
  empty-repo install defaults to overwrite, while existing-repo flows
  (`deploy`, `upgrade`, `refresh`) default to preserve unless explicitly
  overridden.
- If no license exists, preserve mode bootstraps the MIT template with a
  `Project Version` header. Existing licenses are overwritten only when
  explicitly requested.
- Regenerate `.gitignore` from global, profile, and OS fragments, then
  merge existing user entries under a preserved block.
- Default runs overwrite in-place without creating `*_old.*` backups.
  When `--backup-existing` is set, back up overwritten or merged files as
  `*_old.*` and report the backups at the end of install.
- Stamp `Last Updated` values using the UTC install date.
- Support partial doc overwrites via `--docs-include` / `--docs-exclude`, so
  only selected docs are replaced when docs mode overwrites.
- Support policy modes via `--policy-mode preserve|overwrite`.
- Write `devcovenant/registry/local/manifest.json` with the core layout,
  doc types, installed paths, options, active profiles, and policy asset
- Record the UTC timestamp of the install/deploy/upgrade/refresh action.
- Core profile manifests (`devcovenant/core/profiles/<profile>/<profile>.yaml`)
  are shipped as static, authoritative descriptors. `devcovenant refresh`
  keeps user repos on the latest shipped descriptors. Reference notes are
  never materialized into manifests;
  descriptors and manifests define behavior directly.
  Generic `profile.yaml` stubs are still invalid once normalization runs.
- The stock profile set is intentionally slim: global, docs, data, suffixes,
  python, javascript, typescript, java, go, rust, php, ruby, csharp, sql,
  docker, terraform, kubernetes, fastapi, frappe, dart, flutter, swift,
  objective-c. Retired stacks should be added back as custom profiles.
- Install, deploy, and refresh share a unified self-install/self-refresh
  workflow.
  Whatever command runs operates on the host repository: invoking the installed
  package (on `PATH`) targets the current working repo.
  Running `python3` inside the DevCovenant source tree refreshes that repo in
  place without overwriting the existing `devcovenant/` folder, refreshing only
  configs, managed docs, and metadata. The optional
  `devcovenant/config_override` path remains a temporary override for
  experimentation.
- Keep a single `refresh` command that runs registry generation first and then
  policy-block rendering. It fully regenerates
  `devcovenant/registry/local/policy_registry.yaml` from descriptors plus
  overrides (no manual edits), renders the AGENTS policy block from registry
  entries, and rebuilds `devcovenant/registry/local/profile_registry.yaml`.

## Packaging Requirements
- Ship `devcovenant` as a pure-Python package with a console script entry.
- Ship the user-facing `devcovenant/docs/` guides inside the package.
- Include profile assets and policy assets in the sdist and wheel.
- Require Python 3.10+ and declare runtime dependencies in
  `requirements.in`, `requirements.lock`, and `pyproject.toml`; publish
  classifiers through Python 3.14.
- Runtime-hard dependencies for the default profile baseline
  (`global` + `devcovuser` / `devcovrepo`) are `PyYAML`, `semver`,
  `pre-commit`, and `pytest`.
- Profile selection changes policy/config behavior after install, but does not
  change package dependency resolution.
- Publish with MIT license metadata (`license = { file = "LICENSE" }`,
  `License :: OSI Approved :: MIT License` classifier); version-sync enforces
  this under the `devcovrepo` profile.
- Keep `THIRD_PARTY_LICENSES.md` and `licenses/` synchronized with dependency
  changes as defined by the active profile overlays so the
  dependency-license-sync policy passes.
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
- `devcovuser` ignores vendored trees (`vendor`, `third_party`,
  `node_modules`) by default so scans and tests skip bundled dependencies.
- `devcovuser` also skips vendored DevCovenant core paths in
  changelog-coverage (and other scan-based policies) while leaving
  `devcovenant/custom/**` enforced for user-defined extensions.
- For user repos, `devcovuser` minimizes policy noise by excluding
  `devcovenant/**` from changelog-coverage, version-sync,
  last-updated-placement, documentation-growth-tracking, and
  line-length-limit. The same overlays explicitly keep
  `devcovenant/custom/**` and `tests/devcovenant/custom/**` in scope so
  code-style/security policies still enforce custom extensions and their
  tests.

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
