# Installation and Lifecycle
**Last Updated:** 2026-03-30
**Project Version:** 1.0.0

## Overview
This document is the normative home for the lifecycle command contract.
Use it for the machine-install and lifecycle command story.
Keep `devcovenant/docs/contracts.md` nearby when you need the stable document
map for the rest of the runtime surfaces.
It explains how to install the DevCovenant CLI, when to use `pipx` versus a
source checkout, and what each lifecycle command changes inside a repository.

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

- a machine-level way to run DevCovenant:
  `pipx` for normal CLI use, or a managed source checkout when you are
  developing DevCovenant itself

- a git repository

- Python and the toolchain required by the active profile stack

- permission to create or use the managed environment when that policy is
  enabled

## User Install Versus Source Development
Use these two paths deliberately:

1. `pipx` install for normal CLI use.

   This is the preferred machine-install path when you want to use
   DevCovenant in one or more repositories.
   `pipx` keeps DevCovenant in its own application environment instead of
   mixing it into your user-site Python packages.

2. source checkout for DevCovenant development.

   Use the repository-managed environment when you are developing DevCovenant
   itself, testing unreleased runtime changes, or working directly in this
   repository.

If the console script is unavailable in a source checkout, use
`python3 -m devcovenant ...`.
On Windows, `py -m devcovenant ...` is the common equivalent form.
Every public command also accepts `--quiet`, `--normal`, or `--verbose` as a
per-invocation output override.
Those flags override config for that invocation only and work either before
the command name or on the command itself.

## Preferred Machine Install
For ordinary users, install the CLI with `pipx`:

```bash
pipx install devcovenant
devcovenant --version
```

Use these companion commands for the installed CLI:

```bash
pipx upgrade devcovenant
pipx uninstall devcovenant
```

That machine-level install is separate from repository activation.
Installing the CLI makes `devcovenant` available on the machine.
Running `devcovenant install` inside a repository seeds DevCovenant into that
repository.

## Source Checkout And Contributor Use
Use a source checkout when you need to develop DevCovenant rather than simply
use it.

In that mode:

- create or reuse the repo-managed environment

- run DevCovenant from that environment

- use the governed gate workflow for repository changes

This repository's own managed-environment policy documents the bootstrap
commands for that contributor path.

## Install Versus Deploy
The shortest accurate model is:

1. `install` is setup.

   It copies the runtime, seeds config, and records enough baseline state for
   the repo to become DevCovenant-managed later. That baseline also seeds the
   tracked manifest inventory that later structure validation and refresh
   reuse.

2. config review is the human checkpoint.

   This is where you decide profile stack, policy activation, runtime contract
   settings under `paths` and `workflow`, doc assets, output behavior, and
   whether `developer_mode` is true or false.

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
This repository keeps `.github/workflows/publish.yml` as a
repository-maintained manual workflow, while the generated
`.github/workflows/ci.yml` now includes a repo-specific `Build` job.
That keeps package and release behavior explicit and reviewable.
That release boundary now includes artifact provenance explicitly:
the `Build` job in `CI` produces the validated dist artifacts and provenance
record, and `publish.yml` should only publish that exact validated CI artifact
instead of rebuilding inside publish.
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

### asset
Materializes one reusable profile asset or managed doc as a Desktop copy.

The destination contract is:

- no second argument: Desktop plus the original asset basename

- second argument such as `OTHERNAME.md`: Desktop plus that file name

The second argument is a filename only, not a path.
Use `--overwrite` when the Desktop target already exists.
`asset` reuses the same rendering machinery that refresh uses for plain
profile assets and the same managed-doc renderer used by descriptor-backed
docs such as `SPEC.md`.

### run
Runs the declared workflow runs for the active contract.
Use it when a gate command tells you that workflow evidence is stale and must
be refreshed before a new start baseline or before end-gate closure.

### clean
Removes disposable build, cache, runtime-registry, or log artifacts according
to the resolved cleanup targets.
Run it only after the active gate session is closed.
The CLI entrypoint lives in `devcovenant/clean.py`, while the flow-layer
implementation that owns cleanup orchestration lives in
`devcovenant/core/flow/clean_command.py`.
When the logs scope is selected, `clean` may delete older run folders, but it
must keep the active clean run folder so the reported summary path stays
available after the command finishes.
It must also protect the configured managed environment generically through the
managed-environment policy metadata instead of through a hardcoded `.venv`
rule, so a bench or another managed environment type can define its own safe
roots.

