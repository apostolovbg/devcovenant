# DevCovenant Delivery Plan
**Last Updated:** 2026-01-11
**Version:** 0.2.0

This plan tracks the migration of DevCovenant into a standalone, self-enforcing
product. It is written to be executable: each phase lists concrete outputs and
validation steps.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Phase 1: Foundation](#phase-1-foundation)
4. [Phase 2: Installer and Uninstaller](#phase-2-installer-and-uninstaller)
5. [Phase 3: Policy Schema
   Standardization](#phase-3-policy-schema-standardization)
6. [Phase 4: Policy Packs and
   API](#phase-4-policy-packs-and-api)
7. [Phase 5: Publishing and
   Migration](#phase-5-publishing-and-migration)

## Overview
DevCovenant is being spun out from multiple production repos. The goal is a
stable, standalone engine that can install into any repository while enforcing
its own policies and documentation quality.

## Workflow
- Keep `AGENTS.md` as the policy source of truth.
- Update policy scripts and tests whenever policies change.
- Keep installation safe and reversible with a manifest.
- Require pre-commit + tests at the start and end of each change window.

## Phase 1: Foundation
Deliverables:
- Package the core engine under `devcovenant/core/` and keep installables,
  docs, and patches under `devcovenant/` so the project can self-host.
- Deliver AGENTS/README/DEVCOVENANT/CONTRIBUTING headers with `devcov`
  markers plus VERSION, CHANGELOG, CITATION, and LICENSE files in place.
- Gate the repo with pre-commit + tests.

Validation:
- `python3 tools/run_pre_commit.py --phase start`
- `python3 tools/run_tests.py`
- `python3 tools/run_pre_commit.py --phase end`

## Phase 2: Installer and Uninstaller
Deliverables:
- Provide CLI install/uninstall commands (`devcovenant install`, `uninstall`)
  with manifest tracking, `devcov_core_include` switches, and doc/config/mode
  flags.
- Preserve user docs via `devcov begin`/`end` markers unless the user
  explicitly requests overwrites (`--force-docs`, `--force-config`, etc.).
- Default installs keep `devcov_core_include: false`, add GPL-3.0
  (if missing), and inject standard CI workflows that install pre-commit,
  pytest, PyYAML, and semver.
- Ensure no compatibility shims remain—everything time-critical runs through
  CLI commands and manifest-controlled modules.
- Provide an uninstall helper that removes `devcov` sections while leaving
  existing human-written content untouched.

Validation:
- Install into a scratch repo and confirm docs are preserved.
- Uninstall and confirm managed blocks are removed.
- Reinstall over an existing repo and confirm custom policies/fixers remain.

## Phase 3: Policy Schema Standardization
Deliverables:
- Require shared selectors metadata for every policy and keep the `apply`
  activation flag so policies can toggle without removing definitions.
- Emit `fiducial` policy reminders and offer a CLI-driven `restore-stock-text`
  helper when policy prose diverges from scripts.
- Track policy text hashes so the engine refuses to proceed when policies
  describe different rules than the code.

Validation:
- Update `devcovenant/core/parser.py` and tests.
- Add a migration checklist for downstream repos.

## Phase 4: Policy Packs and API
Deliverables:
- Formal policy API that surfaces selectors, metadata, and fixers for every
  policy.
- Maintain built-in checks under `core/policy_scripts/` and core fixers under
  `core/fixers/`.
- Allow repositories to contribute custom policies/fixers from
  `custom/policy_scripts/` and `custom/fixers/` without mutating the stock
  implementation.

Validation:
- Add an example custom policy using the new API.
- Ensure patch overrides work without modifying core scripts.

## Phase 5: Publishing and Migration
Deliverables:
- Publish to PyPI and document GitHub install path.
- Migrate Copernican, GCV-ERP custom, and infra repos
  to the standalone install.
- Remove compatibility shims once the new CLI approach is validated.
- Ensure the standalone engine runs in these repos as if freshly installed.

Validation:
- Each repo installs DevCovenant from the standalone source.
- Pre-commit, tests, and CI pass with no policy drift.

## Next Steps
- Finalize the Copernican and GCV-ERP migrations so they install this
  standalone DevCovenant as if from scratch while keeping their policy
  configuration in sync.
