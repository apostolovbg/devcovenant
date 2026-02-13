# DevCovenant Specification
**Last Updated:** 2026-02-13
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
defined in descriptors, resolved through profile/config overlays into registry
metadata, and compiled into the `AGENTS.md` policy block for runtime parsing.
The system must keep enforcement logic, registry state, and rendered
documentation synchronized so drift is detectable and reversible.

### API Freeze Charter
- Freeze API semantics and contracts, not inventories. Existing command,
  metadata, and runtime contract behavior must not change silently.
- Minor-version evolution is additive only (new commands, metadata keys,
  profiles, translators, and policies).
- Breaking behavior changes require explicit migration notes and versioned
  contract updates in this specification.
- Forward-only implementation: implement the current contract directly.
  Do not keep legacy fallback paths and do not add anti-legacy rejection
  logic unless a policy explicitly requires that behavior.

## Workflow
- Run the gated workflow for every change: pre-commit start, tests,
  pre-commit end.
- `devcovenant gate --start` must run before edits but is not required to
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
  and user config overrides. The resolved metadata is written into the policy
  registry and rendered into `AGENTS.md`, which always lists every policy
  (core + custom) and shows the repo’s working values. Common metadata keys
  must appear in every policy block, and policy-specific keys from YAML are
  included even when empty so the schema is visible without a separate metadata
  schema file. The policy block is fully managed; users must not edit it
  directly.
- Runtime policy parsing reads `AGENTS.md` policy blocks as the execution
  input. The local registry stores synchronized hashes and resolved metadata
  copies for integrity checks, diagnostics, and reporting.

### Engine behavior
- Load policy modules from `devcovenant/core/policies/<id>/<id>.py` with
  custom overrides in `devcovenant/custom/policies/<id>/<id>.py`.
- Load translator declarations from active language profile manifests and
  resolve translation through the engine runtime, not through per-policy
  adapter maps.
- Translator declarations live in language profile YAML and include
  extension routing and translation strategy configuration.
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
- Supported commands: `check`, `gate`, `test`, `install`, `deploy`,
  `upgrade`, `refresh`, `undeploy`, `uninstall`, and `update_lock`.
- The command surface is a frozen contract; new commands are allowed only
  as additive registered commands and must not change existing command
  semantics.
- CLI parsing is command-scoped (dispatcher). `devcovenant <command> --help`
  must show only options for that command and must not leak unrelated
  lifecycle flags.
- All commands run against the current working repository root. Target override
  flags (`--target`, `--repo`) are not part of the public contract.
- `check` defaults to auto-fix and exits non-zero on blocking violations or
  sync issues.
- `check --nofix` runs an audit-only pass.
- `check --norefresh` skips the startup full refresh for that check run.
- `gate --start` runs full pre-commit
  (`python3 -m pre_commit run --all-files`) and records start-gate metadata in
  `devcovenant/registry/local/test_status.json`.
- `gate --end` runs full pre-commit, reruns tests/hooks until clean when
  fixers modify files, then records end-gate metadata.
- `test` runs `python3 -m unittest discover -v` first, then `pytest` against
  `tests/`, and records results through the gate status metadata.
- CLI output emits stage banners and short status steps (registry refresh,
  engine init, command execution) so runs are traceable without flooding.
- Lifecycle command logic lives in the root command modules
  (`devcovenant/install.py`, `devcovenant/upgrade.py`,
  `devcovenant/uninstall.py`, `devcovenant/undeploy.py`,
  `devcovenant/refresh.py`) rather than same-name scripts under
  `devcovenant/core/`.
- Explicit metadata-normalization commands are unnecessary; refresh already
  resolves metadata via descriptors + profile overlays + config overrides.

### Install, deploy, upgrade, refresh model
- `install` places DevCovenant into a repo and writes a generic,
  devcovuser-enabled config stub (sets `install.generic_config: true`). It
  must seed canonical generic defaults (`devcov_core_include: false` and
  default active profiles for user repos), never deploy managed docs/assets/
  registries, and force a user config edit before activation. If DevCovenant
  is already present, `install` must stop immediately and instruct the user to
  run `upgrade`.
