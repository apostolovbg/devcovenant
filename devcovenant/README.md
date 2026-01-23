# DevCovenant (Repository Guide)
**Last Updated:** 2026-01-23
**Version:** 0.2.6

**DevCovenant Version:** 0.2.6
**Status:** Active Development
**License:** DevCovenant License v1.0

<!-- DEVCOV:BEGIN -->
**Doc ID:** DEVCOVENANT-README
**Doc Type:** devcovenant-guide
**Managed By:** DevCovenant
<!-- DEVCOV:END -->

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
7. [Install Behavior Reference](#install-behavior-reference)
8. [Installer Behavior (File by File)](#installer-behavior-file-by-file)
9. [Install Manifest](#install-manifest)
10. [Managed Documentation Blocks](#managed-documentation-blocks)
11. [Editable Notes in AGENTS](#editable-notes-in-agents)
12. [Core Exclusion and Config](#core-exclusion-and-config)
13. [Language Profiles](#language-profiles)
14. [Check Modes and Exit Codes](#check-modes-and-exit-codes)
15. [Auto-Fix Behavior](#auto-fix-behavior)
16. [Policy Registry and Stock Text](#policy-registry-and-stock-text)
17. [Policy Scripts and Fixers](#policy-scripts-and-fixers)
18. [DevFlow Gates and Test Status](#devflow-gates-and-test-status)
19. [Dependency and License Tracking](#dependency-and-license-tracking)
20. [Templates and Packaging](#templates-and-packaging)
21. [Uninstall Behavior](#uninstall-behavior)
22. [CI and Automation](#ci-and-automation)
23. [Troubleshooting](#troubleshooting)

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
- `devcovenant normalize-metadata` (insert missing metadata keys)
- `devcovenant restore-stock-text --policy <id>`
- `devcovenant restore-stock-text --all`
- `devcovenant install --target <path>`
- `devcovenant update --target <path>`
- `devcovenant uninstall --target <path>`

Normalize-metadata uses `devcovenant/templates/AGENTS.md` as the schema.
Empty metadata values (blank strings or empty lists) are treated as unset,
so defaults still apply. Use `--schema` to point at a different AGENTS file
and `--no-set-updated` to avoid flipping `updated: true` on changed policy
blocks.

Selector roles
--------------
Policies can declare `selector_roles` to enable standardized selector
triplets. Each role name produces `role_globs`, `role_files`, and
`role_dirs` metadata keys. Custom role names are allowed and interpreted
by the policy script. Normalization infers roles from legacy selector
keys (for example, `include_suffixes` or `guarded_paths`) and inserts
the triplets without overwriting existing values.
Documentation-growth-tracking defaults to the roles `user_facing`,
`user_visible`, and `doc_quality`, with legacy selector keys mapped into
role triplets during normalization.

The `tools/*.py` scripts support the repo workflow (pre-commit/test gates).

## Install Modes and Options
Install is for new repos. Use `devcovenant update` to refresh existing
installs. Install supports:
- `--install-mode auto`: infer new vs. existing and refuse if already
  installed.
- `--install-mode empty`: treat the repo as new.

Docs, config, and metadata handling defaults are derived from the mode:
- `--docs-mode preserve|overwrite`
- `--config-mode preserve|overwrite`
- `--metadata-mode preserve|overwrite|skip`

Updates default to preserve docs/config/metadata, append missing policies,
and run metadata normalization.
- `--policy-mode preserve|append-missing|overwrite`

Targeted overrides:
- `--license-mode inherit|preserve|overwrite|skip`
- `--version-mode inherit|preserve|overwrite|skip`
- `--pyproject-mode inherit|preserve|overwrite|skip`
- `--ci-mode inherit|preserve|overwrite|skip`
- `--docs-include README,AGENTS,...` (limit overwrites to named docs)
- `--docs-exclude CONTRIBUTING,...` (omit docs from overwrite targets)
- `--include-spec` / `--include-plan` (create optional SPEC/PLAN docs)
- `--preserve-custom` / `--no-preserve-custom`
- `--force-docs` / `--force-config`
- `--version <x.x|x.x.x>` to avoid prompts when `VERSION` is missing.
Doc selectors use extension-less names like `README` or `AGENTS`.

## Install Behavior Reference
The installer keeps repo content intact by default and only
overwrites when explicitly instructed. Summary:
- `AGENTS.md`: replaced by template; editable notes preserved.
- `README.md`: content preserved; headers refreshed; managed block added.
- `CHANGELOG.md` / `CONTRIBUTING.md`: preserved unless docs overwrite is
  requested, in which case originals are backed up as `*_old.*`.
- `SPEC.md` / `PLAN.md`: optional; created only with `--include-spec` or
  `--include-plan`, otherwise preserved if they already exist.
- `.gitignore`: regenerated and merged with a preserved user block.
- Config files: preserved unless `--config-mode overwrite` (or forced).

## Installer Behavior (File by File)
Install targets new repositories. Use `devcovenant update` for existing
repos; it preserves content by default and refreshes managed blocks.

- `devcovenant/`: core engine always installs; `custom/` scripts and fixers
  are preserved by default on updates.
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
- `SPEC.md`, `PLAN.md`: optional; existing content is preserved while
  headers refresh. Use `--include-spec` / `--include-plan` to create
  them when missing.
- `CHANGELOG.md`, `CONTRIBUTING.md`: replaced only when docs mode overwrites;
  otherwise content is preserved while headers and managed blocks refresh.
- `--docs-include` / `--docs-exclude` limit which docs are overwritten when
  `--docs-mode overwrite` is selected.
- `VERSION`: created on demand. Accepts `x.x` or `x.x.x` and normalizes to
  `x.x.0`. `--version` avoids prompts.
- `LICENSE`: created from the GPL-3.0 template if missing. Overwritten only
  when the license mode requests it, and the original is backed up first.
- `pyproject.toml`: preserved or overwritten based on `--pyproject-mode`.
- `devcovenant/manifest.json`: always written or refreshed by install,
  update, or first-run checks.

All `Last Updated` headers are stamped with the UTC install date.

## Install Manifest
The installer writes `devcovenant/manifest.json` with:
- `schema_version`: manifest schema version.
- `updated_at`: ISO timestamp in UTC.
- `mode`: `install` or `update`.
- `core`: required core directories and files.
- `docs`: doc paths grouped by type (`core`, `optional`, `custom`).
- `custom`: allowed user-writable paths (`devcovenant/custom/**`).
- `generated`: generated files such as registries or test status.
- `installed`: lists of installed paths by group (`core`, `config`, `docs`).
- `doc_blocks`: list of docs that received managed blocks.
- `options`: resolved install options (docs/config/metadata modes, version,
  core inclusion, and preservation flags).

Use this file to audit what DevCovenant changed in the target repo. The
structure guard reads it to validate core layout and managed docs. If the
manifest is missing (manual migration), the first DevCovenant run creates
it automatically.

Manifest schema (summary):
```json
{
  "schema_version": 1,
  "updated_at": "2026-01-22T00:00:00Z",
  "mode": "install|update",
  "core": {
    "dirs": ["devcovenant/core"],
    "files": ["devcovenant/cli.py"]
  },
  "docs": {
    "core": ["AGENTS.md"],
    "optional": ["SPEC.md"],
    "custom": []
  },
  "custom": {
    "dirs": ["devcovenant/custom"],
    "files": []
  },
  "generated": {
    "dirs": [],
    "files": ["devcovenant/registry.json"]
  },
  "installed": {
    "core": [],
    "config": [],
    "docs": []
  },
  "doc_blocks": ["AGENTS.md"],
  "options": {
    "policy_mode": "append-missing"
  }
}
```

## Managed Documentation Blocks
DevCovenant-managed blocks are wrapped as:
```
<!-- DEVCOV:BEGIN -->
**Doc ID:** README
**Doc Type:** repo-readme
**Managed By:** DevCovenant

... managed content ...
<!-- DEVCOV:END -->
```

Every managed doc receives a top-of-file block just below the standard header
lines (`Last Updated`, `Version`, and any additional header markers). The
installer inserts or replaces these blocks while leaving surrounding text
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
```

Only the DevCovenant repo should set `devcov_core_include: true`.

## Language Profiles
For multi-language repos, configure `language_profiles` and
`active_language_profiles` in `devcovenant/config.yaml` to extend the
engine’s file suffix inventory without rewriting the full list. Each profile
can provide a `suffixes` list that is merged into `engine.file_suffixes`.

## Check Modes and Exit Codes
Run checks through the CLI:
```bash
devcovenant check

devcovenant check --mode startup

devcovenant check --mode pre-commit
```

- `startup` is used at session start to detect drift early.
- `lint` focuses on faster checks and avoids heavy operations.
- `pre-commit` matches the gating workflow.
- `normal` is the default for full enforcement.

`check` exits non-zero if blocking violations or sync issues exist. Use
`devcovenant check --fix` to apply auto-fixes when available.

## Auto-Fix Behavior
Policies that declare `auto_fix: true` may include fixers. When `--fix` is
supplied, DevCovenant applies fixers in place and then reruns the checks.
Fixer logic lives under `devcovenant/core/fixers/`, and custom fixers can
live under `devcovenant/custom/fixers/`.

## Policy Registry and Stock Text
Policy definitions in `AGENTS.md` are hashed into
`devcovenant/registry.json`. When policy text changes, set `updated: true`,
update scripts and tests, then run:
```bash
devcovenant update-hashes
```

Stock policy wording is stored in `devcovenant/core/stock_policy_texts.yaml`.
Restore it with:
```bash
devcovenant restore-stock-text --policy <id>
```

## Policy Scripts and Fixers
Policy scripts resolve in this order:
1. `devcovenant/custom/policy_scripts/`
2. `devcovenant/core/policy_scripts/`

Custom scripts fully replace the built-in policy. Built-in fixers live under
`devcovenant/core/fixers`, custom fixers live under
`devcovenant/custom/fixers`, and core fixers are skipped whenever a custom
policy override exists.

## DevFlow Gates and Test Status
DevCovenant enforces the gate sequence for every change:
1. `python3 tools/run_pre_commit.py --phase start`
2. `python3 tools/run_tests.py`
3. `python3 tools/run_pre_commit.py --phase end`

The status file at `devcovenant/test_status.json` records timestamps and
commands. The `devflow-run-gates` policy reads it to enforce the workflow.

## Dependency and License Tracking
Runtime dependencies are recorded in `requirements.in`, pinned in
`requirements.lock`, and mirrored in `pyproject.toml`. When those files
change, update `THIRD_PARTY_LICENSES.md` and the license texts in `licenses/`.
The dependency-license-sync policy checks that the license report includes
all touched manifests under `## License Report`.

## Templates and Packaging
When installed from PyPI, DevCovenant copies templates from
`devcovenant/templates/`. The templates include docs, config defaults, tools,
and license text. When running from source, the installer falls back to the
repo files if templates are unavailable.

## Uninstall Behavior
Uninstall removes DevCovenant-managed blocks and, when requested, deletes
installed docs. Use:
```bash
devcovenant uninstall --target /path/to/repo

devcovenant uninstall --target /path/to/repo --remove-docs
```

## CI and Automation
The recommended CI workflow runs the same gate sequence used locally. Ensure
PyYAML and semver are installed so policy scripts and dependency checks run
cleanly. For tagged releases, run `python -m build` and `twine check dist/*`
before publishing.

## Troubleshooting
- Missing console script: use `python3 -m devcovenant`.
- Policy drift: run `devcovenant update-hashes`.
- Missing scripts: confirm the policy id matches the script filename.
- Unexpected violations: review policy metadata and custom overrides.
