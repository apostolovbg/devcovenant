# Workflow
**Last Updated:** 2026-03-29
**Project Version:** 1.0.0

## Overview
Use this document for the gate sequence, CI contract, and run-artifact
handling.
When you need the exact command order or need to understand how the generated
CI workflow relates to local work, start here.
Use it together with `devcovenant/docs/contracts.md` when you need the stable
gate-sequence or CI-ownership contract.

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
It is how DevCovenant proves that checks, fixes, tests, and closing state all
happened in the right order.

## What Each Command Is For
### check
Read-only audit.
Use it when you want to inspect the repository without opening or closing a
gate session.

### gate --status
Session inspection.
Use it when you want to know whether a gate session is open and which run logs
matter most right now. It reports the latest completed public workflow stage,
including `mid`, by reading both runtime ledgers.

### gate --start
Opens the tracked work session.
It runs the start pre-commit pass and records the baseline the later checks use
for change-scoped behavior.

### gate --mid
Required pre-run preflight.
It is where hook mutations and DevCovenant autofixes must surface before test
results are recorded.

### run
Runs every configured workflow run in validated declared order and records
evidence for each one in the active workflow session.
In this repo that currently means the `tests` run, which runs the two-step
`unittest` plus `pytest` sequence.
Every public command also accepts `--quiet`, `--normal`, or `--verbose` as a
per-invocation output override.

### gate --end
Runs the closing pre-commit pass and records closure state.
It only closes the session after every declared run for the current
session has fresh passing evidence.

## Why gate --mid Exists
`gate --mid` is what keeps workflow-run evidence honest.
Without it, a pre-commit hook or DevCovenant autofix could change files after
the last meaningful pre-run check and before the recorded run results.

That is why the practical rule is: run `gate --mid` before `devcovenant run`.
Think of the sequence as `gate --start -> gate --mid loop (rerun until clean)`
before `run` and `gate --end`. If `gate --mid` changes files or reports
blocking problems, clear them and run it again before `devcovenant run`.

## Standard Sequence
Use this exact order for ordinary repository work:

1. `devcovenant gate --start`
2. make the change
3. `devcovenant gate --mid`
4. rerun `gate --mid` if it changed files or reported blocking complaints
5. `devcovenant run`
6. `devcovenant gate --end`

If the console script is unavailable, use `python3 -m devcovenant ...`.
On Windows, `py -m devcovenant ...` is the common equivalent form.

## Read-Only Audit Path
If you are investigating without making a governed edit, use:

```bash
devcovenant check
devcovenant gate --status
```

Use `check` as the default read-only audit command and `gate --status` when
you need current lifecycle state. Once you move from inspection to governed
changes, follow the normal gate sequence.

## Run Artifact Contract
Every command run writes evidence artifacts.
When you see `Run logs: ...`, inspect them in this order:

1. `summary.txt`
2. `tail.txt` if present
3. `stdout.log` and `stderr.log`

This is the fastest way to understand a failure without rerunning commands in a
noisier mode.
That pointer should stay valid after the command finishes; for example,
`clean --logs` may prune older run folders, but it must not delete the active
clean run's own artifact directory.
Cleanup reporting should also stay readable.
When cleanup skips protected matches inside the managed environment, the run
artifacts should summarize that by protected root instead of dumping hundreds
of nested cache paths.

## Recovery Rules
### Start gate failed
Clear the reported problem first.
Do not treat a failed start gate as a usable baseline.
If start reports stale workflow runs from the previous closed
session, run `devcovenant run` and then rerun `devcovenant gate --start`.

### Mid gate changed files
Run `gate --mid` again until it stops introducing new blocking state.
Then run `run`.

### End gate reported new changes
Inspect the latest run logs, clear the problem, rerun `run` if required, and
rerun `gate --end`.
If end reports stale workflow runs, rerun `devcovenant run` and then
rerun `gate --end`.

### Managed environment error
If the resolved managed interpreter path exists but is not executable,
DevCovenant stops explicitly.
Fix the path or permissions and rerun the appropriate command.

