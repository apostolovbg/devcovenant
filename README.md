# Project Name
**Doc ID:** README
**Doc Type:** repo-readme
**Project Version:** 1.0.0
**Last Updated:** 2026-03-13
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
**Read first:** `AGENTS.md` is the canonical source of truth. See
`devcovenant/README.md` for usage and lifecycle workflow details.
<!-- DEVCOV:END -->

DevCovenant is a Repository Governance Framework.
It is an SDLC policy and evidence engine, AI-resilient by design and usable
without AI.
It keeps governance prose, runtime enforcement, and daily workflow behavior
synchronized.

It is built for repositories where process drift causes real cost: regressions
that pass locally, undocumented behavior changes, policy text that no longer
matches checks, and release notes that do not reflect what actually changed.

## Table of Contents
1. [Overview](#overview)
2. [Glossary (Canonical Terms)](#glossary-canonical-terms)
3. [Why DevCovenant](#why-devcovenant)
4. [Quick Start](#quick-start)
5. [Runtime Model](#runtime-model)
6. [Evidence Artifacts](#evidence-artifacts)
7. [Command Surface](#command-surface)
8. [Lifecycle](#lifecycle)
9. [Workflow](#workflow)
10. [Policy Activation and Metadata](#policy-activation-and-metadata)
11. [Profiles and Translators](#profiles-and-translators)
12. [Extension Surfaces](#extension-surfaces)
13. [Docs Map](#docs-map)
14. [License](#license)
<!-- REPO-ONLY:BEGIN -->
Repo-only:
- [Repo Layout](#repo-layout)
- [Dogfooding Notes](#dogfooding-notes)
<!-- REPO-ONLY:END -->

## Overview
DevCovenant treats policy prose as executable contract, not static guidance.
The runtime compiles policy definitions from managed docs, resolves metadata
through profile and config layers, and enforces the result through a required
start -> mid preflight loop -> test -> end gate sequence.

This model gives teams one source of truth for:
- what is required
- where requirements are configured
- how requirements are validated
- what evidence exists for each session

## Glossary (Canonical Terms)
Use this glossary as the canonical source for core DevCovenant nouns in docs,
help text, and plan language. Reuse these terms verbatim in headings and
contract statements when possible.

- `gate session`: a tracked enforcement session with explicit
  `start`/`test`/`end` phases and recorded evidence.
- `check`: the read-only audit command that evaluates policies and produces
  logs/summaries without writing gate lifecycle state.
- `policy`: an executable rule package consisting of descriptor metadata,
  runtime logic, and optional autofix behavior.
- `profile`: a repo-specific adapter that selects and parameterizes policies
  and translators via metadata overlays, assets, and related selectors/hooks.
- `translator`: a language-aware adapter that normalizes source into shared
  internal units consumed by policies.
- `evidence artifact`: a generated runtime artifact used to prove what
  happened (for example gate status, per-run logs, and run summaries).
- `registry`: generated DevCovenant metadata/state stores, including repo-local
  runtime registries under `devcovenant/registry/local/`.
- `installation folder`: the repo-local `devcovenant/` directory installed
  into a repository and used for runtime code, config, docs, and local state.

Synonym discipline:
- Prefer the canonical terms above in headings, help text, and contract docs.
- Casual synonyms are acceptable in explanatory prose only when the canonical
  term appears first or nearby.
- Prefer `gate session` (not just `gate`) when clarifying lifecycle semantics.
- `rule` may be used as a casual synonym for `policy` in explanations, but
  `policy` remains the canonical system noun.

## Why DevCovenant
DevCovenant is opinionated about failure modes that are common in active
repositories:

- process rules become tribal knowledge instead of executable checks
- changelog and documentation coverage become inconsistent
- metadata is scattered and hard to audit
- policy scripts and policy prose drift apart
- teams argue about sequence instead of shipping work

DevCovenant addresses these by making workflow sequence and policy contracts
explicit, generated, and testable.

## Quick Start
Use this flow in a repository where DevCovenant is already available:

```bash
devcovenant install
# edit devcovenant/config.yaml and set install.generic_config: false
devcovenant deploy
devcovenant gate --start
# make your edits
# pre-test mutating preflight; rerun until clean
devcovenant gate --mid
devcovenant test
devcovenant gate --end
```

If the console script is not available on PATH, use:

```bash
python3 -m devcovenant <command>
```

On Windows, a common equivalent is:

```bash
py -m devcovenant <command>
```

Minimum first-pass config review:
1. confirm `profiles.active`
2. confirm `policy_state` enablement choices
3. confirm `engine.fail_threshold`
4. confirm `engine.output_mode` (`verbose`, `normal`, or `quiet`)
5. set `install.generic_config: false` before `deploy`

### See It Work in 90 Seconds
Use this short ritual to prove the evidence model before deeper setup work.
It uses explicit commands (not a hidden demo wrapper) and focuses on stable
cues rather than exact timestamps.

```bash
devcovenant check
devcovenant test
devcovenant gate --status
```

What to look for:
1. `devcovenant check` prints a `Run logs:` pointer and writes
   `summary.txt`/`summary.json` without changing gate session lifecycle state.
2. `devcovenant test` prints a `Run logs:` pointer, records test-command
   evidence, and keeps full command output in the run folder even when console
   output is condensed.
3. `devcovenant gate --status` prints short lifecycle state plus a `Latest
   Relevant Logs:` pointer you can open first for artifact-first triage.

Artifact-first triage order:
1. `summary.txt`
2. `tail.txt` (if present)
3. `stderr.log` / `stdout.log`

If you want the full lifecycle proof (not the 90-second ritual), run the
normal gate sequence:
`devcovenant gate --start` -> `devcovenant gate --mid` loop ->
`devcovenant test` -> `devcovenant gate --end`.

## Runtime Model
Core runtime ownership:
- policy parsing/execution: `devcovenant/core/services/policy_engine.py`
- metadata merge precedence: `devcovenant/core/services/metadata.py`
- profile discovery/merge: `devcovenant/core/services/profile_registry.py`
- translator routing: `devcovenant/core/services/translator_engine.py`
- refresh orchestration: `devcovenant/core/flow/refresh.py`
- gate sequencing/state: `devcovenant/core/flow/gate.py`
- shared command execution: `devcovenant/core/runtime/execution.py`
- shared output policy: `devcovenant/core/runtime/output.py`
- run-artifact logging substrate: `devcovenant/core/runtime/run_logging.py`

Runtime data stores:
- source of policy truth:
  managed policy block in `AGENTS.md`
- generated runtime state:
  `devcovenant/registry/local/*`
- session ledger:
  `devcovenant/registry/local/gate_status.json`

The session ledger tracks gate timestamps, resolved command evidence, and
session baseline metadata used by gate-aware policies.

Canonical core terminology (for example `gate session`, `check`, `policy`,
`profile`, `translator`, and `evidence artifact`) is defined in
`devcovenant/README.md` under `Glossary (Canonical Terms)`.

## Evidence Artifacts
DevCovenant produces evidence artifacts that show what happened during a gate
session or command run. Treat these as the primary proof surfaces for
workflow state, command results, and failure triage.

Runtime-local evidence artifacts (generated, untracked):
- gate session ledger evidence:
  `devcovenant/registry/local/gate_status.json` records gate session state,
  phase timestamps, and command/test evidence used by gate-aware policies.
- command-run evidence folders:
  `devcovenant/logs/<run-id>-<command>/` stores per-run artifacts for top-level
  commands.
- run metadata evidence:
  `run.json` records command identity, argv, timing, and exit status.
- summary evidence:
  `summary.txt` and `summary.json` provide human-readable and machine-readable
  triage summaries.
- output evidence:
  `stdout.log`, `stderr.log`, and `tail.txt` preserve full command output and a
  bounded quick-inspection tail.

Tracked closure-proof references (repository governance docs):
- changelog entries provide per-slice traceability (`Change`/`Why`/`Impact`
  plus file coverage or equivalent references)
- plan/acceptance docs record planned work criteria and closure notes

Artifact usage guidance:
- inspect `summary.txt` first, then `tail.txt`, then full logs
- use `devcovenant gate --status` to inspect lifecycle state without reruns
- treat printed `Run logs:` pointers as the canonical entrypoint to run
  evidence artifacts

## Command Surface
Primary governance commands:
- `devcovenant check`:
  run read-only audit checks (no gate session lifecycle writes)
- `devcovenant gate --start`:
  run pre-commit, open a gate session baseline, and own refresh/autofix
  orchestration
  (honoring `engine.auto_fix_enabled`)
- `devcovenant gate --mid`:
  run a non-lifecycle mid-session pre-commit sweep (mutating hooks/checks may
  apply) to surface complaints before `devcovenant test`
- `devcovenant test`:
  execute resolved `devflow-run-gates.required_commands` and record test
  command evidence for the active gate session
- `devcovenant gate --end`:
  run end hooks, enforce sequence completion, and close the gate session

Lifecycle and maintenance commands:
- `devcovenant install`
- `devcovenant deploy`
- `devcovenant clean`
- `devcovenant refresh`
- `devcovenant upgrade`
- `devcovenant undeploy`
- `devcovenant uninstall`
- `devcovenant update_lock`

Practical usage guidance:
- use `check` for broad audit-only policy validation
- use `gate --mid` as the required pre-test mutating preflight inside an open
  gate session
- use gate commands for mandatory gate-session workflow and mutating checks
- use `devcovenant gate --status` for short read-only gate session inspection
- use `clean` to remove disposable build/cache artifacts after package/build
  validation without touching logs, local registry evidence, or `.venv`
- use `refresh` when descriptors/profiles/templates change
- use `update_lock` when dependency inputs changed and license artifacts must
  be reconciled

## Lifecycle
DevCovenant separates installation from activation intentionally.

Lifecycle contract:
- `install`:
  copy package files and seed generic config stub
- `deploy`:
  require explicit non-generic config, then materialize managed outputs
- `clean`:
  remove disposable build/cache artifacts from resolved profile/config targets
- `refresh`:
  regenerate registries, managed blocks, and generated governance files
- `upgrade`:
  reconcile core from source on every run, then refresh
- `undeploy`:
  remove managed artifacts while keeping core/config
- `uninstall`:
  remove DevCovenant footprint from the repository

Generated artifacts owned by refresh include:
- `devcovenant/registry/local/policy_registry.yaml`
- `devcovenant/registry/local/profile_registry.yaml`
- `devcovenant/registry/local/manifest.json`
- managed policy block in `AGENTS.md`
- generated sections in `devcovenant/config.yaml`
- `.pre-commit-config.yaml`
- `.gitignore`
- `.github/workflows/governance-and-test.yml`

## Workflow
Required edit cycle:

1. `devcovenant gate --start`
2. clear start-gate complaints before editing
3. apply edits
4. if complaints appear, clear them before continuing
5. `devcovenant gate --mid` pre-test sweep (rerun until clean)
6. `devcovenant test`
7. `devcovenant gate --end`

Important execution semantics:
- start gate must pass before a valid baseline is recorded
- start gate cannot open a new session while one is already open
- mid gate requires an open session, may mutate files, and does not write
  gate lifecycle state
- end gate may require explicit operator reruns (`test`, then `gate --end`)
  until tree state is clean
- end gate records closure only on success
- when `managed-environment` is active, CLI commands invoked from a
  non-managed interpreter are automatically re-executed in the managed
  interpreter when local managed-environment runtime is present; lifecycle
  bootstrap/teardown commands (`install`, `deploy`, `undeploy`, `uninstall`)
  are intentionally excluded
- if a resolved managed interpreter path is present but not executable,
  DevCovenant emits an explicit managed-environment error instead of crashing
  and then uses `managed_rerun_commands` when a wrapper fallback is configured
- if direct managed interpreter resolution is unavailable, configured
  `managed_rerun_commands` can rerun the command through wrapper adapters
  (for example bench/xenv launchers)
- if edits happened after previous end gate, start gate can open a recovery
  gate session and validate that unsessioned delta before baseline rewrite

`devcovenant test` executes the resolved required command chain in declared
order. In `engine.tests_output_mode: normal`, test progress stays concise with
deterministic `[n/total] <command>` markers, optional
`Please wait. In progress...` heartbeat messages during long silent waits,
and full command output preserved in evidence artifacts under run logs.

## Policy Activation and Metadata
Activation and behavior are separate concepts:
- activation:
  `devcovenant/config.yaml -> policy_state`
  (with `severity: critical` policies remaining enforced)
- behavior:
  resolved metadata from descriptor/profile/config layers

Metadata resolution order:
1. descriptor defaults
2. active profile overlays
3. autogen metadata overlays
4. user metadata overlays
5. autogen metadata overrides
6. user metadata overrides
7. policy activation application from `policy_state`

Ownership model:
- profiles:
  reusable stack/layout defaults
- user config layers:
  repository-specific deltas
- policy descriptor:
  schema/contract keys and minimal defaults

Refresh materializes a full alphabetical `policy_state` map, preserves user
booleans, seeds new policy IDs, and removes stale IDs. Critical-severity
policies can still appear as `false` in `policy_state`, but runtime
enforcement ignores that disable toggle and emits an explicit diagnostic.

## Profiles and Translators
Profiles contribute metadata overlays, cleanup overlays, selectors, assets,
and hook fragments.
Profiles do not activate policies.

Language profiles may also declare translators and test-event adapters:
- translators:
  convert language-specific files into normalized units for policy code
- test-event adapters:
  emit normalized test lifecycle events for gate-session evidence

Framework/ops/tooling profiles can still contribute policy metadata, including
`devflow-run-gates.required_commands`, but translator ownership remains a
language-profile responsibility.

## Extension Surfaces
Extension paths:
- custom policies:
  `devcovenant/custom/policies/<policy-id>/`
- custom profiles:
  `devcovenant/custom/profiles/<profile-name>/`

Extension guidance:
1. keep descriptor defaults minimal and type-safe
2. move stack-dependent operational values into profiles
3. use config overlays/overrides only for repository deltas
4. update docs and tests in the same work slice as runtime behavior changes
5. keep managed-block boundaries intact (`<!-- DEVCOV* -->`)

## Docs Map
This README is the canonical docs entrypoint for the packaged documentation
set.

### Documentation Tiers
- universal/package docs:
  `devcovenant/README.md` and `devcovenant/docs/*.md` (install/use/runtime
  behavior)
- repo-internal governance docs (source checkout only):
  `AGENTS.md`, `PLAN.md`, `POLICY_MAP.md`, and `PROFILE_MAP.md`
- runtime evidence artifacts (generated, untracked):
  `devcovenant/logs/*` and `devcovenant/registry/local/*`

### Start Here
- [What It Is](#overview):
  category identity, glossary, runtime model, and evidence artifacts
- [Install and Run](#quick-start):
  first command sequence, lifecycle contract, and workflow expectations
- [See It Work in 90 Seconds](#see-it-work-in-90-seconds):
  quick evidence ritual using `check`, `test`, and `gate --status`
- [Adapt and Customize](#profiles-and-translators):
  profiles, translators, extension surfaces, and deeper policy docs

Detailed package docs under `devcovenant/docs/`:
- `installation.md`:
  install/deploy/upgrade/teardown lifecycle runbooks
- `workflow.md`:
  gate contract, session semantics, and the canonical 90-second evidence ritual
- `config.md`:
  ownership model and metadata merge rules
- `profiles.md`:
  profile metadata, assets, hooks, and translator ownership
- `policies.md`:
  descriptor/runtime contracts and deep policy behavior
- `translators.md`:
  translator declaration, resolution, and failure patterns
- `registry.md`:
  generated registry contracts and evidence files
- `refresh.md`:
  deterministic regeneration behavior and outputs
- `troubleshooting.md`:
  failure signatures and recovery runbooks

Local architecture READMEs (source checkout):
- `devcovenant/core/README.md`
- `devcovenant/builtin/policies/README.md`
- `devcovenant/builtin/profiles/README.md`
- `devcovenant/custom/README.md`
- `devcovenant/custom/policies/README.md`
- `devcovenant/custom/profiles/README.md`
- `devcovenant/registry/README.md`

Suggested reading paths:
- operators:
  `README.md` -> `devcovenant/docs/workflow.md` ->
  `devcovenant/docs/troubleshooting.md`
- policy/profile authors:
  `devcovenant/docs/policies.md` -> `devcovenant/docs/profiles.md` ->
  `devcovenant/docs/translators.md`
- release owners:
  `devcovenant/docs/installation.md` -> `devcovenant/docs/refresh.md` ->
  `devcovenant/docs/registry.md`

<!-- REPO-ONLY:BEGIN -->
## Repo Layout
Source-checkout-only governance docs:
- `AGENTS.md`:
  canonical policy source for this repository
- `SPEC.md`:
  specification-layer usage guide
- `PLAN.md`:
  execution backlog and delivery tracking
- `POLICY_MAP.md`:
  policy inventory and metadata families
- `PROFILE_MAP.md`:
  profile inventory and translator ownership summary
- `.github/workflows/governance-and-test.yml`:
  refresh-generated governance gate pipeline (tracked in this repository)
- `.github/workflows/build.yml`:
  repository-maintained build validation after successful governance run
- `.github/workflows/publish.yml`:
  repository-maintained manual release publication workflow
- `devcovenant/`:
  CLI scripts and core runtime modules
- `tests/devcovenant/`:
  mirrored runtime and policy tests

## Dogfooding Notes
This repository is governed by the same start/test/end contract it ships.
Behavior changes are expected to update runtime code, docs, and tests in one
slice so policy prose and enforcement do not diverge.
<!-- REPO-ONLY:END -->

## License
This project is released under the MIT License.
