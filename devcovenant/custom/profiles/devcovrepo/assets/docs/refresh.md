# Refresh Behavior

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Full Refresh](#full-refresh)
- [Automatic Registry Refresh](#automatic-registry-refresh)
- [Gitignore Regeneration](#gitignore-regeneration)

## Overview
`devcovenant refresh` is the canonical full refresh command. It keeps
registries, managed docs, policy blocks, and generated configs aligned with
the active profiles and policy descriptors.

## Workflow
1. Lightweight registry refresh runs at the start of each CLI command.
2. `devcovenant refresh` runs a full managed refresh.
3. `deploy` and `upgrade` also run a full refresh as part of their workflow.

## Full Refresh
The full refresh command regenerates local registries, profile registry state,
config autogen sections, the merged `.gitignore`, and generated
`.pre-commit-config.yaml`. It also syncs managed doc blocks/headers for docs
selected by `doc_assets`.

## Automatic Registry Refresh
DevCovenant runs an internal lightweight registry refresh before command
execution so metadata stays current during normal checks/tests. This is an
implementation detail, not a separate user-facing command.

## Gitignore Regeneration
`.gitignore` is rebuilt from profile fragments and merged with any
user-provided entries. This keeps platform-specific ignores consistent
across installs while preserving local additions.
