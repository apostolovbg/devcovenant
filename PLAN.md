# DevCovenant Delivery Plan
**Last Updated:** 2026-01-11
**Version:** 0.2.0

This plan tracks the roadmap from a working standalone repository to a
polished, publishable package that anyone can install and then inject into a
target repository with a single command.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Phase 1: Packaging & PyPI Publication](#phase-1-packaging--pypi-publication)
4. [Phase 2: Installer / CLI Experience](#phase-2-installer--cli-experience)
5. [Phase 3: Migration Guide for Existing Repos](#phase-3-migration-guide-for-existing-repos)
6. [PyPI Registration](#pypi-registration)
7. [Next Steps](#next-steps)

## Overview
DevCovenant already enforces its policies, keeps policy text in sync, and
protects its own documentation. This plan now prioritizes packaging, publication,
and user-friendly installation before sweeping the anchored production repos
forward to the new release.

## Workflow
- Always gate changes with `python3 tools/run_pre_commit.py --phase start`,
  `python3 tools/run_tests.py`, and `python3 tools/run_pre_commit.py --phase end`.
- Keep `AGENTS.md` + policy scripts in sync; update hashes when prose changes.
- Preserve installer manifests and custom policy scripts during updates.
- Treat the changelog as the contract for release notes whenever files change.

## Phase 1: Packaging & PyPI Publication
Deliverables:
- Finalize `pyproject.toml` metadata (long description, classifiers, license,
  keywords) so `python -m build` produces a clean wheel + sdist.
- Add automated builds/publishing (GitHub Actions or similar) that run `python
  -m build` and `twine check`, then upload with `twine upload dist/*` on tagged
  releases.
- Publish DevCovenant to PyPI (or TestPyPI for a dry run) and document the
  recommended install command (`pip install devcovenant` plus `python3 -m
  devcovenant.cli install --target <repo>`).
- Keep release notes in `CHANGELOG.md` and mention any files touched by the
  packaging work.

Validation:
- Run `python -m build` locally and `twine check dist/*`.
- Test installing the built wheel from a local `pip install dist/devcovenant-*`.
- Confirm the new CLI bundle works and installs clean docs/manifests into a
  fresh repo.

## Phase 2: Installer / CLI Experience
Deliverables:
- Ensure the CLI entry point (e.g., `devcovenant.cli`) exposes install/uninstall,
  and document those commands in README + docs.
- Bundle helper scripts (`tools/run_pre_commit.py`, `tools/run_tests.py`,
  `devcov_check.py`, etc.) so installs mimic the repository layout.
- Document how custom policy scripts/fixers stay in `devcovenant/custom/` and how
  the installer preserves them (`--preserve-custom` behavior).
- Publish or mention prebuilt installers (scripts, wrappers) so users can run the
  install command without hunting for files.

Validation:
- Run the installer on a scratch repo and verify the manifest, docs, and custom
  scripts are preserved.
- Confirm `devcovenant check --mode startup` runs inside the installed tree.

## Phase 3: Migration Guide for Existing Repos
Deliverables:
- Outline step-by-step migration plans for Copernican, GCV-ERP custom, and
  GCV-ERP infra, including any policy or config adjustments required.
- Capture QA steps (pre-commit/tests) so those repos pass DevFlow gates after the
  upgrade.
- Include guidance on re-running `devcovenant install` with `--preserve-custom`
  to keep existing scripts/policy patches untouched.

Validation:
- Each of the three repos installs the new release from PyPI and runs the gate
  sequence without policy drift.
- Custom scripts remain executable in their `custom/` directories after the
  migration.

## PyPI Registration
- Yes, you must register an account on https://pypi.org/ (or use an existing one)
  to upload releases.
- Create an API token scoped to the `devcovenant` project and store it securely
  (CI secrets, keyring, etc.).
- Use `twine upload --username __token__ --password <token>` or configure your
  automation to reference the token so future releases happen without manual
  logins.

## Next Steps
- Publish the first packaged release to PyPI and update README/CHANGELOG with the
  install instructions.
- Coordinate with Copernican, GCV-ERP custom, and infra teams to migrate their
  installs.
- Keep monitoring `devcovenant` releases and ensure each new version updates the
  policy registry (`python3 -m devcovenant.cli update-hashes`).
