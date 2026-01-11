# Custom Policy Scripts
**Last Updated:** 2026-01-11
**Version:** 0.2.0

Place repo-specific policy scripts here. If a policy id matches a built-in
policy, the custom version takes precedence.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Naming Rules](#naming-rules)
4. [Testing Expectations](#testing-expectations)

## Overview
Custom policies are the extension point for rules that only apply to a single
repo or organization. Keep them minimal and document their metadata inside the
`AGENTS.md` policy block.

## Workflow
1. Create the policy block in `AGENTS.md`.
2. Implement the policy in this folder.
3. Add tests under `devcovenant/core/tests/test_policies/`.
4. Run `python3 -m devcovenant.cli update-hashes`.

## Naming Rules
Policy scripts are named after the policy id, using snake case. For example,
`my-custom-policy` becomes `my_custom_policy.py`.

## Testing Expectations
Every custom policy should have a test that exercises at least one passing and
one failing case. This keeps policy behavior predictable as the repo evolves.
