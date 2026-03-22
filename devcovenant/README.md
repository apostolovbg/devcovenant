# DevCovenant
**Doc ID:** README
**Doc Type:** repo-readme
**Project Version:** 1.0.0
**Last Updated:** 2026-03-22
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->

<!-- DEVCOV:END -->

![DevCovenant banner](https://raw.githubusercontent.com/apostolovbg/devcovenant/main/devcovenant/docs/banner.png)

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
14. [Security, Privacy, and Support](#security-privacy-and-support)
15. [Docs Map](#docs-map)
16. [License](#license)

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
4. confirm `core_invariants` metadata such as required test commands
5. confirm `policy_state` enablement choices
6. confirm `engine.fail_threshold`
7. confirm `engine.output_mode` (`verbose`, `normal`, or `quiet`)
8. set `install.config_reviewed: true` before `deploy`

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
Use this section for fast orientation only.
Primary detailed homes:
- `devcovenant/docs/workflow.md`:
  gate/session behavior, command sequence, and evidence flow in use
- `devcovenant/docs/installation.md`:
  lifecycle commands and first integration boundaries
- `devcovenant/docs/config.md`:
  runtime control surface and ownership model
- `devcovenant/docs/architecture.md`:
  layered runtime/service boundaries and stable architecture contracts
- `devcovenant/docs/registry.md`:
  tracked versus runtime registry surfaces

Fast ownership map:
- policy parsing/execution: `devcovenant/core/services/policy_engine.py`
- metadata merge precedence: `devcovenant/core/services/metadata.py`
- profile discovery/merge: `devcovenant/core/services/profile_registry.py`
- translator routing: `devcovenant/core/services/translator_engine.py`
- refresh orchestration: `devcovenant/core/flow/refresh.py`
- gate sequencing/state: `devcovenant/core/flow/gate.py`
- shared command execution: `devcovenant/core/runtime/execution.py`
- shared output policy: `devcovenant/core/runtime/output.py`
- run-artifact logging substrate: `devcovenant/core/runtime/run_logging.py`

## Evidence Artifacts
DevCovenant writes explicit proof surfaces for command runs and gate
sessions.

Main artifact families:
- concise gate session ledger:
  `devcovenant/registry/runtime/gate_status.json`
- heavy gate session snapshot:
  `devcovenant/registry/runtime/session_snapshot.json`
- per-command run folders:
  `devcovenant/logs/<run-id>-<command>/`
- tracked closure references:
  `CHANGELOG.md` and `PLAN.md`

Artifact-first triage order:
1. `summary.txt`
2. `tail.txt`
3. `stderr.log` / `stdout.log`

Primary detailed homes:
- `devcovenant/docs/workflow.md` for command/gate evidence in sequence
- `devcovenant/docs/registry.md` for tracked versus runtime registry meaning
- `devcovenant/docs/troubleshooting.md` for recovery use

## Command Surface
Command families:
- audit and gate sequence:
  `check`, `gate --start`, `gate --mid`, `test`, `gate --end`,
  `gate --status`
- lifecycle and maintenance:
  `install`, `deploy`, `refresh`, `upgrade`, `clean`, `undeploy`,
  `uninstall`, `policy`

Operational note:
- `devcovenant policy dependency-management refresh-all` is the canonical
  dependency-maintenance command surface.
- `devcovenant update_lock` remains a compatibility alias for that one
  dependency-management command.

Primary detailed homes:
- `devcovenant/docs/workflow.md` for `check`, gate commands, and `test`
- `devcovenant/docs/installation.md` for lifecycle commands
- `devcovenant/docs/refresh.md` for refresh-owned regeneration

## Lifecycle
Keep the lifecycle boundary simple:
- `install` is setup
- config review is the human decision point
- `deploy` is activation
- the first full gate cycle proves that activation is usable

For the exact lifecycle contract, scenarios, and command-by-command behavior,
use `devcovenant/docs/installation.md`.
For refresh-owned outputs, use `devcovenant/docs/refresh.md`.

## Workflow
Canonical sequence:
1. `devcovenant gate --start`
2. edit and clear complaints while working
3. `devcovenant gate --mid` until clean
4. `devcovenant test`
5. `devcovenant gate --end`

This README keeps the short operator view.
For the exact workflow contract, recovery rules, session model, and command
semantics, use `devcovenant/docs/workflow.md`.
In `engine.tests_output_mode: normal`, test progress stays concise while full
command output remains available in run-log artifacts.

## Policy Activation and Metadata
Short rule:
- `policy_state` decides whether a normal policy is on or off
- `core_invariants` carries metadata for DevCovenant's own non-optional
  runtime contracts
- descriptors, profiles, and config metadata decide how that policy behaves

Primary detailed homes:
- `devcovenant/docs/config.md` for activation authority and ownership
- `devcovenant/docs/policies.md` for descriptor/runtime behavior
- `devcovenant/docs/profiles.md` for metadata origin and overlays

## Profiles and Translators
Profiles describe repo shape; translators describe language-aware conversion
for policy runtime.
Profiles do not activate policies by themselves.

Primary detailed homes:
- `devcovenant/docs/profiles.md` for profiles, assets, selectors, and hooks
- `devcovenant/docs/translators.md` for translator declarations and runtime
  resolution

## Extension Surfaces
Extension paths:
- custom policies: `devcovenant/custom/policies/<policy-id>/`
- custom profiles: `devcovenant/custom/profiles/<profile-name>/`

Use:
- `devcovenant/docs/policies.md` for custom policy authoring
- `devcovenant/docs/profiles.md` for custom profiles and managed-doc assets

## Security, Privacy, and Support
Public trust surfaces live in the repository root:
- `SECURITY.md`:
  vulnerability reporting, disclosure expectations, and static-analysis triage
- `PRIVACY.md`:
  local data handling, run-log boundaries, session-snapshot scope, and cleanup
- `SUPPORT.md`:
  maintenance posture, support scope, and what to include in a good report

## Docs Map
This README is the canonical docs entrypoint for the packaged documentation
set.
In this repository, `README.md` is the authored source and
`devcovenant/README.md` is the synced packaged guide with repo-only sections
removed.

Documentation architecture rule:
- this README is the entrypoint and quick operator view
- each detailed topic has one primary home under `devcovenant/docs/`
- other docs should point back to that primary home instead of restating the
  same contract in full

### Documentation Tiers
- universal/package docs:
  `devcovenant/README.md` and `devcovenant/docs/*.md` (install/use/runtime
  behavior)
- public trust docs (repository root):
  `SECURITY.md`, `PRIVACY.md`, and `SUPPORT.md`
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

Primary homes under `devcovenant/docs/`:
- `installation.md`:
  lifecycle commands, bootstrap, integration scenarios, and teardown
- `workflow.md`:
  exact gate contract, session semantics, and evidence ritual
- `config.md`:
  config ownership, review model, and runtime control surface
- `project_governance.md`:
  lifecycle metadata fields and rendering surfaces
- `profiles.md`:
  profile metadata, assets, hooks, and custom profile shape
- `policies.md`:
  policy descriptors, runtime behavior, and authoring contract
- `translators.md`:
  translator declaration, resolution, and failure patterns
- `architecture.md`:
  stable runtime architecture contracts and layered boundaries
- `registry.md`:
  tracked/runtime registry meaning and integrity surfaces
- `refresh.md`:
  refresh-owned regeneration behavior and managed-doc rules
- `troubleshooting.md`:
  failure signatures and recovery loops

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

## License
This project is released under the
MIT (Massachusetts Institute of Technology) License.
