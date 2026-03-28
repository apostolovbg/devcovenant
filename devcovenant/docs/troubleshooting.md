# Troubleshooting
**Last Updated:** 2026-03-28
**Project Version:** 1.0.0

## Overview
Use this guide when DevCovenant is blocking work and you need the fastest clean
way back to a stable state.

The normal debug order is:

1. read the command's `summary.txt`
2. inspect `tail.txt` if present
3. inspect `stdout.log` and `stderr.log`
4. rerun the right command, not a random louder one

## Fast Triage
Ask these questions first:

1. was this a read-only audit or an active gate session?
2. which command failed?
3. did a gate stage mutate files?
4. is the problem in config, metadata, generated state, or tests?

## Gate Failures
If `gate --start` fails, clear the reported problem before editing.
A failed start gate is not a usable baseline.

If `gate --mid` fails, clear the issue and rerun `gate --mid` until it is
clean before running `test`.

If `gate --end` fails, inspect the latest run logs, rerun `test` if required,
and then rerun `gate --end`.

## Changelog Coverage Problems
The two common causes are:

- the latest entry does not reflect the current slice

- the summary lines do not use accepted action verbs

When that happens, fix the top entry instead of adding noise below it.

## Registry Drift
If the tracked registry looks stale or inconsistent, run `devcovenant refresh`
or the normal gate workflow.
If the problem persists, inspect the owning profile, config, or descriptor
instead of hand-editing the registry.

## Config And Metadata Problems
If behavior looks wrong, inspect these in order:

1. `devcovenant/config.yaml`
2. active profile descriptors and overlays
3. the tracked registry
4. `AGENTS.md` generated policy and invariant output

Most "runtime mystery" problems are really metadata-resolution problems.

## Managed Environment Problems
If the managed interpreter exists but is not executable, DevCovenant stops with
an explicit error.
Fix the interpreter path or permissions, then rerun the appropriate command.

## Installed CLI Problems
If you installed DevCovenant with `pipx` and the `devcovenant` command is
missing, check the machine install first instead of debugging repository
config:

1. run `pipx list`
2. run `pipx ensurepath`
3. open a new shell and rerun `devcovenant --version`

If you are in a source checkout, do not confuse that machine install with the
repo-managed environment.
Use `python3 -m devcovenant ...` when the checkout does not expose the console
script directly.

## Translator And Profile Problems
If a language-specific policy path seems wrong, verify that the active language
profile owns the relevant translator and that no overlapping profile is trying
to claim the same extension ambiguously.

## Build And Publish Problems
When build or publish assurance fails, check:

- workflow logs

- scanner output

- package metadata

- SBOM and artifact generation steps

Then fix the owning surface instead of papering over the symptom in CI.
