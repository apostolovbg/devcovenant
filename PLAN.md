# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.0
**Project Stage:** stable
**Maintenance Stance:** active
**Compatibility Policy:** breaking-allowed
**Versioning Mode:** versioned
**Last Updated:** 2026-03-26
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `PLAN.md` to track active implementation work below this block.
<!-- DEVCOV:END -->
Use this plan to close the remaining pre-release gaps surfaced by the
external audit and the follow-on workflow-contract review before
DevCovenant starts true SemVer release discipline.

## Table of Contents
1. [Overview](#overview)
2. [Audit Baseline](#audit-baseline)
3. [Working Rules](#working-rules)
4. [Workflow-Phase Redesign Baseline](#workflow-phase-redesign-baseline)
5. [Active Remediation](#active-remediation)
6. [Validation Routine](#validation-routine)

## Overview
- The large stabilization and polish work is already done and should be
  preserved.
- The current external audit verdict is:
  - close but not ready
- The remaining risks are no longer architectural emptiness or uncontrolled
  sprawl.
- The remaining risks are release-truthfulness and workflow-contract defects:
  - what the artifacts actually ship
  - what CI actually proves
  - whether publish uses the exact proven artifact
  - whether the dependency lock contract is stable and environment-safe
  - whether the docs explain the intended first-activation lifecycle clearly
  - whether gate mechanics depend on customizable policy state instead of a
    formal workflow-extension contract
  - whether the workflow-extension redesign is actually complete in code,
    command ownership, CI, and docs rather than only partially generalized
- Do not start true release-candidate or SemVer-cut work until the blocker,
  high-severity, and workflow-contract items below are resolved.

## Audit Baseline
The external audit surfaced these remaining findings:

1. blocker: built artifacts do not ship
   `devcovenant/core/contracts/invariants/*.yaml`, so the documented
   install -> review -> deploy lifecycle can fail from the real wheel/sdist

2. blocker: CI and release smoke checks do not prove the real artifact
   lifecycle; they prove startup/help/status, not install -> review -> deploy

3. high: publish rebuilds artifacts instead of publishing the exact
   previously validated artifact for the tested SHA

4. high: `requirements.lock` refresh semantics are environment-sensitive and
   can treat emitted pip option lines as semantic lock changes

5. medium: docs do not yet state clearly enough that normal repos should reach
   the first reviewed baseline before seeding repo-specific custom
   policies/profiles

6. low: the defensive cleanup of leaked dev-only test paths is heuristic and
   may deserve later hardening, but it is not a release blocker now

Follow-on design review added one more release-relevant concern:

7. high: gate/workflow mechanics still blur two different contracts:
   - customizable policy behavior
   - required workflow phases and their pass/fail recording
   That boundary must be formalized before the first real SemVer-governed
   line so required workflow behavior does not depend on whether a normal
   policy happens to be enabled.

8. high: the workflow-phase redesign is still only partially migrated:
   - core still exposes and teaches a top-level `devcovenant test` command
   - runtime still special-cases the `tests` phase instead of treating it as a
     normal declared phase under one generic execution path
   - profile schema still leaks command-alias concerns
   - CI, AGENTS, and docs still teach the test-centric workflow instead of the
     generic required-phase workflow
   - the tracked workflow schema advertises runner and success-contract kinds
     that the runtime does not fully execute yet
   This leaves the feature looking stitched in rather than fully native.

Treat Findings 1 through 4, 7, and 8 as release blockers for the first real
release candidate.

## Working Rules
- Work in dependency order unless a real blocker forces reordering.
- Keep remediation narrow and audit-backed.
- Fix shipped-artifact truth before release-story polish.
- Prefer objective proof over reassurance:
  - built artifact contents
  - isolated wheel/sdist lifecycle runs
  - workflow definitions
  - publish provenance
  - lockfile behavior under different environments
  - gate session records and required phase results
- Do not start SemVer ritual, orphaning, or release-history cleanup while
  blocker findings remain open.
- Keep each item concrete enough that another person can continue it without
  reconstructing hidden context.
- When an item is complete, rewrite it to state what landed and what is now
  true because of it.
- Keep the current managed-document preservation contract unless an explicit
  plan item changes it:
  - missing docs may be created from descriptors
  - empty docs may be replaced fully
  - one-line docs may be replaced fully
  - otherwise, only managed header lines and explicit `<!-- DEVCOV* -->`
    blocks may change

## Workflow-Phase Redesign Baseline
This section records the intended design before implementation so the
workflow/gate redesign does not drift into another half-implicit model.

### Core Principle
DevCovenant must distinguish between:

- workflow phases that the engine requires and records
- policies that inspect or mutate repository state

Those are different contracts.
A customizable policy must not be part of gate's mechanical foundation.

### Workflow Shape
Core owns three reserved anchors:

- `start`
- `mid`
- `end`

Everything else is a declared workflow phase between `mid` and `end`.
The model is therefore:

- `start`
- `mid`
- zero or more declared phases
- `end`

Examples of declared phases:

- `tests`
- `artifact-proof`
- `assurance`
- `schema-validate`
- `manual-attestation`

### Ownership Split
Core owns:

- gate session lifecycle
- anchor phases (`start`, `mid`, `end`)
- workflow-phase ordering rules
- runtime session recording
- required-phase completion checks
- the command surface for generic phase execution

Profiles own:

- declared workflow phases
- whether a phase is enabled or required
- ordering metadata for those phases
- how a phase runs
- the success contract the phase uses

Policies own:

- checks
- autofix
- explicit policy commands and runtime actions
- tracked policy descriptors and generated policy artifacts
- policy-local runtime state in a namespaced runtime location or an explicit
  declared location when a policy truly needs one

Builtin versus custom does not decide ownership.
Contract type decides ownership.

### Registry Ownership
Tracked core registry data should hold generated workflow truth, for example
in `devcovenant/registry/registry.yaml`:

```yaml
workflow_contract:
  schema_version: 1
  anchors:
    - id: start
      owner: core
      phase_kind: gate_anchor
      required: true
    - id: mid
      owner: core
      phase_kind: gate_anchor
      required: true
    - id: end
      owner: core
      phase_kind: gate_anchor
      required: true
  phases:
    - id: tests
      owner: profile
      owner_id: global
      enabled: true
      required: true
      position:
        after: mid
        before: end
        order: 100
      runner:
        kind: command_group
        commands:
          - python3 -m unittest discover -v
          - pytest
      success_contract:
        kind: all_commands_exit_zero
      recording:
        record_in_session: true
        summary_label: Tests
```

Runtime core registry data should move to a workflow-session record under
`devcovenant/registry/runtime/`, for example:

- `devcovenant/registry/runtime/workflow_session.json`

That runtime file should record:

- session id
- session status
- head SHA at session start
- workflow contract version
- anchor results
- declared phase results
- required/optional status
- timestamps
- run ids
- attempt counts
- verified SHA or verified tree fingerprint for each phase result

### Start-Gate Carry-Forward Rule
`gate --start` must not only open a new session.
It must also care about the last required workflow-extension results.

That means `start` should block when the previous workflow state says a
required declared phase is still unclean, failed, missing, or stale in a way
that would have blocked the previous slice from closing honestly.

The intended rule is:

- if the previous required phase results are clean and satisfied for the last
  closed session, `start` may open a new session
- if the previous required phase results are not clean, `start` must fail and
  require the operator to clear that state first

This must apply to required declared phases generally, not only to today's
hardcoded test expectations.

### End-Gate Rule
`gate --end` must validate:

1. `start` passed for the active session
2. `mid` passed for the active session
3. every required declared phase between `mid` and `end` passed for the
   active session
4. only then may `end` pass and close the session

This keeps gate coherent even when different repositories define different
middle phases.

### Phase Runner Kinds
Declared workflow phases should use a closed runner vocabulary:

```yaml
runner:
  kind: command_group | runtime_action | policy_command | manual_attestation
```

Recommended meanings:

- `command_group`: run one or more concrete commands
- `runtime_action`: run a core or profile-owned runtime action by id
- `policy_command`: run an explicit policy command surface
- `manual_attestation`: record a human-asserted step under an explicit
  attestation contract

### Success Contracts
Declared workflow phases should use a closed success-contract vocabulary.
The contract set should include all of the following now:

```yaml
success_contract:
  kind: |
    all_commands_exit_zero |
    runtime_action_success |
    policy_command_success |
    manual_attested |
    external_artifact_check
```

Recommended meanings:

- `all_commands_exit_zero`: every command in the phase completed successfully
- `runtime_action_success`: the named runtime action reported success
- `policy_command_success`: the named policy command reported success
- `manual_attested`: the required attestation record exists and is valid
- `external_artifact_check`: a declared external artifact contract validated
  successfully

`external_artifact_check` should not stay a future idea.
It belongs in the initial schema because artifact truth is already a real
release requirement for this project.

The runtime must support every declared runner kind and every declared
success-contract kind that the tracked schema accepts.
If the schema admits a phase kind that the runtime cannot execute, the
workflow contract is not yet honest.

### Profile Contribution Schema
Profiles should contribute phases through a dedicated key such as
`workflow_phases`, not indirectly through policy metadata.
For example:

```yaml
workflow_phases:
  - id: tests
    enabled: true
    required: true
    after: mid
    before: end
    order: 100
    runner:
      kind: command_group
      commands:
        - python3 -m unittest discover -v
        - pytest
    success_contract:
      kind: all_commands_exit_zero
    recording:
      summary_label: Tests
```

Repo-specific profiles may then contribute phases such as
`artifact-proof` cleanly without pretending they are policies.

The `workflow_phases` declaration should stay focused on phase behavior and
must not try to smuggle root-command ownership into profile metadata.

### Command-Surface Target
Core should own the public workflow command surface directly.
The target command set is:

- `devcovenant gate --start`
- `devcovenant gate --mid`
- `devcovenant run`
- `devcovenant gate --end`

The explicit rerun surface is:

- `devcovenant phase run <id>`

Under this target model:

- `devcovenant run` executes all enabled required declared phases for the
  active session in deterministic order
- `devcovenant phase run <id>` executes exactly one declared phase
- `devcovenant test` does not remain a top-level root command
- profiles do not define or own top-level CLI aliases

This keeps workflow execution generic, keeps root command ownership in core,
and stops the `tests` phase from looking privileged by command-surface
accident.

### `run` Contract
`devcovenant run` should:

1. resolve the active tracked workflow contract
2. collect enabled required phases between `mid` and `end`
3. execute them in deterministic declared order
4. record each phase result in the runtime workflow session
5. stop on first required-phase failure
6. exit zero only when all required phases for that run pass

If no required phases exist, `run` should:

- report that there are no required declared phases for the active contract
- exit successfully without pretending work happened

### No Profile-Owned Command Aliases
Profiles own:

- phase ids
- phase ordering
- runner metadata
- success-contract metadata
- recording labels

Core owns:

- root command names
- how operators invoke workflow execution
- how rerun instructions are rendered in gate messaging

That means fields such as a canonical top-level `test` alias should not
survive the final migration.

### Policy-Local Runtime State
Policy-local runtime state is valid, but mutable runtime state should not
live in packaged policy source folders by default.
The default location should be a namespaced runtime area, for example:

- `devcovenant/registry/runtime/policies/<policy-id>/...`

A policy may declare an explicit alternate path when it truly needs one, but
that should be explicit metadata, not the default physical layout.

This keeps source-of-truth surfaces separate from mutable runtime state and
avoids packaging, cleanup, and drift confusion.

### Migration Direction
The clean migration path is:

1. formalize the workflow-phase schema and runtime-session schema
2. migrate the current `test` phase onto that contract first
3. update `devflow-run-gates` to validate declared required phases instead of
   hardcoded required commands
4. then add any new intermediate phases through profile-owned workflow
   metadata rather than policy enablement side effects

### Current Design Correction
The first workflow-phase migration landed only part of the intended design.
It correctly introduced:

- tracked `workflow_contract`
- runtime `workflow_session.json`
- required-phase enforcement in `gate --start` and `gate --end`
- profile-owned declaration of the `tests` phase

But it still left visible half-step behavior in place:

- top-level `devcovenant test` remains a root command
- runtime still special-cases the `tests` phase
- gate messaging still renders `devcovenant test`
- CI still runs `devcovenant test`
- AGENTS and user-facing docs still teach the test-centric workflow
- profile metadata still carries command-surface concerns
- the schema admits runner and success-contract kinds that runtime does not
  actually execute yet

The next implementation item must close that gap fully rather than treating
the current state as finished.

## Active Remediation
1. [done] Ship Core Invariant Descriptors In Built Artifacts.
   What landed:
   - added `devcovenant/core/contracts/invariants/*.yaml` to the wheel and
     sdist packaging surface at the real source of truth in `pyproject.toml`
     and `MANIFEST.in`
   - added packaging regressions that now assert the invariant descriptors are
     present in both wheel and sdist artifacts
   - updated the installation and architecture docs so the shipped package
     boundary names the invariant-descriptor requirement explicitly
   - fixed the dependency-management false positive surfaced by this
     package-manifest edit so already-synchronized license artifacts do not
     require fake touch churn just to satisfy the gate
   - proved the real artifact behavior from temp-built artifacts:
     both an isolated wheel install and an isolated sdist install completed
     `install -> config review -> deploy` successfully
   What is now true:
   - wheel and sdist both ship the core invariant descriptor YAMLs the runtime
     resolves at deploy time
   - packaging regressions now reject a return to source-only invariant
     descriptors
   - the external-audit blocker is closed at the artifact level, not just in
     metadata theory

2. [done] Prove The Real Artifact Lifecycle In CI.
   What landed:
   - replaced the shallow workflow startup checks with real built-artifact
     lifecycle proof in the repo-specific `build-and-install-test` job
   - the generated `Checks` workflow now proves that the built wheel and built
     sdist can complete `install -> config review -> deploy -> check` in a
     temporary git repository
   - the same repo-specific job now proves the documented `pipx`
     machine-install path with the same activation flow instead of only
     checking `--version`, `check --help`, or `gate --status`
   - the dependent `build.yml` workflow now uses the same wheel and sdist
     lifecycle proof before artifact upload instead of help-only smoke checks
   - updated the workflow, profiles, and installation docs so the written CI
     contract names real artifact activation proof instead of shallow CLI boot
   What is now true:
   - CI proves the public built-artifact lifecycle from wheel, sdist, and
     `pipx`, not just CLI startup
   - the external-audit blocker is closed at the workflow-proof level
   - the repo no longer claims an artifact path in docs that CI fails to
     exercise at the activation boundary

3. [done] Publish The Exact Previously Validated Artifact.
   What landed:
   - removed rebuild-in-publish behavior from `publish.yml`
   - `build.yml` now emits a small provenance artifact beside the validated
     distributions, recording the Build run id, tested head SHA, and dist
     checksums
   - `publish.yml` now accepts a specific successful Build run id, validates
     that run through the GitHub Actions API, downloads the distributions and
     provenance from that exact run, verifies the downloaded dist checksums,
     and only then publishes to PyPI
   - added a regression test that locks the release-workflow contract so
     publish cannot quietly drift back to rebuilding from source
   - updated the installation and workflow docs so the release-provenance rule
     is explicit where operators look for build/publish behavior
   What is now true:
   - publish uses the exact previously validated artifact instead of building
     a fresh one in the publish workflow
   - the uploaded artifact is tied to one specific successful Build run and
     its tested head SHA
   - the external-audit high-severity provenance finding is closed at the
     workflow-contract level

4. [done] Lock The `requirements.lock` Contract And Fix Runtime Semantics.
   What landed:
   - tightened the dependency-management runtime so environment-specific pip
     control lines such as index and trusted-host directives are excluded from
     Python lock semantic comparison
   - scrubbed those non-semantic pip option lines from the written
     `requirements.lock` body as well, so refresh now normalizes leaked
     environment-specific output back to the stable contract instead of
     preserving it
   - added targeted regressions for both critical cases:
     emitted option lines that should not count as lock drift, and existing
     leaked option lines that should be removed during refresh
   - updated the policy docs so the contract is explicit:
     `requirements.lock` stores normalized dependency-resolution content,
     while environment-specific package-source behavior belongs in
     dependency-management metadata/config
   What is now true:
   - lock refresh no longer treats emitted pip source options as meaningful
     dependency-resolution changes
   - `requirements.lock` no longer absorbs environment-sensitive pip option
     lines into the stable lock body under the intended contract
   - the external-audit high-severity lockfile-semantics finding is closed at
     the runtime, regression, and documentation levels

5. [done] Formalize The Workflow-Phase Extension Contract.
   Landed:
   - added `devcovenant/core/services/workflow_contract.py` to resolve the
     tracked workflow contract with reserved anchors (`start`, `mid`, `end`),
     profile-declared phases, required-phase ids, runner kinds, and
     success-contract kinds
   - added `devcovenant/core/runtime/workflow_session.py` and the runtime
     `devcovenant/registry/runtime/workflow_session.json` surface so core
     workflow state is no longer squeezed into `gate_status.json`
   - kept `gate_status.json` as the short lifecycle and pre-commit ledger,
     while moving required-phase truth into `workflow_session.json`
   - moved the Python stack's `tests` phase into the builtin Python profile's
     new `workflow_phases` declaration instead of keeping workflow truth in
     `devflow-run-gates.required_commands`
   - added the generic `devcovenant phase run <id>` command surface as the
     first explicit one-phase runner
   - updated `gate --start` so recovery start blocks when the previous closed
     session has stale required phases, not only stale tests
   - updated `gate --end` so closure requires fresh passing evidence for every
     required declared phase bound to the active session
   - updated `devflow-run-gates` so it validates pre-commit evidence from
     `gate_status.json` and required-phase evidence from
     `workflow_session.json`
   - updated tracked registry writing so `workflow_contract` is recorded in
     `devcovenant/registry/registry.yaml`
   - updated registry inventory defaults so the new core files and runtime
     workflow-session artifact are part of the expected DevCovenant surface
   - rewrote the affected tests around the new contract and added coverage for
     tracked workflow-contract export
   What is now true:
   - workflow structure is no longer inferred from normal policy enablement
   - required workflow behavior no longer depends on a customizable policy
     being enabled just to make gate mechanics coherent
   - the tracked registry records the generated workflow contract explicitly
   - runtime workflow sessions record anchors and declared phases separately
   - start and end gates validate declared required phases generally rather
     than only one hardcoded test-centric case
   - `tests` is the first real declared workflow phase under the new contract
   - the remaining redesign work is no longer about inventing workflow phases;
     it is about finishing the command/runtime/docs/CI migration so the
     feature stops looking half-test-centric

6. [done] Clarify The First-Activation Lifecycle For Custom Extensions.
   What landed:
   - updated the operator-facing installation docs to say explicitly that a
     normal repository should reach the first reviewed DevCovenant baseline
     before adding repo-specific custom policies or profiles
   - updated the custom profile guidance to say that repo-specific custom
     profiles come after the initial `install` -> config review -> `deploy`
     activation has already proven the base contract
   - updated the custom policy guidance to say that repo-specific custom
     policies also come after that first reviewed baseline
   - kept the explanation consistent with deploy cleanup behavior so the
     cleanup rule now reads as lifecycle discipline rather than arbitrary
     deletion of a supposedly supported extension surface
   - added a regression test that locks the baseline-first wording into the
     docs contract
   What is now true:
   - a normal operator can read the first-time setup and customization docs
     and see the intended lifecycle plainly:
     baseline first, then repo-specific custom extensions
   - the external audit's documentation-gap finding about first activation is
     now closed at both the docs and regression-test levels

7. [done] Re-run The External-Grade Release Audit.
   What landed:
   - reran the outside-in audit against the current staged release-candidate
     tree rather than against design intent alone
   - verified built artifact contents directly from a fresh isolated temp copy
     of the repo:
     - wheel and sdist both contain
       `devcovenant/core/contracts/invariants/*.yaml`
     - wheel and sdist do not contain legacy `update_lock`,
       `governance-and-test`, or `dependabot.yml` entries
   - reran isolated lifecycle proof against the built artifacts:
     - wheel: `install` -> config review -> `deploy` -> `check`
     - sdist: `install` -> config review -> `deploy` -> `check`
     - `pipx` install from the built wheel: same operator lifecycle proof
   - reread the generated CI and publish workflows and confirmed that:
     - `Checks` proves the governed run plus scanner steps
     - `Build` proves real artifact lifecycle from the tested SHA
     - `Publish` consumes a selected successful `Build` artifact and verifies
       provenance instead of rebuilding
   - reran focused regressions for the remaining truthfulness surfaces:
     - dependency-lock semantics
     - workflow-phase/gate contract
     - workflow-session / required-phase recording
     - package-doc contract wording
   What is now true:
   - the external-grade audit no longer finds substantive blocker or
     high-severity mismatches in shipped artifacts, CI proof, publish
     provenance, dependency-lock semantics, installation/customization docs,
     or workflow-contract truthfulness
   - that audit closed the earlier artifact, publish, lockfile, and
     first-activation remediation set
   - a later workflow-command audit then identified the still-half-migrated
     `devcovenant test` / workflow-phase command model captured in Item 8

8. [not done] Complete The `run` / Workflow-Phase Migration.
   Goal:
   - replace the test-centric public workflow with one core-owned generic
     workflow execution surface
   - make workflow extensions look native in code, docs, CI, and operator
     messaging
   - align runtime support with the full tracked schema so no allowed phase
     contract remains a paper-only promise
   Why this matters:
   - the current workflow redesign is only half-migrated
   - the repo still teaches and privileges `devcovenant test`, which keeps the
     `tests` phase special even though the architecture now says workflow
     phases are generic
   - schema truth must match runtime truth before the first SemVer-governed
     public line
   Design decisions for this item:
   - `devcovenant run` is the top-level command that replaces
     `devcovenant test`
   - `devcovenant run` executes all enabled required declared phases for the
     active session in deterministic order
   - `devcovenant phase run <id>` remains the explicit one-phase rerun surface
   - top-level workflow commands are core-owned, not profile-owned
   - profile phase metadata must not define command aliases
   - the current structural policy `modules-need-tests` is not automatically
     renamed to `test-engine` during this migration unless its responsibility
     changes as well
   - if a later rename happens, it must use a name that matches the policy's
     real job; a structural source-to-test policy should not be given an
     execution-engine name by accident
   Work packages in dependency order:
   1. Root command and ownership rewrite.
      File scope:
      - `devcovenant/cli.py`
      - a new core command module for `run`
      - retirement or removal path for `devcovenant/test.py`
      - `devcovenant/phase.py`
      Work to do:
      - add the top-level `run` command
      - remove `test` from the public root-command dispatcher
      - keep explicit single-phase execution in `phase run <id>`
      - resolve managed-environment stages by workflow behavior rather than a
        one-off `test` branch
      Done when:
      - `devcovenant run` is the public top-level workflow execution command
      - `devcovenant test` is no longer part of the root CLI contract

   2. Runtime execution unification.
      File scope:
      - `devcovenant/core/runtime/execution.py`
      - any runtime helpers that still special-case test runs
      Work to do:
      - remove the dedicated test-only privileged path as the canonical
        workflow executor
      - make declared phases execute through one generic path
      - support every allowed runner kind:
        `command_group`, `runtime_action`, `policy_command`,
        `manual_attestation`
      - support every allowed success-contract kind:
        `all_commands_exit_zero`, `runtime_action_success`,
        `policy_command_success`, `manual_attested`,
        `external_artifact_check`
      - make runtime failures mention `devcovenant run` or
        `devcovenant phase run <id>`, not `devcovenant test`
      Done when:
      - `tests` is not privileged in runtime flow control
      - any allowed schema kind is truly executable

   3. Gate and invariant migration.
      File scope:
      - `devcovenant/core/flow/gate.py`
      - `devcovenant/core/services/devflow_run_gates.py`
      - `devcovenant/core/contracts/invariants/devflow_run_gates.yaml`
      - `devcovenant/core/runtime/workflow_session.py`
      Work to do:
      - render rerun instructions through `run` by default
      - keep explicit `phase run <id>` wording for targeted recovery cases
      - make `start` carry-forward checks and `end` closure checks speak in
        required-phase language consistently
      - reduce or retire leftover dependence on `gate_status.json` for phase
        truth where `workflow_session.json` is the real source
      Done when:
      - gate messaging no longer teaches `devcovenant test`
      - the invariant validates anchors plus required phases without any
        test-centric fallback language

   4. Workflow-contract schema cleanup.
      File scope:
      - `devcovenant/core/services/workflow_contract.py`
      - `devcovenant/core/services/profile_registry.py`
      - `devcovenant/core/services/registry.py`
      - `devcovenant/core/flow/refresh.py`
      - `devcovenant/registry/registry.yaml`
      - profile manifests such as
        `devcovenant/builtin/profiles/python/python.yaml`
      Work to do:
      - remove command-surface alias ownership from profile metadata
      - keep phase metadata focused on phase behavior only
      - regenerate tracked registry output to match the final contract
      Done when:
      - profile manifests declare phases, not root command aliases
      - tracked registry reflects the final command-neutral phase schema

   5. CI and generated workflow migration.
      File scope:
      - `.github/workflows/ci-and-test.yml`
      - `devcovenant/builtin/profiles/global/assets/ci-and-test.yml`
      - any release/build workflows that still teach the old command shape
      Work to do:
      - replace `python -m devcovenant test` with the new top-level
        `python -m devcovenant run`
      - keep explicit `phase run <id>` only where a specific rerun is
        intentionally needed
      Done when:
      - generated GitHub Actions surfaces teach the same workflow contract as
        AGENTS and the docs

   6. Full documentation and managed-asset rewrite.
      File scope:
      - `AGENTS.md`
      - `README.md`
      - `devcovenant/README.md`
      - `CONTRIBUTING.md`
      - `SPEC.md`
      - `PLAN.md`
      - `devcovenant/docs/workflow.md`
      - `devcovenant/docs/installation.md`
      - `devcovenant/docs/architecture.md`
      - `devcovenant/docs/profiles.md`
      - `devcovenant/docs/policies.md`
      - `devcovenant/docs/registry.md`
      - matching global/profile doc assets
      Work to do:
      - rewrite the canonical workflow as
        `gate --start -> gate --mid -> run -> gate --end`
      - replace test-centric recovery wording with required-phase wording
      - explain clearly that:
        - core owns workflow commands
        - profiles own declared phases
        - policies do not own workflow structure
      - remove claims that `devcovenant test` is a friendly alias
      Done when:
      - there is no stale public instruction to run `devcovenant test`
        outside historical changelog context

   7. Test-suite migration.
      File scope:
      - CLI tests
      - gate tests
      - workflow-session tests
      - workflow-contract tests
      - profile-registry tests
      - docs-contract tests
      - CI/workflow contract tests
      Work to do:
      - rewrite assertions that currently expect `devcovenant test`
      - add coverage for `devcovenant run`
      - add coverage that each supported runner kind and each supported
        success-contract kind is actually executable under the runtime
      - add coverage that start and end guidance names `run` and targeted
        `phase run <id>` correctly
      Done when:
      - the test suite locks the final generic workflow surface instead of the
        old alias model

   8. Policy naming follow-up decision.
      File scope:
      - `modules-need-tests` descriptor/module/tests/profile references/docs
      Work to do:
      - decide whether the current policy keeps its structural identity or is
        renamed to a more honest structural name such as `test-structure`
      - do not rename it to `test-engine` unless its actual responsibility
        changes from structural enforcement into workflow execution ownership
      Done when:
      - the policy name and the policy job mean the same thing

   Done when:
   - `devcovenant run` is the canonical top-level workflow execution command
   - `devcovenant phase run <id>` is the explicit per-phase rerun path
   - `devcovenant test` is no longer a public root command
   - runtime no longer special-cases `tests`
   - every allowed runner kind and success-contract kind is actually supported
   - profile phase metadata no longer leaks command-alias ownership
   - AGENTS, docs, CI, and gate messages all teach the same workflow
   - any remaining references to `devcovenant test` are historical only

9. [not done] Prepare The First Real Release Candidate.
   Goal:
   - start the real release-candidate cut only after the external-grade
     remediation audit is clean and the `run` migration is complete.
   Why this matters:
   - SemVer release discipline should begin after proof, not before it
   - history cleanup or orphaning before then would hide work in progress
     instead of certifying a stable candidate
   Work to do:
   - confirm that the current public governance state
     (`1.0.0`, `stable`, `active`, `breaking-allowed`, `versioned`)
     is still the intended truth for the release candidate
   - rerun the full governed workflow on the exact release-candidate tree
   - rerun the artifact proof on the exact release-candidate tree
   - if branch-history cleanup or orphaning is still desired, do it only after
     the already-proven release-candidate tree exists
   - rerun a short post-history-change smoke audit if tree identity changes
   Done when:
   - the release candidate is proven, truthfully labeled, and ready for the
     first real release mechanics

## Validation Routine
- For every remediation slice, run:
  1. `devcovenant gate --mid`
  2. `devcovenant test`
  3. `devcovenant gate --end`
  4. `devcovenant check`
- For packaged-surface work, also run:
  1. `python -m build`
  2. `twine check dist/*`
  3. inspect wheel and sdist contents directly when a packaging-boundary issue
     is in scope
- For artifact-lifecycle work, also run:
  1. isolated wheel lifecycle proof:
     `install -> config review -> deploy`
  2. isolated sdist lifecycle proof:
     `install -> config review -> deploy`
  3. installed-CLI proof when the public install story is in scope
- For workflow-contract redesign work, also run:
  1. tracked-registry generation checks for the workflow contract
  2. runtime-session migration and schema tests
  3. start-gate carry-forward failure tests for unresolved required phases
  4. end-gate closure tests for required declared phases
  5. phase-runner tests for each supported runner kind in scope
  6. success-contract tests for each supported success-contract kind in scope
  7. `devcovenant run` orchestration tests for ordered required-phase execution
  8. root-command tests that `devcovenant test` is retired from the public CLI
     once the migration lands
  9. policy-state ownership tests so mutable policy-local state stays out of
     tracked or packaged source surfaces unless explicitly declared

- Until Item 8 lands, ordinary governed development in this repo still uses the
  current live workflow command surface.
- Item 8 itself must migrate the repo, docs, and CI to the `run` surface
  coherently in one contract-aligned slice rather than leaving a mixed model.
