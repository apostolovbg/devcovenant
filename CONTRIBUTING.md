# Contributing
**Last Updated:** 2026-01-12
**Version:** 0.2.4

<!-- DEVCOV:BEGIN -->
**Read first:** `AGENTS.md` is canonical. `DEVCOVENANT.md` explains the
architecture and install/update/uninstall lifecycle.
<!-- DEVCOV:END -->

DevCovenant is self-enforcing. Every change must respect the policy workflow
and keep documentation synchronized with behavior.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Editing Policies](#editing-policies)
4. [Adding Policies](#adding-policies)
5. [Documentation Standards](#documentation-standards)
6. [Install/Uninstall Changes](#installuninstall-changes)
7. [Changelog](#changelog)

## Overview
Before contributing:
1. Read `AGENTS.md` for policy definitions.
2. Read `DEVCOVENANT.md` for architecture and schema.
3. Check `PLAN.md` for current priorities and sequencing.

## Workflow
Run the standard gates in order:
```bash
python3 tools/run_pre_commit.py --phase start
python3 tools/run_tests.py
python3 tools/run_pre_commit.py --phase end
```

## Editing Policies
When changing policy blocks in `AGENTS.md`:
1. Set `updated: true` in the policy block.
2. Update the policy script and its tests.
3. Run `python3 -m devcovenant.cli update-hashes`.
4. Reset `updated: false`.

## Adding Policies
- Built-in policies live in `devcovenant/core/policy_scripts/`.
- Built-in fixers live in `devcovenant/core/fixers/`.
- Repo-specific policies live in `devcovenant/custom/policy_scripts/`.
- Add tests under `devcovenant/core/tests/test_policies/`.

## Documentation Standards
- Update last-updated headers when editing docs.
- Keep line lengths at 79 characters unless a policy says otherwise.
- Maintain the DevCovenant-managed blocks in docs.

## Install/Uninstall Changes
If you change install or uninstall behavior:
- Update `DEVCOVENANT.md` and `devcovenant/README.md`.
- Keep the install manifest logic intact.
- Ensure uninstall removes managed blocks cleanly.

## Changelog
List every touched file under the current version entry in `CHANGELOG.md`.
Use ISO dates and keep entries newest-first.
