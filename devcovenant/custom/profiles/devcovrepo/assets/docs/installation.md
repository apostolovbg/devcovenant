# Installation and Update

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Lifecycle Commands](#lifecycle-commands)
- [No-touch Runs](#no-touch-runs)
- [Examples](#examples)
- [Undeploy and Uninstall](#undeploy-and-uninstall)

## Overview
DevCovenant separates installation of the core from deployment of managed
docs and assets. Install copies `devcovenant/` and writes a generic config
stub. Deploy activates managed docs, policy blocks, registries, and the
generated `.gitignore`. Update refreshes managed content without replacing
core files. Upgrade replaces the core when a newer version is available and
then runs update. Refresh rebuilds registries and config autogen data only.

Use `python3 -m devcovenant` when the console entry is not available.

## Workflow
1. Run `install` to copy the core and generate a generic config stub.
2. Edit `devcovenant/config.yaml` and set `install.generic_config: false`.
3. Run `deploy` to activate managed docs, registries, and gitignore.
4. Use `update` for managed refreshes or `upgrade` for core updates.

## Lifecycle Commands
- `install`: copy the core plus a generic config stub. It never deploys
  managed docs/assets. If a newer core is available, install prompts for
  `upgrade` first.
- `deploy`: requires a non-generic config (`install.generic_config: false`).
  It writes managed docs/assets/registries, regenerates `.gitignore`, and
  runs a registry refresh.
- `update`: refresh managed docs/assets/registries using the existing core.
  It never upgrades core files.
- `upgrade`: replace core files when the source version is newer, apply
  policy replacements, then run `update`.
- `refresh`: registry-only regeneration plus config autogen refresh.
- `undeploy`: remove managed blocks/registries and generated `.gitignore`
  fragments while keeping core + config.

## No-touch Runs
`--no-touch` copies only the DevCovenant package and records the run in the
local manifest. Use it to stage a later deploy.

## Examples
```bash
devcovenant install --target /path/to/repo
# edit devcovenant/config.yaml (set install.generic_config: false)
devcovenant deploy --target /path/to/repo

devcovenant update --target /path/to/repo
devcovenant upgrade --target /path/to/repo

python3 -m devcovenant refresh --target /path/to/repo
```

## Undeploy and Uninstall
`undeploy` removes managed blocks and registries but keeps the core so you
can adjust config and redeploy. `uninstall` removes the entire DevCovenant
footprint from the repo.
