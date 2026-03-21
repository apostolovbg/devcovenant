# Installation and Lifecycle

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Lifecycle Commands](#lifecycle-commands)
- [Examples](#examples)
- [Undeploy and Uninstall](#undeploy-and-uninstall)

## Overview
DevCovenant separates installation of the core from deployment of managed
docs and assets. `install` copies `devcovenant/` and writes a
review-required config
stub. `deploy` activates managed docs, policy blocks, registries, and the
generated `.gitignore`. `refresh` is the standard full managed refresh for an
already installed repo. `upgrade` reconciles core from source on every run and
then runs refresh.

The practical model is:
- `install` is safe setup
- config review is the human decision point
- `deploy` is activation
- the first full gate cycle proves the activated baseline is actually clean

Use `python3 -m devcovenant` when the
CLI (command-line interface) entry is not available.
For source-checkout launches, DevCovenant suppresses Python cache-file writes
automatically, so `python3 -m devcovenant ...` does not leave
repo-local `devcovenant/__pycache__/` drift behind.

## Workflow
1. Run `install` to copy the core and generate a review-required config
   baseline.
2. If the repo already contains DevCovenant-shaped docs such as `SPEC.md`,
   `README.md`, or `PLAN.md`, keep them in place.
3. Edit `devcovenant/config.yaml`, confirm whether the repo is a normal repo
   using DevCovenant or a repo used to develop DevCovenant itself, and set
   `developer_mode` accordingly.
4. Set `install.config_reviewed: true`.
5. Run `deploy` to activate managed docs, registries, and gitignore.
6. Run the first full gate cycle to prove the baseline:
   `gate --start` -> `gate --mid` -> `test` -> `gate --end`.
7. Use `refresh` for normal managed refreshes and `upgrade` for core updates.

Three common starting situations:
- empty repo:
  `install` writes the core and config; `deploy` creates the managed baseline
- repo seeded with `SPEC.md` or `README.md`:
  the first `deploy` adopts compatible DevCovenant-shaped docs instead of
  overwriting their authored body
- existing repo with real files:
  `install` leaves ordinary files alone and `deploy` adds DevCovenant around
  them using the normal managed-doc preservation rules

## Lifecycle Commands
- `install`: copy the core plus a review-required config baseline. It never
  deploys
  managed docs/assets. If DevCovenant already exists, install exits with a
  message to run `upgrade`.
- `deploy`: requires completed config review
  (`install.config_reviewed: true`).
  It writes managed docs/assets/registries, regenerates `.gitignore`, and
  runs a full refresh.
- `install.config_reviewed` is the explicit human review checkpoint.
  It is not a cache key or a hidden runtime switch. It simply means a human
  has reviewed the starting config and is ready to activate it.
- when `developer_mode: false`, deploy removes repo-only DevCovenant
  development paths that do not belong in normal repos, including
  `devcovenant/custom/policies/**`,
  `devcovenant/custom/profiles/devcovrepo/**`, and
  `tests/devcovenant/core/**`
- pre-authored DevCovenant-shaped docs such as `SPEC.md`, `README.md`, or
  `PLAN.md` are adopted during refresh/deploy when their `Doc ID` / `Doc Type`
  match the target doc and their
  `DevCovenant Version` matches or exceeds the running runtime. Header-only
  docs keep their authored body while headers are upgraded; managed-block docs
  keep user content outside the managed block while the block/header refreshes.
  Older DevCovenant-shaped docs are replaced instead of being imported.
- `refresh`: run a full managed refresh using the installed core. It updates
  registries, managed docs/blocks, merged `.gitignore`, and generated
  pre-commit config.
- `upgrade`: reconcile core from source on every run, then run `refresh`.
- managed-environment runtime notes: when a managed interpreter path exists but
  is not executable, DevCovenant emits an explicit managed-environment error
  and stops so the interpreter path or permissions can be fixed directly.
- unhandled CLI runtime exceptions are normalized into explicit typed errors,
  while traceback details remain available in run logs.
- `undeploy`: remove managed blocks/registries and generated `.gitignore`
  fragments while keeping core + config.
- launcher truth: DevCovenant does not rely on repo-root startup hooks or
  in-package pre-import bootstrap tricks to control source-checkout bytecode
  writes. Top-level `python3 -m devcovenant ...` bytecode behavior is owned by
  the shell/CI (continuous integration) environment before Python starts.

## Examples
```bash
devcovenant install
# review devcovenant/config.yaml (set install.config_reviewed: true)
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
