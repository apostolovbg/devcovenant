# Project Governance
**Last Updated:** 2026-03-20
**Project Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [What It Governs](#what-it-governs)
- [Configuration Contract](#configuration-contract)
- [Rendering Surfaces](#rendering-surfaces)
- [Relationship to Version Governance](#relationship-to-version-governance)
- [Defaults and Examples](#defaults-and-examples)
- [Workflow](#workflow)

## Overview
`project-governance` is the repository-owned lifecycle metadata service for a
DevCovenant-managed repository.

It is not an AGENTS policy-block entry.
It is configured directly in `devcovenant/config.yaml`, resolved by
`devcovenant/core/services/project_governance.py`, and then surfaced into the
generated runtime and documentation outputs that need that state.

Its job is to answer questions like:
- what lifecycle stage is this project in?
- what is the current development stance?
- is this repository intentionally unversioned or actively versioned?
- should managed docs show a real version token or an explicit unversioned
  label?
- should the changelog use `## Version ...` or `## Unreleased`?

## What It Governs
`project-governance` owns lifecycle metadata, not version-rule enforcement.

Primary fields:
- `stage`
- `development_stance`
- `versioning_mode`
- `codename`
- `build_identity`
- `unversioned_label`
- `unreleased_heading`
- `changelog_file`

Validation behavior:
- `stage` must be in the allowed stage list
- `development_stance` must be in the allowed stance list
- `versioning_mode` must be either `versioned` or `unversioned`
- versioned repos must still provide a real declared project version when
  managed docs need to render one
- intentionally unversioned repos must keep the top changelog release heading
  aligned with the configured unreleased heading

## Configuration Contract
The source of truth lives at the top level of `devcovenant/config.yaml`:

```yaml
project-governance:
  stage: stable
  development_stance: active-development
  versioning_mode: versioned
  codename: ""
  build_identity: ""
  unversioned_label: Unversioned
  unreleased_heading: "## Unreleased"
  changelog_file: CHANGELOG.md
```

Fresh generic installs currently default to an intentionally unversioned
baseline:

```yaml
project-governance:
  stage: prototype
  development_stance: experimental
  versioning_mode: unversioned
  unversioned_label: Unversioned
  unreleased_heading: "## Unreleased"
```

That means a new repo can be governed immediately without inventing a fake
numbered release.

## Rendering Surfaces
The resolved project-governance state is intentionally visible.

Tracked/config/runtime surfaces:
- `devcovenant/config.yaml`:
  the human-owned source of truth
- `devcovenant/registry/registry.yaml`:
  the resolved tracked record of project-governance state

Managed document surfaces:
- `AGENTS.md`:
  header lines plus a dedicated `Project Governance` section after the
  workflow block and before the generated policy block
- `SPEC.md`:
  project-governance header lines
- `PLAN.md`:
  project-governance header lines
- `CHANGELOG.md`:
  project-governance header lines

Rendered values:
- `Project Version` comes from the resolved governance state
- `Project Stage`, `Development Stance`, and `Versioning Mode` are rendered
  in opted-in docs
- optional `Project Codename` and `Build Identity` appear only when configured

Changelog behavior:
- `versioned` mode keeps `## Version ...`
- `unversioned` mode requires the configured unreleased heading, typically
  `## Unreleased`

## Relationship to Version Governance
`project-governance` and `version-governance` are intentionally orthogonal.

`project-governance` answers:
- what stage is the project in?
- what stance is it operating under?
- should docs/changelog behave as versioned or unversioned?

`version-governance` answers:
- what version scheme does this repo use?
- is the current version token valid for that scheme?
- did progression/bump rules pass?

Examples:
- a stable versioned repo can use:
  - `project-governance.versioning_mode: versioned`
  - `version-governance.scheme: semver`
- an intentionally unversioned prototype can use:
  - `project-governance.versioning_mode: unversioned`
  - `version-governance: false`
- a versioned repo can still be `experimental`, `maintenance`, or any other
  allowed stance

## Defaults and Examples
Versioned example:

```yaml
project-governance:
  stage: stable
  development_stance: active-development
  versioning_mode: versioned
  codename: helios
```

Unversioned example:

```yaml
project-governance:
  stage: prototype
  development_stance: experimental
  versioning_mode: unversioned
  unversioned_label: Unversioned
  unreleased_heading: "## Unreleased"
```

Surface effect of the unversioned example:
- managed docs render `Project Version: Unversioned`
- `AGENTS.md` still shows stage/stance/mode explicitly
- the changelog must start its live release section with `## Unreleased`

## Workflow
When you change project-governance metadata:
1. edit `devcovenant/config.yaml`
2. run the normal gate workflow
3. let refresh regenerate managed doc headers and tracked registry state
4. verify `AGENTS.md`, `SPEC.md`, `PLAN.md`, `CHANGELOG.md`, and
   `devcovenant/registry/registry.yaml` reflect the new resolved state

Operational rule:
- treat `project-governance` as human-owned repo metadata
- do not treat it like a policy toggle in `policy_state`
- keep `version-governance` decisions separate from lifecycle-state decisions
