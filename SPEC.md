# Project Specification
**Doc ID:** SPEC
**Doc Type:** specification
**Project Version:** 1.0.0
**Project Stage:** stable
**Maintenance Stance:** active
**Compatibility Policy:** forward-only
**Versioning Mode:** versioned
**Last Updated:** 2026-03-30
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `SPEC.md` only for durable repository contracts below this block.
<!-- DEVCOV:END -->

Use this document for durable project requirements and stable product
decisions.
Keep temporary execution work in `PLAN.md`, change history in
`CHANGELOG.md`, and workflow law in `AGENTS.md`.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Project Intent](#project-intent)
4. [Goals](#goals)
5. [Non-Goals](#non-goals)
6. [Users and Actors](#users-and-actors)
7. [Core Workflows](#core-workflows)
8. [Functional Requirements](#functional-requirements)
9. [Non-Functional Requirements](#non-functional-requirements)
10. [Data and State](#data-and-state)
11. [Interfaces and Dependencies](#interfaces-and-dependencies)
12. [Constraints and Assumptions](#constraints-and-assumptions)
13. [Acceptance Criteria](#acceptance-criteria)
14. [Open Questions](#open-questions)
15. [Pointers](#pointers)

## Overview
- Project summary: DevCovenant is a CLI-first repository governance framework
  that unifies workflow sequencing, configurable policy enforcement, managed
  documentation and generated files, and evidence-bearing command execution.
- Primary problem: repositories drift when workflow law, policy prose,
  generated governance files, and runtime behavior evolve separately.
  DevCovenant exists to make those procedural failures explicit,
  reproducible, and inspectable.
- Current scope: the product governs a git repository through
  `devcovenant/config.yaml`, `AGENTS.md`, managed docs, tracked and runtime
  registries, declared workflow runs, and evidence artifacts written under
  `devcovenant/logs/`.
- Success signal: a repository can install DevCovenant, review and deploy its
  contract, execute the governed workflow, inspect trustworthy evidence, and
  extend the system through profiles, policies, assets, and translators
  without splitting docs from code.

## Workflow
- Keep durable product requirements here.
- Keep active execution work in `PLAN.md`.
- Update this spec when stable project contracts change.
- Update operational docs in the same slice when runtime behavior changes.
- Treat this spec as the durable product contract, not as a temporary audit
  notebook or release-prep checklist.

## Project Intent
DevCovenant is meant for repositories where the expensive failures are not
syntax mistakes but procedural drift. A team forgets a required run, a hook
rewrites files after the last meaningful preflight, a changelog fails to
cover what changed, a generated file drifts from the configuration that is
supposed to own it, or release automation proves something narrower than the
public workflow it claims to protect.

The durable intent of DevCovenant is to make those failures first-class.
Repositories should be able to declare how they work, how they are governed,
what files and docs DevCovenant is allowed to manage, which workflow runs are
required, and how evidence is recorded. Operators should then be able to use
that contract through a small CLI surface and inspect the resulting evidence
without guessing what really happened.

The product is therefore not just a linter bundle and not just a documentation
generator. It is a repository governance runtime with explicit workflow,
configurable policy enforcement, managed assets and docs, deterministic
registry generation, and artifact-backed operational proof.

## Goals
- Make the repository workflow explicit, enforceable, and evidence-backed.
- Keep policy prose, runtime behavior, and generated governance surfaces in
  sync.
- Preserve a clear boundary between engine-owned runtime checks and
  repository-configurable policies.
- Allow reusable stack behavior to be expressed through profiles instead of
  repeated local ad hoc config.
- Keep operator-facing commands inspectable through stable run-log artifacts,
  concise summaries, and deterministic runtime state.
- Support built-artifact and publish proof that matches the same public
  workflow the product teaches to human operators.

Goals describe outcomes, not implementation tasks.

## Non-Goals
- DevCovenant is not a hosted governance service or central SaaS control
  plane.
- DevCovenant is not a GUI product; the primary interface is the CLI plus
  repository files.
- DevCovenant is not a general-purpose CI replacement for every workflow a
  repository might ever run.
- DevCovenant is not a policy engine that mutates files silently during
  read-only checks.
- DevCovenant is not meant to hide repository law in runtime internals while
  leaving docs as vague marketing prose.
- DevCovenant is not a substitute for repository-specific judgment about
  which policies, profiles, and lifecycle settings a repository should adopt.

This section prevents scope drift by stating what the project is
intentionally not trying to do.

## Users and Actors
- Primary actor: repository contributors and operators.
  They need a small command surface, a trustworthy workflow sequence,
  deterministic guidance when commands fail, and run artifacts they can read
  quickly.
- Secondary actor: repository maintainers and governance owners.
  They need to define project identity, select active profiles, enable or
  disable configurable policies, review generated outputs, and trust the
  tracked registry as the resolved contract surface.
- Extension actor: profile, policy, and translator authors.
  They need reusable extension surfaces with stable ownership boundaries so
  stack behavior can be added without rewriting core runtime assumptions.
- Operational actor: CI and release automation.
  It needs non-interactive command behavior, deterministic generated files,
  build-proof workflows for wheel, sdist, and `pipx`, and publish behavior
  that consumes already validated artifacts and provenance rather than
  rebuilding blindly.

## Core Workflows
1. Repository activation
   - Trigger: a repository wants to adopt DevCovenant.
   - Main path: machine install with `pipx` or source checkout,
     `devcovenant install`, human review of `devcovenant/config.yaml`,
     `devcovenant deploy`, and a first successful governed gate cycle.
   - Result: the repository becomes DevCovenant-managed with reviewed config,
     generated governance surfaces, tracked registry state, and a working
     baseline.

2. Governed change slice
   - Trigger: a contributor needs to make any governed change, including docs.
   - Main path: `devcovenant gate --start`, edit while clearing complaints,
     `devcovenant gate --mid` until clean, `devcovenant run`,
     `devcovenant gate --end`.
   - Result: the repository closes with fresh run evidence, closed gate state,
     updated changelog coverage, and inspectable run artifacts.

3. Read-only audit and recovery
   - Trigger: an operator wants to inspect current state without starting a
     new work slice, or needs to understand why a gate or run failed.
   - Main path: `devcovenant check`, `devcovenant gate --status`, then
     artifact-first inspection of `summary.txt`, `tail.txt`, `stdout.log`,
     and `stderr.log`.
   - Result: the current resolved contract and recent runtime evidence are
     understandable without hidden mutation.

4. Refresh and asset materialization
   - Trigger: config, profile, policy, or managed-doc ownership changes, or
     an operator wants a reusable asset copy.
   - Main path: `devcovenant refresh` regenerates managed outputs;
     `devcovenant asset FILE.ext [OUTPUTNAME.ext]` materializes a Desktop copy
     of a reusable profile asset or managed doc.
   - Result: governed surfaces are synchronized, or a reusable asset is
     materialized through the same rendering machinery that refresh uses.

5. CI, build proof, and publish
   - Trigger: source-tree CI, built-artifact proof, or manual release.
   - Main path: generated `CI` runs the main `governance` job and dependent
     `Build` proof, where wheel, sdist, and documented `pipx` install paths
     all execute `gate --start -> gate --mid -> run -> gate --end -> check`;
     manual `publish.yml` then downloads the validated CI artifacts and
     provenance and verifies them before release.
   - Result: the shipped artifact is backed by the same workflow contract the
     product teaches locally.

## Functional Requirements
### Command Surface And Lifecycle
- DevCovenant shall expose the public top-level commands `asset`, `check`,
  `clean`, `deploy`, `gate`, `install`, `policy`, `refresh`, `run`,
  `undeploy`, `uninstall`, and `upgrade`.
- Every public command shall accept `--quiet`, `--normal`, or `--verbose` as
  per-invocation output overrides.
- `install` shall seed repository-local DevCovenant runtime files and a
  review-required config baseline without activating the governed outputs.
- `deploy` shall require reviewed config and shall activate the governed
  contract by running the full refresh path.
- `refresh` shall regenerate tracked registry state, managed docs, generated
  config sections, generated workflow files, and other refresh-owned surfaces.
- `upgrade` shall reconcile the installed DevCovenant package from source and
  then run refresh.
- `undeploy` shall remove managed outputs while preserving the installed core
  and config.
- `uninstall` shall remove the DevCovenant footprint from the repository.
- `clean` shall remove disposable build, cache, log, and runtime-registry
  artifacts without deleting tracked registry state.
- `asset` shall materialize one reusable profile asset or managed doc as a
  Desktop copy, optionally renamed by a filename-only second argument and
  guarded by `--overwrite` when the target already exists.

### Workflow And Evidence
- The governed work slice shall be `gate --start`, `gate --mid`, `run`,
  `gate --end`.
- `check` shall remain read-only and shall not open or close a gate session.
- `gate --status` shall report the latest completed public workflow stage,
  including `mid`.
- `gate --start` shall open a tracked session and record the session baseline
  snapshot used for later change-scoped behavior.
- `gate --mid` shall act as the required pre-run preflight and shall surface
  hook mutations and blocking DevCovenant complaints before run evidence is
  recorded.
- `run` shall execute all enabled declared workflow runs in validated declared
  order and record evidence for them in the active workflow session.
- `gate --end` shall only close the session when every declared run required
  for the active session has fresh passing evidence.
- Every command shall write run artifacts under `devcovenant/logs/`, and the
  primary debug entrypoint shall be the emitted `Run logs:` path and its
  `summary.txt`.
- Child-command output suppression in normal mode shall not make successful
  commands fail spuriously; successful PTY-backed child completion shall be
  treated as normal completion even when Linux PTY EOF races raise `EIO`
  before the child exit is fully reaped.

### Workflow Contract And Extensibility
- The workflow contract shall reserve the anchors `start`, `mid`, and `end`.
- Profiles shall declare workflow runs that execute between `mid` and `end`.
- Declared workflow runs shall support executable ordering via `after`,
  `before`, and `order`.
- Unknown ordering references shall fail contract resolution.
- Cyclic ordering rules shall fail contract resolution.
- Supported runner kinds shall be `command_group`, `runtime_action`,
  `policy_command`, and `manual_attestation`.
- Supported success-contract kinds shall be `all_commands_exit_zero`,
  `runtime_action_success`, `policy_command_success`, `manual_attested`, and
  `external_artifact_check`.
- Run freshness shall be explicit metadata. The default freshness contract
  shall ignore `CHANGELOG.md`, and runs shall be allowed to declare broader or
  stricter freshness behavior.
- Manual attestation runs shall remain explicit operator-confirmed steps,
  satisfied through the declared attestation-key environment variable rather
  than through hidden interactive prompts.

### Configuration And Governance
- `devcovenant/config.yaml` shall be the main repository operating contract.
- Config shall preserve a clear ownership split between user-owned sections
  and refresh-owned autogen sections.
- `project-governance` shall define repository identity and lifecycle state,
  including project name, project description, stage, maintenance stance,
  compatibility policy, and versioning mode.
- Managed docs, tracked registry outputs, and related rendered public surfaces
  shall derive their identity headers from `project-governance`.
- Policy activation shall remain config-driven through `policy_state`.
- Profiles shall be selected through `profiles.active`.
- Engine behavior such as output mode, test output mode, autofix enablement,
  log retention, and bytecode-cache routing shall be controlled through the
  `engine` section.

### Profiles, Assets, And Translators
- Profiles shall be the reusable stack-behavior surface for overlays,
  workflow runs, managed assets, pre-commit fragments, CI fragments, suffix
  inventories, and translators.
- Profiles shall not directly enable or disable configurable policies.
- The `asset` command and `refresh` shall reuse the same rendering machinery
  for plain profile assets and descriptor-backed managed docs.
- Translator ownership shall stay with language profiles so policies can stay
  language-agnostic.
- Profile resolution and generated outputs shall be deterministic across
  filesystems and operating systems.

### Policies And Engine Checks
- DevCovenant shall preserve a hard boundary between engine-owned runtime
  checks and configurable policies.
- Configurable policies shall remain the repository-facing enforcement units.
- Policy checks shall remain read-only.
- File mutation during check flows shall only occur through autofix when
  autofix is enabled.
- Explicit policy operations shall run through the namespaced command surface
  `devcovenant policy <policy-id> <command>`.
- Policy runtime actions shall be reusable operational surfaces callable by
  policy commands and autofixers.

### Registry, Runtime State, And Managed Docs
- Tracked registry state shall live in `devcovenant/registry/registry.yaml`
  and represent resolved durable contract state.
- Runtime-local state shall live under `devcovenant/registry/runtime/` and
  remain disposable.
- `gate_status.json` shall remain the short gate lifecycle ledger.
- `workflow_session.json` shall remain the durable runtime record for the
  active or last session's anchors, runs, freshness evidence, and run
  snapshots.
- Managed documents shall follow preservation rules: missing docs may be
  created, empty docs may be replaced, one-line docs may be replaced, and
  otherwise only managed headers and managed blocks may change.
- AGENTS shall remain a generated governance surface whose workflow block,
  project-governance block, and policy block stay synchronized with resolved
  runtime state.

### Packaging, CI, And Publish
- The published package shall ship the runtime-facing docs, built-in policies,
  built-in profiles, translators, and managed assets required for install-time
  and runtime behavior.
- The published package shall not ship live repository state such as
  `devcovenant/config.yaml`, tracked registry outputs, runtime registry state,
  timestamped log folders, or development debris.
- The generated `CI` workflow shall remain the source-tree CI surface in
  `.github/workflows/ci.yml`.
- Repo-specific `Build` proof inside `CI` shall prove the public workflow on
  wheel, sdist, and documented `pipx` install surfaces.
- Manual publish shall consume validated CI artifacts and provenance and shall
  verify `ci_run_id`, `ci_run_attempt`, `head_sha`, and artifact hashes before
  publishing.
- Publish shall not rebuild a fresh dist artifact after CI has already proved
  the release candidate artifact.

## Non-Functional Requirements
- Performance: refresh, check, gate, and run behavior shall favor deterministic
  file traversal and concise operator output, with full detail preserved in
  run artifacts rather than requiring verbose console streaming by default.
- Reliability: workflow sequencing, managed-environment resolution, run
  freshness, and publish provenance shall fail explicitly on broken state
  rather than silently guessing past contract violations.
- Security: human review shall remain explicit at activation time, publish
  shall remain manual, provenance shall be validated before release, and
  command execution shall use tokenized subprocess invocation rather than
  ad hoc shell-string evaluation.
- Maintainability: the implementation shall preserve the layered split between
  `core/flow`, `core/runtime`, `core/services`, `core/lib`, and
  `core/contracts`, and docs shall be updated in the same slice when stable
  behavior changes.
- Usability: operators shall be able to understand state through a small CLI
  surface, stable command names, summary-first run logs, human-readable config,
  and deterministic generated files.

## Data and State
- Important entities:
  - `devcovenant/config.yaml` as the repository operating contract
  - `AGENTS.md` as the enforced workflow and policy law surface
  - managed docs such as `README.md`, `SPEC.md`, `PLAN.md`, and
    `CHANGELOG.md`
  - tracked registry state in `devcovenant/registry/registry.yaml`
  - runtime state in `devcovenant/registry/runtime/`
  - run-log folders under `devcovenant/logs/`
  - packaged artifacts and CI provenance records
- Important state transitions:
  - uninstalled repository -> installed baseline -> reviewed config ->
    deployed governed repository
  - no session -> open gate session -> mid-cleared session -> run-evidenced
    session -> closed session
  - stale workflow evidence -> fresh passing run evidence -> stale again when
    relevant files change
  - unmanaged docs -> managed docs with preserved authored body and managed
    headers or blocks
- Persistence rules:
  - tracked registry state is durable and committed
  - runtime registry state is local evidence and disposable
  - package metadata and built artifacts are derived outputs
  - run logs are evidence artifacts subject to retention and cleanup rules
- Audit and traceability needs:
  - every governed command run must be inspectable through run artifacts
  - session-scoped changelog coverage must remain traceable to the active work
    slice
  - publish provenance must identify the CI run and artifact set it is
    releasing

## Interfaces and Dependencies
- External interfaces:
  - CLI commands under `devcovenant`
  - repository files such as `devcovenant/config.yaml`, `AGENTS.md`, managed
    docs, `.github/workflows/ci.yml`, and `.github/workflows/publish.yml`
  - Desktop asset materialization via `devcovenant asset`
  - GitHub Actions for CI, built-artifact proof, and manual publish
  - environment variables for manual attestation and runtime behavior
- Internal interfaces:
  - `core/flow` for lifecycle orchestration and workflow validation
  - `core/runtime` for execution, output policy, run logging, and runtime
    registry paths
  - `core/services` for metadata resolution, policy execution, managed docs,
    and tracked registry behavior
  - `core/lib` for shared helper logic
  - `core/contracts` for shared contract definitions
- Dependencies:
  - Python 3.10+
  - `packaging`, `pre-commit`, `pip-tools`, `PyYAML`, `pytest`, and `semver`
  - a git repository and filesystem access sufficient to manage repo-owned
    files
- Compatibility expectations:
  - the package version is `1.0.0`
  - the repository is `stable`, `active`, and `versioned`
  - the repository compatibility policy is `forward-only`
  - version-governance metadata uses the SemVer scheme, even though stricter
    SemVer enforcement is a separate governance choice from the presence of a
    SemVer-shaped version string

## Constraints and Assumptions
- Constraint: DevCovenant is a repository-local, file-centric tool. It assumes
  the repository itself is the source of governance truth.
- Constraint: the primary interface is a Python CLI, so Python availability is
  required on developer and CI paths.
- Constraint: managed docs and generated governance files must remain readable
  and inspectable in-tree rather than being hidden in remote service state.
- Assumption: repositories adopting DevCovenant can review config explicitly
  between `install` and `deploy`.
- Assumption: repositories can commit tracked registry and managed output
  changes that result from real contract updates.
- Assumption: CI and release proof for this repository continue to run through
  GitHub Actions.
- Explicit tradeoff: DevCovenant prefers explicit evidence, generated state,
  and stable ownership boundaries over silent convenience or hidden implicit
  behavior.

## Acceptance Criteria
- A normal user can install DevCovenant with `pipx`, run `devcovenant install`
  in a repository, review `devcovenant/config.yaml`, run `deploy`, and reach a
  working governed baseline.
- A contributor can complete a governed slice through `gate --start`,
  `gate --mid`, `run`, and `gate --end`, and the repository records usable
  run artifacts and closed session state.
- `check` and `gate --status` can explain current repository and lifecycle
  state without opening or closing a session.
- Declared workflow runs execute in validated graph order, including `after`,
  `before`, `order`, reserved anchors, and cycle rejection.
- Profiles, policies, managed docs, translators, and assets can extend the
  repository contract without breaking the ownership split between engine-owned
  runtime checks, configurable policies, and profile-owned stack behavior.
- The tracked registry reflects resolved durable contract state, while the
  runtime registry reflects recent execution evidence.
- Built wheel, sdist, and documented `pipx` install paths can all prove the
  full public workflow contract in CI.
- Manual publish can release only a validated CI artifact and provenance set
  without rebuilding.

This section should let someone decide whether the project meets the spec
without having to guess what success means.

## Open Questions
- Are there future product requirements for non-Python runtimes or additional
  operator surfaces beyond the current CLI-first, file-centric model?
- What additional shipped examples or reference repos would make profile,
  policy, and managed-doc authoring easier for downstream adopters?

Keep unresolved questions here only while they are still real.
Once answered, fold the answer into the relevant section above.

## Pointers
- `README.md` for the shortest product overview and command map.
- `devcovenant/docs/installation.md` for install, deploy, upgrade, clean,
  undeploy, and uninstall behavior.
- `devcovenant/docs/workflow.md` for gate sequencing, workflow runs, output
  modes, CI mapping, and recovery.
- `devcovenant/docs/config.md` for `devcovenant/config.yaml` ownership and
  project-governance behavior.
- `devcovenant/docs/project_governance.md` for the public identity and
  lifecycle metadata contract.
- `devcovenant/docs/profiles.md` for profiles, assets, translators, and
  workflow-run declarations.
- `devcovenant/docs/policies.md` for configurable policy behavior, policy
  commands, and runtime actions.
- `devcovenant/docs/registry.md` for tracked registry and runtime registry
  behavior.
- `devcovenant/docs/architecture.md` for the layered runtime and internal
  ownership map.
