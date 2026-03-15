# Workflow

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Gated Sequence](#gated-sequence)
- [Test Runner](#test-runner)
- [CI Notes](#ci-notes)

## Overview
DevCovenant enforces a fixed development workflow to keep policy checks,
tests, and pre-commit hooks aligned. The gate sequence is mandatory for
any change, including documentation-only edits.

## Workflow
1. Run the pre-commit start gate.
2. Make the necessary edits and clear blocking complaints.
3. Run the required pre-test mid gate (`gate --mid`) until clean.
4. Run tests through the DevCovenant test runner.
5. Run the pre-commit end gate.

## Gated Sequence
The default commands are:
```bash
devcovenant gate --start
# required pre-test mutating preflight; rerun until clean
devcovenant gate --mid
devcovenant test
devcovenant gate --end
```
Start and end gates record lifecycle state in the local registry.
`gate --mid` is non-lifecycle and exists to surface hook/runtime mutations
before test evidence is recorded.
When using the supported alternate launcher (`python3 -m devcovenant ...`)
from a source checkout, setting `PYTHONPYCACHEPREFIX` before Python starts
prevents repo-local `devcovenant/__pycache__/` drift while preserving
bytecode generation. DevCovenant does not rely on repo-root startup hooks or
in-package bootstrap tricks for that boundary.

## Test Runner
`devcovenant test` executes `python3 -m unittest discover -v` first, then
pytest, to keep coverage consistent across suites and preserve readable
test names. The runner records status so policies can verify that tests ran.
In normal mode, concise progress markers are printed while full output remains
available in run logs.
Unhandled command exceptions are normalized to explicit user-facing errors;
run logs keep full traceback detail for diagnostics.

## CI Notes
CI pipelines should run the same gates. If a pre-commit hook changes files,
rerun `gate --mid` and tests before recording the end gate so test results
post-date any hook or autofix mutations.
When managed-environment is enabled and a resolved managed interpreter path is
not executable, DevCovenant emits an explicit managed-environment error and
stops so the interpreter path or permissions can be fixed directly.
The generated `governance-and-test` workflow now sets `PYTHONPYCACHEPREFIX`
at the job level so top-level DevCovenant launches and child Python commands
write bytecode caches outside the repo tree.
Build/publish workflows that run `python -m devcovenant ...` should set the
same env var as well (for example `${{ runner.temp }}/devcovenant-pycache`).