- `deploy` is the activation step. It requires a non-generic config
  (`install.generic_config: false`), materializes managed docs/assets/
  registries, regenerates `.gitignore`, and runs `refresh` internally. When
  `devcov_core_include` is false, deploy deletes
  `devcovenant/custom/policies/**`, `tests/devcovenant/core/**`, and
  `devcovenant/custom/profiles/devcovrepo/**` before regeneration. This is the
  only command that makes the repo fully “live.”
- `upgrade` explicitly replaces the DevCovenant core when the source version
  is newer than the target repo’s core. It applies `policy_replacements.yaml`
  and then runs `refresh`. `upgrade` is a direct command.
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
- Lifecycle commands do not expose tuning flags in the public CLI; they run
  with their canonical defaults.

#### Install/deploy scenarios
1. Any repo without existing DevCovenant: `install` writes only a generic
   config stub (no docs/assets).
2. Deploy-ready repo: `deploy` requires a non-generic config and writes
   managed docs/assets/registries, then runs `refresh`.
3. Existing DevCovenant: `install` exits with an upgrade instruction and
   performs no install changes.

#### Command matrix (behavioral intent)
- `check`: policy checks with default auto-fix; `--nofix` disables fixing;
  `--norefresh` skips startup refresh.
- `gate`: runs start/end gate pre-commit workflows via `--start`/`--end`.
- `test`: run `python3 -m unittest discover -v` and then `pytest` against
  `tests/`.
- `install`: place core + generic config stub only when DevCovenant is not
  already present. If present, exit with a `devcovenant upgrade` instruction.
  No managed doc deployment.
- `deploy`: materialize managed docs/assets/registries from config, refresh
  `.gitignore`, and run `refresh` internally.
- `upgrade`: copy newer core into the repo and apply policy replacements,
  then run `refresh`.
- `refresh`: full refresh for registries, AGENTS policy block, managed
  docs/assets, and config autogen sections.
- `undeploy`: remove managed blocks/registries and revert generated
  `.gitignore` fragments while keeping core + config.
- `uninstall`: remove the entire DevCovenant footprint and managed blocks.
- `update_lock`: resolve dependency lock targets from
  `dependency-license-sync` metadata (policy defaults + active profile
  overlays + config overrides), refresh supported lockfiles for all active
  ecosystems, and then refresh policy-owned license artifacts. The command
  resolves and runs from the repository root, not raw process CWD.
  Python lock refresh must not short-circuit from cached
  `requirements.in` hashes; it must reconcile against generated lock output
  each run.
  (`THIRD_PARTY_LICENSES.md` / `licenses/`).

### Command/script placement
- User-facing, runnable commands live at the `devcovenant/` root and are
  exposed through the CLI (and callable via `python3 -m devcovenant`).
- File-path command usage is a supported interface and must continue to work
  (for example `python3 devcovenant/gate.py --start` and
  `python3 devcovenant/test.py`).
- Shared policy and engine logic lives under `devcovenant/core/` as internal
  modules; command entrypoints remain rooted at `devcovenant/`.
- `devcovenant/core/tools/` is not a public entrypoint surface; any helper
  meant for users must have a CLI command and a top-level module.
- CLI-exposed modules at `devcovenant/` root are real implementations,
  not forwarding wrappers.
- Avoid duplicate same-name command modules across `devcovenant/` and
  `devcovenant/core/`.
- Do not duplicate CLI helper command sources under profile assets.
  Root command modules are sourced from package-root command scripts only.
- CLI-exposed command modules include (non-exhaustive): `cli.py`,
  `check.py`, `gate.py`, `test.py`, `install.py`, `deploy.py`, `upgrade.py`,
  `refresh.py`, `uninstall.py`, `undeploy.py`, and `update_lock.py`.
  `test.py` executes the merged
  `devflow-run-gates.required_commands` list resolved from profiles and
  config (defaults remain unittest + pytest) and records the exact command
  string in `devcovenant/registry/local/test_status.json`. Language-aware
  policies request translation from the engine runtime, which routes files
  by extension using active language-profile translator declarations;
  policy modules remain language-agnostic.

### Documentation management
- Every managed doc must include `Last Updated` and `Version` headers.
- `devcovenant/README.md` also includes `DevCovenant Version`, sourced from
  the installer package version.
