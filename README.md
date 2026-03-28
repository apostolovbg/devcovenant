# DevCovenant
**Doc ID:** README
**Doc Type:** repo-readme
**Project Version:** 1.0.0
**Last Updated:** 2026-03-28
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->

<!-- DEVCOV:END -->

![DevCovenant banner](https://raw.githubusercontent.com/apostolovbg/devcovenant/main/devcovenant/docs/banner.png)

DevCovenant is a repository governance framework.
It turns workflow law, policy prose, and enforcement evidence into one system
instead of letting them drift apart.

## Overview
Use DevCovenant when a repository needs more than style checks.
It is built for repositories where the expensive failures are procedural:
people skip required steps, policy text stops matching runtime behavior,
release notes lose traceability, and automation becomes harder to trust.

In practice, DevCovenant gives a repository four things:

1. A governed workflow.

   The normal work slice is `gate --start`, edit, `gate --mid`, `run`,
   `gate --end`.

2. Executable policy rules.

   Policies are configured in the repo, surfaced in `AGENTS.md`, and enforced
   by the runtime instead of living only as prose.

3. Managed documentation and generated governance files.

   DevCovenant can keep selected docs, config sections, registry files,
   workflow files, and policy blocks synchronized.

4. Evidence artifacts.

   Each command writes run logs, summaries, and related session state so teams
   can inspect what happened instead of guessing.

## Why It Exists
Repositories usually fail in boring ways, not exotic ones.
A team forgets one workflow run.
A generated file changes after the last workflow run.
A policy says one thing while the runtime does another.
A changelog entry misses the files that actually changed.

DevCovenant is meant to make those failures obvious and repeatable to fix.
It does that by making the workflow explicit, storing the active policy state
in the repo, and producing evidence for each governed command run.

## Quick Start
For most users, the right starting point is an isolated machine install with
`pipx`, followed by repository activation inside the repo you want to govern.

```bash
pipx install devcovenant
devcovenant --version
cd your-repo
devcovenant install
# review devcovenant/config.yaml
# set install.config_reviewed: true
devcovenant deploy
devcovenant gate --start
# make your edits
devcovenant gate --mid
devcovenant run
devcovenant gate --end
```

What those steps mean:

1. `pipx install devcovenant` installs the CLI on your machine in an isolated
   application environment.

2. `devcovenant install` adds the runtime to the target repository and seeds
   `devcovenant/config.yaml`.

3. The config review is the human decision point.

   You decide whether the repo is a normal repository using DevCovenant or a
   repository used to develop DevCovenant itself, which profiles are active,
   which policies are enabled, and which engine settings should govern the
   repo.

4. `deploy` activates the reviewed contract.

   That is when managed docs, registries, generated workflow files, and other
   governed outputs are written.

5. The first full gate cycle proves the activated baseline actually works.

Use a source checkout instead of `pipx` only when you are developing
DevCovenant itself or testing unreleased runtime changes.
In that case, use the repository's managed environment and fall back to
`python3 -m devcovenant ...`.
On Windows, `py -m devcovenant ...` is the common equivalent form.

## Workflow
The standard repository workflow is:

```bash
devcovenant gate --start
# edit files and clear complaints while working
devcovenant gate --mid
devcovenant run
devcovenant gate --end
```

Use the commands this way:

- `check`

  Read-only audit.
  It evaluates the current repo state and writes run logs, but it does not open
  or close a gate session.

- `gate --start`

  Opens a tracked work session and records the baseline that later checks use
  for change-scoped behavior.

- `gate --mid`

  Required pre-run preflight.
  It catches pre-commit or DevCovenant mutations before workflow evidence is
  recorded.

- `run`

  Runs all enabled workflow runs in declared order and records
  evidence for them.

- `gate --end`

  Runs the closing pre-commit pass and records closure state for the session.

When a command emits `Run logs: ...`, start with `summary.txt`.
If that is not enough, inspect `tail.txt`, then `stdout.log` and `stderr.log`.

In `engine.tests_output_mode: normal`, the declared `tests` run keeps
console progress concise and leaves full child output in the run logs.

## Commands
Most operators only need a small command set day to day:

```bash
devcovenant check
devcovenant gate --status
devcovenant gate --start
devcovenant gate --mid
devcovenant run
devcovenant gate --end
devcovenant refresh
devcovenant deploy
devcovenant clean --all
```

Other lifecycle commands such as `upgrade`, `undeploy`, and `uninstall` are
used less often, but they follow the same run-log contract.

Keep machine installation and repository lifecycle separate:

- use `pipx upgrade devcovenant` when you want a newer installed CLI

- use `devcovenant upgrade` inside a repository where DevCovenant is already
  installed and governed

## Configuration Checkpoints
The most important first-review settings in `devcovenant/config.yaml` are:

1. `developer_mode`

   `false` for a normal repository using DevCovenant.
   `true` only when the repository is being used to develop DevCovenant itself.

2. `profiles.active`

   The stack description for the repository.

3. `doc_assets`

   Which managed docs are enabled, disabled, or supplied by custom profiles.

4. `core_invariants`

   DevCovenant-owned runtime invariants such as gate evidence requirements.

5. `policy_state`

   Which customizable policies are on or off.

6. `engine.*`

   Output, autofix, retention, and related runtime behavior.

## What DevCovenant Manages
DevCovenant can manage several different repository surfaces.
This includes the refresh-generated governance gate pipeline, while
repository-maintained workflows remain ordinary repo files when a repo chooses
that split.

DevCovenant can manage several different repository surfaces:

- selected documents

- generated config sections

- policy blocks in `AGENTS.md`

- tracked registry state

- runtime registry state

- generated workflow files

- generated `.gitignore` and pre-commit files

The important preservation rule is simple:
missing docs can be created, empty docs can be replaced, one-line docs can be
replaced, and otherwise DevCovenant should only touch managed headers and
managed blocks.

## Docs Map
Use the shorter map below instead of treating the README as the whole manual.

- [installation.md](devcovenant/docs/installation.md)

  Install, deploy, upgrade, clean, undeploy, uninstall, and first-time setup.

- [workflow.md](devcovenant/docs/workflow.md)

  Exact gate sequence, command choice, run artifacts, and recovery.

- [config.md](devcovenant/docs/config.md)

  How to read `devcovenant/config.yaml`, including project governance,
  doc assets, core invariants, and policy activation.

- [profiles.md](devcovenant/docs/profiles.md)

  Profiles, overlays, assets, and translator ownership.

- [policies.md](devcovenant/docs/policies.md)

  Policy descriptors, runtime actions, policy commands, autofix boundaries,
  and version-governance adapters.

- [refresh.md](devcovenant/docs/refresh.md)

  Refresh behavior, managed docs, descriptor schema, and preservation rules.

- [architecture.md](devcovenant/docs/architecture.md)

  Runtime layers, invariants, evidence flow, and contract map.

- [registry.md](devcovenant/docs/registry.md)

  Tracked registry, runtime registry, and gate-status state.

- [troubleshooting.md](devcovenant/docs/troubleshooting.md)

  Fast recovery paths for common failures.

## Security, Privacy, and Support
Public trust surfaces live in the repo root:

- [SECURITY.md](SECURITY.md)

- [PRIVACY.md](PRIVACY.md)

- [SUPPORT.md](SUPPORT.md)

Use those docs for vulnerability reporting, local data-handling boundaries,
and support expectations.

<!-- REPO-ONLY:BEGIN -->
## Repo Notes
This repository is also the dogfooding repo for DevCovenant itself.
That is why `developer_mode` is enabled here and why the repo contains
additional custom profiles, custom policies, and documentation assets that do
not belong in ordinary user repositories.
<!-- REPO-ONLY:END -->

## License
DevCovenant is released under the MIT License.
See [LICENSE](LICENSE) and
[licenses/THIRD_PARTY_LICENSES.md](licenses/THIRD_PARTY_LICENSES.md).
