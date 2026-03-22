# Installation and Lifecycle
**Last Updated:** 2026-03-22
**Project Version:** 1.0.0

## Overview
This document is the normative home for the lifecycle command contract.
Use it together with `devcovenant/docs/contracts.md` when you need the stable
meaning of install, deploy, refresh, upgrade, clean, undeploy, and uninstall.

DevCovenant separates setup from activation.
That split is deliberate.

`install` puts the runtime into the repository and writes a review-required
config baseline.
`deploy` activates that reviewed config and writes the governed outputs.

That means the important human decision happens between those two commands,
not inside them.
You review `devcovenant/config.yaml`, decide how the repo should behave, and
only then let `deploy` activate the contract.

## Before You Start
You need:

- a git repository

- Python and the toolchain required by the active profile stack

- permission to create or use the managed environment when that policy is
  enabled

If the console script is unavailable, use `python3 -m devcovenant ...`.
On Windows, `py -m devcovenant ...` is the common equivalent form.

## Install Versus Deploy
The shortest accurate model is:

1. `install` is setup.

   It copies the runtime, seeds config, and records enough baseline state for
   the repo to become DevCovenant-managed later.

2. config review is the human checkpoint.

   This is where you decide profile stack, policy activation, core invariant
   settings, doc assets, output behavior, and whether `developer_mode` is true
   or false.

3. `deploy` is activation.

   It runs the full refresh path and writes managed docs, registry outputs, and
   other governed artifacts.

`install.config_reviewed` exists only to make that checkpoint explicit.
It means a human has reviewed the starting config and is ready to activate it.
It is not a cache key and not a hidden runtime switch.

## Common Starting Situations
### Empty Repository
`install` writes the runtime and config baseline.
`deploy` creates the initial managed docs and generated governance files.

### Repository Seeded With DevCovenant-Shaped Docs
If the repo already contains compatible `README.md`, `SPEC.md`, `PLAN.md`, or
similar docs, keep them in place before the first `deploy`.
Refresh can adopt compatible docs instead of overwriting their authored body.

### Existing Repository With Real Content
`install` leaves normal repository files alone.
`deploy` adds DevCovenant around them using the managed-doc preservation rules.

## Lifecycle Commands

Repository-maintained workflows matter here too.
This repository keeps `.github/workflows/build.yml` and
`.github/workflows/publish.yml` as repository-maintained workflows instead of
refresh-generated output, so package and release behavior stay explicit and
reviewable.
### install
Copies the runtime, seeds config, and prepares tracked state.
It does not activate managed docs or generated governance files.
If DevCovenant already exists, `install` stops and points you to `upgrade`.

### deploy
Requires `install.config_reviewed: true`.
Runs the full refresh path and writes the active managed outputs.

### refresh
Rebuilds tracked registry state, managed docs, generated config sections,
generated workflow files, `.gitignore`, and related governed artifacts.

### clean
Removes disposable build, cache, runtime-registry, or log artifacts according
to the resolved cleanup targets.
Run it only after the active gate session is closed.

### upgrade
Reconciles the installed DevCovenant package from source and then runs
`refresh`.
Use it when DevCovenant is already present and you want the newer runtime.

### undeploy
Removes managed outputs while keeping the installed core and config.
Use it when you want to deactivate the governed outputs without uninstalling
DevCovenant entirely.

### uninstall
Removes the DevCovenant footprint from the repository.
Use it only when you are truly removing DevCovenant from the repo.

## First-Time Setup Runbook
Use this as the practical first integration flow:

1. Run `devcovenant install`.

2. Open `devcovenant/config.yaml` and review:

   - `developer_mode`

   - `profiles.active`

   - `doc_assets`

   - `core_invariants`

   - `policy_state`

   - `engine.*`

3. Set `install.config_reviewed: true`.

4. Run `devcovenant deploy`.

5. Prove the activated baseline with the full gate cycle:

   ```bash
   devcovenant gate --start
   devcovenant gate --mid
   devcovenant test
   devcovenant gate --end
   ```

That first full cycle matters.
It is the proof that the repository can actually operate under the reviewed
contract.

## Normal Operating Routine
After the first activation, the usual flow is simpler:

- use `refresh` when you need a full managed regeneration

- use `upgrade` when the runtime itself changes

- use the gate sequence for ordinary repository work

- use `check` when you want a read-only audit

## Developer Mode
`developer_mode: false` means a normal repository using DevCovenant as a tool.

`developer_mode: true` means the repository itself is being used to develop
DevCovenant.
That enables repo-only development surfaces that ordinary user repos should not
keep.

When `developer_mode: false`, deploy cleanup removes repo-only DevCovenant
development paths that do not belong in normal repos.

## Managed Environment Notes
When the managed-environment policy is enabled, later CLI runs can rerun inside
the managed interpreter automatically.
If the resolved interpreter path exists but is not executable, DevCovenant
stops with an explicit error so you can fix the path or permissions directly.

## Quick Reference
```bash
devcovenant install
devcovenant deploy
devcovenant refresh
devcovenant clean --all
devcovenant upgrade
devcovenant undeploy
devcovenant uninstall
```
