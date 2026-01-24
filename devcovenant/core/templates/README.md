# DevCovenant Templates

## Table of Contents
1. Overview
2. Structure
3. Workflow

## Overview
This directory holds the stock template assets DevCovenant installs into
repos. These templates are versioned, shipped with DevCovenant, and are
refreshed on update. The goal is to keep every repo aligned with a single
source of truth while still allowing local customization via the custom
template tree. Treat these files as the reference set for install and
update behavior.

## Structure
Templates are organized by scope:
- `global/` for shared docs and common assets.
- `profiles/<profile>/` for profile-specific assets.
- `policies/<policy>/` for policy-scoped assets.

Template resolution prefers custom overrides first, then falls back to
core assets. See the per-scope READMEs for details and examples.

## Workflow
When adding or updating a template, keep names and paths stable, update the
policy or profile that owns the asset, and ensure the manifest tracks the
new path. Run DevCovenant gates so the registry and changelog stay in sync.
