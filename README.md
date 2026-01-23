# DevCovenant
**Last Updated:** 2026-01-23
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** README
**Doc Type:** repo-readme
**Managed By:** DevCovenant

**Read first:** `AGENTS.md` is the canonical source of truth. See
`devcovenant/README.md` for usage and update workflow details.
<!-- DEVCOV:END -->

DevCovenant is a self-enforcing policy system that keeps human-readable
standards and automated checks in lockstep. It was born inside the Copernican
Suite, hardened through dogfooding in production repos, and is now a
standalone project focused on stability and portability.

If you install DevCovenant into another repository, the user-facing guide
lives in that repo at `devcovenant/README.md`.

## Table of Contents
1. [Overview](#overview)
2. [Why DevCovenant](#why-devcovenant)
3. [How It Works](#how-it-works)
4. [Repo Layout](#repo-layout)
5. [CLI Entry Points](#cli-entry-points)
6. [Install, Update, Uninstall](#install-update-uninstall)
7. [Workflow](#workflow)
8. [Core Exclusion](#core-exclusion)
9. [Dependency and License Tracking](#dependency-and-license-tracking)
10. [Using DevCovenant in Other Repos](#using-devcovenant-in-other-repos)
11. [History and Dogfooding](#history-and-dogfooding)
12. [License](#license)

## Overview
DevCovenant turns policy documents into executable checks. It reads policy
blocks from `AGENTS.md`, syncs them into a hash registry, and runs scripts that
implement those same policies. The result is a single source of truth that
prevents drift between documentation and enforcement.

## Why DevCovenant
Most teams document rules in one place and enforce them elsewhere. That leads
to drift, hidden requirements, and inconsistent enforcement. DevCovenant
eliminates that by making the documentation itself the executable spec.

## How It Works
1. `AGENTS.md` stores policy definitions and metadata blocks.
2. `devcovenant/core/parser.py` extracts and hashes each policy definition.
3. `devcovenant/registry.json` records the policy and script hashes.
4. `devcovenant/core/engine.py` runs policy scripts and reports violations.
5. Policy scripts resolve custom → core, and custom overrides suppress core
   fixers for that policy.
6. Pre-commit and CI run the same engine with the same policy source.

## Repo Layout
- `AGENTS.md`: canonical policy definitions for this repo.
- `SPEC.md`: product requirements (optional in user repos).
- `PLAN.md`: staged roadmap (optional in user repos).
- `devcovenant/`: engine, CLI, policy scripts, templates, and config.
  - `core/`: DevCovenant core engine and built-in policy scripts.
  - `core/policy_scripts/`: built-in policy scripts.
  - `core/fixers/`: built-in auto-fixers for core policies.
  - `custom/policy_scripts/`: repo-specific policies.
  - `custom/fixers/`: repo-specific fixers (optional).
  - `templates/`: packaged install templates for docs, configs, and tools.
- `tools/`: workflow helpers (pre-commit/test gates and status updates).

## CLI Entry Points
DevCovenant ships both a console script and a module entry:
```bash
devcovenant --help
python3 -m devcovenant --help
```

Both entry points execute the same CLI. Use `python3 -m devcovenant` when the
console script is not on your PATH.

## Install, Update, Uninstall
Install DevCovenant into a target repository:
```bash
devcovenant install --target /path/to/repo
```

Install is intended for new repos. Existing installs should use
`devcovenant update` or uninstall/reinstall. On install,
`CHANGELOG.md` and `CONTRIBUTING.md` are replaced with `_old.md`
backups, and `VERSION` defaults to `0.0.1` when missing.

Update an existing installation while preserving policy blocks and
metadata:
```bash
devcovenant update --target /path/to/repo --policy-mode preserve
```

Append missing stock policies without overwriting existing ones (the
default update behavior):
```bash
devcovenant update --target /path/to/repo --policy-mode append-missing
```

Force overwrite docs or config when needed:
```bash
devcovenant update --target /path/to/repo --force-docs

devcovenant update --target /path/to/repo --force-config
```


Normalize policy metadata to include every supported key (empty values
fall back to defaults):
```bash
devcovenant normalize-metadata
```
Schema defaults come from `devcovenant/templates/AGENTS.md`. Use
`--schema` to point at another file and `--no-set-updated` if you do not
want `updated: true` applied to changed policies.

Selector roles
--------------
Use `selector_roles` in policy metadata to declare selector roles. Each
role produces `role_globs`, `role_files`, and `role_dirs`. Custom role
names are supported and interpreted by policy scripts. Normalization will
infer roles from legacy selector keys and insert the role triplets without
overwriting values.


Uninstall uses the same CLI:
```bash
devcovenant uninstall --target /path/to/repo
```

The installer records `devcovenant/manifest.json` so updates and removals
remain safe and predictable. If the target repo has no license file,
DevCovenant installs a GPL-3.0 license by default and will not overwrite an
existing license unless forced. When a file must be replaced, the installer
renames the existing file to `*_old.*` before writing the new one.
Optional docs `SPEC.md` and `PLAN.md` are created only when
`--include-spec` or `--include-plan` are supplied; otherwise existing
files are preserved.
See `devcovenant/README.md` for the full install/update reference.


## Workflow
Adoption guidance:
- Install DevCovenant on a fresh branch.
- Fix all error-level violations first.
- After errors are cleared, ask the repo owner whether to address warnings or
  raise the block level.

DevCovenant expects the following sequence in enforced repos:
1. `python3 tools/run_pre_commit.py --phase start`
2. `python3 tools/run_tests.py`
3. `python3 tools/run_pre_commit.py --phase end`

When policy blocks change, set `updated: true`, run
`devcovenant update-hashes`, then reset the flag.

## Core Exclusion
User repos should keep DevCovenant core excluded from enforcement so updates
remain safe. The installer writes the following into
`devcovenant/config.yaml`:
```yaml
devcov_core_include: false
devcov_core_paths:
  - devcovenant/core
  - devcovenant/__init__.py
  - devcovenant/__main__.py
  - devcovenant/cli.py
  - tools/run_pre_commit.py
  - tools/run_tests.py
  - tools/update_test_status.py
```

Only the DevCovenant repo should set `devcov_core_include: true`. Do not
change or prune the core path list in user repos unless you are actively
implementing DevCovenant itself.

Use `language_profiles` and `active_language_profiles` in
`devcovenant/config.yaml` to extend file suffix coverage for multi-language
projects.

## Dependency and License Tracking
DevCovenant records runtime dependencies in `requirements.in` with pinned
versions in `requirements.lock` and metadata in `pyproject.toml`. Every time
those manifests change, the dependency-license-sync policy requires refreshing
`THIRD_PARTY_LICENSES.md` (see the `## License Report` section) and the text
files under `licenses/`. Those assets keep third-party licenses visible so
reviewers and installers know what the project ships.

## Using DevCovenant in Other Repos
Common commands:
```bash
devcovenant check

devcovenant check --mode pre-commit

devcovenant check --fix

devcovenant update-hashes

devcovenant restore-stock-text --policy <id>
```

See `devcovenant/README.md` in the target repo for the full user guide.

## History and Dogfooding
DevCovenant originated inside the Copernican Suite, then expanded to other
production repos (including the GCV-ERP custom and infra stacks). This repo
continues that dogfooding by enforcing itself with its own policy engine.

## License
This project is released under the DevCovenant License v1.0. Redistribution is
prohibited without explicit written permission.
