# Refresh Behavior

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Refresh-All](#refresh-all)
- [Registry-Only Refresh](#registry-only-refresh)
- [Gitignore Regeneration](#gitignore-regeneration)

## Overview
Refresh keeps DevCovenant registries and config autogen data consistent
with the active profiles and policy descriptors. Managed docs and policy
blocks are handled by deploy/update, while refresh focuses on registry
state, profile registries, and profile-driven repo config such as the
merged `.gitignore` and `.pre-commit-config.yaml`.

## Workflow
1. Registry-only refresh runs at the start of each devcovenant command.
2. Refresh-all runs at the end of deploy/update unless `--skip-refresh` is
   set.
3. Use the `refresh` command when you only need registries and config
   autogen updated.

## Refresh-All
Refresh-all regenerates registries, the profile registry, config autogen
sections, the merged `.gitignore`, and the generated
`.pre-commit-config.yaml`. It does not touch managed docs or policy
blocks.

## Registry-Only Refresh
Registry-only refresh rebuilds local registry files and profile registries
without modifying managed docs, `.gitignore`, or
`.pre-commit-config.yaml`. It also refreshes config autogen data while
preserving user overrides. Missing runtime registry stubs (manifest,
policy assets, test status) are created on demand.

## Gitignore Regeneration
`.gitignore` is rebuilt from profile fragments and merged with any
user-provided entries. This keeps platform-specific ignores consistent
across installs while preserving local additions.
