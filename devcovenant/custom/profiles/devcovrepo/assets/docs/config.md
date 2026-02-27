# Configuration

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Config Structure](#config-structure)
- [Profiles and Overrides](#profiles-and-overrides)
- [Examples](#examples)

## Overview
`devcovenant/config.yaml` captures the active profiles, metadata overrides,
and lifecycle knobs. The file is tracked in the repo so CI and other
contributors use the same enforcement settings. Generated registry files
can be rebuilt, but config stays under version control.
When the file is missing, DevCovenant seeds a generic stub from the
global config template and marks it as generic until reviewed.
On every full refresh, DevCovenant regenerates autogen-owned config
sections while preserving user-owned settings.

## Workflow
1. Choose profiles that match the repo tech stack.
2. Add overrides for policies that need custom selectors or enforcement.
3. Set `install.generic_config: false` once the config is reviewed so
   `devcovenant deploy` can run.
4. Keep the config file committed so the same rules apply in CI.

## Config Structure
The core sections are:
- `profiles.active` for the profile list.
- `doc_assets` for autogen vs. user-managed doc lists.
- `autogen_metadata_overrides` for profile-derived metadata overlays.
- `user_metadata_overrides` for per-policy overrides applied last.
- `policy_state` for authoritative policy on/off activation.
- `pre_commit` for `.pre-commit-config.yaml` overrides.
- `install.generic_config` to guard deploys until the config is reviewed.

Key `engine` knobs used in this repo include:
- `output_mode` / `tests_output_mode` for console verbosity and test-run
  progress behavior.
- `logs_keep_last` for run-log retention (`0` keeps all runs).
- `auto_fix_enabled` for gate-managed autofix orchestration (`check` stays
  read-only regardless).
- `pycache_prefix_enabled` and `pycache_prefix` for routing Python bytecode
  caches away from the repo tree via `PYTHONPYCACHEPREFIX` while preserving
  bytecode generation fidelity.

## Profiles and Overrides
Overrides merge in the order: policy defaults, profile overlays, then
config overrides (autogen first, user last). Config overrides replace
targeted keys rather than appending. This lets a repo adjust a policy
without editing core files or the policy descriptor.
For dependency and license tracking, the active profiles supply the
`dependency-license-sync` manifest list; use config overrides when your
repo has custom manifest names.
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
environment stage commands. For top-level fallback launches
(`python3 -m devcovenant ...`), set `PYTHONPYCACHEPREFIX` in the shell/CI
environment before Python starts if you want to prevent repo-local
`__pycache__` creation for the launcher process itself.

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
  dependency-license-sync:
    dependency_role_files:
      - intent=>requirements.in
      - resolved=>requirements.lock
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
