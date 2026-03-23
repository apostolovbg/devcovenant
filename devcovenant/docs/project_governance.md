# Project Governance
**Last Updated:** 2026-03-23
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
`project_name`: any non-empty string. Default seed value: `Project Name`.

`project_description`: any non-empty string. Default seed value is the install
template prompt text that asks you to describe what the project ships.

`stage`: one value from `allowed_stages`. The default allowed set is
`prototype`, `alpha`, `beta`, `stable`, `mature`, `deprecated`, `archived`.

`development_stance`: one value from `allowed_development_stances`. The
default allowed set is `experimental`, `active-development`, `maintenance`,
`release-managed`, `frozen`, `sunset`.

`versioning_mode`: `versioned` or `unversioned`.

`codename`: optional free-form string.

`build_identity`: optional free-form string.

`unversioned_label`: any non-empty string used as the displayed project
version in unversioned mode. Default: `Unversioned`.

`unreleased_heading`: any non-empty string used as the required top visible
changelog heading in unversioned mode. Default: `## Unreleased`.

`changelog_file`: any non-empty repo-relative path string. Default:
`CHANGELOG.md`.

`allowed_stages`: non-empty list of allowed stage tokens. Repositories may
tighten or rename this list, but `stage` must always be one of its entries.

`allowed_development_stances`: non-empty list of allowed stance tokens.
Repositories may tighten or rename this list, but `development_stance` must
always be one of its entries.

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