## Package Build Surface
The published package intentionally ships the runtime-facing docs and profile
assets that DevCovenant needs at install time:

- the packaged `devcovenant/README.md` and `devcovenant/VERSION`

- the built-in policy descriptors under `devcovenant/builtin/policies`

- the built-in profile descriptors, translators, and asset templates under
  `devcovenant/builtin/profiles`

- the core invariant descriptors under
  `devcovenant/core/contracts/invariants`

- the packaged docs under `devcovenant/docs`

- the tracked `README.md` files for `devcovenant/logs` and
  `devcovenant/registry`

The published package must not ship live repository state or development
debris such as:

- `devcovenant/config.yaml`

- `devcovenant/registry/registry.yaml`

- `devcovenant/registry/runtime/**`

- timestamped runtime log folders

- local test trees, build trees, or `*.egg-info` outputs

`MANIFEST.in` and `pyproject.toml` should keep that boundary explicit.
Package builds should be quiet: no stale MANIFEST exclusions, no ambiguous
package-discovery warnings, and no accidental runtime-state leakage.

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

   - `paths`

   - `doc_assets`

   - `workflow`

   - `policy_state`

   - `engine.*`

3. Set `install.config_reviewed: true`.

4. Run `devcovenant deploy`.

5. Prove the activated baseline with the full gate cycle:

   ```bash
   devcovenant gate --start
   devcovenant gate --mid
   devcovenant run
   devcovenant gate --end
   ```

That first full cycle matters.
It is the proof that the repository can actually operate under the reviewed
contract.
For a normal repository, that proof should come before adding any
repo-specific custom policies or profiles under `devcovenant/custom/`.
Reach the first reviewed baseline first.
Then add custom extensions deliberately on top of an already-working normal
activation.
Separately, this repository's artifact automation now proves the earlier
activation boundary directly from the built wheel, the built sdist, and the
documented `pipx` machine-install path.
That proof now runs the same full public workflow on all three install
surfaces:
`gate --start`, `gate --mid`, `run`, `gate --end`, then `check`.
That keeps release proof honest at the package boundary instead of proving a
narrower install-only path than the one the package docs actually promise.

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
That is why the baseline-first rule matters:
if a normal repo seeds repo-specific custom policy/profile paths before its
first reviewed activation, deploy cleanup can legitimately prune those
dev-only-looking paths before the repository has established its intended
custom shape.
The intended lifecycle is:
review baseline first, then add repo-specific custom extensions.

## Managed Environment Notes
When the managed-environment policy is enabled, DevCovenant resolves one target
execution environment for each CLI stage.
It first reuses the current interpreter when that interpreter already matches
the metadata contract and its declared external prerequisites still resolve.
If not, it selects the configured interpreter or environment root and only
then runs `managed_commands` to prepare it.
That keeps `gate --start` non-destructive once a repo-managed `.venv`, bench,
or other configured interpreter already satisfies the contract.
If the resolved interpreter path exists but is not executable, DevCovenant
stops with an explicit error so you can fix the path or permissions directly.

## Quick Reference
```bash
pipx install devcovenant
pipx upgrade devcovenant
devcovenant install
devcovenant deploy
devcovenant asset SPEC.md
devcovenant asset SPEC.md OTHERNAME.md
devcovenant refresh
devcovenant policy dependency-management refresh-all
devcovenant clean --all
devcovenant upgrade
devcovenant undeploy
devcovenant uninstall
```

`clean --all` removes build, cache, runtime-registry, and log artifacts.
Its `registry` scope means runtime registry only:
`devcovenant/registry/runtime/` is disposable, while the tracked
`devcovenant/registry/registry.yaml` is preserved.

Dependency refresh is no longer a special top-level command.
Use the namespaced policy command surface instead:
`devcovenant policy dependency-management refresh-all`.
That policy command now runs through the shared runtime execution layer, so it
inherits the same managed-environment and output-mode behavior as the rest of
the CLI.

The generated Python `pyproject.toml` also renders long repo-owned
`project_description` values through a wrapped TOML string form.
That keeps the physical source lines short without truncating the logical
package description that install/deploy synchronize from project-governance.
