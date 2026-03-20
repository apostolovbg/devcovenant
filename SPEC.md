# DevCovenant Specification
**Doc ID:** SPEC
**Doc Type:** specification
**Project Version:** 1.0.0
**Project Stage:** stable
**Development Stance:** active-development
**Versioning Mode:** versioned
**Last Updated:** 2026-03-20
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `SPEC.md` only for durable repository contracts below this block.
<!-- DEVCOV:END -->

This is a generic SPEC guide template.

Use `SPEC.md` only when your repository needs a durable specification layer.
If your repo does not need one, keep this file brief and route details to
your operational documentation.

## Table of Contents
1. [Overview](#overview)
2. [When To Use SPEC](#when-to-use-spec)
3. [Workflow](#workflow)
4. [Ownership Boundaries](#ownership-boundaries)
5. [Recommended Structure](#recommended-structure)
6. [Maintenance Rules](#maintenance-rules)
7. [Pointers](#pointers)

## Overview
`SPEC.md` is for durable repository-level contracts only.
Do not use it as a backlog, scratchpad, or temporary planning area.

## When To Use SPEC
- Use SPEC when your repo needs a stable internal contract document.
- Skip SPEC if AGENTS and operational docs already cover your needs.
- Keep it small, explicit, and implementation-facing.

## Workflow
- Follow your repo's required gate workflow before and after edits.
- Update SPEC only when durable contracts actually change.
- Update operational docs in the same work slice when behavior changes.

## Ownership Boundaries
- `AGENTS.md`: workflow law, policy source, and temporary editable notes.
- `PLAN.md`: active work backlog.
- `docs/*`: operational and user-facing behavior guides.
- `SPEC.md`: optional stable contract layer for this repository only.

## Recommended Structure
- Overview: what this repo treats as invariant.
- Functional requirements: stable behavior contracts.
- Non-functional requirements: quality, determinism, security baselines.
- Pointers: links to detailed operational docs.

If your repo needs architecture invariants, keep them in a dedicated
architecture doc and keep SPEC at the meta-contract level.

## Maintenance Rules
- Prefer one-way pointers from SPEC to docs.
- Do not make docs depend on SPEC to be understandable.
- Keep SPEC synchronized with runtime reality.
- Remove stale sections instead of keeping historical leftovers.
- If your repo stops using SPEC, keep this file as a short usage note only.

## Pointers
Add pointers to the docs that hold your runtime and operational contracts.
