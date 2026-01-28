# DevCovenant Reference
**Last Updated:** 2026-01-12
**Version:** 0.2.5

<!-- DEVCOV:BEGIN -->
This reference document is maintained by DevCovenant. Edit only outside the
managed blocks or update via the install script.
<!-- DEVCOV:END -->

This document explains DevCovenant's architecture, policy schema, and the
install/update/uninstall lifecycle. `AGENTS.md` remains the canonical source
of truth for policy definitions.

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Policy Schema](#policy-schema)
4. [Policy Lifecycle](#policy-lifecycle)
5. [Install, Update, Uninstall](#install-update-uninstall)
6. [Workflow](#workflow)
7. [Documentation Blocks](#documentation-blocks)
8. [Repository Standards](#repository-standards)
9. [Roadmap](#roadmap)

## Overview
DevCovenant enforces the policies written in `AGENTS.md`. It prevents drift
between what a repo claims to enforce and what its tooling actually enforces.

## Architecture
Core components:
- `devcovenant/core/parser.py` reads policy blocks from `AGENTS.md`.
- `devcovenant/registry.json` stores hashes for policy text and scripts.
- `devcovenant/core/engine.py` orchestrates checks, fixes, and reporting.
- `devcovenant/cli.py` exposes `check`, `sync`, `test`, `update-hashes`,
  `restore-stock-text`, `install`, and `uninstall`.
- `devcovenant/core/install.py` and `devcovenant/core/uninstall.py` implement
  install/update/remove behavior.

Policy scripts live in three folders:
- `devcovenant/core/policy_scripts/`: built-in policies shipped by DevCovenant.
- `devcovenant/core/policy_scripts/fixers/`: built-in auto-fixers kept beside
  each policy they support.
- `devcovenant/core/fixers/`: compatibility wrappers for legacy imports.
- `devcovenant/custom/policy_scripts/`: repo-specific policies.
- `devcovenant/custom/fixers/`: repo-specific fixers (optional).
- `devcovenant/common_policy_patches/`: patch scripts for built-ins (Python
  preferred; JSON/YAML supported).

Script resolution order is custom → core. Option resolution order is
config → patch → policy metadata → script defaults.

Templates and installer assets live under `devcovenant/templates/` so packaged
installs have access to standard docs, config files, and helper scripts.

## Policy Schema
Each policy block includes:

### Standard fields
Standard fields apply to all policies:
- `id`, `status`, `severity`, `auto_fix`, `updated`, `applies_to`
- `enforcement`, `apply` (true/false policy activation)
- `include_prefixes`, `exclude_prefixes`, `include_globs`, `exclude_globs`
- `include_suffixes`, `exclude_suffixes`, `force_include_globs`
- `force_exclude_globs`, `notes`

### Policy-specific fields
Each policy can define its own keys (for example `version_file`,
`required_commands`, or `changelog_file`). Document these in the policy block
so contributors understand how to extend the system.

## Policy Lifecycle
Statuses communicate how a policy should be handled:
- `new`: needs script and tests.
- `active`: enforced.
- `fiducial`: enforced, plus always surfaces the policy text as a reminder.
- `updated`: policy text changed; update scripts/tests, then reset.
- `deprecated`: still defined but not enforced long term.
- `deleted`: no longer used.

When editing a policy block, set `updated: true`, run
`devcovenant update-hashes`, then set it back to `false`.

Stock policy text is stored in `devcovenant/core/stock_policy_texts.json`.
Use `devcovenant restore-stock-text --policy <id>` to revert edited text back
to its canonical wording.

## Install, Update, Uninstall
DevCovenant installs the full tooling stack into a target repo, including the
common/custom/patch policy folders and workflow helpers.

Install (use `python3` if `devcovenant` is not on your PATH):
```bash
devcovenant install --target /path/to/repo
python3 -m devcovenant install --target /path/to/repo
```

Update (same command; defaults preserve docs/config in existing repos):
```bash
devcovenant install --target /path/to/repo
```

Force overwrites when needed:
```bash
devcovenant install --target /path/to/repo --force-docs

devcovenant install --target /path/to/repo --force-config
```

CLI modes let you handle empty vs. existing repos explicitly:
```bash
devcovenant install --target /path/to/repo --install-mode empty

devcovenant install --target /path/to/repo --install-mode existing
```

Fine-grained control for existing repos:
```bash
devcovenant install --target /path/to/repo \
  --docs-mode preserve --config-mode preserve --metadata-mode preserve
```

Uninstall:
```bash
devcovenant uninstall --target /path/to/repo
```

Uninstall and remove installed docs:
```bash
devcovenant uninstall --target /path/to/repo --remove-docs
```

The `tools/install_devcovenant.py` and `tools/uninstall_devcovenant.py` files
are compatibility wrappers that simply forward arguments to the CLI.

The installer creates `.devcov/install_manifest.json` to track what was
installed and which docs were modified. If a target repo lacks a license file,
DevCovenant installs a GPL-3.0 license by default and will not overwrite an
existing license unless forced. When overwrite is requested, the installer
renames the existing file to `*_old.*` before writing a replacement.

Install behavior highlights:
- `README.md` keeps existing content but gets a standard header plus a managed
  block (Table of Contents, Overview, Workflow, DevCovenant) when missing.
- `DEVCOVENANT.md` is always backed up to `*_old.*` and replaced by the
  template to keep the reference text canonical.
- `SPEC.md` and `PLAN.md` keep existing content but receive updated headers; if
  missing, minimal templates are created.
- `CHANGELOG.md` and `CONTRIBUTING.md` are backed up (`*_old.*`) and replaced
  with standard DevCovenant templates (including logging examples).
- If `VERSION` is missing, the installer prompts for a version (`x.x` or
  `x.x.x`, normalized to `x.x.0`). All standard docs get that version header.
- If `CITATION.cff` is missing, the installer prompts to create it; skipping
  disables citation enforcement in `AGENTS.md`.
- `.gitignore` is regenerated from a universal template and merges existing
  user entries under a preserved section.
- `Last Updated` headers are stamped with the UTC install date.
- `--version` and `--citation-mode` pre-seed metadata and avoid prompts.

DevCovenant core lives under `devcovenant/core`, plus the wrapper entrypoints
and install tools listed in `devcov_core_paths`. The installer sets
`devcov_core_include: false` in user repos so core files are excluded from
policy enforcement and remain update-safe. Only the DevCovenant repo should
enable core inclusion.

## Workflow
Adoption guidance:
- Install DevCovenant on a fresh branch.
- Clear error-level violations first.
- After errors are cleared, ask the repo owner how to handle warnings and info.

DevCovenant expects this gate sequence in enforced repos:
1. `python3 devcovenant/core/run_pre_commit.py --phase start`
2. `python3 devcovenant/core/run_tests.py`
3. `python3 devcovenant/core/run_pre_commit.py --phase end`

At session start, run `python3 devcov_check.py check --mode startup` or
`devcovenant check --mode startup` to detect policy drift early.

## Documentation Blocks
DevCovenant-managed blocks are wrapped as:
```
<!-- DEVCOV:BEGIN -->
... managed content ...
<!-- DEVCOV:END -->
```

Install, update, and uninstall scripts insert or remove these regions so the
surrounding human-authored content stays untouched. Policy reminders such as
`documentation-growth-tracking`, `policy-text-presence`, and
`last-updated-placement` direct contributors back to these markers whenever
managed docs must grow or a policy’s prose drifts.
- Wrap new policy guidance in a fresh block and add the standard
  `Last Updated / Version` header so validators such as
  `last-updated-placement` can find the timestamp.

## Repository Standards
- `AGENTS.md` is the single source of truth for policies.
- Versions and last-updated headers must stay synchronized.
- Code and documentation adhere to a 79-character line limit unless explicitly
  overridden in a policy.
- Documentation growth tracking treats user-facing files as any code or config
  that affects user interactions, API surfaces, integrations, or workflow
  behavior. When those files change, update the doc set and explicitly mention
  the impacted components by name.
- `devcovenant/config.yaml` may declare language profiles to extend file
  suffix coverage for multi-language projects.
- Dependency manifests (`requirements.in`, `requirements.lock`,
  `pyproject.toml`) must remain aligned with `THIRD_PARTY_LICENSES.md` and the
  `licenses/` directory whenever dependencies change.

## Roadmap
See `PLAN.md` for the staged roadmap and migration sequencing.
