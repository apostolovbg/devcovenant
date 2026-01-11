# DevCovenant (Repository Guide)
**Last Updated:** 2026-01-11
**Version:** 0.1.1
**DevCovenant Version:** 0.1.1
**Status:** Active Development
**License:** DevCovenant License v1.0

This file is installed into a target repository at `devcovenant/README.md`.
It explains how to use DevCovenant inside that repo. The root `README.md`
should remain dedicated to the repository's actual project.

## Table of Contents
1. [What DevCovenant Does](#what-devcovenant-does)
2. [Quick Start](#quick-start)
3. [Where Policies Live](#where-policies-live)
4. [Policy Script Layout](#policy-script-layout)
5. [Running Checks](#running-checks)
6. [Adding or Updating Policies](#adding-or-updating-policies)
7. [Patching Built-In Policies](#patching-built-in-policies)
8. [CI and Automation](#ci-and-automation)
9. [Troubleshooting](#troubleshooting)
10. [Uninstall](#uninstall)

## What DevCovenant Does
DevCovenant enforces the policies written in `AGENTS.md`. It reads those
policies, validates them against their scripts, and reports actionable
violations. The result is a single source of truth that prevents policy drift.

## Quick Start
If DevCovenant is installed, start with:
```bash
python tools/run_pre_commit.py --phase start
python tools/run_tests.py
python tools/run_pre_commit.py --phase end
```

You can also run the engine directly:
```bash
python -m devcovenant.cli check
python -m devcovenant.cli check --mode pre-commit
python -m devcovenant.cli check --fix
```

## Where Policies Live
`AGENTS.md` is the canonical policy document. Every policy is defined there in
plain language plus a `policy-def` metadata block. DevCovenant parses those
blocks and enforces them.

## Policy Script Layout
DevCovenant installs the full engine and scripts inside the repo:
- `devcovenant/common_policy_scripts/`: built-in checks shipped with
  DevCovenant.
- `devcovenant/custom_policy_scripts/`: repo-specific checks.
- `devcovenant/common_policy_patches/`: YAML overrides for built-ins.

Policy resolution order:
1. Custom script with matching policy id.
2. Built-in script with matching policy id.
3. Compatibility shim (legacy `policy_scripts/`).

Option resolution order:
1. Config overrides in `devcovenant/config.yaml`.
2. Patch overrides in `common_policy_patches/<policy_id>.yml`.
3. Metadata values from the `policy-def` block.
4. Script defaults.

## Running Checks
Common commands:
```bash
python -m devcovenant.cli check
python -m devcovenant.cli check --mode lint
python -m devcovenant.cli check --mode pre-commit
python -m devcovenant.cli update-hashes
```

DevCovenant returns a non-zero exit code when blocking violations exist.
Use `--fix` to apply auto-fixes when available.

## Adding or Updating Policies
1. Add or edit the policy block in `AGENTS.md`.
2. Create or update the matching script:
   - Built-in? Update `common_policy_scripts/`.
   - Repo-specific? Use `custom_policy_scripts/`.
3. Update or add tests under `devcovenant/tests/`.
4. Set `updated: true` in the policy block.
5. Run `python -m devcovenant.cli update-hashes`.
6. Reset `updated: false` and run the workflow gates.

## Patching Built-In Policies
Create a YAML file named after the policy id:
```
common_policy_patches/<policy_id>.yml
```

Example:
```yaml
max_length: 100
include_prefixes: src
```

Patches let you override built-in defaults without editing the core script.

## CI and Automation
CI should run:
- `python tools/run_pre_commit.py --phase start`
- `python tools/run_tests.py`
- `python tools/run_pre_commit.py --phase end`

The pre-commit hook uses the same engine and policy set.

## Troubleshooting
- Policy drift: run `python -m devcovenant.cli update-hashes`.
- Unexpected violations: confirm metadata in `AGENTS.md` and patches.
- Script not found: confirm policy id matches the script filename.

## Uninstall
Run the uninstall script from the DevCovenant source repo:
```bash
python tools/uninstall_devcovenant.py --target /path/to/repo
```

Use `--remove-docs` to delete docs that were installed by DevCovenant.
