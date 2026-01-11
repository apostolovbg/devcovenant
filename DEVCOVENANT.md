# DevCovenant Reference
**Last Updated:** 2026-01-11
**Version:** 0.1.1

<!-- DEVCOVENANT:BEGIN -->
This reference document is maintained by DevCovenant. Edit only outside the
managed blocks or update via the install script.
<!-- DEVCOVENANT:END -->

This document explains DevCovenant's architecture, policy schema, and
installation lifecycle. `AGENTS.md` remains the canonical source of truth for
policy definitions.

## 1. Purpose
DevCovenant enforces the policies written in `AGENTS.md`. It prevents drift
between what a repo claims to enforce and what its tooling actually enforces.

## 2. Architecture Overview
Core components:
- `devcovenant/parser.py` reads policy blocks from `AGENTS.md`.
- `devcovenant/registry.json` stores hashes for policy text and scripts.
- `devcovenant/engine.py` orchestrates checks, fixes, and reporting.
- `devcovenant/cli.py` exposes `check`, `sync`, `test`, and `update-hashes`.

Policy scripts live in three folders:
- `devcovenant/common_policy_scripts/`: built-in policies shipped by
  DevCovenant.
- `devcovenant/custom_policy_scripts/`: repo-specific policies.
- `devcovenant/common_policy_patches/`: YAML overrides for built-in defaults.

Script resolution order is custom → common → compatibility shim.
Option resolution order is config → patch → policy metadata → script defaults.

## 3. Policy Schema
Each policy block includes:

### 3.1 Standard fields
Standard fields apply to all policies:
- `id`, `status`, `severity`, `auto_fix`, `updated`, `applies_to`
- `enforcement`, `waiver` (legacy), `apply` (planned replacement)
- `include_prefixes`, `exclude_prefixes`, `include_globs`, `exclude_globs`
- `include_suffixes`, `exclude_suffixes`, `force_include_globs`
- `force_exclude_globs`, `notes`

### 3.2 Policy-specific fields
Each policy can define its own keys (for example `version_file`,
`required_commands`, or `changelog_file`). Document these in the policy block
so contributors understand how to extend the system.

## 4. Policy Lifecycle
Statuses communicate how a policy should be handled:
- `new`: needs script and tests.
- `active`: enforced.
- `updated`: policy text changed; update scripts/tests, then reset.
- `deprecated`: still defined but not enforced long term.
- `deleted`: no longer used.

When editing a policy block, set `updated: true`, run
`python -m devcovenant.cli update-hashes`, then set it back to `false`.

## 5. Install, Update, Uninstall
DevCovenant is installed into a target repo by copying the full tooling
(including common/custom/patch scripts) plus workflow helpers and metadata.

Install:
```bash
python tools/install_devcovenant.py --target /path/to/repo
```

Update:
```bash
python tools/install_devcovenant.py --target /path/to/repo
```

Force overwrites when needed:
```bash
python tools/install_devcovenant.py --target /path/to/repo --force-docs
python tools/install_devcovenant.py --target /path/to/repo --force-config
```

Uninstall:
```bash
python tools/uninstall_devcovenant.py --target /path/to/repo
```

Uninstall and remove installed docs:
```bash
python tools/uninstall_devcovenant.py --target /path/to/repo --remove-docs
```

The installer creates `.devcovenant/install_manifest.json` to track what was
installed and which docs were modified.

## 6. Documentation Blocks
DevCovenant-managed blocks are wrapped as:
```
<!-- DEVCOVENANT:BEGIN -->
... managed content ...
<!-- DEVCOVENANT:END -->
```

Install and uninstall scripts insert and remove these blocks without touching
user-written content outside the markers.

## 7. Self-Enforcement (Dogfooding)
This repo enforces itself through DevCovenant. Required workflow:
1. `python tools/run_pre_commit.py --phase start`
2. `python tools/run_tests.py`
3. `python tools/run_pre_commit.py --phase end`

## 8. Repository Standards
- `AGENTS.md` is the single source of truth for policies.
- Versions and last-updated headers must stay synchronized.
- Code and documentation adhere to a 79-character line limit unless
  explicitly overridden in a policy.

## 9. Roadmap
See `PLAN.md` for the staged roadmap toward a fully standalone distribution
and downstream migration plan.
