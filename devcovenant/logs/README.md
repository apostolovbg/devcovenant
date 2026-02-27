# Run Logs
**Last Updated:** 2026-02-25
**Version:** 1.0.0

## Overview
This directory is the canonical runtime log root for DevCovenant command runs.
Per-run folders are local execution artifacts used for debugging and audit
triage. They are repository runtime state, not source-of-truth docs.

## Layout
Planned per-run folders contain stable artifacts such as:
- `run.json`
- `summary.txt`
- `summary.json`
- `stdout.log`
- `stderr.log`
- `tail.txt`

The file `latest.json` is a lightweight pointer to the most recent run folder.

## Workflow
Read summaries first, then open targeted log slices only when deeper detail is
needed. Treat generated log contents as local state. Commit only tracked docs
in this directory. The shared `run_logging` runtime allocates and updates these
artifacts for command runs.
