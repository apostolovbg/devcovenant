# Contributing
**Last Updated:** 2026-02-27
**Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
**Doc ID:** CONTRIBUTING
**Doc Type:** contributing-guide
**Managed By:** DevCovenant

**Read first:** `AGENTS.md` is canonical. See `devcovenant/README.md`
for lifecycle guidance and workflow details.
<!-- DEVCOV:END -->

Use this file as a fast entry point, then follow `AGENTS.md`, `PLAN.md`,
`devcovenant/README.md`, and `devcovenant/docs/architecture.md`.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)

## Overview
- `AGENTS.md`: policy source and workflow contract.
- `devcovenant/docs/architecture.md`: stable runtime contracts.
- `PLAN.md`: active backlog and done/not-done state.
- `devcovenant/README.md`: command and lifecycle usage guide.
- `SPEC.md`: optional specification layer usage guide.

## Workflow
Always use the gate sequence for repository edits:

```bash
devcovenant gate --start
# pre-test mutating preflight; rerun until clean
devcovenant gate --mid
devcovenant test
devcovenant gate --end
```

If a gate fails, fix the issue and rerun the full sequence.
Stage completed changes before handoff.
