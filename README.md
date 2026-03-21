# Project Name
**Doc ID:** README
**Doc Type:** repo-readme
**Project Version:** 1.0.0
**Last Updated:** 2026-03-21
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->

<!-- DEVCOV:END -->

DevCovenant is a Repository Governance Framework.
It is an SDLC (software development lifecycle) policy and evidence engine,
AI (artificial intelligence)-resilient by design and usable without AI.
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
5. [Project Governance](#project-governance)
6. [Runtime Model](#runtime-model)
7. [Evidence Artifacts](#evidence-artifacts)
8. [Command Surface](#command-surface)
9. [Lifecycle](#lifecycle)
10. [Workflow](#workflow)
11. [Policy Activation and Metadata](#policy-activation-and-metadata)
12. [Profiles and Translators](#profiles-and-translators)
13. [Extension Surfaces](#extension-surfaces)
14. [Docs Map](#docs-map)
15. [License](#license)
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

How to read this README:
- for a quick explanation of what DevCovenant does in a repository, start
  with `Why DevCovenant` and `Quick Start`
- for first-time integration, read `Quick Start`, `Lifecycle`, and
  `Workflow`
- for the configuration model behind the behavior, read
  `Project Governance`, `Policy Activation and Metadata`, and
  `Profiles and Translators`

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
  runtime registries under `devcovenant/registry/runtime/`.
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

That makes it useful in two different ways at the same time:
- as an operator tool, it tells you what to run and what to fix next
- as an explanatory tool, it exposes why the workflow exists instead of
  hiding it behind wrapper magic

## Quick Start
Use this flow in a repository where DevCovenant is already available:

```bash
devcovenant install
# review devcovenant/config.yaml
# confirm developer_mode
# set install.config_reviewed: true
devcovenant deploy
devcovenant gate --start
# make your edits
# pre-test mutating preflight; rerun until clean
devcovenant gate --mid
devcovenant test
devcovenant gate --end
```

What each step means:
- `install` puts the DevCovenant runtime and a review-required
  `devcovenant/config.yaml` into the repo
- your config review decides how this repo should use DevCovenant
- `deploy` activates that reviewed config by generating managed docs,
  registries, and other governed files
- the first full gate cycle proves that the activated baseline is actually
  clean and usable

`install.config_reviewed` is the human review checkpoint for first-time
integration.
It is not a hidden runtime flag or a cache key.
It simply means "a human has reviewed this config and is ready to let deploy
activate it."

If the console script is not available on PATH, use the
CLI (command-line interface) module entry form:

```bash
python3 -m devcovenant <command>
```

For source-checkout launches, zero repo-local launcher-process bytecode
control belongs to shell or CI (continuous integration)
`PYTHONPYCACHEPREFIX`, not to an in-package bootstrap hook.

On Windows, a common equivalent is:

```bash
py -m devcovenant <command>
```

Minimum first-pass config review:
1. confirm whether this repo is a normal repo using DevCovenant or a repo
   used to develop DevCovenant itself
2. set `developer_mode` accordingly
3. confirm `profiles.active`
4. confirm `policy_state` enablement choices
5. confirm `engine.fail_threshold`
6. confirm `engine.output_mode` (`verbose`, `normal`, or `quiet`)
7. set `install.config_reviewed: true` before `deploy`

Common starting situations:
1. Empty repo:
   `install` adds DevCovenant and the review-required config, then `deploy`
   creates the initial managed docs and generated governance files.
2. Repo seeded with `SPEC.md` and optionally `README.md`:
   put those docs in the repo before `install`; if they are compatible
   DevCovenant-shaped docs, the first `deploy` adopts them and upgrades their
   managed regions while preserving their authored body.
3. Existing repo with real files:
   `install` leaves the repo's ordinary files alone and `deploy` adds
   DevCovenant around them using the managed-doc preservation rules.

For a more detailed integration view:
- use `devcovenant/docs/installation.md` for the full first-time runbook
- use `devcovenant/docs/config.md` for the practical review model behind
  `devcovenant/config.yaml`
- use `devcovenant/docs/workflow.md` for the reasoning behind the gate
  sequence, not only the command order

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

## Project Governance
`project-governance` is the repo-owned lifecycle contract for the project
itself.
It lives directly in `devcovenant/config.yaml`, not in the generated AGENTS
policy block.

It governs:
- `stage`
- `development_stance`
- `versioning_mode`
- optional `codename`
- optional `build_identity`
- the displayed unversioned label and unreleased changelog heading

This service is orthogonal to `version-governance`:
- `project-governance` describes the project's lifecycle posture
- `version-governance` validates actual version format/progression rules

That lets a repo be:
- versioned and stable
- versioned and experimental
- intentionally unversioned while still fully governed

Resolved project-governance state surfaces in:
- `devcovenant/config.yaml`
- `devcovenant/registry/registry.yaml`
- the dedicated `Project Governance` section in `AGENTS.md`
- headers in `AGENTS.md`, `SPEC.md`, `PLAN.md`, and `CHANGELOG.md`

For the detailed field contract, rendering surfaces, and changelog behavior,
see `devcovenant/docs/project_governance.md`.

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
  `devcovenant/registry/runtime/*`
- session ledger:
  `devcovenant/registry/runtime/gate_status.json`
- session snapshot companion:
  `devcovenant/registry/runtime/session_snapshot.json`

The session ledger stays concise and readable. Heavy session baseline,
snapshot, and test-event payloads live in the companion session snapshot file.

Canonical core terminology (for example `gate session`, `check`, `policy`,
`profile`, `translator`, and `evidence artifact`) is defined in
`devcovenant/README.md` under `Glossary (Canonical Terms)`.

## Evidence Artifacts
DevCovenant produces evidence artifacts that show what happened during a gate
session or command run. Treat these as the primary proof surfaces for
workflow state, command results, and failure triage.

Runtime-local evidence artifacts (generated, untracked):
- gate session ledger evidence:
  `devcovenant/registry/runtime/gate_status.json` records concise gate session
  state, phase timestamps, and pointer metadata for heavy session artifacts.
- gate session snapshot evidence:
  `devcovenant/registry/runtime/session_snapshot.json` records heavy baseline,
  snapshot, exemption, and test-event payloads used by gate-aware policies.
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
  evidence artifacts; `uninstall` is the one exception because it removes the
  installation folder that normally stores run logs

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
- `devcovenant clean --all|--build|--cache|--registry|--logs`
  run cleanup only when no gate session is open; close the gate first
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
  validation, including unpacked release trees like `<project>-<version>/`,
  without touching logs, runtime registry state, or `.venv`
- use `refresh` when descriptors/profiles/templates change
- use `update_lock` when dependency inputs changed and license artifacts must
  be reconciled

## Lifecycle
DevCovenant separates installation from activation intentionally.

Think about the boundary like this:
- `install` is setup
- config review is the human decision point
- `deploy` is activation
- the first `gate --start` -> `gate --mid` -> `test` -> `gate --end` cycle
  is the proof that activation succeeded

Lifecycle contract:
- `install`:
  copy package files, seed a review-required config baseline, and seed tracked
  registry
  structure without shipping repo-generated registry/log runtime payloads
- `install` does not activate managed docs yet; it stops and waits for config
  review
- `deploy`:
  require completed config review, then materialize managed outputs
- `deploy` is the first point where the repo becomes actively governed by the
  reviewed config
- `clean`:
  remove disposable build/cache/runtime-registry/log artifacts from resolved
  profile/config targets while keeping tracked registry/log README files
  protected
- `refresh`:
  regenerate the tracked registry, managed blocks, and generated governance
  files; recreate `devcovenant/registry/registry.yaml` when missing without
  inventing runtime state
- `upgrade`:
  reconcile core from source on every run, preserve runtime registry/log state
  plus config, then refresh the tracked registry
- `undeploy`:
  remove managed artifacts while keeping core/config
- `uninstall`:
  remove DevCovenant footprint from the repository; this command does not
  leave a durable run-log folder because it removes `devcovenant/`

Generated artifacts owned by refresh include:
- `devcovenant/registry/registry.yaml` policy inventory and hash data
- `devcovenant/registry/registry.yaml` profile inventory and active-profile
  state
- `devcovenant/registry/registry.yaml` tracked structural inventory used by
  integrity checks
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
  DevCovenant emits an explicit managed-environment error and stops so the
  interpreter path or permissions can be fixed directly
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
  emit normalized test lifecycle events for gate-session evidence only when
  the active profile stack declares them explicitly

Framework/ops/tooling profiles can still contribute policy metadata, including
`devflow-run-gates.required_commands`, but translator ownership remains a
language-profile responsibility. DevCovenant does not keep a hidden generic
test-event adapter path: unmatched test commands are skipped unless a profile
declares `generic_test_event_adapter_factory` on purpose.

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

Managed-doc extension note:
- custom profiles may also ship managed-doc descriptors under their
  `assets/` tree; add the target doc path to `doc_assets.autogen` to turn
  that custom managed doc on for one repo
- remove a builtin doc from `doc_assets.autogen` to turn that managed doc
  off for one repo; `AGENTS.md` stays mandatory

## Docs Map
This README is the canonical docs entrypoint for the packaged documentation
set.
In this repository, `README.md` is the authored source and
`devcovenant/README.md` is the synced packaged guide with repo-only sections
removed.

### Documentation Tiers
- universal/package docs:
  `devcovenant/README.md` and `devcovenant/docs/*.md` (install/use/runtime
  behavior)
- repo-internal governance docs (source checkout only):
  `AGENTS.md`, `PLAN.md`, `POLICY_MAP.md`, and `PROFILE_MAP.md`
- runtime evidence artifacts (generated, untracked):
  `devcovenant/logs/*` and `devcovenant/registry/runtime/*`

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
- `project_governance.md`:
  lifecycle metadata contract, rendering surfaces, and unversioned/versioned
  behavior
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
This project is released under the
MIT (Massachusetts Institute of Technology) License.
