# Troubleshooting
**Last Updated:** 2026-03-15
**Project Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Quick Triage Flow](#quick-triage-flow)
- [Gate Failures](#gate-failures)
- [Changelog Coverage Loops](#changelog-coverage-loops)
- [Registry Drift](#registry-drift)
- [Translator Resolution Errors](#translator-resolution-errors)
- [Config and Metadata Surprises](#config-and-metadata-surprises)
- [Teardown Recovery](#teardown-recovery)
- [Build and Publish Issues](#build-and-publish-issues)
- [Escalation Checklist](#escalation-checklist)

## Overview
This page focuses on high-frequency failure patterns and exact recovery
actions.

Treat troubleshooting as part of normal gate workflow. Most failures are
sequence mistakes, stale generated artifacts, or metadata-shape mismatches.

## Workflow
Use one reproducible loop:
1. ensure you have a valid open session (`gate --start`)
2. reproduce one failure category
3. apply one focused fix
4. run `devcovenant test`
5. run `devcovenant gate --end`
6. if end introduces follow-up changes, rerun until clean

## Quick Triage Flow
1. Confirm start/test/end command order.
2. Read the first blocking failure fully.
3. Identify failing contract:
   - workflow evidence
   - changelog coverage
   - metadata/config
   - profile/translator resolution
   - generated registry drift
4. Fix the root cause before secondary warnings.
5. Re-run test and end gate.

Run-log substrate note:
- `devcovenant/core/runtime/run_logging.py` now defines the shared per-run
  log substrate under `devcovenant/logs/`; root CLI commands now print a
  run-log pointer and write summary artifacts you can inspect before opening
  full stdout/stderr logs.
- In `engine.tests_output_mode: normal`, test status output stays concise and
  flood-prone child output is suppressed; use the printed run-log pointer for
  details.
- Treat the printed `Run logs:` path as the primary debug entrypoint for
  command-run evidence artifacts during DevCovenant failures.
- Inspect run evidence artifacts in order: `summary.txt`, then `tail.txt`
  (if present), then full logs (`stderr.log`/`stdout.log`).
- Avoid ad-hoc output redirects for DevCovenant commands when official run
  artifacts already exist.
- Use `devcovenant gate --status` for lifecycle inspection before rerunning
  gates when you only need current session state or latest run evidence.
- Prefer non-PTY execution for non-interactive DevCovenant commands.
- Prefer low-frequency polling for long-running commands using this cadence:
  `5s`, `15s`, `30s`, `45s`, `60s`, `90s`, `120s`, `150s`, `180s`, `240s`,
  then every `60s`.
- Use that cadence internally, but do not narrate polling steps/cadence in
  routine progress updates unless asked.
- Normal-mode live streaming can be acceptable when concise, but verbose
  streaming can consume significant tokens; prefer summaries/tails/logs
  first.
- Normal-mode live streaming is acceptable for routine progress visibility.
- Reserve verbose streaming for explicit human request, missing official run
  artifacts, or interactive I/O needs.
- Keep operator updates concise during long runs: report what changed, what
  passed/failed, and the next step instead of narrating routine waits.
- Avoid posting polling-by-poll updates unless the human explicitly asks for
  that detail.
- For a quick confidence check before deep troubleshooting, run the 90-second
  evidence ritual from `devcovenant/docs/workflow.md`
  (`devcovenant check` -> `devcovenant test`).

If multiple policies fail, prioritize:
1. malformed config/registry errors
2. workflow evidence errors
3. changelog/documentation coverage
4. quality warnings

## Gate Failures
Typical symptoms:
- no active open session for `gate --end`
- start gate fails due to pre-commit issues
- start gate recovery/reconcile requires an explicit `devcovenant test`
  before retrying `gate --start` (gate commands never run tests internally)
- if recovery start still asks for tests after you already ran them, verify no
  newer test-relevant edits were made after the test run before retrying start
- required test commands reported as missing
- command re-exec messages appear before command body runs
- end gate rerun loop due to hook/test mutation

Recovery actions:
1. if start failed, clear hook violations and rerun start
2. if end says no open session, run start first
3. if required commands mismatch:
   - inspect resolved command metadata: `required_commands`
   - run `devcovenant test` again
4. if managed-environment auto re-exec fails:
   - confirm `expected_interpreters` and `expected_paths` point to the
     intended environment launcher path
   - if a managed interpreter path exists but is not executable, fix
     permissions or path ownership; DevCovenant now reports this explicitly
     instead of raising raw interpreter-exec tracebacks
   - confirm managed bootstrap commands can create the interpreter for
     non-start invocations
   - manual-command guidance expands tokens to concrete paths when
     available; missing values display explicit placeholders like
     `<managed_python>`
   - verify guard-loop errors are not caused by symlink-collapsed
     interpreter paths
5. if end keeps mutating files:
   - inspect which hooks/autofix helpers are changing files
   - rerun until no further mutation or resolve nondeterminism
6. if `devcov-structure-guard` reports repo bytecode artifacts:
   - delete `devcovenant/**/__pycache__/` and `*.py[cod]` files
   - if the artifacts came from source-checkout alternate launcher runs
     (`python3 -m devcovenant ...`), set `PYTHONPYCACHEPREFIX` before Python
     starts (shell/CI env) to prevent future repo-local launcher-process
     bytecode drift
   - DevCovenant does not promise that boundary through repo-root startup
     hooks or an in-package bootstrap helper
   - for repeated local alternate-launcher runs, use a shell wrapper (see
     `devcovenant/docs/installation.md`) that exports
     `PYTHONPYCACHEPREFIX` before invoking `python3 -m devcovenant`
   - keep `engine.pycache_prefix_enabled: true` (and optional
     `engine.pycache_prefix`) in `devcovenant/config.yaml` so DevCovenant-
     managed Python subprocesses also route bytecode caches outside the repo
   - rerun `devcovenant test` and `devcovenant gate --end`

Signal to watch:
- successful end must record closure timestamp and command evidence in
  `devcovenant/registry/runtime/gate_status.json`
- use `devcovenant gate --status` before rerunning gates when you only need to
  inspect session state or the latest relevant run logs

## Changelog Coverage Loops
Typical symptoms:
- "fresh top entry required" errors
- Change/Why/Impact verb validation failures
- Files block missing touched paths

Recovery actions:
1. add one new top changelog entry for current session date
2. keep prior entries intact beneath it
3. include Change/Why/Impact lines with allowed action verbs
4. include exact touched file paths in Files block
5. rerun test and end gate

Common loop causes:
- editing old entries instead of adding fresh top entry
- forgetting autogenerated/touched files (for example synced readme)
- running end gate before tests in the same work slice

## Registry Drift
Typical symptoms:
- integrity guard reports policy/profile registry mismatch
- generated hashes differ from current descriptor/profile content

Recovery actions:
1. run `devcovenant refresh`
2. inspect regenerated files under `devcovenant/registry/runtime/`
3. run `devcovenant test`
4. run `devcovenant gate --end`

If drift persists:
- verify descriptor/profile files are not edited inside managed blocks
- confirm refresh ran from repository root
- confirm no post-refresh tool is rewriting generated artifacts

## Translator Resolution Errors
Typical symptoms:
- no translator can handle a file extension
- multiple translators match one file (ambiguous ownership)
- translator declaration shape is invalid
- translator entrypoint path escapes profile root

Recovery actions:
1. confirm active language profiles in `config.yaml`
2. inspect translator declarations in profile manifests
3. ensure extension ownership is unique per active profile stack
4. validate entrypoint module/callable paths and containment rules
5. rerun tests and end gate

## Config and Metadata Surprises
Typical symptoms:
- refresh rewrites expected manual edits
- resolved metadata does not match intended behavior
- policy appears enabled/disabled unexpectedly

Recovery actions:
1. identify ownership of the affected key:
   - autogen-owned section
   - user-owned section
2. use overlays for additive behavior
3. use overrides for replacement behavior
4. inspect resolved metadata in:
   - AGENTS managed policy block
   - `devcovenant/registry/registry.yaml`
5. verify `policy_state` booleans for activation

Checklist for config edits:
- avoid editing autogen sections directly
- keep YAML types explicit
- rerun refresh after profile/descriptor changes

## Teardown Recovery
Typical symptoms:
- `undeploy` or `uninstall` warns about config parse issues
- local config is malformed and normal refresh/check fails

Recovery actions:
1. run teardown command directly; recovery mode is expected
2. verify managed blocks/registry cleanup happened
3. repair `devcovenant/config.yaml` before re-deploy
4. rerun full gate sequence after remediation

Use `undeploy` for temporary removal of managed outputs.
Use `uninstall` for full tool removal.

## Build and Publish Issues
Typical symptoms:
- package build validation errors
- missing license artifacts in wheel/sdist checks
- governance workflow trigger issues
- publish workflow behavior mismatch

Recovery actions:
1. run local build and `twine check`
2. install produced wheel in a temporary environment and smoke-test CLI
3. verify legal artifacts from packaging contract are present
4. verify governance workflow trigger key is literal `on:`
5. run `devcovenant refresh` if generated workflow drifted

Repository policy:
- publish remains manual (`workflow_dispatch`)
- release-control steps stay human-approved for destructive operations

## Escalation Checklist
Escalate for human review when:
- gate status payload is persistently malformed after refresh/restart
- hooks or tests are nondeterministic across repeated clean reruns
- translator ambiguity cannot be resolved by profile ownership changes
- policy descriptor schema changes are required to proceed

When escalating, include:
1. failing command and exit code
2. first blocking error text
3. current session state (`open` or `closed`)
4. files changed in this slice
