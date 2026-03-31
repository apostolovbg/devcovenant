# Workflow
**Last Updated:** 2026-03-31
**Project Version:** 1.0.1

## Overview
Use this document for the gate sequence, workflow-run contract, CI mapping,
and run-artifact handling.
When you need the exact command order or need to understand how the generated
CI workflow relates to local work, start here.
Use it together with `devcovenant/docs/contracts.md` when you need the stable
workflow or CI-ownership contract.

The normal DevCovenant work slice is:

```bash
devcovenant gate --start
# edit files and clear complaints while working
devcovenant gate --mid
devcovenant run
devcovenant gate --end
```

That sequence is the workflow.
It is not a suggestion and not a wrapper convenience.
It is how DevCovenant proves that hooks, checks, runs, and closing state all
happened in the right order.

## What Each Command Is For
### check
Read-only audit.
Use it when you want to inspect the repository without opening or closing a
gate session.

### gate --status
Session inspection.
Use it when you want to know whether a gate session is open and which run logs
matter most for the current session.
It reports the latest completed public workflow stage, including `mid`, by
reading both runtime ledgers.

### gate --start
Opens the tracked work session.
It records the baseline that later checks use for change-scoped behavior.
If `gate --start` fails, the repository is not in a usable baseline state yet.
Fix the reported problem first.

### gate --mid
Required pre-run preflight.
It catches pre-commit or DevCovenant mutations before workflow evidence is
recorded.
If it reports hook-induced changes, apply or clear them and rerun
`gate --mid` until it is clean.
Treat the middle of the flow as `gate --start`, then a `gate --mid` loop
until clean, and only then `run`.

### run
Executes the declared workflow runs for the active contract.
This is the middle of the workflow, not the whole workflow by itself.

### gate --end
Runs the closing pre-commit pass and records closure state for the session.
If required workflow evidence is stale or failing, end-gate will tell you to
refresh that evidence before it can close the session.

## Workflow Contract
The public workflow contract has four stages:
1. `gate --start`
2. `gate --mid`
3. `run`
4. `gate --end`

The reserved workflow anchors are:
- `start`
- `mid`
- `end`

Declared workflow runs live between `mid` and `end`.
Profiles contribute those runs through `workflow_runs`.
The workflow layer validates and orders them using executable positioning
fields:
- `after`
- `before`
- `order`

Unknown references fail contract resolution.
Cycles fail contract resolution.
The final run order is graph-resolved, not decorative metadata.

## Run Artifacts
Every DevCovenant command writes a run folder under `devcovenant/logs/`.
When a command prints `Run logs: ...`, use the artifacts in this order:
1. `summary.txt`
2. `tail.txt` when present
3. `stdout.log`
4. `stderr.log`

That is the primary debug contract.
The CLI can stream child output, but run artifacts remain the stable record.

## Runtime Workflow State
The workflow runtime uses two local ledgers:
- `devcovenant/registry/runtime/gate_status.json`
- `devcovenant/registry/runtime/workflow_session.json`

`gate_status.json` is the short lifecycle ledger for gate stages and required
pre-commit evidence.
`workflow_session.json` records the declared runs for the active session,
their pass/fail state, their freshness evidence, and the snapshots the runtime
uses to decide whether a run is still fresh.

The tracked counterpart to that runtime state is `workflow_contract` in
`devcovenant/registry/registry.yaml`.
That tracked section records the reserved anchors, the declared runs, the
resolved run order, and the run metadata the engine must enforce.

The path knobs that feed the workflow runtime live in ordinary config
sections such as `paths.*` and `workflow.*`.
There is no separate engine metadata family for workflow law.

## Freshness
Workflow runs are not only pass/fail.
They also have freshness rules.
The default contract ignores `CHANGELOG.md`, so changelog-only edits remain
within gate scope without forcing a rerun of otherwise fresh workflow evidence.
Profiles may declare broader or stricter freshness behavior when a run needs
it.

## CI Mapping
The generated source-tree CI workflow lives at `.github/workflows/ci.yml`.
Its visible workflow name is `CI`.

The ownership split is:
1. the builtin `global` profile owns the generic base workflow
2. active profiles may contribute `ci_and_test` fragments that extend that
   workflow for repo families or stack families
3. local `config.ci_and_test.*` keys are for repo-local overlays or, rarely,
   a full local replacement

The global base should stay generic.
If a repository family needs extra proof or extra source-tree steps, that
extension should come from profile-owned CI fragments instead of from the
builtin base.

Generated `.pre-commit-config.yaml` excludes also follow the resolved ignore
contract. Active-profile `ignore_dirs` feed the shared pre-commit exclude
block, and setuptools-style `*.egg-info` metadata directories are always
excluded as disposable build outputs.
Generated workflow jobs that invoke Python should keep transient bytecode
caches outside the repository checkout, and the runtime snapshot layer also
ignores
repo-local `*.pyc`, `__pycache__`, and known cache roots such as
`.gha-pycache` if a runner or shell leaks them back in anyway.

When a repository adds installed-artifact proof, that proof should exercise
the same public workflow the package docs promise across the install surfaces
the repository supports.
If a repository documents `pipx` as the normal operator entrypoint, the
installed-CLI proof should stay on that CLI through the full gate/run/end
cycle even when DevCovenant re-executes into a managed repository
environment internally.
If a repository declares a Python support floor, release CI should prove that
floor explicitly instead of relying only on newer interpreter runs.
If a repository adds a separate release workflow, that workflow should consume
validated artifacts and provenance from the proof boundary rather than
rebuilding a fresh distribution later.
If that release workflow runs inline Python for provenance or artifact checks,
it should also set up an explicit interpreter instead of relying on whatever
ambient `python` happens to be on the runner image.
Pin GitHub Action refs to immutable commit SHAs and keep them current as
runner runtimes evolve; proof and release workflows should use Node 24-capable
action releases or equivalent non-JS steps instead of carrying older Node
20-only refs forward.

## Managed Environment In Workflow Execution
When the managed-environment policy is enabled, DevCovenant resolves one target
execution environment for each stage.
It first reuses the current interpreter when that interpreter already satisfies
the contract.
If not, it selects the configured interpreter or environment root and only
then runs `managed_commands` to prepare it.
If the policy does not declare automatic bootstrap commands yet, non-gate
`command` stage operations may keep using the current interpreter until the
target environment exists.

That keeps `gate --start` non-destructive once a configured environment already
satisfies the contract.
It also keeps the workflow portable across normal `.venv` repos, other managed
environment layouts, and installed-artifact proof repos.
The matcher is symlink-safe, so the selected interpreter stays anchored to the
declared environment root even when the launcher points at a shared base
Python binary.

For Python-owned tools such as the pre-commit gate hook, execution runs
`python -m pre_commit` through the selected interpreter instead of depending
on a console-script shim.

## Recovery Rules
Use these recovery rules consistently:
- if `gate --start` fails, fix the start-gate complaint before editing
- if `gate --mid` fails, rerun `gate --mid` until clean before `run`
- if `run` fails, inspect run artifacts first, fix the cause, then rerun `run`
- if `gate --end` fails, inspect logs, refresh required workflow evidence, and
  rerun `gate --end`
- if you are unsure where a slice stands, use `devcovenant gate --status`

## Practical Rule
The workflow contract is the public law surface.
Profiles may extend the middle of the workflow by declaring runs, but they do
not get to redefine the four-stage sequence itself.
