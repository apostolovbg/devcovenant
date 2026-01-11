# Contributing
**Last Updated:** 2026-01-11
**Version:** 0.1.1

<!-- DEVCOVENANT:BEGIN -->
**Read first:** `AGENTS.md` is canonical. `DEVCOVENANT.md` explains the
architecture and install/update/uninstall lifecycle.
<!-- DEVCOVENANT:END -->

DevCovenant is self-enforcing. Every change must respect the policy workflow
and keep documentation synchronized with behavior.

## Before You Start
1. Read `AGENTS.md` for policy definitions.
2. Read `DEVCOVENANT.md` for architecture and schema.
3. Check `PLAN.md` for current priorities and sequencing.

## Required Workflow
Run the standard gates in order:
```bash
python tools/run_pre_commit.py --phase start
python tools/run_tests.py
python tools/run_pre_commit.py --phase end
```

## Editing Policies
When changing policy blocks in `AGENTS.md`:
1. Set `updated: true` in the policy block.
2. Update the policy script and its tests.
3. Run `python -m devcovenant.cli update-hashes`.
4. Reset `updated: false`.

## Adding Policies
- Built-in policies live in `devcovenant/common_policy_scripts/`.
- Repo-specific policies live in `devcovenant/custom_policy_scripts/`.
- Add tests under `devcovenant/tests/test_policies/`.

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
