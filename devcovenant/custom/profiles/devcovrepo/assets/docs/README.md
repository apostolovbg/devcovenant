# DevCovenant Docs

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Suggested Layout](#suggested-layout)
- [Guidelines](#guidelines)

## Overview
This folder holds deeper, repo-specific documentation that complements the
top-level README: design notes, adapter guides, release rituals, and
troubleshooting playbooks. It is shipped by the devcovrepo profile and
monitored by documentation-growth-tracking overlays.

## Workflow
Treat this directory like code: add new files as topics emerge, keep headings
structured, and link directly to code/policy locations. Changes here should be
captured in the changelog and kept consistent with profiles/maps.

## Suggested Layout
- `architecture.md` — engine and registry flow.
- `policies.md` — writing/adapting policies and tests.
- `profiles.md` — profile catalog conventions and asset expectations.
- `release.md` — release steps and required checks.

## Guidelines
- Keep entries concise and actionable; link to code paths and policies.
- Maintain clear headings so doc-growth tracking can score depth.
- Prefer one topic per file; expand the layout list as the surface grows.
