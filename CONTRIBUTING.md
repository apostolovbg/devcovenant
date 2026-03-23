# Contributing
**Doc ID:** CONTRIBUTING
**Doc Type:** contributing-guide
**Project Version:** 1.0.0
**Last Updated:** 2026-03-23
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
It defines the standard contributor workflow used by
DevCovenant-managed repositories. Add repository-specific contributor
notes below the managed section.
<!-- DEVCOV:END -->

## Overview
This repository is managed by DevCovenant.
Read [README.md](README.md) first for the operator-facing product overview and
read [AGENTS.md](AGENTS.md) for the enforced workflow law that governs every
work slice in this repo.

This guide is the shorter contributor checkpoint.
Use it when you need a quick reminder of how work is expected to land, which
commands must run, and which generated surfaces should never be edited by hand.

## Before You Change Files
Make sure you understand:

- the active workflow law in `AGENTS.md`

- the current plan in `PLAN.md` when the repo is in an active roadmap slice

- the current project requirements in `SPEC.md` when the repo uses a spec

- whether the repository expects the managed environment to be active first

## Workflow
Follow the canonical gate sequence for every repository change, including
code-only and documentation-only edits:

```bash
python3 -m devcovenant gate --start
python3 -m devcovenant gate --mid
python3 -m devcovenant test
python3 -m devcovenant gate --end
```

If the console script is available on PATH, use `devcovenant ...` instead of
`python3 -m devcovenant ...`.

## Changelog And Documentation
Update `CHANGELOG.md` in the same session when repository rules require it.
Update the relevant docs in the same slice when behavior, workflow,
configuration, or other user-facing surfaces changed.

## Managed Files
Never edit content inside managed `<!-- DEVCOV* -->` blocks by hand.
Change the owning inputs and let refresh or the gate workflow regenerate the
managed output.

## Repository Notes
Add repository-specific contributor notes here. This section is preserved
across DevCovenant refresh and upgrade runs.
