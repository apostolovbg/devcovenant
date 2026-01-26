# DevCovenant Specification
**Last Updated:** 2026-01-24
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
- Run a startup check at session start (`python3 -m devcovenant check --mode
  startup`).
- When policy text changes, set `updated: true`, update scripts/tests, run
  `devcovenant update-hashes`, then reset `updated: false`.
- Log every change in `CHANGELOG.md` under the current version header.

## Functional Requirements
### Policy definitions and registry
- Parse policy blocks from `AGENTS.md` and capture the descriptive text that
  follows each `policy-def` block.
- Hash policy definitions and scripts into
  `devcovenant/registry/registry.json`.
- Expose `restore-stock-text` to reset policy prose to canonical wording.
- Support `custom: true/false` metadata to mark custom policy prose that
  bypasses stock text sync checks.
- Provide an optional semantic-version-scope policy (`apply: false` by
  default) that requires one SemVer scope tag in the latest changelog
  entry and matches the bump to major/minor/patch semantics.
- Maintain a canonical metadata schema that lists all supported keys (common
  and policy-specific) so every policy block can be normalized on demand.

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
  (`python3 -m devcovenant`) that both route to the same CLI.
- Supported commands: `check`, `sync`, `test`, `update-hashes`,
  `restore-stock-text`, `install`, `update`, `uninstall`,
  `normalize-metadata`.
- `check` exits non-zero when blocking violations or sync issues are present.
- `sync` runs a startup-mode check and reports drift.
- `test` runs `pytest` against `tests/`, which now hosts the relocated policy
  and engine suites under `tests/devcovenant/`.
  That root-level tree mirrors the package layout and sits outside the
  installable `devcovenant` package, so only source distributions (via
  `MANIFEST.in`) carry it.
- `install` and `uninstall` delegate to `devcovenant/core/install.py` and
  `devcovenant/core/uninstall.py`.
- `update` supports managed-block-only refreshes and policy-mode control.
- `normalize-metadata` inserts any missing policy keys with safe placeholders
  while preserving existing values.

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

### Configuration and extension
- `devcovenant/config.yaml` must support `devcov_core_include` and
  `devcov_core_paths` for core exclusion.
- Config is generated from global defaults plus active profiles and must
  include `profiles.generated.file_suffixes` so profile selections are
  visible to users and tooling.
- Config should expose global knobs for `paths`, `docs`, `install`,
  `update`, `engine`, `hooks`, `reporting`, `ignore`, and `policies` so
  repos can tune behavior without editing core scripts.
- The profile catalog is generated into
  `devcovenant/registry/profile_catalog.yaml` by scanning profile manifests.
  Active profiles are recorded under `profiles.active` in config and extend
  file suffix coverage through catalog definitions.
- Custom profiles are declared by adding a profile manifest plus assets
  under `devcovenant/custom/profiles/<name>/`.
- Profile assets live under `devcovenant/core/profiles/<name>/assets/` and
  `devcovenant/custom/profiles/<name>/assets/`, with `global/assets/`
  covering shared docs and tooling.
- Policy assets are declared inside policy folders under
  `devcovenant/core/policies/<policy>/assets/`. Install/update compiles
  the results into `devcovenant/registry/policy_assets.yaml`. Custom
  overrides live under `devcovenant/custom/policies/<policy>/assets/`.
  Assets install only when a policy is enabled and its `profile_scopes`
  match active profiles.
- Template indexes live at `devcovenant/core/profiles/README.md` and
  `devcovenant/core/policies/README.md`.
- Profile assets and policy overlays live in profile manifests at
  `devcovenant/core/profiles/<name>/profile.yaml`, with custom overrides
  under `devcovenant/custom/profiles/<name>/profile.yaml`. Profile assets
  are applied for active profiles, and profile overlays merge into
  `config.yaml` under `policies`.

## Policy Requirements
- Every policy definition includes descriptive prose immediately after the
  metadata block.
