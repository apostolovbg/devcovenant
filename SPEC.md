# DevCovenant Specification
**Last Updated:** 2026-01-23
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
- Hash policy definitions and scripts into `devcovenant/registry.json`.
- Expose `restore-stock-text` to reset policy prose to canonical wording.
- Support `custom: true/false` metadata to mark custom policy prose that
  bypasses stock text sync checks.
- Maintain a canonical metadata schema that lists all supported keys (common
  and policy-specific) so every policy block can be normalized on demand.

### Engine behavior
- Load policy scripts from `devcovenant/core/policy_scripts/` with support for
  custom overrides in `devcovenant/custom/policy_scripts/`.
- When a custom policy script exists, it fully replaces the built-in policy
  and suppresses core fixers for that policy.
- Respect `apply`, `severity`, `status`, and `enforcement` metadata for each
  policy.
- Support `startup`, `lint`, `pre-commit`, and `normal` modes.
- Apply auto-fixers when allowed, using fixers located under
  `devcovenant/core/fixers/` and any custom fixers under
  `devcovenant/custom/fixers/`.

### CLI commands
- Provide a console entry point (`devcovenant`) and module entry
  (`python3 -m devcovenant`) that both route to the same CLI.
- Supported commands: `check`, `sync`, `test`, `update-hashes`,
  `restore-stock-text`, `install`, `update`, `uninstall`,
  `normalize-metadata`.
- `check` exits non-zero when blocking violations or sync issues are present.
- `sync` runs a startup-mode check and reports drift.
- `test` runs `pytest` against `devcovenant/core/tests/`.
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

### Configuration and extension
- `devcovenant/config.yaml` must support `devcov_core_include` and
  `devcov_core_paths` for core exclusion.
- Language profiles are defined in `language_profiles` and activated via
  `active_language_profiles` to extend file suffix coverage.

## Policy Requirements
- Every policy definition includes descriptive prose immediately after the
  metadata block.
- Built-in policies have canonical text stored in
  `devcovenant/core/stock_policy_texts.yaml`.
- `apply: false` disables enforcement without removing definitions.
- `fiducial` policies remain enforced and always surface their policy text.
- Selector keys (`include_*`, `exclude_*`, `force_*`, `watch_*`) are supported
  across policy definitions for consistent scoping.
- Policy metadata normalization must be able to add missing keys without
  changing existing values or policy text.
- Support policy replacement metadata via
  `devcovenant/core/policy_replacements.yaml`. During updates, replaced
  policies move to custom and are marked deprecated when enabled; disabled
  policies are removed along with their custom scripts and fixers.
- Record update notices (replacements and new stock policies) in
  `devcovenant/manifest.json` and print them to stdout.

## Installation Requirements
- Install the full DevCovenant toolchain into the target repo, including the
  `devcovenant/` tree, `tools/` helpers, and CI workflow templates.
- Use packaged templates from `devcovenant/templates/` when installed from
  PyPI; fall back to repo files when running from source.
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
- Regenerate `.gitignore` from a universal baseline and merge existing user
  entries under a preserved block.
- Always back up overwritten or merged files as `*_old.*`, even when
  merges succeed, and report the backups at the end of install.
- Stamp `Last Updated` values using the UTC install date.
- Support partial doc overwrites via `--docs-include` / `--docs-exclude`, so
  only selected docs are replaced when docs mode overwrites.
- Support policy update modes via `--policy-mode preserve|append-missing|`
  `overwrite`.
- Write `devcovenant/manifest.json` with the core layout, doc types,
  installed paths, options, active profiles, policy asset mappings, and
  the UTC timestamp of the install or update.

## Packaging Requirements
- Ship `devcovenant` as a pure-Python package with a console script entry.
- Include templates and policy assets in the sdist and wheel.
- Require Python 3.10+ and declare runtime dependencies in
  `requirements.in`, `requirements.lock`, and `pyproject.toml`.
- Keep `THIRD_PARTY_LICENSES.md` and `licenses/` synchronized with dependency
  changes so the dependency-license-sync policy passes.

## Non-Functional Requirements
- Checks must be fast enough for pre-commit usage on typical repos.
- Violations must be clear, actionable, and reference the policy source.
- Install and uninstall operations must be deterministic and reversible.
