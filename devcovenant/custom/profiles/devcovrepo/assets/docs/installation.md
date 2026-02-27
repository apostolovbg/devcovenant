# Installation and Lifecycle

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Lifecycle Commands](#lifecycle-commands)
- [Examples](#examples)
- [Undeploy and Uninstall](#undeploy-and-uninstall)

## Overview
DevCovenant separates installation of the core from deployment of managed
docs and assets. `install` copies `devcovenant/` and writes a generic config
stub. `deploy` activates managed docs, policy blocks, registries, and the
generated `.gitignore`. `refresh` is the standard full managed refresh for an
already installed repo. `upgrade` replaces the core when a newer version is
available and then runs refresh.

Use `python3 -m devcovenant` when the console entry is not available.
If you launch from a source checkout and want to avoid repo-local
`devcovenant/__pycache__/` drift while preserving bytecode generation, set
`PYTHONPYCACHEPREFIX` before Python starts (for example in CI job `env` or a
shell wrapper).

## Workflow
1. Run `install` to copy the core and generate a generic config stub.
2. Edit `devcovenant/config.yaml` and set `install.generic_config: false`.
3. Run `deploy` to activate managed docs, registries, and gitignore.
4. Use `refresh` for normal managed refreshes and `upgrade` for core updates.
5. Run gated edits with `start -> mid -> test -> end`.

## Lifecycle Commands
- `install`: copy the core plus a generic config stub. It never deploys
  managed docs/assets. If a newer core is available, install exits with a
  message to run `upgrade`.
- `deploy`: requires a non-generic config (`install.generic_config: false`).
  It writes managed docs/assets/registries, regenerates `.gitignore`, and
  runs a full refresh.
- `refresh`: run a full managed refresh using the installed core. It updates
  registries, managed docs/blocks, merged `.gitignore`, and generated
  pre-commit config.
- `upgrade`: replace core files when the source version is newer, then run
  `refresh`.
- `undeploy`: remove managed blocks/registries and generated `.gitignore`
  fragments while keeping core + config.

## Examples
```bash
devcovenant install
# edit devcovenant/config.yaml (set install.generic_config: false)
devcovenant deploy

devcovenant refresh
devcovenant upgrade

# edit-session workflow
devcovenant gate --start
devcovenant gate --mid
devcovenant test
devcovenant gate --end
```

## Undeploy and Uninstall
`undeploy` removes managed blocks and registries but keeps the core so you
can adjust config and redeploy. `uninstall` removes the entire DevCovenant
footprint from the repo.
