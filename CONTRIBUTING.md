# Contributing
**Last Updated:** 2026-01-11
**Version:** 0.1.1

Before contributing:
1. Read `AGENTS.md` first. It is the canonical source of truth.
2. Read `DEVCOVENANT.md` for system architecture and policy schema.
3. Review `PLAN.md` for current priorities.

## Workflow
- Start with `python tools/run_pre_commit.py --phase start`.
- Make scoped changes and update docs/changelog as needed.
- Run `python tools/run_tests.py`.
- Finish with `python tools/run_pre_commit.py --phase end`.

## Policy changes
- When editing policy blocks, set `updated: true` and run
  `python devcovenant/update_hashes.py` before committing.
- Keep policy-specific fields documented in the policy definition.
