# DevCovenant (Repository Guide)
**Last Updated:** 2026-01-12
**Version:** 0.2.5
**DevCovenant Version:** 0.2.5
**Status:** Active Development
**License:** DevCovenant License v1.0

This file is installed into a target repository at `devcovenant/README.md`.
It explains how to use DevCovenant inside that repo. The root `README.md`
should remain dedicated to the repository's actual project.

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Workflow](#workflow)
4. [CLI Entry Points](#cli-entry-points)
5. [CLI Command Reference](#cli-command-reference)
6. [Install Modes and Options](#install-modes-and-options)
7. [Installer Behavior (File by File)](#installer-behavior-file-by-file)
8. [Install Manifest](#install-manifest)
9. [Managed Documentation Blocks](#managed-documentation-blocks)
10. [Editable Notes in AGENTS](#editable-notes-in-agents)
11. [Core Exclusion and Config](#core-exclusion-and-config)
12. [Language Profiles](#language-profiles)
13. [Check Modes and Exit Codes](#check-modes-and-exit-codes)
14. [Auto-Fix Behavior](#auto-fix-behavior)
15. [Policy Registry and Stock Text](#policy-registry-and-stock-text)
16. [Policy Scripts, Fixers, and Patches](#policy-scripts-fixers-and-patches)
17. [DevFlow Gates and Test Status](#devflow-gates-and-test-status)
18. [Dependency and License Tracking](#dependency-and-license-tracking)
19. [Templates and Packaging](#templates-and-packaging)
20. [Uninstall Behavior](#uninstall-behavior)
21. [CI and Automation](#ci-and-automation)
22. [Troubleshooting](#troubleshooting)

## Overview
DevCovenant enforces the policies written in `AGENTS.md`. It parses those
policies, validates them against their scripts, and reports violations with
clear severity levels. The system is designed to keep policy text,
enforcement logic, and documentation synchronized.

## Quick Start
If DevCovenant is installed, start with (use `python3` unless `python`
already points to Python 3):
```bash
pip install devcovenant

devcovenant install --target .

python3 tools/run_pre_commit.py --phase start
python3 tools/run_tests.py
python3 tools/run_pre_commit.py --phase end
```

If you built DevCovenant locally, `pip install dist/devcovenant-*` before
running `devcovenant install --target .` so the wheel files are reused.

## Workflow
DevCovenant requires the gated workflow for every change, including
documentation updates:
1. `python3 tools/run_pre_commit.py --phase start`
2. `python3 tools/run_tests.py`
3. `python3 tools/run_pre_commit.py --phase end`

When policy text changes, set `updated: true`, update scripts/tests, run
`devcovenant update-hashes`, then reset the flag.

## CLI Entry Points
DevCovenant ships both a console script and a module entry:
```bash
devcovenant --help
python3 -m devcovenant --help
```

Use the module entry if the console script is not on your PATH.

## CLI Command Reference
The primary commands are:
- `devcovenant check` (default enforcement)
- `devcovenant check --mode startup|lint|pre-commit|normal`
- `devcovenant check --fix` (apply auto-fixes when allowed)
- `devcovenant sync` (startup sync check)
- `devcovenant test` (runs `pytest devcovenant/core/tests/`)
- `devcovenant update-hashes` (refresh `devcovenant/registry.json`)
- `devcovenant restore-stock-text --policy <id>`
- `devcovenant restore-stock-text --all`
- `devcovenant install --target <path>`
- `devcovenant uninstall --target <path>`

The `tools/*.py` helpers are compatibility wrappers that forward to the CLI.

## Install Modes and Options
The installer can run in three modes:
- `--install-mode auto`: infer install vs. update based on the target.
- `--install-mode empty`: treat the repo as new.
- `--install-mode existing`: treat the repo as a pre-existing install.

Docs, config, and metadata handling defaults are derived from the mode:
- `--docs-mode preserve|overwrite`
- `--config-mode preserve|overwrite`
- `--metadata-mode preserve|overwrite|skip`

Targeted overrides:
- `--license-mode inherit|preserve|overwrite|skip`
- `--version-mode inherit|preserve|overwrite|skip`
- `--pyproject-mode inherit|preserve|overwrite|skip`
- `--ci-mode inherit|preserve|overwrite|skip`
- `--citation-mode prompt|create|skip`
- `--preserve-custom` / `--no-preserve-custom`
- `--force-docs` / `--force-config`
- `--version <x.x|x.x.x>` to avoid prompts when `VERSION` is missing.

## Installer Behavior (File by File)
When DevCovenant installs into an existing repo, the following behaviors
apply:

- `devcovenant/`: core engine always installs; `custom/` and
  `common_policy_patches/` are preserved by default on existing installs.
- `devcov_check.py`, `tools/run_pre_commit.py`, `tools/run_tests.py`,
  `tools/update_test_status.py`: always overwritten from the package.
- `.pre-commit-config.yaml`, `.github/workflows/ci.yml`: preserved when
  `--config-mode preserve`, otherwise overwritten. Use `--ci-mode skip` to
  skip CI installs.
- `.gitignore`: regenerated from the universal baseline and merged with any
  existing user entries under a preserved block.
- `AGENTS.md`: always replaced by the template. If an existing file is found,
  the editable section content is preserved under `# EDITABLE SECTION`.
- `README.md`: existing content is preserved, headers are refreshed, and the
  managed block is inserted to add missing sections.
- `DEVCOVENANT.md`: always backed up to `*_old.*` and replaced by the template.
- `SPEC.md`, `PLAN.md`: existing content is preserved while headers are
  updated; missing files are created from minimal templates.
- `CHANGELOG.md`, `CONTRIBUTING.md`: always backed up to `*_old.*` and
  replaced by the standard templates.
- `VERSION`: created on demand. Accepts `x.x` or `x.x.x` and normalizes to
  `x.x.0`. `--version` avoids prompts.
- `LICENSE`: created from the GPL-3.0 template if missing. Overwritten only
  when the license mode requests it, and the original is backed up first.
- `CITATION.cff`: created if missing and approved by prompt (or if
  `--citation-mode create` is used). If skipped, citation enforcement is
  disabled in `AGENTS.md` by setting `version-sync.citation_file: __none__`.
- `pyproject.toml`: preserved or overwritten based on `--pyproject-mode`.
- `.devcov/install_manifest.json`: always written with install metadata.

All `Last Updated` headers are stamped with the UTC install date.

## Install Manifest
The installer writes `.devcov/install_manifest.json` with:
- `updated_at`: ISO timestamp in UTC.
- `mode`: `install` or `update`.
- `installed`: lists of installed paths by group (`core`, `config`, `docs`).
- `doc_blocks`: list of docs that received managed blocks.
- `options`: resolved install options (docs/config/metadata modes, version,
  citation mode, core inclusion, and preservation flags).

Use this file to audit what DevCovenant changed in the target repo.

## Managed Documentation Blocks
DevCovenant-managed blocks are wrapped as:
```
<!-- DEVCOV:BEGIN -->
... managed content ...
<!-- DEVCOV:END -->
```

The installer inserts or replaces these blocks while leaving surrounding text
untouched. Policies like `documentation-growth-tracking` and
`policy-text-presence` depend on these markers, so do not edit them manually
outside of the DevCovenant workflow.

## Editable Notes in AGENTS
`AGENTS.md` contains a dedicated editable section, located just below the
first `<!-- DEVCOV:END -->` marker and labeled `# EDITABLE SECTION` when the
file is installed. The installer preserves any existing notes in that region
and reinserts them on subsequent installs. Use this area for repo-specific
working memory, decisions, and constraints.

## Core Exclusion and Config
User repos should keep DevCovenant core excluded from enforcement so updates
remain safe. The installer sets this automatically in
`devcovenant/config.yaml`:
```yaml
devcov_core_include: false
devcov_core_paths:
  - devcovenant/core
  - devcovenant/__init__.py
  - devcovenant/__main__.py
  - devcovenant/cli.py
  - devcov_check.py
  - tools/run_pre_commit.py
  - tools/run_tests.py
  - tools/update_test_status.py
  - tools/install_devcovenant.py
  - tools/uninstall_devcovenant.py
```

Only the DevCovenant repo should set `devcov_core_include: true`.

## Language Profiles
For multi-language repos, configure `language_profiles` and
`active_language_profiles` in `devcovenant/config.yaml` to extend the
engine’s file suffix inventory without rewriting the full list. Each profile
can provide a `suffixes` list that is merged into `engine.file_suffi