## Output Modes
`engine.output_mode` controls normal command output.
Run declarations may also point at a narrower config field for their own
reporting behavior. In the built-in `tests` run, that hook points to
`engine.tests_output_mode`.

Every public command and subcommand also accepts a per-invocation override:

- `--quiet`
- `--normal`
- `--verbose`

Those flags override config for that invocation only.
They work in both forms:

```bash
devcovenant --verbose run
devcovenant gate --mid --quiet
devcovenant run --normal
```

If the override matches the configured mode already, DevCovenant simply stays
in that mode.

In `normal` test mode, DevCovenant keeps console progress concise and leaves
full child output in the run logs.
That is why the log artifacts matter.
The shared child-command runner also treats Linux PTY EOF races as normal
command completion once the child exits, so successful CI and proof-gate runs
do not fail after emitting their full output.
Profiles declare those richer reporting hooks under
`workflow_runs[*].recording`, so output-mode overrides, event adapters, and
workflow profiling are run-owned instead of hardcoded by run id.
The runtime ownership now matches that behavior more closely:
event-adapter loading lives in `devcovenant/core/runtime/event.py`, and
policy-check summary rendering lives in
`devcovenant/core/runtime/policy_reporting.py` instead of in the services
layer. The same runtime boundary now owns namespaced policy-command parsing
and runtime-action dispatch, so `devcovenant policy ...` runs through the same
execution layer as `devcovenant run`.

## Run Freshness
Workflow runs stay fresh only while their declared freshness
contract still matches the current repository state.
That contract is now run metadata, not a hidden `tests` special case.

The default run freshness contract is:

- `kind: ignore_paths`
- `ignored_files: [CHANGELOG.md]`
- `ignored_globs: []`

That means changelog-only edits remain gate-scoped, but they do not stale an
already-passed run by themselves.
If a run should stale on every change instead, declare:

```yaml
freshness:
  kind: any_change
```

If a run should ignore a broader generated surface, declare:

```yaml
freshness:
  kind: ignore_paths
  ignored_files:
    - CHANGELOG.md
  ignored_globs:
    - docs/generated/**
```

## Workflow Session Surfaces
DevCovenant now splits workflow evidence between two runtime files:

- `devcovenant/registry/runtime/gate_status.json`
- `devcovenant/registry/runtime/workflow_session.json`

`gate_status.json` stays the short lifecycle ledger for gate stages and the
pre-commit evidence they require.
`workflow_session.json` records the declared workflow runs for the
active session, their pass/fail status, their last-session binding, and the
runtime snapshots used to decide whether a run is still fresh.
`gate --status` reads both files so it can report the real public lifecycle
stage, including `mid`, without pretending the workflow is only
`start -> run -> end`.
The `devflow-run-gates` invariant may override `gate_status_file` and
`workflow_session_file`, but both files must stay inside
`devcovenant/registry/runtime/` so workflow evidence remains runtime-owned.

The tracked counterpart to that runtime state is
`workflow_contract` in `devcovenant/registry/registry.yaml`.
That tracked section records the reserved anchors, the declared runs coming
from active profiles, and the run ids the engine must enforce.
The helper ownership now matches that split:

- `devcovenant/core/runtime/registry.py` owns runtime evidence paths
- `devcovenant/core/services/tracked_registry.py` owns tracked registry paths
- `devcovenant/core/flow/policy_check_context.py` owns gate/session-derived
  check-context assembly for policy runs
- `devcovenant/core/flow/workflow_contract.py` owns workflow-contract
  normalization and run resolution
- `devcovenant/core/flow/gate_status_validation.py` owns gate-status payload
  parsing and schema validation

## CI Mapping
The generated CI workflow lives at
`.github/workflows/ci.yml`.
Its visible workflow name is `CI`.

The ownership split matters:

1. the builtin `global` profile owns the generic base workflow

2. active profiles may contribute `ci_and_test` fragments that add
   repo-family source-tree steps

