# DevCovenant Specification
**Last Updated:** 2026-01-12
**Version:** 0.2.2

This specification defines what DevCovenant must do for both the standalone
project and for any repository that installs it.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Functional Requirements](#functional-requirements)
4. [Policy Requirements](#policy-requirements)
5. [Installation Requirements](#installation-requirements)
6. [Non-Functional Requirements](#non-functional-requirements)

## Overview
DevCovenant is a self-enforcing policy engine. It reads policy definitions from
`AGENTS.md`, enforces them through policy scripts, and prevents drift between
human documentation and automated checks. The system must be portable, safe to
install, and reversible without losing user documentation.

## Workflow
- Policies are defined in `AGENTS.md` and treated as the source of truth.
- Policy changes require updates to scripts and tests.
- Hash synchronization prevents policy/script drift.
- The standard gate sequence is pre-commit start → tests → pre-commit end.
- The gate sequence must run for every repository change (code, config,
  or docs).
  If a repo lacks automated tests, still run the pre-commit hooks and note the
  absence before finishing the workflow.
- Use `python3` for helper scripts when available (`python` only if it points
  to Python 3 on the host system).

## Release Readiness Review
- Confirm `tools/run_pre_commit.py --phase start` completes successfully before
  tagging a release candidate. Run `python3 tools/run_tests.py` and ensure
  `tools/run_pre_commit.py --phase end` finishes as well. The
  `devflow-run-gates` policy enforces these gates even for documentation
  changes.
- Ensure policy hashes are up-to-date
  (`python3 -m devcovenant.cli update-hashes`).
- The changelog must mention every file touched during the prep work.
- The registry (`devcovenant/registry.json`) should reflect the new hashes.
- Build artifacts with `python -m build`.
- Validate the wheel and sdist via `twine check dist/*`.
- Run the `publish.yml` workflow before the public release so reproduction is
  straightforward.
- Target a test tag and ensure the workflow uses `PYPI_API_TOKEN`.

## Functional Requirements
- Parse policy definitions from `AGENTS.md`.
- Run policy scripts and report violations by severity.
- Support auto-fix where policies allow it.
- Maintain a registry of policy and script hashes.
- Provide a CLI for `check`, `sync`, `test`, and `update-hashes` commands.
- Provide wrapper scripts for pre-commit and test gating.
- Provide a CLI-only installer with explicit modes for empty vs. existing
  repositories and options to preserve or overwrite docs/config/metadata.
- Support multi-language repos via configurable language profiles that extend
  the engine’s file suffix inventory.
- Expose management commands (`install`, `uninstall`, `restore-stock-text`,
  `sync`, `update-hashes`) so every action happens through DevCovenant’s CLI.
- Organize built-in components under `devcovenant/core/` and keep repo-facing
  extensions in `devcovenant/custom/`, including `policy_scripts` and `fixers`.
- Load auto-fixers from `core/fixers` and allow repositories to add helpers
  within `custom/fixers`.
- Inject DevCovenant-managed documentation via `devcov begin` / `devcov end`
  markers and standardized headers so installs never need manual edits.

## Policy Requirements
- Every policy definition must include descriptive text.
- Built-in policies ship with canonical text stored in DevCovenant.
- If canonical text is modified in a repo, DevCovenant must warn and guide
  the agent to either restore stock text or patch the policy logic.
- Provide a command to restore stock policy text by policy id.
- Policies must support an `apply` flag that enables or disables enforcement
  without removing the definition.
- Policies with status `fiducial` must be enforced and emit a reminder that
  includes the policy text on every run.
- The dependency-license-sync policy ensures dependency manifests refresh
  `THIRD_PARTY_LICENSES.md` and the `licenses/` directory, and that the
  `## License Report` section records every change so summaries stay aligned
  with the tracked dependencies.
- Policy definitions must expose the shared selectors (`include_*`,
  `exclude_*`, `force_include_*`, `watch_*`) so repositories can reason about
  scope consistently.
- `devcov_core_include`, stored in `config.yaml`, governs whether the
  `devcovenant/core/` tree is scanned by policies. User installs default to
  `false` so DevCovenant can update itself without triggering violations
  against its own implementation.

## Installation Requirements
- Install the full DevCovenant toolchain into the target repo.
- Preserve existing user documentation unless explicitly overridden.
- Inject DevCovenant-managed doc blocks using `devcov` markers.
- Track installations with `.devcov/install_manifest.json`.
- If no license exists, install a GPL-3.0 license by default.
- Default user installs to `devcov_core_include: false` so core files remain
  excluded from enforcement and update-safe.
- Treat `SPEC.md` and `PLAN.md` as required documentation files during
  installation and enforcement.
- Preserve custom policy scripts, patches, and configuration during updates
  unless explicitly overridden.
- Install or update CI workflows to ensure pre-commit, pytest, PyYAML, and
  semver dependencies are available for checks.
- Track dependencies in `requirements.in`, `requirements.lock`, and
  `pyproject.toml`. Keep `THIRD_PARTY_LICENSES.md` and the `licenses/`
  directory synchronized with those manifests so each dependency change also
  refreshes the recorded license text and the `## License Report`.
- Provide an uninstall routine that strips DevCovenant-managed blocks from
  documentation, optionally removing the inserted sections while leaving the
  rest of the file untouched.
- Rewrite existing files only when install-time switches demand it; otherwise
  fold DevCovenant additions into reserved regions marked with `devcov begin`
  / `devcov end` so user content survives updates.
- Operate purely through CLI commands; no compatibility shims or loose scripts
  should remain on disk after installation.

## Non-Functional Requirements
- The engine must run quickly enough for pre-commit usage.
- Policies must produce actionable, readable violation messages.
- Documentation must meet minimum quality standards.
- Installation and removal must be deterministic and reversible.
