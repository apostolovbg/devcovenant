# DevCovenant
**Last Updated:** 2026-01-28
**Version:** 0.2.6
<p align="center">
  <img
src="https://raw.githubusercontent.com/apostolovbg/devcovenant/main/banner.png"
    alt="DevCovenant"
    style="width: 100%;"
  />
</p>

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
<!-- REPO-ONLY:BEGIN -->
4. [Repo Layout](#repo-layout)
<!-- REPO-ONLY:END -->
5. [CLI Entry Points](#cli-entry-points)
6. [Install, Update, Uninstall](#install-update-uninstall)
7. [Workflow](#workflow)
8. [Core Exclusion](#core-exclusion)
9. [Dependency and License Tracking](#dependency-and-license-tracking)
10. [Using DevCovenant in Other Repos](#using-devcovenant-in-other-repos)
<!-- REPO-ONLY:BEGIN -->
11. [History and Dogfooding](#history-and-dogfooding)
<!-- REPO-ONLY:END -->
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
3. `devcovenant/registry/local/policy_registry.yaml` records policy/script
   hashes along with metadata handles, profile coverage, asset hints, and
   core/custom origin for every policy (enabled or disabled).
4. `devcovenant/core/engine.py` runs policy scripts and reports violations.
5. Policy scripts resolve custom → core, and custom overrides suppress core
   fixers for that policy.
6. Pre-commit and CI run the same engine with the same policy source.

<!-- REPO-ONLY:BEGIN -->
## Repo Layout
- `AGENTS.md`: canonical policy definitions for this repo.
- `SPEC.md`: product requirements (optional in user repos).
- `PLAN.md`: staged roadmap (optional in user repos).
- `devcovenant/`: engine, CLI, policy implementations, profiles, assets, and
  config.
  - `core/`: DevCovenant core engine, built-in policies, and profiles.
  - `core/policies/`: built-in policy implementations; each policy folder
    contains `<policy>.py`, `tests/`, `fixers/`, and `assets/`.
  - `core/profiles/`: profile definitions (`profile.yaml`) plus `assets/`.
  - `custom/policies/`: repo-specific policy overrides (same layout as core).
  - `custom/profiles/`: repo-specific profile overrides and assets.
  - `registry/`: generated registry files (`policy_registry.yaml`,
    `manifest.json`, `profile_catalog.yaml`, `policy_assets.yaml`) that
    include live policy map metadata so tooling can read policy coverage
    without parsing `AGENTS.md`.
- `.devcov-state/`: ephemeral state such as `test_status.json` for the
  devflow gates.
- `core/*.py`: workflow helpers (pre-commit/test gates, status updates, and
  the check wrapper).
<!-- REPO-ONLY:END -->


## CLI Entry Points
DevCovenant ships both a console script and a module entry:
```bash
devcovenant --help
python3 -m devcovenant --help
```

Both entry points execute the same CLI. Use `python3 -m devcovenant` when the
console script is not on your PATH.

## Document assets
The `global` profile installs AGENTS.md, README.md, SPEC.md, PLAN.md,
CHANGELOG.md, CONTRIBUTING.md, and `devcovenant/README.md` by default from the
YAML descriptors in `devcovenant/core/profiles/global/assets/`. Use the new
`doc_assets.autogen` and `doc_assets.user` config sections to pin
which docs the profile refreshes.
Keep the other docs as manual overrides.
Whenever these docs are touched, the `last-updated-placement` policy refreshes
the `**Last Updated:** YYYY-MM-DD` header via its fixer.
It sets the value to the current UTC date so the recorded timestamp matches the
latest edit.

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

Skip all doc/policy/metadata writes by appending `--no-touch` to `install` or
`update`. That flag copies just the `devcovenant/` package (including the
default `devcovenant/config.yaml`), leaves the rest of the repo untouched,
and still records the run in `devcovenant/registry/local/manifest.json` so
you can finish the install later when you are ready:

```bash
devcovenant install --target /path/to/repo --no-touch
devcovenant update --target /path/to/repo --no-touch
```


Normalize policy metadata to include every supported key (empty values
fall back to defaults):
```bash
devcovenant normalize-metadata
```
Schema defaults come from
`devcovenant/core/profiles/global/assets/AGENTS.md`. Use `--schema` to
point at another file and `--no-set-updated` if you do not want
`updated: true` applied to changed policies.

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

The installer records `devcovenant/registry/local/manifest.json` so updates and
removals remain safe and predictable. If the target repo has no license file,
DevCovenant installs an MIT license by default and will not overwrite an
existing license unless forced. When a file must be replaced, the installer
renames the existing file to `*_old.*` before writing the new one. Managed
docs such as `SPEC.md` and `PLAN.md` are part of the profile-driven doc asset
graph, so they are generated (and refreshed) alongside the other auto-managed
documents—there is no special CLI flag to toggle them. See
`devcovenant/README.md` for the full install/update reference.


## Workflow
Adoption guidance:
- Install DevCovenant on a fresh branch.
- Fix all error-level violations first.
- After errors are cleared, ask the repo owner whether to address warnings or
  raise the block level.

DevCovenant expects the following sequence in enforced repos:
1. `python3 devcovenant/run_pre_commit.py --phase start`
2. `python3 devcovenant/run_tests.py`
3. `python3 devcovenant/run_pre_commit.py --phase end`

During `--phase end`, if pre-commit modifies files, the script automatically
reruns `devcovenant/run_tests.py` before recording the end timestamp so
tests always post-date any auto-fixes.

When policy blocks change, set `updated: true`, run
`devcovenant update-policy-registry`, then reset the flag.

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
  - devcovenant/run_pre_commit.py
  - devcovenant/run_tests.py
  - devcovenant/update_test_status.py
  - devcovenant/core/check.py
```

Only the DevCovenant repo should set `devcov_core_include: true`. Do not
change or prune the core path list in user repos unless you are actively
implementing DevCovenant itself.

Use `profiles.active` in `devcovenant/config.yaml` to extend file suffix
coverage for multi-language projects.
Set `version.override` when you want config-driven installs to emit a specific
project version in generated assets (for example, `pyproject.toml`).
Apply that override before any `VERSION` file exists.

The DevCovenant repository activates a dedicated `devcovrepo` profile.
It overrides `new-modules-need-tests` metadata so the `devcovenant/**` sources
and the mirrored `tests/devcovenant/**` suites (core/custom policies and
profiles) stay aligned.

User repositories that do not enable `devcovrepo` instead keep the
`devcovuser` profile active so `devcovenant/**` stays out of enforcement while
`devcovenant/custom/**` continues to run.

That profile also contributes a `.gitignore` fragment that keeps
`devcovenant/config.yaml` local to this repo. User repos that do not enable
that profile continue to commit `devcovenant/config.yaml`, ensuring their
runtime configuration travels with their source tree.

For a “no-touch” install, copy the `devcovenant/` package into the target repo,
adjust `devcovenant/config.yaml` to taste, and run
`devcovenant install --target` later. The installer honors any existing config
unless `--force-config` is supplied, letting teams pre-seed their configuration
before DevCovenant runs for the first time.

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

devcovenant update-policy-registry

devcovenant restore-stock-text --policy <id>
```

See `devcovenant/README.md` in the target repo for the full user guide.

<!-- REPO-ONLY:BEGIN -->
## History and Dogfooding
DevCovenant originated inside the Copernican Suite, then expanded to other
production repos (including the GCV-ERP custom and infra stacks). This repo
continues that dogfooding by enforcing itself with its own policy engine.
<!-- REPO-ONLY:END -->

## License
This project is released under the DevCovenant License v1.0. Redistribution is
prohibited without explicit written permission.
