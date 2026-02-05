# Refresh Behavior

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Refresh-All](#refresh-all)
- [Registry-Only Refresh](#registry-only-refresh)
- [Gitignore Regeneration](#gitignore-regeneration)

## Overview
Refresh keeps the DevCovenant state consistent with the active profiles
and policy descriptors. It rebuilds registries, updates managed blocks,
regenerates `.gitignore`, and synchronizes assets. Refresh is designed to
run safely in CI because it can skip touching user docs or config when
needed.

## Workflow
1. Registry-only refresh runs at the start of each devcovenant command.
2. Full refresh-all runs at the end of install/update by default.
3. Use flags like `--skip-refresh` to bypass the final full refresh.

## Refresh-All
Full refresh regenerates managed docs, policy blocks, registries, and
profile-driven assets. It is used after install/update so the repo matches
the latest policy descriptors.

## Registry-Only Refresh
Registry-only refresh rebuilds local registry files without modifying
managed docs or config (unless missing). This keeps CI runs deterministic
without dirtying the working tree.

## Gitignore Regeneration
`.gitignore` is rebuilt from profile fragments and merged with any
user-provided entries. This keeps platform-specific ignores consistent
across installs while preserving local additions.
