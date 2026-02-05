# DevCovenant Docs

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Doc Catalog](#doc-catalog)
- [Conventions](#conventions)

## Overview
This folder holds the detailed, user-facing guides for DevCovenant.
`devcovenant/README.md` remains the top-level guide, while these docs
explain the deeper mechanics, profiles, policies, and workflows.

## Workflow
Treat these files like code: update them alongside any behavior changes,
add examples for new flags or metadata, and keep cross-links current.
Updates here are tracked by the `documentation-growth-tracking` policy.

## Doc Catalog
- `installation.md` — install, update, uninstall, and no-touch runs.
- `config.md` — config structure, overrides, and profile selection.
- `profiles.md` — profile anatomy, assets, overlays, and suffixes.
- `policies.md` — policy descriptors, metadata, and custom policies.
- `adapters.md` — adapter design and language-specific logic.
- `registry.md` — local registry files and how they are refreshed.
- `refresh.md` — refresh-all vs registry-only behavior.
- `workflow.md` — required gates, pre-commit, and test runners.
- `troubleshooting.md` — common errors and how to resolve them.

## Conventions
- Keep headings consistent and link back to code paths where useful.
- Prefer short, copy-pasteable examples over long prose.
- Keep the newest information aligned with `SPEC.md` and `PLAN.md`.