- Built-in policies have canonical text stored in
  `devcovenant/registry/stock_policy_texts.yaml`.
- Policies declare `profile_scopes` metadata to gate applicability;
  global policies use `profile_scopes: global`.
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
  changing existing values or policy text.
- Support policy replacement metadata via
  `devcovenant/registry/policy_replacements.yaml`. During updates, replaced
  policies move to custom and are marked deprecated when enabled; disabled
  policies are removed along with their custom scripts and fixers.
- Record update notices (replacements and new stock policies) in
  `devcovenant/registry/manifest.json` and print them to stdout.

## Installation Requirements
- Install the full DevCovenant toolchain into the target repo, including the
  `devcovenant/` tree, `tools/` helpers, and CI workflow assets.
- Use packaged assets from `devcovenant/core/profiles/` and
  `devcovenant/core/policies/` when installed from PyPI; fall back to repo
  files when running from source.
- Install modes: `auto`, `empty`; use mode-specific defaults for docs,
  config, and metadata handling. Use `devcovenant update` for existing repos.
- When install finds DevCovenant artifacts, it refuses to proceed unless
  `--auto-uninstall` is supplied or the user confirms the uninstall prompt.
- `--disable-policy` sets `apply: false` for listed policy IDs during
  install/update.
- Update mode defaults to preserving policy blocks and metadata; managed blocks
  can be refreshed independently of policy definitions.
- Preserve custom policy scripts and fixers by default on existing installs
  (`--preserve-custom`), with explicit overrides available.
- `AGENTS.md` is always written from the template; if a prior `AGENTS.md`
  exists, preserve its editable section under `# EDITABLE SECTION`.
- `README.md` keeps user content, receives the standard header, and gains a
  managed block with missing sections (Table of Contents, Overview, Workflow,
  DevCovenant).
- `SPEC.md` and `PLAN.md` are optional. Existing files get header refreshes;
  missing files are created only when `--include-spec` or `--include-plan`
  are supplied.
- `CHANGELOG.md` and `CONTRIBUTING.md` are always replaced on install
  (backing up to `*_old.md`); updates refresh managed blocks only.
- `VERSION` is created on demand. Prefer an existing VERSION, otherwise
  read version fields from `pyproject.toml`, otherwise prompt. If prompting
  is skipped, default to `0.0.1`. The `--version` flag overrides detection
  and accepts `x.x` or `x.x.x` (normalized to `x.x.0`).
- If no license exists, install the GPL-3.0 template with a `Project Version`
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
- Write `devcovenant/registry/manifest.json` with the core layout, doc types,
  installed paths, options, active profiles, policy asset mappings,
  and the UTC timestamp of the install or update. Profile manifests
  drive profile assets and overlays, even when not listed as assets.

## Packaging Requirements
- Ship `devcovenant` as a pure-Python package with a console script entry.
- Include profile assets and policy assets in the sdist and wheel.
- Require Python 3.10+ and declare runtime dependencies in
  `requirements.in`, `requirements.lock`, and `pyproject.toml`.
- Keep `THIRD_PARTY_LICENSES.md` and `licenses/` synchronized with dependency
  changes so the dependency-license-sync policy passes.
- DevCovenant's own test suites live under the repository root `tests/`
  tree (e.g., `tests/devcovenant/core/...`); tooling should continue to ship
  that directory via `MANIFEST.in` while keeping it outside the installable
  `devcovenant` package. Policies reuse metadata (e.g., `tests_watch_dirs`,
  `selector_roles`, and policy-specific selector options) so the suite can
  move freely under `tests/` without hard-coded paths. Profile or repo
  overrides set these metadata values when they relocate tests elsewhere.
- The tests tree mirrors the package layout (core/custom and their profile
  directories) so interpreter or scanner modules in `devcovenant/core/profiles`
  or `devcovenant/custom/profiles` can rely on corresponding suites under
  `tests/devcovenant/core/profiles/` and
  `tests/devcovenant/custom/profiles/`.

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
