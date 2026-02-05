# Installation and Update

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Install Modes](#install-modes)
- [Update Behavior](#update-behavior)
- [No-touch Runs](#no-touch-runs)
- [Examples](#examples)
- [Uninstall](#uninstall)

## Overview
DevCovenant installs into a target repository by copying the package and
materializing managed documents, registries, and config. Install is for
first-time setup. Update refreshes the same artifacts without replacing
`devcovenant/` unless you force it. Source checkouts and the packaged CLI
share the same commands; use `python3 -m devcovenant` when the console
entry is not available.

## Workflow
1. Choose a target repository path.
2. Run `devcovenant install` for a new repo or `devcovenant update` for an
   existing install.
3. Run the enforced gates: pre-commit start, tests, pre-commit end.
4. Review and commit the generated docs and registries.

## Install Modes
- `devcovenant install --target /path/to/repo` installs a full baseline.
- Install writes new docs into the repo, backing up existing files as
  `*_old.*` when replacements are required.
- Install seeds `devcovenant/VERSION` when missing.

## Update Behavior
- Update refreshes managed docs, registries, and config defaults while
  preserving policy text and overrides.
- `--force-docs` or `--force-config` override existing files.
- `--skip-refresh` avoids the final refresh-all step when a fast run is
  needed for tests.

## No-touch Runs
Use `--no-touch` to copy only the package into the target repo while
recording the run in the local manifest. This mode is useful for staged
rollouts where you want to apply the doc/config changes later.

## Examples
```bash
devcovenant install --target /path/to/repo

devcovenant update --target /path/to/repo --policy-mode append-missing

python3 -m devcovenant update --target /path/to/repo --force-docs
```

## Uninstall
Uninstall reverses the installation steps and removes managed artifacts.
Use it to roll back a broken install, then rerun install or update to
restore a clean baseline.