- Every managed doc must include a top-of-file managed block inserted just
  below the header lines. The block records the `Doc ID`, `Doc Type`, and
  management ownership, and uses the standard markers:
  `<!-- DEVCOV:BEGIN -->` and `<!-- DEVCOV:END -->`.
- Managed block metadata lines are generated from descriptor fields
  (`doc_id`, `doc_type`, `managed_by`). Descriptor `managed_block` content is
  body-only and must not duplicate those metadata lines.
- `AGENTS.md` must also include a dedicated workflow block managed with
  `<!-- DEVCOV-WORKFLOW:BEGIN -->` and `<!-- DEVCOV-WORKFLOW:END -->`.
  The workflow block content comes from descriptor metadata, not copied marker
  text inside generic `body` fields.
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
  block scaffolding. Markers are generated by the renderer and must not be
  copied as literal marker lines from descriptor `body` content. Outside-of-
  block stock text is injected only when a
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
- Config is seeded from the global config template
  (`devcovenant/core/profiles/global/assets/config.yaml`) and then refreshed
  on every full refresh path. Runtime refresh preserves user-owned settings,
  regenerates autogen-owned sections, and keeps the commented template
  structure in the rendered file.
- Config exposes `version.override` so config-driven installs can declare
  the project version that templated assets (for example, `pyproject.toml`)
  should use when no version file exists yet.
- Provide the dedicated `devcovrepo`/`devcovuser` profiles so the DevCovenant
  repository can opt into its own test overrides while user repositories keep
  `devcovenant/**` out of enforcement while still keeping
  `devcovenant/custom/**` monitored.
- The `global` profile is always active. Other shipped defaults (`docs`) are
  enabled by default but can be trimmed from
  `profiles.active` when a user wants to stop applying their assets or
  metadata overlays.
- Config should expose the runtime knobs actually consumed by core logic:
  `devcov_core_include`, `devcov_core_paths`, `profiles`, `paths`, `version`,
  `docs`, `doc_assets`, `install`, `engine`, `pre_commit`, `policy_state`,
  `freeze_core_policies`, `ignore`, `autogen_metadata_overrides`, and
  `user_metadata_overrides`. Generated config remains the canonical override
  template and documents each supported key with inline comments in the
  profile asset template.
- Config also exposes `doc_assets` (with `autogen` and `user` lists).
  Repositories can drive which managed docs the active profiles (for example,
  `global`, `docs`, `devcovenant`) synthesize versus which remain purely
  user-maintained.
- Managed-doc targets resolve as `doc_assets.autogen` minus `doc_assets.user`.
  Deploy/refresh sync only those docs from descriptors. AGENTS policy content
  is generated from policy registry entries and becomes the runtime parser
  input.
- This mirrors the policy override structure (`autogen_metadata_overrides` and
  `user_metadata_overrides`) so teams can lift the default curated assets into
  their own configs when needed.
- Path-valued scalar metadata keys (singular `*_file`, `*_path`, `*_dir`,
  `*_root`) must be emitted as scalar strings in generated
  `autogen_metadata_overrides` and normalized as scalar strings at runtime.
  List-valued selectors (`*_files`, `*_globs`, `*_dirs`, `*_paths`) remain
  list-driven.
- The profile registry is generated into
  `devcovenant/registry/local/profile_registry.yaml` by scanning
  profile manifests.
- Active profiles are recorded under `profiles.active` in config and extend
  file suffix coverage through registry definitions.
- On every refresh, `policy_state` is rewritten as a full alphabetical map
  of all effective policy IDs (core + custom with custom-over-core same-ID
  precedence). Existing booleans are preserved, new IDs are seeded from the
  current resolved `enabled` default, and stale IDs are removed.
- Custom profiles are declared by adding a profile manifest plus assets
  under `devcovenant/custom/profiles/<name>/`.
- Core vs custom profile origin is inferred by manifest location
  (`devcovenant/core/profiles` vs `devcovenant/custom/profiles`); no
  dedicated `custom` profile type key is used.
- Only language profiles may declare translators. Framework/ops/tooling/repo
  profiles do not select translators; they contribute overlays/assets/hooks
  and file-selection metadata.