3. local `config.ci_and_test.*` keys are for repo-local overlays or,
   rarely, a full local replacement

The global base should stay language-agnostic.
If a repository family needs extra CI proof, that extension should come from
the relevant profile instead of from the generic global template.
The clean shape is to keep one main `governance` job for source-tree truth
and add any repo-specific `Build` job through the profile-owned
`ci_and_test` surface instead of through the global base.

In this repository, the active repo-specific profile extends the main
`governance` job with `pip-audit` and Bandit steps, and it also adds a
dependent `Build` job.
That `Build` job then verifies the documented installed workflow on all three
public install paths:

- built wheel: `gate --start -> gate --mid -> run -> gate --end -> check`

- built sdist: `gate --start -> gate --mid -> run -> gate --end -> check`

- documented `pipx` machine-install path:
  `pipx install -> install -> deploy -> refresh`, then
  `gate --start -> gate --mid -> run -> gate --end -> check`

That keeps source-tree CI generated and profile-extended, while keeping
artifact-release proof in a repo-specific `Build` job instead of pushing it
back into the generic global CI base.
When an upstream scanner advisory has no published fix release yet, a narrow
reviewed exception may also live in that repo-specific CI layer.
Keep that exception explicit, documented, and easy to delete once upstream
publishes a real fix path.

This repository also keeps `publish.yml` as a repo-maintained manual release
workflow.
It consumes the result of `CI`, while the `Build` job itself lives inside the
generated CI workflow.
The `Build` job follows the same truthfulness rule: it should prove the real
artifact lifecycle from the built wheel and sdist, not just that the CLI can
print help.
Those proof steps should enter their temp repositories directly instead of
relying on indented subshell heredocs that can break shell parsing in GitHub
Actions.
The `publish.yml` workflow follows the provenance side of that same rule:
it should accept a specific successful `CI` run, download the validated
artifact and provenance from that run, verify the recorded `ci_run_id`,
`ci_run_attempt`, `head_sha`, and artifact hashes, and publish without
rebuilding a fresh dist inside publish.

## Managed Environment In CI
CI should bootstrap DevCovenant with a normal Python launcher and then let the
managed-environment contract take over.
Do not hardcode shell activation for one environment type such as a virtual
environment.

That rule keeps CI generic:

1. bootstrap Python installs DevCovenant's own dependencies

2. DevCovenant resolves the configured managed environment for the stage

3. stage commands prepare or reuse that environment through metadata such as
   `expected_paths`, `expected_interpreters`, and `managed_commands`

In this repository, the main `governance` job stays generic and runs the
source-tree contract directly with normal `python -m devcovenant ...`
commands from the checkout.
The repo-specific artifact proof repos intentionally do something narrower:
they bootstrap with the installed wheel, sdist, or `pipx` CLI first, then
create `.venv` inside the proof repo and hand the governed
`gate --start -> gate --mid -> run -> gate --end -> check` path to
`.venv/bin/python -m devcovenant`.
That keeps the source-tree job generic while still proving that the installed
artifact can materialize and use the managed environment contract without
interpreter drift.

## Refresh-Owned Config Normalization
Refresh can clean up stale generated-config defaults when they would otherwise
change runtime behavior accidentally.
One current example is the legacy all-empty `clean.overrides` block: refresh
collapses that stale shape back to `{}` so profile-driven cleanup targets stay
active unless a repository explicitly replaces one cleanup key on purpose.
Another is cleanup protection itself: cleanup targets come from profiles and
config, but the active managed environment and the active clean run directory
are runtime-protected paths resolved separately from those delete lists.
Refresh also keeps generated ownership deterministic across filesystems:
profile and policy discovery are sorted before tracked outputs such as
`registry.yaml` or generated blocks are written, so Linux CI and local macOS
or Windows checkouts do not churn the same generated files in different
orders.

## Operator Checklist
Before you close a slice, confirm:

1. start gate ran successfully
2. mid gate is clean
3. tests ran successfully
4. end gate is clean
5. changelog and docs are in scope where behavior changed
6. the relevant files are staged
