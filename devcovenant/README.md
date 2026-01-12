# DevCovenant (Repository Guide)
**Last Updated:** 2026-01-12
**Version:** 0.2.4
**DevCovenant Version:** 0.2.4
**Status:** Active Development
**License:** DevCovenant License v1.0

This file is installed into a target repository at `devcovenant/README.md`.
It explains how to use DevCovenant inside that repo. The root `README.md`
should remain dedicated to the repository's actual project.

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Workflow](#workflow)
4. [Severity and Block Levels](#severity-and-block-levels)
5. [Agent Prompt Recipes](#agent-prompt-recipes)
6. [Where Policies Live](#where-policies-live)
7. [Policy Script Layout](#policy-script-layout)
8. [Core Exclusion](#core-exclusion)
9. [Running Checks](#running-checks)
10. [Adding or Updating Policies](#adding-or-updating-policies)
11. [Patching Built-In Policies](#patching-built-in-policies)
12. [Documentation Growth Tracking](#documentation-growth-tracking)
13. [CI and Automation](#ci-and-automation)
14. [Troubleshooting](#troubleshooting)
15. [Uninstall](#uninstall)

## Overview
DevCovenant enforces the policies written in `AGENTS.md`. It reads those
policies, validates them against their scripts, and reports actionable
violations. The system is designed to keep policy text, enforcement logic, and
documentation synchronized.

## Quick Start
If DevCovenant is installed, start with (use `python3` unless `python`
already points to Python 3); install the published release first if you
haven’t installed it yet:
```bash
pip install devcovenant
python3 -m devcovenant.cli install --target .
python3 tools/run_pre_commit.py --phase start
python3 tools/run_tests.py
python3 tools/run_pre_commit.py --phase end
```

If you built DevCovenant locally, `pip install dist/devcovenant-*` before
running `python3 -m devcovenant.cli install --target .` so the wheel files
are reused.

## Workflow
Adoption workflow for an existing repo:
1. Create a new branch dedicated to the initial DevCovenant rollout.
2. Run DevCovenant in default mode (error-level blocking only).
3. Fix all error-level violations first.
4. Ask the repo owner how to handle warnings and info-level rules.
5. Merge only after the error set is clean and expectations are agreed.

If the repo has no license file, the installer writes a GPL-3.0 license by
default. Replace it if your project requires a different license.

When policies change:
1. Update the policy text in `AGENTS.md`.
2. Set `updated: true` in the policy block.
3. Update the policy script and tests.
4. Run `python3 -m devcovenant.cli update-hashes`.
5. Reset `updated: false` and run the workflow gates.

## Severity and Block Levels
Recommended defaults during adoption:
- Error: version sync, last-updated, changelog coverage, devflow gates,
  registry sync, read-only boundaries, and security policies.
- Warning: code style, documentation quality, naming clarity.
- Info: documentation growth reminders.

Default block level should be `error` so the agent is not overwhelmed during
first adoption. Raise the block level to `warning` or `info` only after the
error backlog is cleared and the repo owner approves.

## Agent Prompt Recipes
Use the following prompts with an AI agent:
- "Solve all error-level violations." (default adoption step)
- "List warning-level violations and ask me before fixing."
- "Add a new policy called <name> with severity <level>."
- "Disable policy <id> for now."
- "Raise severity of <id> to error."
- "Lower severity of <id> to warning."
- "Enable documentation quality checks for <file set>."
- "Update hashes after policy changes."
- "Restore stock policy text for <id>."

## Where Policies Live
`AGENTS.md` is the canonical policy document. Every policy is defined there in
plain language plus a `policy-def` metadata block. DevCovenant parses those
blocks and enforces them.

## Policy Script Layout
DevCovenant installs the full engine and scripts inside the repo:
- `devcovenant/core/`: DevCovenant core engine and built-in policy scripts.
- `devcovenant/core/policy_scripts/`: built-in checks shipped with DevCovenant.
- `devcovenant/core/fixers/`: built-in auto-fixers.
- `devcovenant/custom/policy_scripts/`: repo-specific checks.
- `devcovenant/common_policy_patches/`: patch scripts for built-ins (Python
  preferred; JSON/YAML supported).

Script resolution order is custom → core. Option
resolution order is config → patch → policy metadata → script defaults.

## Core Exclusion
User repos should keep DevCovenant core excluded from enforcement so updates
remain safe. The installer sets this automatically in
`devcovenant/config.yaml`:
```yaml
devcov_core_include: false
devcov_core_paths:
  - devcovenant/core
  - devcovenant/__init__.py
  - devcovenant/__main__.py
  - devcovenant/cli.py
  - devcov_check.py
  - tools/run_pre_commit.py
  - tools/run_tests.py
  - tools/update_test_status.py
  - tools/install_devcovenant.py
  - tools/uninstall_devcovenant.py
```

Only the DevCovenant repo should set `devcov_core_include: true`. Do not
change or prune the core path list in user repos unless you are actively
developing DevCovenant.

For multi-language repos, configure `language_profiles` and
`active_language_profiles` in `devcovenant/config.yaml` to extend the
engine’s file suffix inventory without rewriting the full list.

## Running Checks
Common commands (use `python3` if available):
```bash
python3 -m devcovenant.cli check
python3 -m devcovenant.cli check --mode lint
python3 -m devcovenant.cli check --mode pre-commit
python3 -m devcovenant.cli check --fix
python3 -m devcovenant.cli restore-stock-text --policy <id>
python3 -m devcovenant.cli restore-stock-text --all
```

## Install & Uninstall
Install DevCovenant into another repository:
```bash
python3 -m devcovenant install --target /path/to/repo
```

Uninstall:
```bash
python3 -m devcovenant uninstall --target /path/to/repo
```

The `tools/install_devcovenant.py` and `tools/uninstall_devcovenant.py`
helpers simply forward the arguments to the CLI for compatibility.

Use `--fix` to apply auto-fixes when available. The CLI exits non-zero when
blocking violations exist.

## Pre-release Review
Before tagging a release, confirm the following areas:

1. **Gate enforcement**
   - `tools/run_pre_commit.py --phase start` succeeded on the current tree.
   - `python3 tools/run_tests.py` and `tools/run_pre_commit.py --phase end`
     followed, so the gate sequence completed.
   - The `devflow-run-gates` policy now treats every doc or code edit as
     requiring the status file so skipped runs are blocked.
2. **Policy sync**
   - `python3 -m devcovenant.cli update-hashes` ran after policy changes.
   - `devcovenant/registry.json` reflects the new hashes.
   - `devcov-check` passes.
3. **Packaging**
   - `python -m build` and `twine check dist/*` succeed locally
     for wheel+sdist.
   - The `publish.yml` workflow publishes on `v*` tags using the
     `PYPI_API_TOKEN`.
4. **Documentation**
   - README, SPEC, PLAN, and `CHANGELOG.md` describe the mandatory workflow,
     gates, and migration roadmap for downstream repos.
5. **Changelog coverage**
   - Each touched file appears in `CHANGELOG.md:11-20`.
   - Entries remain newest-first so release notes are chronological.

Rerun these steps in a clean tree before pushing a release tag.
This ensures nothing under the new contract slips through.


## Adding or Updating Policies
Policy definitions live in `AGENTS.md`:
```markdown
## Policy: Example Policy

```policy-def
id: example-policy
status: active
severity: error
auto_fix: false
updated: false
apply: true
applies_to: *.py
```

Explain the rule in plain language.
```

Built-in policies belong in `core/policy_scripts/`. Repo-specific
policies belong in `custom/policy_scripts/`. Always add tests under
`devcovenant/core/tests/test_policies/`.

Set `apply: false` to disable a policy without deleting it. Use status
`fiducial` to keep the policy enforced while also emitting a reminder with the
policy text on every run.

## Patching Built-In Policies
Create a patch file named after the policy id. Python patches are preferred,
but JSON or YAML files with the same basename are supported for static
overrides:
```
common_policy_patches/<policy_id>.py
```

Supported entry points (choose one):
- `PATCH`: module-level dict of overrides.
- `get_patch() -> dict`: return an overrides dict.
- `patch_options(options, policy, context, repo_root) -> dict`: compute
  overrides dynamically using any subset of those arguments.

Example:
```python
def patch_options(options, **kwargs):
    return {"max_length": 100, "include_prefixes": ["src"]}
```

Patch scripts override built-in defaults without editing the core script.

## Documentation Growth Tracking
The documentation growth policy treats user-facing files as any code or
configuration that affects user interactions, API surfaces, integrations, or
workflow behavior. Configure it with:
- `user_facing_prefixes`, `user_facing_globs`, `user_facing_suffixes`,
  `user_facing_files`, `user_facing_keywords` (and the
  `user_facing_exclude_*` variants).
- `user_visible_files` to declare which docs must be updated.

When user-facing files change, at least one doc in the declared set must be
edited. If `require_mentions` is enabled, those docs must mention the changed
components by name (tokens derived from the file path). Use
`mention_stopwords` and `mention_min_length` to tune the token matching. The
policy can also enforce quality gates like required headings, minimum section
count, and minimum word count.

## CI and Automation
CI should run:
- `python3 tools/run_pre_commit.py --phase start`
- `python3 tools/run_tests.py`
- `python3 tools/run_pre_commit.py --phase end`

The pre-commit hook uses the same engine and policy set.

## Troubleshooting
- Policy drift: run `python3 -m devcovenant.cli update-hashes`.
- Missing scripts: confirm the policy id matches the script filename.
- Unexpected violations: check metadata in `AGENTS.md` and patch files.

## Uninstall
Run the uninstall script from the DevCovenant source repo:
```bash
python3 tools/uninstall_devcovenant.py --target /path/to/repo
```

Use `--remove-docs` to delete docs that were installed by DevCovenant.
