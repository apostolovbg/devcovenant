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
2. Make the necessary edits.
3. Run tests through the DevCovenant test runner.
4. Run the pre-commit end gate.

## Gated Sequence
The default commands are:
```bash
devcovenant gate --start
devcovenant test
devcovenant gate --end
```
The start and end gates record timestamps in the local registry.
When using the fallback launcher (`python3 -m devcovenant ...`) from a source
checkout, setting `PYTHONPYCACHEPREFIX` before Python starts prevents repo-
local `devcovenant/__pycache__/` drift while preserving bytecode generation.

## Test Runner
`devcovenant test` executes `python3 -m unittest discover -v` first, then
pytest, to keep coverage consistent across suites and preserve readable
test names.
The runner records status so policies can verify that tests ran.

## CI Notes
CI pipelines should run the same gates. If a pre-commit hook changes files,
run the tests again before recording the end gate so test results post-date
any auto-fixes.
The generated `governance-and-test` workflow now sets `PYTHONPYCACHEPREFIX`
at the job level so top-level DevCovenant launches and child Python commands
write bytecode caches outside the repo tree.
Build/publish workflows that run `python -m devcovenant ...` should set the
same env var as well (for example `${{ runner.temp }}/devcovenant-pycache`).
