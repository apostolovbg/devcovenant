# DevCovenant
**Last Updated:** 2026-01-11
**Version:** 0.1.1

DevCovenant is a self-enforcing policy system that keeps human-readable
standards and automated checks in lockstep. It is designed to prevent
repository drift while staying simple enough to run in any repo.

Start here:
1. Read `AGENTS.md` first. It is the canonical source of truth.
2. Read `DEVCOVENANT.md` for architecture, policy schema, and lifecycle.
3. Read `CONTRIBUTING.md` for workflow and guardrails.

This repo dogfoods DevCovenant to keep itself consistent and stable.

## Quick facts
- Policies are defined in `AGENTS.md` and synchronized into
  `devcovenant/registry.json`.
- The CLI lives in `devcovenant/cli.py`.
- `tools/run_pre_commit.py` and `tools/run_tests.py` enforce the cadence.

## License
This project is released under the DevCovenant License v1.0. Redistribution
is prohibited without explicit written permission.
