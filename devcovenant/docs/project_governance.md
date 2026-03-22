# Project Governance
**Last Updated:** 2026-03-22
**Project Version:** 1.0.0

## Overview
This document is the normative home for the `project-governance` contract.
Use it together with `devcovenant/docs/contracts.md` when you need the
stable meaning of repository identity and lifecycle metadata.

`project-governance` is where a repository states what it is called, how mature
it is, and how DevCovenant should label its public governance surfaces.
It is not a packaging afterthought and it is not derived from `pyproject.toml`.
Other public surfaces render from this metadata.

## Core Fields
The contract includes:

- `project_name`

- `project_description`

- `stage`

- `development_stance`

- `versioning_mode`

- optional `codename`

- optional `build_identity`

- `unversioned_label`

- `unreleased_heading`

- `changelog_file`

## What It Controls
Project-governance metadata feeds several visible surfaces:

- managed README identity

- generated governance headers in managed docs that opt into those headers

- tracked registry state

- changelog and release-heading behavior

- package metadata surfaces that are synchronized from repository identity

## Working Rule
If the repository identity, maturity, or versioning stance changes, update
`project-governance` first and then let the governed outputs regenerate.
That keeps the repo's public identity sourced from one place instead of being
duplicated across unrelated files.
