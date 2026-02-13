# Contributing
**Last Updated:** 2026-02-13
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** CONTRIBUTING
**Doc Type:** contributing-guide
**Managed By:** DevCovenant

**Read first:** `AGENTS.md` is canonical. See `devcovenant/README.md`
for lifecycle guidance and workflow details.
<!-- DEVCOV:END -->

This file is intentionally brief. Use it as the entry point, then follow the
full guidance in `devcovenant/README.md` and the policy definitions in
`AGENTS.md`.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)

## Overview
- Read `AGENTS.md` for policy definitions and required workflow.
- Read `devcovenant/README.md` for architecture, schema, and lifecycle
  rules.
- Check `PLAN.md` for current priorities.
This guide stays short by design. It exists to point you to the canonical
rules and to remind you that DevCovenant enforcement applies to every
change, including documentation-only updates.

## Workflow
Follow the canonical gate sequence (details in `devcovenant/README.md`):
```bash
python3 -m devcovenant gate --start
python3 -m devcovenant test
python3 -m devcovenant gate --end
```
If the console script is not on your PATH, use `python3 -m devcovenant`
instead of `devcovenant` for CLI commands.
If the gate sequence fails, fix the violations and rerun the full sequence
before submitting changes.
