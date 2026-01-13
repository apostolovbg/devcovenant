# DevCovenant Specification
**Last Updated:** 2026-01-12
**Version:** 0.2.5

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
- Run a startup check at session start (`devcov_check.py check --mode
  startup` or `python3 -m devcovenant check --mode startup`).
- When policy text changes, set `updated: true`, update scripts/tests, run
  `devcovenant update-hashes`, then reset `updated: false`.
- Log every change in `CHANGELOG.md` under the current version header.

## Functional Requirements
### Policy definitions and registry
- Parse policy blocks from `AGENTS.md` and capture the descriptive text that
  follows each `policy-def` block.
- Hash policy definitions and scripts into `devcovenant/registry.json`.
- Expose `restore-stock-text` to reset policy prose to canonical wording.

### Engine behavior
- Load policy scripts from `devcovenant/core/policy_scripts/` with support for
  custom overrides in `devcovenant/custom/policy_scripts/` and patch scripts
  in `devcovenant/common_policy_patches/`.
- Respect `apply`, `severity`, `status`, and `enforcement` metadata for each
  policy.
- Support `startup`, `lint`, `pre-commit`, and `normal` modes.
- Apply auto-fixers when allowed, using fixers located under
  `devcovenant/core/policy_scripts/fixers/` and compatibility wrappers in
  `devcovenant/core/fixers/`.

### CLI commands
- Provide a console entry point (`devcovenant`) and module entry
  (`python3 -m devcovenant`) that both route to the same CLI.
- Supported commands: `check`, `sync`, `test`, `update-hashes`,
  `restore-stock-text`, `install`, `uninstall`.
- `check` exits non-zero when blocking violations or sync issues are present.
- `sync` runs a startup-mode check and reports drift.
- `test` runs `pytest` against `devcovenant/core/tests/`.
- `install` and `uninstall` delegate to `devcovenant/core/install.py` and
  `devcovenant/core/uninstall.py`.

### Documentation management
- Every managed doc must include `Last Updated` and `Version` headers.
- `devcovenant/README.md` also includes `DevCovenant Version`, sourced from
  the installer package version.
- Managed blocks are wrapped in `<!-- DEVCOV:BEGIN -->` and
  `<!-- DEVCOV:END -->`.

### Configuration and extension
- `devcovenant/config.yaml` must support `devcov_core_include` and
  `devcov_core_paths` for core exclusion.
- Language profiles are defined in `language_profiles` and activated via
  `active_language_profiles` to extend file suffix coverage.

## Policy Requirements
- Every policy definition includes descriptive prose immediately after the
  metadata block.
- Built-in policies have canonical text stored in
  `devcovenant/core/stock_policy_texts.json`.
- `apply: false` disables enforcement without removing definitions.
- `fiducial` policies remain enforced and always surface their policy text.
- Selector keys (`include_*`, `exclude_*`, `force_*`, `watch_*`) are supported
  across policy definitions for consistent scoping.

## Installation Requirements
- Install the full DevCovenant toolchain into the target repo, including the
  `devcovenant/` tree, `tools/` helpers, and CI workflow templates.
- Use packaged templates from `devcovenant/templates/` when installed from
  PyPI; fall back to repo files when running from source.
- Install modes: `auto`, `empty`, `existing`; use mode-specific defaults for
  docs, config, and metadata handling.
- Preserve custom policy scripts and patches by default on existing installs
  (`--preserve-custom`), with explicit overrides available.
- `AGENTS.md` is always written from the template; if a prior `AGENTS.md`
  exists, preserve its editable section under `# EDITABLE SECTION`.
- `README.md` keeps user content, receives the standard header, and gains a
  managed block with missing sections (Table of Contents, Overview, Workflow,
  DevCovenant).
- `DEVCOVENANT.md` is always backed up to `*_old.*` and replaced by the
  standard template during install or update.
- `SPEC.md` and `PLAN.md` keep content when present (header-only update) and
  are created from minimal templates when missing.
- `CHANGELOG.md` and `CONTRIBUTING.md` are backed up as `*_old.*` and replaced
  with standard DevCovenant templates.
- `VERSION` is created on demand. Accept `x.x` or `x.x.x`, normalize to
  `x.x.0`, and apply across headers.
- If no license exists, install the GPL-3.0 template with a `Project Version`
  header. Only overwrite licenses when explicitly requested.
- If `CITATION.cff` is missing, prompt to create it. When skipped, disable
  citation enforcement in `AGENTS.md` by setting
  `version-sync.citation_file: __none__`.
- Regenerate `.gitignore` from a universal baseline and merge existing user
  entries under a preserved block.
- Stamp `Last Updated` values using the UTC install date.
- Write `.devcov/install_manifest.json` with installed paths, options, and the
  UTC timestamp of the install or update.

## Packaging Requirements
- Ship `devcovenant` as a pure-Python package with a console script entry.
- Include templates and policy assets in the sdist and wheel.
- Require Python 3.10+ and declare runtime dependencies in
  `requirements.in`, `requirements.lock`, and `pyproject.toml`.
- Keep `THIRD_PARTY_LICENSES.md` and `licenses/` synchronized with dependency
  changes so the dependency-license-sync policy passes.

## Non-Functional Requirements
- Checks must be fast enough for pre-commit usage on typical repos.
- Violations must be clear, 