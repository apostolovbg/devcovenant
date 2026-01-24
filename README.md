# DevCovenant
**Last Updated:** 2026-01-24
**Version:** 0.2.5
<p align="center">
  <img
    src="banner.png"
    alt="DevCovenant"
    style="width: 100%;"
  />
</p>

<!-- DEVCOV:BEGIN -->
**Read first:** `AGENTS.md` is the canonical source of truth. See
`DEVCOVENANT.md` for architecture and lifecycle details.
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
7. [Install Behavior Cheat Sheet](#install-behavior-cheat-sheet)
8. [Workflow](#workflow)
9. [Core Exclusion](#core-exclusion)
10. [Dependency and License Tracking](#dependency-and-license-tracking)
11. [Using DevCovenant in Other Repos](#using-devcovenant-in-other-repos)
12. [History and Dogfooding](#history-and-dogfooding)
13. [License](#license)

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
5. Pre-commit and CI run the same engine with the same policy source.

## Repo Layout
- `AGENTS.md`: canonical policy definitions for this repo.
- `DEVCOVENANT.md`: architecture, schema, and lifecycle reference.
- `SPEC.md`: product requirements and functional expectations.
- `PLAN.md`: staged roadmap and migration sequencing.
- `devcovenant/`: engine, CLI, policy scripts, templates, and config.
  - `core/`: DevCovenant core engine and built-in policy scripts.
  - `core/policy_scripts/`: built-in policy scripts.
  - `core/policy_scripts/fixers/`: built-in auto-fixers shipped alongside
    each policy.
  - `core/fixers/`: compatibility wrappers that re-export fixers for older
    code.
  - `custom/policy_scripts/`: repo-specific policies.
  - `custom/fixers/`: repo-specific fixers (optional).
  - `common_policy_patches/`: patch scripts for built-ins (Python preferred;
    JSON/YAML supported).
  - `templates/`: packaged install templates for docs, configs, and tools.
- `tools/`: thin wrappers that invoke `devcovenant` commands.

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

Update an existing installation without overwriting docs/config:
```bash
devcovenant install --target /path/to/repo
```

Force overwrite docs or config when needed:
```bash
devcovenant install --target /path/to/repo --force-docs

devcovenant install --target /path/to/repo --force-config
```

The `tools/install_devcovenant.py` helper is a thin wrapper around the CLI, so
older automation can keep calling it. Uninstall is similar:
```bash
devcovenant uninstall --target /path/to/repo
```

The installer records `.devcov/install_manifest.json` so updates and removals
remain safe and predictable. If the target repo has no license file,
DevCovenant installs a GPL-3.0 license by default and will not overwrite an
existing license unless forced. When a file must be replaced, the installer
renames the existing file to `*_old.*` before writing the new one.
`DEVCOVENANT.md` is always replaced so the reference doc stays canonical.


## Install Behavior Cheat Sheet
- `AGENTS.md`: replaced by template; editable notes preserved under
  `# EDITABLE SECTION`.
- `README.md`: content preserved, headers refreshed, managed block
  inserted when required sections are missing.
- `DEVCOVENANT.md`: backed up to `*_old.*` and replaced by the template.
- `SPEC.md` and `PLAN.md`: content preserved with refreshed headers,
  created if missing.
- `CHANGELOG.md` and `CONTRIBUTING.md`: backed up and replaced by the
  standard templates.
- `.gitignore`: regenerated and merges user entries under a preserved
  block.
- `VERSION`: created or updated on demand; `x.x` is normalized to `x.x.0`.
- `LICENSE`: created from the GPL-3.0 template if missing; overwrite
  only when explicitly requested.
- `CITATION.cff`: created on prompt or via `--citation-mode create`; when
  skipped, citation enforcement is disabled in `AGENTS.md`.
- `.devcov/install_manifest.json`: always written with install metadata.
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
  - devcov_check.py
  - tools/run_pre_commit.py
  - tools/run_tests.py
  - tools/update_test_status.py
  - tools/install_devcovenant.py
  - tools/uninstall_devcovenant.py
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
