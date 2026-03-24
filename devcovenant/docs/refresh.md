# Refresh Behavior
**Last Updated:** 2026-03-23
**Project Version:** 1.0.0

## Overview
This document is the normative home for the managed-documents contract.
Use it together with `devcovenant/docs/contracts.md` when you need the stable
rules for regeneration, preservation, adoption, and descriptor ownership.

`refresh` is the deterministic regeneration boundary for DevCovenant's tracked
outputs.
It updates the governed files that DevCovenant owns, but it does not invent
fake live session state.

## What Refresh Owns
Refresh can regenerate:

- tracked registry state

- generated config sections

- managed policy output in `AGENTS.md`

- generated workflow and tooling files

- managed docs selected through `doc_assets`

- generated `.gitignore` and pre-commit files

If profiles, descriptors, or managed templates changed, refresh is the point
where those changes become real in the repository.

## When Refresh Runs
A full refresh runs in:

- `devcovenant refresh`

- `devcovenant deploy`

- `devcovenant upgrade`

- gate-owned refresh/autofix paths during the governed workflow

`check` is read-only and does not run startup refresh.

## Managed Docs
Managed docs are descriptor-driven.
The managed-doc runtime owns:

- descriptor loading

- descriptor validation

- header rendering

- managed block rendering

- adoption of compatible seeded docs

- replacement of known old generic scaffolds

That keeps document behavior centralized instead of spreading it across many
commands.

## Preservation Rules
The practical preservation rules are:

- missing doc: may be created

- empty doc: may be replaced

- one-line doc: may be replaced

- otherwise: only managed headers and managed blocks should change

That rule is what allows DevCovenant to manage docs without treating ordinary
human-written prose as disposable.

## Managed Doc Descriptor Schema
A managed-doc descriptor defines the target path, identity headers, managed
block content, and body template.
Some docs can also opt into project-governance header rendering.

The descriptor is the source of structure.
The live file is the source of preserved authored content outside the managed
areas.

Some descriptors intentionally keep the managed block empty.
That is the rule for `README.md` and `devcovenant/README.md` in this
repository: the `<!-- DEVCOV:BEGIN -->` / `<!-- DEVCOV:END -->` block stays
present but empty by design so DevCovenant does not inject runtime prose at
the top of user-facing README surfaces.

## Custom Managed Docs
Profiles can add custom managed docs through their asset trees.
That is how repo-specific docs such as API, auth, or error contracts can be
introduced without hardcoding those docs into the global baseline.

## Validation And Failure Modes
Refresh should fail explicitly when a managed-doc descriptor is invalid.
It should not guess what a broken descriptor meant.

The common failure classes are:

- missing descriptor for an enabled managed doc

- invalid descriptor shape

- broken target/template mapping

- conflicting managed-doc ownership

## Practical Rule
If a refresh-related change seems confusing, ask two questions first:

1. which descriptor owns this output?
2. is the file supposed to be preserved, regenerated, or adopted?

Most refresh confusion becomes much easier once those two ownership questions
are answered.