- Profile assets live under `devcovenant/core/profiles/<name>/assets/` and
  `devcovenant/custom/profiles/<name>/assets/`, with `global/assets/`
  covering shared docs and tooling.
- Policy assets are profile-owned and declared in profile manifests
  (`assets` lists). Policy descriptors remain metadata/prose definitions and
  are not used as stock asset sources during deploy/refresh.

### Pre-commit configuration by profile
- Each profile declares a `pre_commit` fragment describing the repos and hooks
  it requires; fragments are registered inside
  `devcovenant/registry/local/profile_registry.yaml` under the profile
  manifest metadata so installs can regenerate `.pre-commit-config.yaml`
  whenever profile selections change.
- The global profile owns the DevCovenant hook baseline and shared defaults.
  Language-specific hooks belong to their language profiles.
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
  hook set so commands such as `gate --start/--end` know which config to
  execute and can rerun the merge if profiles change during a session.
- Include a “Pre-commit config refactor” phase in `PLAN.md` that references
  this SPEC section and clarifies the merge metadata keys.
- Add tests verifying the generated config matches the manifest for sample
  profile combinations.
- Assets install only when a policy is enabled in config. Scope keys are
  removed; applicability is driven by resolved metadata and translator
  availability.
- Template indexes live at `devcovenant/core/profiles/README.md` and
  `devcovenant/core/policies/README.md`.
- Profile assets and policy overlays live in profile manifests at
  `devcovenant/core/profiles/<name>/<name>.yaml`, with custom overrides
  under `devcovenant/custom/profiles/<name>/<name>.yaml`. Profile assets
  are create-if-missing for active profiles, and profile overlays merge into
  `config.yaml` under `autogen_metadata_overrides` (with
  `user_metadata_overrides` taking precedence when set).
- Profile asset manifests do not define `mode` fields. Asset handling is
  deterministic: create missing targets only; never overwrite existing files.
- Profile manifests provide overlays/assets/hooks and file-selection metadata.
  Policy activation is config-only through `policy_state`.
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
- Policies are activated only by config (`policy_state`), not by profile
  manifests, scope keys, or runtime overrides. `AGENTS.md` still lists every
  policy (core + custom); the resolved `enabled` flag reflects config state.
- Runtime checks parse policies from the AGENTS policy block and execute
  that resolved state directly. Registry metadata is synchronized diagnostic
  state and never replaces AGENTS as runtime input.
- Policy and profile scope keys are removed. Profiles contribute metadata
  overlays and assets only; policy YAML still carries defaults. Descriptors,
  manifests, and registry outputs remain authoritative for metadata
  resolution, while runtime activation comes from `policy_state` compiled
  into AGENTS.
- Metadata resolution precedence is fixed: policy descriptor defaults ->
  active profile overlays -> `autogen_metadata_overrides` ->
  `user_metadata_overrides` -> `policy_state` activation application.
- Install/upgrade planning and policy asset application must resolve `enabled`
  from descriptor metadata defaults overridden by config `policy_state`, write
  those resolved values to registry metadata, and then compile AGENTS from the
  registry entries. The rendered AGENTS policy block is the runtime parser
  source and must match activation outcomes.
- Stock policy assets are profile-owned (`global` and active profile manifests)
  and are not installed directly from core policy descriptors.
- Custom policy assets are also profile-owned via active profile `assets`
  declarations. There is no descriptor fallback flag in config.
- `dependency-license-sync` must be manifest-agnostic: profiles or config
  overlays provide `dependency_files`, while the core policy metadata remains
  general. The devcovrepo profile sets DevCovenant’s own dependency
  manifests.
- `update_lock` consumes resolved `dependency-license-sync` metadata as its
  single source of truth. The command must not hardcode a Python-only
  manifest list; it refreshes whichever ecosystem lockfiles are declared by
  active profile metadata, runs from resolved repo root, and then calls
  policy-owned license refresh logic. It does not use
  `requirements.in` hash caches to skip Python lock reconciliation.
- A full refresh runs at the start of every `devcovenant check` invocation.
  It rebuilds `devcovenant/registry/local/*`, regenerates the `AGENTS.md`
  policy block, syncs managed docs, and refreshes generated config/profile
  metadata before policy evaluation.
