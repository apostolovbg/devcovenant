# DevCovenant Delivery Plan
**Last Updated:** 2026-01-11
**Version:** 0.1.1

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
- Package core code under `devcovenant/`.
- Split core implementation into `devcovenant/core` and keep repo-facing
  configuration, patches, and docs at the root of `devcovenant/`.
- Provide `AGENTS.md`, `DEVCOVENANT.md`, `README.md`, `CONTRIBUTING.md`.
- Add `VERSION`, `CHANGELOG.md`, `CITATION.cff`, `LICENSE`.
- Enforce pre-commit, tests, and CI for this repo.

Validation:
- `python3 tools/run_pre_commit.py --phase start`
- `python3 tools/run_tests.py`
- `python3 tools/run_pre_commit.py --phase end`

## Phase 2: Installer and Uninstaller
Deliverables:
- `tools/install_devcovenant.py` with manifest tracking and CLI-only modes
  for empty vs. existing repos.
- Explicit CLI options to preserve/overwrite docs, config, and metadata files
  (LICENSE, VERSION, CITATION, pyproject).
- Update-safe installs that preserve `custom/policy_scripts`,
  `common_policy_patches`, and `config.yaml` by default.
- `tools/uninstall_devcovenant.py` that strips managed blocks safely.
- Install/update modes that avoid overwriting user docs unless requested.
- CI templates that install pre-commit, pytest, PyYAML, and semver so hooks
  and tests run in GitHub Actions.
- Default installs to `devcov_core_include: false` in
  `devcovenant/config.yaml`.

Validation:
- Install into a scratch repo and confirm docs are preserved.
- Uninstall and confirm managed blocks are removed.
- Reinstall over an existing repo with custom scripts and confirm they
  remain intact.

## Phase 3: Policy Schema Standardization
Deliverables:
- Enforce standard metadata fields in every policy block.
- Document policy-specific fields consistently.
- Standardize `apply` as the policy activation flag and remove waiver-only
  metadata.

Validation:
- Update `devcovenant/core/parser.py` and tests.
- Add a migration checklist for downstream repos.

## Phase 4: Policy Packs and API
Deliverables:
- Formal policy API for custom checks and fixers.
- Built-in policy pack in `core/policy_scripts/`.
- Stable extension points for repo-specific policies and patches.

Validation:
- Add an example custom policy using the new API.
- Ensure patch overrides work without modifying core scripts.

## Phase 5: Publishing and Migration
Deliverables:
- Publish to PyPI and document GitHub install path.
- Migrate Copernican, GCV-ERP custom, and infra repos to standalone.
- Keep compatibility shims during transition.

Validation:
- Each repo installs DevCovenant from the standalone source.
- Pre-commit, tests, and CI pass with no policy drift.
