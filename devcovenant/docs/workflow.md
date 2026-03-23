# Workflow
**Last Updated:** 2026-03-22
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
devcovenant test
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
matter most right now.

### gate --start
Opens the tracked work session.
It runs the start pre-commit pass and records the baseline the later checks use
for change-scoped behavior.

### gate --mid
Required pre-test preflight.
It is where hook mutations and DevCovenant autofixes must surface before test
results are recorded.

### test
Runs the configured test command chain and records evidence for it.
In this repo that is the two-run `unittest` plus `pytest` sequence.

### gate --end
Runs the closing pre-commit pass and records closure state.

## Why gate --mid Exists
`gate --mid` is what keeps test evidence honest.
Without it, a pre-commit hook or DevCovenant autofix could change files after
the last meaningful pre-test check and before the recorded test results.

That is why the practical rule is: run `gate --mid` before tests.
Think of the sequence as `gate --start -> gate --mid loop (rerun until clean)`
before `test` and `gate --end`. If `gate --mid` changes files or reports
blocking problems, clear them and run it again before tests.

## Standard Sequence
Use this exact order for ordinary repository work:

1. `devcovenant gate --start`
2. make the change
3. `devcovenant gate --mid`
4. rerun `gate --mid` if it changed files or reported blocking complaints
5. `devcovenant test`
6. `devcovenant gate --end`

If the console script is unavailable, use `python3 -m devcovenant ...`.
On Windows, `py -m devcovenant ...` is the common equivalent form.

## Read-Only Audit Path
If you are investigating without making a governed edit, use:

```bash
devcovenant check
devcovenant gate --status
```

That gives you the current policy result plus the latest session state without
opening a new slice.

## Run Artifact Contract
Every command run writes evidence artifacts.
When you see `Run logs: ...`, inspect them in this order:

1. `summary.txt`
2. `tail.txt` if present
3. `stdout.log` and `stderr.log`

This is the fastest way to understand a failure without rerunning commands in a
noisier mode.

## Recovery Rules
### Start gate failed
Clear the reported problem first.
Do not treat a failed start gate as a usable baseline.

### Mid gate changed files
Run `gate --mid` again until it stops introducing new blocking state.
Then run `test`.

### End gate reported new changes
Inspect the latest run logs, clear the problem, rerun `test` if required, and
rerun `gate --end`.

### Managed environment error
If the resolved managed interpreter path exists but is not executable,
DevCovenant stops explicitly.
Fix the path or permissions and rerun the appropriate command.

## Output Modes
`engine.output_mode` controls normal command output.
`engine.tests_output_mode` controls test command output.

In `normal` test mode, DevCovenant keeps console progress concise and leaves
full child output in the run logs.
That is why the log artifacts matter.

## CI Mapping
The generated CI workflow lives at
`.github/workflows/governance-and-test.yml`.
Its visible workflow name is `CI and Tests`.

The ownership split matters:

1. the builtin `global` profile owns the generic base workflow

2. active profiles may contribute `governance_and_test` fragments that add
   repo-family jobs or steps

3. local `config.governance_and_test.*` keys are for repo-local overlays or,
   rarely, a full local replacement

The global base should stay language-agnostic.
If a repository family needs extra CI proof, such as a supported-language
compatibility matrix or assurance scanners, that extra job should come from
the relevant profile instead of from the generic global template.

This repository also keeps `build.yml` and `publish.yml` as repo-maintained
release workflows.
They consume the result of `CI and Tests`, but they are not part of the
generated governance workflow itself.

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

In this repository, repo-specific CI jobs prime the managed environment with
`python -m devcovenant gate --status > /dev/null` before running their focused
checks.
The important part is not the exact command.
The important part is that CI exercises the managed-environment contract
generically, so a different environment type such as a bench can work through
the same metadata-driven path.

## Operator Checklist
Before you close a slice, confirm:

1. start gate ran successfully
2. mid gate is clean
3. tests ran successfully
4. end gate is clean
5. changelog and docs are in scope where behavior changed
6. the relevant files are staged
