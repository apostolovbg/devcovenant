# DevCovenant Reference
**Last Updated:** 2026-01-11
**Version:** 0.1.1

<!-- DEVCOV:BEGIN -->
This reference document is maintained by DevCovenant. Edit only outside the
managed blocks or update via the install script.
<!-- DEVCOV:END -->

This document explains DevCovenant's architecture, policy schema, and
installation lifecycle. `AGENTS.md` remains the canonical source of truth for
policy definitions.

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
- `devcovenant/cli.py` exposes `check`, `sync`, `test`, and `update-hashes`.

Policy scripts live in three folders:
- `devcovenant/core/policy_scripts/`: built-in policies shipped by
  DevCovenant.
- `devcovenant/core/fixers/`: built-in auto-fixers for common policies.
- `devcovenant/core/policy_scripts/`: compatibility shims for legacy policies.
- `devcovenant/custom/policy_scripts/`: repo-specific policies.
- `devcovenant/common_policy_patches/`: patch scripts for built-ins (Python
  preferred; JSON/YAML supported).

Script resolution order is custom → common → compatibility shim.
Option resolution order is config → patch → policy metadata → script defaults.

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
`python3 -m devcovenant.cli update-hashes`, then set it back to `false`.

Stock policy text is stored in `devcovenant/core/stock_policy_texts.json`.
Use `python3 -m devcovenant.cli restore-stock-text --policy <id>` to revert
edited stock text back to its canonical wording.

## Install, Update, Uninstall
DevCovenant installs the full tooling stack into a target repo, including the
common/custom/patch policy folders and workflow helpers.

Install (use `python3` if available):
```bash
python3 tools/install_devcovenant.py --target /path/to/repo
```

Update:
```bash
python3 tools/install_devcovenant.py --target /path/to/repo
```

Force overwrites when needed:
```bash
python3 tools/install_devcovenant.py --target /path/to/repo --force-docs
python3 tools/install_devcovenant.py --target /path/to/repo --force-config
```

CLI modes let you handle empty vs. existing repos explicitly:
```bash
python3 tools/install_devcovenant.py --target /path/to/repo --mode empty
python3 tools/install_devcovenant.py --target /path/to/repo --mode existing
```

Fine-grained control for existing repos:
```bash
python3 tools/install_devcovenant.py --target /path/to/repo \
  --docs-mode preserve --config-mode preserve --metadata-mode preserve
```

Uninstall:
```bash
python3 tools/uninstall_devcovenant.py --target /path/to/repo
```

Uninstall and remove installed docs:
```bash
python3 tools/uninstall_devcovenant.py --target /path/to/repo --remove-docs
```

The installer creates `.devcov/install_manifest.json` to track what was
installed and which docs were modified. If a target repo lacks a license file,
DevCovenant installs GPL-3.0 by default and will not overwrite an existing
license unless forced. When overwrite is requested, the installer renames the
existing file to `*_old.*` before writing a replacement.

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
1. `python3 tools/run_pre_commit.py --phase start`
2. `python3 tools/run_tests.py`
3. `python3 tools/run_pre_commit.py --phase end`

## Documentation Blocks
DevCovenant-managed blocks are wrapped as:
```
<!-- DEVCOV:BEGIN -->
... managed content ...
<!-- DEVCOV:END -->
```

Install and uninstall scripts insert and remove these blocks without touching
user-written content outside the markers.

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

## Roadmap
See `PLAN.md` for the staged roadmap toward a fully standalone distribution
and downstream migration plan.