- Profiles are explicit—no inheritance or family defaults; each profile lists
  its own assets, suffixes, and overlays.
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
- `MANIFEST.in` must not explicitly include repo-root managed docs
  (`AGENTS.md`, `SPEC.md`, `PLAN.md`, `CHANGELOG.md`, `CONTRIBUTING.md`).
  Package artifacts should ship package docs/assets under `devcovenant/`
  (plus required package metadata files such as root `README.md` and license
  files), not this repo's internal managed-document set.
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
  for every policy and wired through the shared translator runtime.
  They work across every language/profile combination that the policy supports.
- Generate `devcovenant/registry/local/policy_registry.yaml` dynamically from
  policy descriptors, script discovery, and metadata resolution. The registry
  stores synchronized hashes, script paths, assets, and resolved metadata for
  every policy (enabled or disabled) as diagnostic/integrity state. The
  AGENTS policy block is compiled from this registry, and AGENTS is the
  canonical runtime parser surface.
- The legacy `devcovenant/registry.json` storage and the accompanying
  `update_hashes.py` helper were retired and removed, leaving
  `devcovenant/registry/local/policy_registry.yaml` as the single
  canonical hash store. Any residual legacy artifacts in the tree should be
  deleted (registry.json, prior `*_old` backups, GPL license template) and
  removed from manifests, schemas, and policy references so refresh/install
  no longer expect them.


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
- Metadata resolution order is policy defaults → profile overlays →
  `autogen_metadata_overrides` → `user_metadata_overrides` →
  `policy_state` activation application. If no profile declares a metadata key,
  the policy default is kept. The resolved metadata is written into the local
  policy registry and rendered into `AGENTS.md` for every policy (active or
  not), with `enabled` reflecting config activation. Metadata is rendered in
  vertical YAML-style lines (lists continue on indented lines) rather than
  comma-joined horizontal values.
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

### Translator Runtime Contract
- Translator declarations are profile metadata owned by active language
  profiles. Policy code must not hardcode extension-to-adapter mappings.
- Each translator declaration includes translator ID, extension set,
  `can_handle` routing strategy, and `translate` strategy/entrypoint.
- For each policy-selected file, the engine resolves translator candidates by
  extension from active language profiles, evaluates `can_handle`, and then:
  zero matches -> policy violation (no translator), one match -> use it,
  multiple matches -> policy violation (ambiguous translator).
- Translators return a normalized, policy-agnostic `LanguageUnit` payload.
  Policies and fixers consume this shared structure instead of per-policy
  language adapter APIs.

## Installation Requirements
- Install the full DevCovenant toolchain into the target repo, including the
  `devcovenant/` tree plus root command modules (`check.py`, `test.py`,
  `install.py`, `deploy.py`, `upgrade.py`, `refresh.py`, `uninstall.py`,
  `undeploy.py`, `update_lock.py`) and CI workflow assets.
- Lifecycle installs copy helper command scripts from the package-root
  modules as part of the `devcovenant/` tree; profile assets must not carry
  duplicate helper-script source files.
- Use packaged assets from `devcovenant/core/profiles/` and
  `devcovenant/core/policies/` when installed from PyPI; fall back to repo
  files when running from source.
- Install is single-mode: copy `devcovenant/` and seed generic config only.
  Use `devcovenant deploy` for first activation and `devcovenant refresh` for
  ongoing regeneration.
- When install finds DevCovenant artifacts, it refuses to proceed and prints
  an explicit message to run `devcovenant upgrade`.
- Managed docs (AGENTS/README/PLAN/SPEC/CHANGELOG) refresh their headers and
  managed blocks on deploy/upgrade/refresh with UTC timestamps. Install does
  not materialize managed docs; deploy, upgrade, and refresh always preserve
  user content outside managed blocks.
- Deploy/upgrade defaults preserve policy blocks and metadata; managed blocks
  can be refreshed independently of policy definitions.
- Preserve custom policy scripts and fixers by default on existing installs
  in lifecycle internals.
- `devcovenant/config.yaml` is refreshed on every full refresh path.
  Autogen sections are regenerated each run, while user-controlled settings
  and overrides are preserved from the existing file.
