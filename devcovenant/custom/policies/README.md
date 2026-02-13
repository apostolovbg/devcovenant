# Custom Policies

## Table of Contents
1. Overview
2. Metadata and Assets
3. Workflow

## Overview
Custom policies live under `devcovenant/custom/policies/<policy>/` and
override core policy scripts/descriptors when the policy id matches.

## Metadata and Assets
Policy metadata still comes from descriptors and profile overlays, but policy
assets are profile-owned. Declare asset files under active profile manifests
(`devcovenant/core/profiles/*/*.yaml` or
`devcovenant/custom/profiles/*/*.yaml`) using `assets` path/template entries.

## Workflow
Adjust policy code/descriptor here, tune metadata via profile/config overlays,
and manage any asset files through profiles. After changes, run the
DevCovenant gates so registry, AGENTS policy block, and changelog stay
synchronized.

When a custom policy replaces a core policy id, keep the metadata contract
stable unless you are intentionally evolving that policy's public behavior.
Prefer adding metadata keys over redefining existing ones, and document every
semantic change in `SPEC.md` and `PLAN.md` before implementation. This keeps
custom policy behavior reviewable, reproducible, and aligned with the
repository workflow.
