# Contributing
**Doc ID:** CONTRIBUTING
**Doc Type:** contributing-guide
**Project Version:** 1.0.0
**Last Updated:** 2026-03-15
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
It defines the standard contributor workflow used by
DevCovenant-managed repositories. Add repository-specific contributor
notes below the managed section.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Repository Notes](#repository-notes)

## Overview
This repository is managed by DevCovenant.
`AGENTS.md` is the canonical source for repository workflow and policy
rules.
`devcovenant/README.md` explains the DevCovenant commands, lifecycle,
configuration schema, and evidence artifacts used in this repository.
Check `PLAN.md` for active implementation work when the repository uses
a plan.

## Workflow
Follow the canonical gate sequence for every repository change,
including documentation-only edits:

```bash
python3 -m devcovenant gate --start
# pre-test mutating preflight (may need reruns until clean)
python3 -m devcovenant gate --mid
python3 -m devcovenant test
python3 -m devcovenant gate --end
```

If the console script is not on your PATH, use
`python3 -m devcovenant` instead of `devcovenant` for CLI commands.
If the gate sequence fails, clear violations and rerun the required
commands until the repository is clean.
If managed-environment is enabled and the resolved interpreter is not
directly executable, DevCovenant emits an explicit error and stops so the
managed interpreter path or permissions can be fixed directly.
<!-- DEVCOV:END -->

## Repository Notes

Add repository-specific contributor notes here. This section is preserved
across DevCovenant upgrade and refresh runs.
