# Configuration

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Config Structure](#config-structure)
- [Profiles and Overrides](#profiles-and-overrides)
- [Examples](#examples)

## Overview
`devcovenant/config.yaml` captures the active profiles, metadata overrides,
and lifecycle knobs. The file is tracked in the repo so
CI (continuous integration) and other contributors use the same enforcement
settings. Generated registry files
can be rebuilt, but config stays under version control.
When the file is missing, DevCovenant seeds a review-required baseline from the
global config template and blocks deploy until that review is completed.
On every full refresh, DevCovenant regenerates autogen-owned config
sections while preserving user-owned settings.

Practical mental model:
- `install` gives the repo this file plus the DevCovenant runtime
- your review of this file decides how the repo should behave
- `deploy` is blocked until that review is done
- after that, refresh, deploy, gates, and tests all read this file as the
  repo's active operating contract

## Workflow
1. Choose profiles that match the repo tech stack.
2. Add overrides for policies that need custom selectors or enforcement.
3. Confirm whether this repo is a normal repo using DevCovenant or a repo
   used to develop DevCovenant itself, then set `developer_mode`
   accordingly.
4. Set `install.config_reviewed: true` once the config is reviewed so
   `devcovenant deploy` can run.
5. Keep the config file committed so the same rules apply in CI.

Practical first-review checklist:
1. decide whether this is a normal repo using DevCovenant or a repo used to
   develop DevCovenant itself, then set `developer_mode`
2. confirm the active profile stack in `profiles.active`
3. confirm `core_invariants` metadata such as required test commands and
   gate-status paths
4. confirm which policies should be on or off in `policy_state`
5. confirm the important `engine` settings such as output mode, fail
   threshold, and autofix behavior
6. confirm the managed-doc list in `doc_assets`
7. then flip `install.config_reviewed: true`

`install.config_reviewed` is the explicit human review checkpoint.
It is not a runtime cache or a hidden deploy flag.

## Config Structure
The core sections are:
- `profiles.active` for the profile list.
- `doc_assets` for the managed-doc list, optional custom managed docs, and
  exclusion entries.
- `core_invariants` for DevCovenant-owned runtime-invariant metadata.
- `autogen_metadata_overrides` for profile-derived metadata overlays.
- `user_metadata_overrides` for per-policy overrides applied last.
- `policy_state` for authoritative policy on/off activation.
- `pre_commit` for `.pre-commit-config.yaml` overrides.
- `install.config_reviewed` to guard deploys until the config review is
  complete.
- `developer_mode` to declare whether the repository is merely using
  DevCovenant or is actually being used to develop DevCovenant itself.

Managed-doc guidance:
- keep `AGENTS.md` in `doc_assets.autogen`
- remove a builtin doc from `doc_assets.autogen` to turn it off for this repo
- add custom docs to `doc_assets.autogen` only after creating matching
  descriptors under an active profile `assets/` tree
- use `doc_assets.user` when you want to keep the full autogen list visible
  but exclude a specific doc from managed-doc sync

Key `engine` knobs used in this repo include:
- `output_mode` / `tests_output_mode` for console verbosity and test-run
  progress behavior.
- `logs_keep_last` for run-log retention (`0` keeps all runs).
- `auto_fix_enabled` for gate-managed autofix orchestration (`check` stays
  read-only regardless).
- `pycache_prefix_enabled` and `pycache_prefix` for routing Python cache
  files away from the repo tree for DevCovenant-managed child Python
  commands.

## Profiles and Overrides
Overrides merge in the order: policy defaults, profile overlays, then
config overrides (autogen first, user last). Config overrides replace
targeted keys rather than appending. This lets a repo adjust a policy
without editing core files or the policy descriptor.
For dependency and license tracking, the active profiles supply the
`dependency-management` manifest list; use config overrides when your
repo has custom manifest names.
For DevCovenant-owned invariants such as gate evidence, registry integrity,
and required runtime structure, use the first-class `core_invariants`
section instead of `policy_state`.
Version tracking defaults also come from profiles (for example, the
global/default profiles set baseline role targets while custom profiles
can override the `version_file` and add role selectors. Use config
overrides to point `version-sync` at a different canonical source or
role-target mapping.
Changelog coverage can be tuned by setting `summary_verbs` (the allowed
action verbs for Change/Why/Impact summaries) and adding `skipped_globs`
entries such as `*_old.*` when backup artifacts should not trigger logging.
Pre-commit config is built from profile fragments (global first), then
merged with `pre_commit.overrides` from config. Profile `ignore_dirs`
are converted into an `exclude` regex so hooks skip the same paths.
Stock and custom policy assets are profile-owned through profile `assets`
declarations for active profiles.
When `pycache_prefix_enabled: true`, an empty `pycache_prefix` (`''`) means
DevCovenant will choose a stable repo-specific temp path automatically.
Relative paths resolve from repo root; absolute paths are used as-is.
This routing applies to DevCovenant-managed Python subprocesses and managed
environment stage commands. For top-level source-checkout launches
(`python3 -m devcovenant ...`), DevCovenant suppresses Python cache-file
writes automatically so the launcher process does not leave repo-local
`__pycache__` drift behind.
When `managed-environment` is enabled, non-managed interpreter launches
auto-rerun in the managed interpreter. If that resolved path exists but is not
executable, runtime emits an explicit managed-environment error and stops so
the managed interpreter path or permissions can be fixed directly.

## Examples
```yaml
profiles:
  active:
    - global
    - python
    - docker
user_metadata_overrides:
  changelog-coverage:
    enforcement: active
    summary_verbs:
      - update
      - updated
      - fix
      - fixed
    skipped_globs:
      - "*_old.*"
  dependency-management:
    dependency_role_files:
      - intent=>requirements.in
      - resolved=>requirements.lock
core_invariants:
  devflow-run-gates:
    required_commands:
      - python3 -m unittest discover -v
      - pytest
pre_commit:
  overrides:
    repos:
      - repo: https://github.com/pre-commit/pre-commit-hooks
        rev: v4.6.0
        hooks:
          - id: check-toml
engine:
  pycache_prefix_enabled: true
  pycache_prefix: ''
```
