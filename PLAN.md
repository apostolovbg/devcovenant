# DevCovenant Delivery Plan
**Last Updated:** 2026-01-12
**Version:** 0.2.5

This plan tracks the roadmap from a working standalone repository to a
polished, published package that anyone can install and roll out across
existing repos with minimal friction.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Current State](#current-state)
4. [Phase 1: Release Hygiene](#phase-1-release-hygiene)
5. [Phase 2: Installer and Docs](#phase-2-installer-and-docs)
6. [Phase 3: Migration Guide](#phase-3-migration-guide)
7. [Phase 4: Post-Release Support](#phase-4-post-release-support)
8. [Next Steps](#next-steps)

## Overview
DevCovenant already enforces its policies, keeps policy text in sync, and
protects its own documentation. This plan focuses on release readiness,
installer reliability, and clear migration steps for production repos.

## Workflow
- Always gate changes with
  `python3 tools/run_pre_commit.py --phase start`,
  `python3 tools/run_tests.py`, and
  `python3 tools/run_pre_commit.py --phase end`.
- Keep `AGENTS.md` + policy scripts in sync; update hashes when prose changes.
- Preserve installer manifests and custom policy scripts during updates.
- Treat the changelog as the contract for release notes whenever files change.

## Current State
- Packaging uses `pyproject.toml` with a console script entry point.
- Templates for docs/config/tools are bundled under `devcovenant/templates/`.
- The installer merges README headers, preserves SPEC/PLAN content, and
  backs up and replaces `CHANGELOG.md` and `CONTRIBUTING.md` by default.
- The CLI exposes install/uninstall, update-hashes, and restore-stock-text.

## Phase 1: Release Hygiene
Deliverables:
- Validate `python -m build` and `twine check dist/*` in a clean environment.
- Confirm the `devcovenant` console script runs on Python 3.10+.
- Ensure `MANIFEST.in` includes templates and policy assets.
- Verify `requirements.in`, `requirements.lock`, and `pyproject.toml` remain
  aligned with `THIRD_PARTY_LICENSES.md` and `licenses/`.
- Confirm `publish.yml` uses the correct PyPI token and tags.

Validation:
- Install the wheel into a clean virtual environment.
- Run `devcovenant --help` and `devcovenant check --mode startup`.
- Install into a scratch repo and verify docs, config, and manifest output.

## Phase 2: Installer and Docs
Deliverables:
- Keep `SPEC.md`, `DEVCOVENANT.md`, and `devcovenant/README.md` aligned with
  current install behavior and CLI options.
- Keep template copies in sync with their root equivalents.
- Expand documentation around install modes, prompts, and backups.
- Capture edge cases (missing VERSION, skipped CITATION) in tests.

Validation:
- Run installer in `empty` and `existing` modes and verify outcomes.
- Confirm editable notes in `AGENTS.md` are preserved on reinstall.

## Phase 3: Migration Guide
Deliverables:
- Outline step-by-step migration plans for Copernican, GCV-ERP custom, and
  GCV-ERP infra, including policy or config adjustments required.
- Capture QA steps (pre-commit/tests) so those repos pass DevFlow gates after
  the upgrade.
- Document `--preserve-custom` behavior to keep existing custom policies and
  patches intact.

Validation:
- Each repo installs the release from PyPI and runs the gate sequence without
  policy drift.
- Custom scripts remain executable in their `custom/` directories after the
  migration.

## Phase 4: Post-Release Support
Deliverables:
- Track issues from first adopters and document fixes.
- Monitor packaging regressions (entry points, templates, metadata).
- Maintain clear release notes in `CHANGELOG.md` and tag migrations.

## Next Steps
- Run a clean build and confirm the publish workflow succeeds end-to-end.
- Keep documentation updated to reflect install prompts and defaults.
- Draft migration playbooks for the three legacy repos.
