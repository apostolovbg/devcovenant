# Privacy and Data Handling
**Doc ID:** PRIVACY
**Doc Type:** privacy-policy
**Project Version:** 1.0.1b4
**Last Updated:** 2026-04-16
**DevCovenant Version:** 1.0.1b4

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use this document for repository-specific privacy and local
data-handling notes.
<!-- DEVCOV:END -->

## Table of Contents
- [Overview](#overview)
- [What DevCovenant Stores Locally](#what-devcovenant-stores-locally)
- [What Run Logs Contain](#what-run-logs-contain)
- [What Session Snapshots Contain](#what-session-snapshots-contain)
- [What DevCovenant Does Not Do](#what-devcovenant-does-not-do)
- [Cleanup And Retention](#cleanup-and-retention)
- [Workflow](#workflow)
- [Before Sharing Artifacts](#before-sharing-artifacts)

## Overview
DevCovenant is designed as a repository-local governance tool.
It records local evidence artifacts so operators can understand what happened
in a work slice, but it does not contain outbound telemetry or analytics in
its own runtime.

This document explains what DevCovenant stores locally, what those artifacts
mean, and what still requires operator judgment before sharing logs.

## What DevCovenant Stores Locally
DevCovenant stores local runtime evidence in two main places:
- `devcovenant/logs/<run-id>/`
- `devcovenant/registry/runtime/`

Typical local artifacts include:
- `run.json`
- `summary.txt`
- `summary.json`
- `stdout.log`
- `stderr.log`
- `tail.txt`
- `gate_status.json`
- `session_snapshot.json`
- `latest.json`

These artifacts exist to explain command results, gate state, and session
scope.
They are local evidence artifacts, not a telemetry stream.

## What Run Logs Contain
`run.json` stores structured run metadata such as:
- command name
- start and finish timestamps
- current working directory and repository root
- interpreter provenance
- repo-relative artifact paths
- sanitized command arguments and sanitized run metadata when a field looks
  like it carries a secret

`stdout.log`, `stderr.log`, and `tail.txt` are different:
- they preserve command output as emitted
- they are not content-aware secret scrubbers
- if a child tool prints a secret, that printed value will appear in the log

That distinction matters:
- structured metadata gets obvious secret-like values redacted
- raw command output stays faithful to what the command emitted

## What Session Snapshots Contain
`devcovenant/registry/runtime/session_snapshot.json` stores gate-session
scope evidence such as:
- path and hash baselines
- session start/end snapshots
- test event payloads
- document-exemption baselines

These snapshots are path-and-hash style evidence artifacts.
They are not meant to store full source-file contents.

## What DevCovenant Does Not Do
DevCovenant itself does not:
- send analytics or usage telemetry to a remote service
- upload your repository contents as part of normal command execution
- turn local run logs into a remote monitoring feed

Important boundary:
- DevCovenant can run external tools you configure or invoke, such as
  dependency resolvers, test commands, or pre-commit hooks
- those tools may have their own network or data-handling behavior
- this document describes DevCovenant's own runtime behavior, not every child
  tool you choose to run through it

## Cleanup And Retention
You control cleanup and retention.
Useful commands include:
- `devcovenant clean --logs`
- `devcovenant clean --registry`
- `devcovenant clean --all`

Retention for run-log folders is also controlled through
`devcovenant/config.yaml -> engine.logs_keep_last`.

Tracked governance data in `devcovenant/registry/registry.yaml` is different
from disposable runtime evidence under `devcovenant/registry/runtime/`.
Do not treat those two surfaces as the same thing.

## Workflow
Use this document during ordinary operations like this:
- read it before sharing `summary.txt`, `tail.txt`, `stdout.log`,
  `stderr.log`, or `session_snapshot.json` outside the local repo
- use it with `SECURITY.md` when a report is security-sensitive and still
  needs reproduction evidence
- use it with `SUPPORT.md` when you are preparing a normal help request and
  want to know which artifacts are safe and useful to send

## Before Sharing Artifacts
Before sending artifacts to another person:
- review `summary.txt` first
- inspect `stdout.log` and `stderr.log` for printed secrets or private paths
- remove or redact private repository details when they are not needed for the
  report
- prefer sharing the smallest artifact set that still reproduces the issue

For support requests, start with `summary.txt`, `tail.txt`, and the exact
command you ran.
