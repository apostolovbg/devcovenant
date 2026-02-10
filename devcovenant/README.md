# DevCovenant
**Last Updated:** 2026-02-10
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** README
**Doc Type:** repo-readme
**Managed By:** DevCovenant

**Read first:** `AGENTS.md` is the canonical source of truth. See
`devcovenant/README.md` for usage and lifecycle workflow details.
<!-- DEVCOV:END -->

DevCovenant is a self-enforcing policy system that keeps human-readable
standards and automated checks in lockstep. It was born inside the Copernican
Suite, hardened through dogfooding in production repos, and is now a
standalone project focused on stability and portability.

If you install DevCovenant into a repository, the user-facing guide lives
at `devcovenant/README.md`.

## Table of Contents
1. [Overview](#overview)
2. [Why DevCovenant](#why-devcovenant)
3. [How It Works](#how-it-works)
4. [Document assets](#document-assets)
5. [Extended Docs](#extended-docs)
6. [CLI Entry Points](#cli-entry-points)
7. [Install, Deploy, Refresh, Upgrade](#install-deploy-refresh-upgrade)
8. [Workflow](#workflow)
9. [Core Exclusion](#core-exclusion)
10. [Dependency and License Tracking](#dependency-and-license-tracking)
11. [Using DevCovenant](#using-devcovenant)
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

## Extended Docs
Detailed guides live in `devcovenant/docs/` and are meant to be referenced
from day-to-day development. Start here:
- `devcovenant/docs/installation.md` for install/deploy/refresh/upgrade flows.
- `devcovenant/docs/config.md` for config structure and overrides.
- `devcovenant/docs/profiles.md` for profile anatomy and overlays.
- `devcovenant/docs/policies.md` for policy descriptors and scripts.
- `devcovenant/docs/adapters.md` for language-specific adapter design.
- `devcovenant/docs/registry.md` for registry files and refresh semantics.
- `devcovenant/docs/refresh.md` for full refresh behavior.
- `devcovenant/docs/workflow.md` for the enforced gate sequence.
- `devcovenant/docs/troubleshooting.md` for common errors and fixes.

## Install, Deploy, Refresh, Upgrade
Install copies the DevCovenant core and writes a generic config stub. It
never deploys managed docs or assets, so you can edit the config before the
repo goes live:
```bash
devcovenant install --target /path/to/repo
# edit devcovenant/config.yaml (set install.generic_config: false)
devcovenant deploy --target /path/to/repo
```

Refresh rebuilds managed docs/assets/registries using the existing core:
```bash
devcovenant refresh --target /path/to/repo
```

Upgrade replaces the core when the source version is newer, applies policy
replacements, and then runs refresh:
```bash
devcovenant upgrade --target /path/to/repo
```

Use `python3 -m devcovenant` for source checkouts when the console entry is
not on PATH.

Undeploy removes managed blocks and generated registry/config artifacts while
keeping the installed core, and uninstall removes the full DevCovenant
footprint:
```bash
devcovenant undeploy --target /path/to/repo
devcovenant uninstall --target /path/to/repo
```

The installer records `devcovenant/registry/local/manifest.json` so updates and
removals remain safe and predictable. If the target repo has no license file,
DevCovenant installs an MIT license by default and will not overwrite an
existing license unless forced. When `--backup-existing` is set, the
installer renames the existing file to `*_old.*` before writing the new one.
Version fallback order is: CLI `--version`, `config.version.override`, existing
valid `devcovenant/VERSION`, `pyproject.toml`, prompt, then `0.0.1`.
Existing-repo lifecycle commands (`deploy`, `refresh`, `upgrade`) default to
preserve mode for version/license and only overwrite when explicitly requested.
Managed docs such as `SPEC.md` and `PLAN.md` are part of the profile-driven
doc asset
graph, so they are generated (and refreshed) alongside the other auto-managed
documents—there is no special CLI flag to toggle them. See
`devcovenant/README.md` for the full lifecycle reference.


## Workflow
Adoption guidance:
- Install DevCovenant on a fresh branch.
- Fix all error-level violations first.
- After errors are cleared, ask the repo owner whether to address warnings or
  raise the block level.

DevCovenant expects the following sequence in enforced repos:
1. `python3 -m devcovenant check --start`
2. `python3 -m devcovenant test`
3. `python3 -m devcovenant check --end`

Shortcut: `devcovenant test` runs the same pytest + unittest sequence and
records status via the test runner wrapper.

During `--phase end`, if pre-commit modifies files, the script automatically
reruns `python3 -m devcovenant test` before recording the end timestamp so
tests always post-date any auto-fixes.

When policy blocks change, run `devcovenant refresh --target .` to
sync policy hashes.

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
  - devcovenant/check.py
  - devcovenant/test.py
  - devcovenant/install.py
  - devcovenant/deploy.py
  - devcovenant/upgrade.py
  - devcovenant/refresh.py
  - devcovenant/uninstall.py
  - devcovenant/undeploy.py
  - devcovenant/update_lock.py
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

## Dependency and License Tracking
DevCovenant tracks dependencies using the manifest files defined by the
active profiles (for example `requirements.in`/`pyproject.toml` for Python or
`package.json` for JavaScript). When those manifests change, the
dependency-license-sync policy requires refreshing `THIRD_PARTY_LICENSES.md`
(see the `## License Report` section) and the text files under `licenses/`.
Use profile overlays or config overrides to adjust which dependency files are
in scope for a given repo.

## Using DevCovenant
Common commands:
```bash
devcovenant check

devcovenant check --nofix
devcovenant check --start
devcovenant test
devcovenant check --end

devcovenant refresh --target /path/to/repo
devcovenant update_lock
```

See `devcovenant/README.md` for the full user guide.

## License
This project is released under the DevCovenant License v1.0. Redistribution is
prohibited without explicit written permission.