- When deploy runs with `devcov_core_include` set to false, it deletes
  `devcovenant/custom/policies/**`, `tests/devcovenant/core/**`, and
  `devcovenant/custom/profiles/devcovrepo/**` before regenerating managed
  artifacts from active-profile metadata. Upgrade and refresh never perform
  that custom-content cleanup.
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
) are generated during full refresh paths (check/deploy/upgrade/refresh).
  Install writes the manifest scaffold only, then waits for deploy/check.
  These files are local runtime state, excluded from packages, and regenerated
  when missing. Repositories may gitignore them by default, while CI/builds
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
- `CHANGELOG.md` and `CONTRIBUTING.md` are managed docs refreshed on deploy/
  upgrade/refresh; install leaves existing repo docs untouched.
- The configured version file (default `VERSION`, overridden by profile
  overlays like `devcovrepo`) is created on demand. Resolve the target
  version in this order: config `version.override`, existing valid version
  file, `pyproject.toml` version, interactive prompt, then `0.0.1` when
  prompting is unavailable.
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
- Stamp `Last Updated` values using the UTC install date.
- Write `devcovenant/registry/local/manifest.json` with the core layout,
  doc types, installed paths, options, active profiles, and policy asset
- Record the UTC timestamp of the install/deploy/upgrade/refresh action.
- Core profile manifests (`devcovenant/core/profiles/<profile>/<profile>.yaml`)
  are shipped as static, authoritative descriptors. `devcovenant refresh`
  keeps user repos on the latest shipped descriptors. Reference notes are
  never materialized into manifests;
  descriptors and manifests define behavior directly.
  Generic profile-manifest stubs are still invalid once normalization runs.
- The stock profile set is intentionally slim: global, docs, devcovuser,
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
  DevCovenant repo only. Tests are not shipped in packages.
- `modules-need-tests` is a generic repo-wide rule: any in-scope non-test
  module (including existing modules) must have tests under configured
  `tests/` roots. The rule runs as a full repository audit and is
  metadata-driven (`include_*`, `exclude_*`, `watch_dirs`,
  `tests_watch_dirs`) with no hard-coded repo paths.
- For the DevCovenant repo (`devcovrepo`), profile metadata requires a full
  mirror for `devcovenant/**` under `tests/devcovenant/**`.
- For user repos (`devcovuser`), profile metadata requires mirror enforcement
  only for `devcovenant/custom/**` under `tests/devcovenant/custom/**`.
- For all other user-repo modules, tests are still required under `tests/`,
  but internal folder structure is user-defined.
- The `modules-need-tests` policy explicitly requires unit tests. Python test
  files must be unittest-style, and the repository runs
  `python3 -m unittest discover -v` first with `pytest` as piggyback
  execution.
- Tests are current-behavior artifacts: each test must validate the
  corresponding script/module behavior as it exists now. When scripts change,
  corresponding tests are updated; when scripts are deleted, corresponding
  tests are deleted.
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

### Core Responsibility Consolidation
- Internal core responsibilities are consolidated into stable runtime
  domains: policy runtime, metadata runtime, profile runtime, translator
  runtime, refresh runtime, and registry runtime.
- Legacy or duplicate internal modules/functions must be removed when their
  responsibilities are absorbed by the stable runtime domains.
- CLI-exposed scripts remain at `devcovenant/` package root; consolidated
  runtime modules remain internal under `devcovenant/core/`.

## Non-Functional Requirements
- Checks must be fast enough for pre-commit usage on typical repos.
- Violations must be clear, actionable, and reference the policy source.
- Install and uninstall operations must be deterministic and reversible.
- Contract tests must enforce current contract behavior: full alphabetical
  `policy_state` materialization on refresh with state preservation;
  translator ownership by language profiles only; and language-aware policies
  routed through the shared translator runtime without per-policy adapter
  maps.

## Future Direction
- Version 0.2.7 moves more stock policies onto a metadata-driven DSL surfaced
  via `devcovenant/config.yaml`. That lets `AGENTS.md` focus on documentation
  text while selectors, version boundaries, and runtime paths become
  configurable knobs.
- Expect the DSL to replace hard-coded policy metadata (version watching, docs
  location, selectors) with reusable templates keyed by active profiles, while
  still allowing true custom policies to live inside `devcovenant/custom/`.
