# Development Plan
**Doc ID:** PLAN
**Doc Type:** plan
**Project Version:** 1.0.0
**Project Stage:** stable
**Maintenance Stance:** active
**Compatibility Policy:** breaking-allowed
**Versioning Mode:** versioned
**Last Updated:** 2026-03-28
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
4. [Workflow-Phase Redesign Baseline](#workflow-run-redesign-baseline)
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
   - required workflow runs and their pass/fail recording
   That boundary must be formalized before the first real SemVer-governed
   line so required workflow behavior does not depend on whether a normal
   policy happens to be enabled.

8. high: the workflow-run redesign is still only partially migrated:
   - core still exposes and teaches a top-level `devcovenant test` command
   - runtime still special-cases the `tests` run instead of treating it as a
     normal declared run under one generic execution path
   - profile schema still leaks command-alias concerns
   - CI, AGENTS, and docs still teach the test-centric workflow instead of the
     generic required-run workflow
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
  - gate session records and required run results
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

- workflow runs that the engine requires and records
- policies that inspect or mutate repository state

Those are different contracts.
A customizable policy must not be part of gate's mechanical foundation.

### Workflow Shape
Core owns three reserved anchors:

- `start`
- `mid`
- `end`

Everything else is a declared workflow run between `mid` and `end`.
The model is therefore:

- `start`
- `mid`
- zero or more declared runs
- `end`

Examples of declared runs:

- `tests`
- `artifact-proof`
- `assurance`
- `schema-validate`
- `manual-attestation`

### Ownership Split
Core owns:

- gate session lifecycle
- anchor runs (`start`, `mid`, `end`)
- workflow-run ordering rules
- runtime session recording
- required-run completion checks
- the command surface for generic run execution
- the shared output/runtime contract, including per-invocation output-mode
  overrides for all commands

Profiles own:

- declared workflow runs
- whether a run is enabled or required
- ordering metadata for those runs
- how a run runs
- the success contract the run uses

Policies own:

- checks
- autofix
- explicit policy commands and runtime actions
- tracked policy descriptors and generated policy artifacts
- policy-local runtime state in a namespaced runtime location or an explicit
  declared location when a policy truly needs one

Builtin versus custom does not decide ownership.
Contract type decides ownership.

### Output-Mode Contract
Output mode should be a core CLI/runtime contract, not a per-command
special case.

That means:

- configuration supplies the default output mode for each command family
- every command and subcommand should also accept:
  - `--quiet`
  - `--normal`
  - `--verbose`
- CLI overrides apply only to the current invocation
- when no CLI override is present, the command should fall back to the
  configured default
- when the CLI override matches the configured default, the command should
  simply continue in that same mode without special behavior

Command modules should stay as mode-agnostic as possible.
They should emit through the shared output/runtime layer and let that layer
decide what becomes visible in:

- `verbose`
- `normal`
- `quiet`

This matters for future built-in or user-defined commands as well.
If command execution, child-process handling, progress reporting, and
run-log pointers all stay under the shared output/runtime layer, future
policy commands and workflow runs can inherit the three output modes
without bespoke command-level verbosity logic.

### Registry Ownership
Tracked core registry data should hold generated workflow truth, for example
in `devcovenant/registry/registry.yaml`:

```yaml
workflow_contract:
  schema_version: 1
  anchors:
    - id: start
      owner: core
      run_kind: gate_anchor
      required: true
    - id: mid
      owner: core
      run_kind: gate_anchor
      required: true
    - id: end
      owner: core
      run_kind: gate_anchor
      required: true
  runs:
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
- declared run results
- required/optional status
- timestamps
- run ids
- attempt counts
- verified SHA or verified tree fingerprint for each run result

The timestamp contract should stay UTC-only.
If the runtime records the last execution time for a run, it should keep
one canonical field such as `last_run_utc`.
It should not duplicate the same UTC value in both `last_run` and
`last_run_utc`.
That kind of duplicated timestamp naming makes the runtime ledger look
half-migrated and creates pointless schema noise without adding information.

### Start-Gate Carry-Forward Rule
`gate --start` must not only open a new session.
It must also care about the last required workflow-extension results.

That means `start` should block when the previous workflow state says a
required declared run is still unclean, failed, missing, or stale in a way
that would have blocked the previous slice from closing honestly.

The intended rule is:

- if the previous required run results are clean and satisfied for the last
  closed session, `start` may open a new session
- if the previous required run results are not clean, `start` must fail and
  require the operator to clear that state first

This must apply to required declared runs generally, not only to today's
hardcoded test expectations.

### End-Gate Rule
`gate --end` must validate:

1. `start` passed for the active session
2. `mid` passed for the active session
3. every required declared run between `mid` and `end` passed for the
   active session
4. only then may `end` pass and close the session

This keeps gate coherent even when different repositories define different
middle runs.

### Phase Runner Kinds
Declared workflow runs should use a closed runner vocabulary:

```yaml
runner:
  kind: command_group | runtime_action | policy_command | manual_attestation
```

Recommended meanings:

- `command_group`: run one or more concrete shell commands
- `runtime_action`: run a core or profile-owned runtime action by id
- `policy_command`: run an explicit policy command surface by id
- `manual_attestation`: record a human-asserted step under an explicit
  attestation contract

The runner payload shape should also stay honest and non-duplicative.
If the runner kind is `command_group`, it should use one field:

```yaml
runner:
  kind: command_group
  commands:
    - python3 -m unittest discover -v
    - pytest
```

That `commands` field should cover both single-command and multi-command
runs.
A single command is just a one-item list.
There is no need for a parallel singular `command` field when the value still
means “shell commands to execute.”

Singular runner payload names should be reserved for genuinely different
concepts, for example:

```yaml
runner:
  kind: runtime_action
  runtime_action_id: refresh-docs
```

```yaml
runner:
  kind: policy_command
  policy_command_id: dependency-lock-refresh
```

That keeps schema branching meaningful instead of forcing the engine, docs,
and tests to carry one field for “one command” and another field for “many
commands” even though they represent the same execution concept.

### Success Contracts
Declared workflow runs should use a closed success-contract vocabulary.
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

- `all_commands_exit_zero`: every command in the run completed successfully
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
If the schema admits a run kind that the runtime cannot execute, the
workflow contract is not yet honest.

### Policy Participation Rule
Policies should not plug into `run` implicitly just because they are enabled.

The workflow contract should stay explicit:

- profiles declare workflow runs
- runs declare a runner kind and a success contract
- the runtime executes that declared run contract
- policies only participate when the run references an explicit runnable
  policy surface

That means:

- enabling a policy does not automatically make it part of `run`
- disabling a structural policy does not mechanically break workflow
- if a workflow run wants policy participation, it should reference an
  explicit policy-owned runnable contract such as `policy_command_id`

This matters directly for `modules-need-tests`.
That policy is still a structural source-to-test alignment rule.
It does not currently own workflow execution, and the plan must not pretend
that it is what powers `devcovenant run`.
The repo's current `tests` workflow run is profile-declared and command-run.
`modules-need-tests` remains a separate structural constraint unless its
responsibility changes deliberately in a later design slice.

### Profile Contribution Schema
Profiles should contribute runs through a dedicated key such as
`workflow_runs`, not indirectly through policy metadata.
For example:

```yaml
workflow_runs:
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

Repo-specific profiles may then contribute runs such as
`artifact-proof` cleanly without pretending they are policies.

The `workflow_runs` declaration should stay focused on run behavior and
must not try to smuggle root-command ownership into profile metadata.

### Command-Surface Target
Core should own the public workflow command surface directly.
The target command set is:

- `devcovenant gate --start`
- `devcovenant gate --mid`
- `devcovenant run`
- `devcovenant gate --end`

The explicit rerun surface is:

- `devcovenant run`

Under this target model:

- `devcovenant run` executes all enabled required declared runs for the
  active session in deterministic order
- `devcovenant run` executes exactly one declared run
- `devcovenant test` does not remain a top-level root command
- profiles do not define or own top-level CLI aliases

This keeps workflow execution generic, keeps root command ownership in core,
and stops the `tests` run from looking privileged by command-surface
accident.

### `run` Contract
`devcovenant run` should:

1. resolve the active tracked workflow contract
2. collect enabled required runs between `mid` and `end`
3. execute them in deterministic declared order
4. record each run result in the runtime workflow session
5. stop on first required-run failure
6. exit zero only when all required runs for that run pass

If no required runs exist, `run` should:

- report that there are no required declared runs for the active contract
- exit successfully without pretending work happened

### No Profile-Owned Command Aliases
Profiles own:

- run ids
- run ordering
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

1. formalize the workflow-run schema and runtime-session schema
2. migrate the current `test` run onto that contract first
3. update `devflow-run-gates` to validate declared required runs instead of
   hardcoded required commands
4. then add any new intermediate runs through profile-owned workflow
   metadata rather than policy enablement side effects

### Current Design Correction
The first workflow-run migration landed only part of the intended design.
It correctly introduced:

- tracked `workflow_contract`
- runtime `workflow_session.json`
- required-run enforcement in `gate --start` and `gate --end`
- profile-owned declaration of the `tests` run

But it still left visible half-step behavior in place:

- top-level `devcovenant test` remains a root command
- runtime still special-cases the `tests` run
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
   - the generated `CI` workflow now proves that the built wheel
     and built sdist can complete
     `install -> config review -> deploy -> check` in a temporary git
     repository
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
     profile-declared runs, required-run ids, runner kinds, and
     success-contract kinds
   - added `devcovenant/core/runtime/workflow_session.py` and the runtime
     `devcovenant/registry/runtime/workflow_session.json` surface so core
     workflow state is no longer squeezed into `gate_status.json`
   - kept `gate_status.json` as the short lifecycle and pre-commit ledger,
     while moving required-run truth into `workflow_session.json`
   - moved the Python stack's `tests` run into the builtin Python profile's
     new `workflow_runs` declaration instead of keeping workflow truth in
     `devflow-run-gates.required_commands`
   - added the generic `devcovenant run` command surface as the
     first explicit one-run runner
   - updated `gate --start` so recovery start blocks when the previous closed
     session has stale required runs, not only stale tests
   - updated `gate --end` so closure requires fresh passing evidence for every
     required declared run bound to the active session
   - updated `devflow-run-gates` so it validates pre-commit evidence from
     `gate_status.json` and required-run evidence from
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
   - runtime workflow sessions record anchors and declared runs separately
   - start and end gates validate declared required runs generally rather
     than only one hardcoded test-centric case
   - `tests` is the first real declared workflow run under the new contract
   - the remaining redesign work is no longer about inventing workflow runs;
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
     - `CI` proves the governed run plus scanner steps
     - `Build` proves real artifact lifecycle from the tested SHA
     - `Publish` consumes a selected successful `Build` artifact and verifies
       provenance instead of rebuilding
   - reran focused regressions for the remaining truthfulness surfaces:
     - dependency-lock semantics
     - workflow-run/gate contract
     - workflow-session / required-run recording
     - package-doc contract wording
   What is now true:
   - the external-grade audit no longer finds substantive blocker or
     high-severity mismatches in shipped artifacts, CI proof, publish
     provenance, dependency-lock semantics, installation/customization docs,
     or workflow-contract truthfulness
   - that audit closed the earlier artifact, publish, lockfile, and
     first-activation remediation set
   - a later workflow-command audit then identified the still-half-migrated
     `devcovenant test` / workflow-run command model captured in Item 8

8. [not done] Complete The `run` / Workflow-Phase Migration.
   Goal:
   - replace the test-centric public workflow with one core-owned generic
     workflow execution surface
   - make workflow extensions look native in code, docs, CI, and operator
     messaging
   - align runtime support with the full tracked schema so no allowed run
     contract remains a paper-only promise
   - close the remaining contract-hardening gaps around the now-landed `run`
     model so the public workflow surface is truly settled instead of merely
     functional
   Why this matters:
   - the core `run` migration is now materially landed, but the item remains
     open because the adjacent workflow contracts are not all fully locked yet
   - the repo no longer teaches `devcovenant test`, but some workflow behavior
     is still expressed through transitional test-shaped or run-specific
     assumptions
   - schema truth must match runtime truth before the first SemVer-governed
     public line
   - public-contract features such as advanced workflow run kinds, output
     overrides, and artifact-check path semantics should not remain half-
     documented or only implicitly owned
   Design decisions for this item:
   - `devcovenant run` is the top-level command that replaces
     `devcovenant test`
   - `devcovenant run` executes all enabled required declared runs for the
     active session in deterministic order
   - `devcovenant run` remains the explicit one-run rerun surface
   - top-level workflow commands are core-owned, not profile-owned
   - profile run metadata must not define command aliases
   - the visible GitHub Actions workflow name should be `CI`, because `CI`
     is standard, includes tests naturally, and avoids the GitHub sidebar
     ambiguity created by `Workflows`
   - the main generated CI job should use a focused display name such as
     `DevCovenant`, while the dependent repo-specific job should keep a
     concrete name such as `Build and Install`
   - workflow runtime timestamps stay UTC-only and keep one canonical
     timestamp field such as `last_run_utc`
   - command-group runs use `commands` only; a single command is a
     one-item list, not a separate singular schema branch
   - singular execution payload names are reserved for different concepts such
     as `runtime_action_id` or `policy_command_id`; shell command groups must
     not duplicate the same meaning across parallel `command` / `commands`
     fields
   - policies do not participate in `run` implicitly just because they are
     enabled; workflow runs must reference explicit runnable surfaces
   - run-specific richer behavior is allowed, but it must be expressed
     through generic run-reporting hooks or declarative run metadata,
     not through hardcoded `run_id == "tests"` branches in the generic
     workflow executor
   - changelog-only freshness behavior must become an explicit workflow-run
     contract rather than a hidden `tests`-only rule; if changelog-only edits
     should not stale a required run, that exemption must be modeled in
     run metadata and documented as part of the workflow contract
   - file-dependent success checks must stay generic and support:
     `required_files`, `required_globs`, `forbidden_globs`, plus explicit
     relative-versus-absolute path resolution control so any run can verify
     files at any intended path without bespoke runtime branching
   - the advanced workflow kinds are now public workflow-contract surface, not
     merely internal extension hooks:
     `command_group`, `runtime_action`, `policy_command`,
     `manual_attestation`, `all_commands_exit_zero`,
     `runtime_action_success`, `policy_command_success`,
     `manual_attested`, and `external_artifact_check` all need explicit docs,
     examples, and tests
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
      - `devcovenant/run.py`
      Work to do:
      - add the top-level `run` command
      - remove `test` from the public root-command dispatcher
      - keep explicit single-run execution in `run`
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
      - make declared runs execute through one generic path
      - keep policy participation explicit so a run only invokes policy-owned
        behavior when it references a deliberate runnable surface
      - replace remaining `tests`-specific richer behavior with a generic
        run-reporting hook/declarative metadata path so any workflow run
        can opt into the same richer reporting without a hardcoded run id
      - replace the current hidden `tests`-only changelog freshness shortcut
        with an explicit run-freshness contract that can be declared and
        reasoned about generically
      - support every allowed runner kind:
        `command_group`, `runtime_action`, `policy_command`,
        `manual_attestation`
      - support every allowed success-contract kind:
        `all_commands_exit_zero`, `runtime_action_success`,
        `policy_command_success`, `manual_attested`,
        `external_artifact_check`
      - make runtime failures mention `devcovenant run` or
        `devcovenant run`, not `devcovenant test`
      Done when:
      - `tests` is not privileged in runtime flow control or freshness rules
      - enabled policies do not implicitly alter what `run` executes
      - any allowed schema kind is truly executable
      - changelog-only rerun exemptions, if any, are run-declared rather
        than hardcoded by run id

   3. Universal output-mode override contract.
      File scope:
      - `devcovenant/cli.py`
      - shared parser/bootstrap helpers
      - `devcovenant/core/runtime/output.py`
      - `devcovenant/core/runtime/execution.py`
      - command modules that still bypass the shared output/runtime layer
      Work to do:
      - add mutually exclusive `--quiet`, `--normal`, and `--verbose`
        overrides to every top-level command and subcommand surface
      - make the per-invocation override win over config only for that one
        invocation
      - fall back to the configured output mode when no override is supplied
      - treat a CLI override that matches the configured mode as a no-op
      - keep command modules mode-agnostic wherever possible so they do not
        own custom verbosity branches
      - route remaining bespoke command output through the shared
        output/runtime module so future policy commands and workflow runs
        inherit the three modes automatically
      Done when:
      - every public command accepts `--quiet`, `--normal`, or `--verbose`
      - output-mode precedence is consistently CLI override first, config
        default second
      - commands no longer need bespoke verbosity logic to participate in the
        three-mode system

   4. Gate and invariant migration.
      File scope:
      - `devcovenant/core/flow/gate.py`
      - `devcovenant/core/services/devflow_run_gates.py`
      - `devcovenant/core/contracts/invariants/devflow_run_gates.yaml`
      - `devcovenant/core/runtime/workflow_session.py`
      Work to do:
      - render rerun instructions through `run` by default
      - keep explicit `run` wording for targeted recovery cases
      - make `start` carry-forward checks and `end` closure checks speak in
        required-run language consistently
      - reduce or retire leftover dependence on `gate_status.json` for run
        truth where `workflow_session.json` is the real source
      - keep the remaining split honest:
        `gate_status.json` is the short gate/pre-commit ledger,
        `workflow_session.json` is required-run truth
      Done when:
      - gate messaging no longer teaches `devcovenant test`
      - the invariant validates anchors plus required runs without any
        test-centric fallback language

   5. Workflow-contract schema cleanup.
      File scope:
      - `devcovenant/core/flow/workflow_contract.py`
      - `devcovenant/core/services/profile_registry.py`
      - `devcovenant/core/flow/refresh.py`
      - `devcovenant/registry/registry.yaml`
      - profile manifests such as
        `devcovenant/builtin/profiles/python/python.yaml`
      Work to do:
      - remove command-surface alias ownership from profile metadata
      - keep run metadata focused on run behavior only
      - add an explicit run-freshness contract so rerun invalidation rules
        are declared rather than hidden in executor code
      - remove duplicate timestamp fields when they carry the same UTC value
        and keep one canonical workflow runtime timestamp field such as
        `last_run_utc`
      - collapse command-group payloads to `commands` only
      - reserve singular payload names for non-shell ids such as
        `runtime_action_id` and `policy_command_id`
      - tighten file-dependent success contracts so they can express
        required/forbidden file checks against relative or absolute paths
        without bespoke per-run code
      - decide and document the final path contract for workflow evidence:
        either keep `workflow_session.json` runtime-owned and fixed, or
        expose a formal configurable counterpart to `gate_status_file`
      - regenerate tracked registry output to match the final contract
      Done when:
      - profile manifests declare runs, not root command aliases
      - runtime session payloads do not carry same-value timestamp aliases
      - command-group schema no longer duplicates `command` and `commands`
      - run freshness rules are explicit in schema rather than implicit in
        code
      - file-dependent success checks have one generic schema that is not
        tied to test/artifact-only assumptions
      - tracked registry reflects the final command-neutral run schema

   6. CI and generated workflow migration.
      File scope:
      - `.github/workflows/ci-and-test.yml`
      - `.github/workflows/build.yml`
      - `devcovenant/builtin/profiles/global/assets/ci-and-test.yml`
      - any release/build workflows that still teach the old command shape
      Work to do:
      - replace `python -m devcovenant test` with the new top-level
        `python -m devcovenant run`
      - rename the generated workflow from `Workflows` to `CI`
      - rename the main generated job to `DevCovenant`
      - keep the dependent repo-specific verification job under the concrete
        name `Build and Install`
      - keep repo-maintained release workflows (`Build`, `Publish`) distinct
        from the generated CI workflow so the Actions sidebar reads clearly
      - ensure lifecycle-proof shell steps stay parse-stable in GitHub
        Actions and do not rely on fragile indented subshell heredocs
      - make the repo-maintained `Build` workflow listen to the final
        generated CI workflow name
      - keep explicit `run` only where a specific rerun is
        intentionally needed
      Done when:
      - generated GitHub Actions surfaces teach the same workflow contract as
        AGENTS and the docs
      - GitHub Actions reads cleanly as `CI`, `Build`, and `Publish`
        without naming collisions or redundant workflow labels
      - built-artifact lifecycle proof executes cleanly in GitHub Actions
        instead of failing on shell-shape quirks

   7. Full documentation and managed-asset rewrite.
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
      - `PROFILE_MAP.md` / profile-map assets
      - matching global/profile doc assets
      Work to do:
      - rewrite the canonical workflow as
        `gate --start -> gate --mid -> run -> gate --end`
      - replace test-centric recovery wording with required-run wording
      - explain the universal output-mode override contract:
        - config sets the default mode
        - `--quiet`, `--normal`, and `--verbose` override per invocation
        - commands should remain mode-agnostic and rely on the shared output
          layer
      - publish the workflow-run contract explicitly:
        - supported runner kinds
        - supported success-contract kinds
        - compatible runner/success combinations
        - how freshness rules are declared
        - how file-dependent success checks resolve paths
      - explain clearly that:
        - core owns workflow commands
        - profiles own declared runs
        - policies do not own workflow structure
      - remove claims that `devcovenant test` is a friendly alias
      - remove ownership drift such as old `core/services/event.py` references
        or stale `required test commands` language in config docs
      Done when:
      - there is no stale public instruction to run `devcovenant test`
        outside historical changelog context
      - the public docs describe the full workflow-run contract instead of
        only the built-in `tests` run example

   8. Test-suite migration.
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
      - add coverage that every public command accepts `--quiet`,
        `--normal`, and `--verbose`
      - add coverage that CLI overrides beat config for a single invocation
        without mutating config
      - add coverage that workflow-session runtime fields stay UTC-only
        without duplicate same-value aliases
      - add coverage that `command_group` runners use `commands` only and that
        single-command runs remain one-item command lists
      - add coverage that enabled structural policies do not implicitly become
        workflow-run executors
      - add coverage that each supported runner kind and each supported
        success-contract kind is actually executable under the runtime
      - add coverage that advanced public workflow kinds are not only schema-
        accepted but operator-usable, including `manual_attestation`,
        `runtime_action_success`, `policy_command_success`, and
        `external_artifact_check`
      - add coverage that run freshness rules are contract-driven rather
        than hidden in a `tests`-only branch
      - add coverage that start and end guidance names `run` and targeted
        `run` correctly
      Done when:
      - the test suite locks the final generic workflow surface instead of the
        old alias model
      - the advanced workflow-run contract is publicly proved rather than
        only accepted by parser/runtime internals

   9. Policy naming follow-up decision.
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
   - `devcovenant run` is the explicit per-run rerun path
   - `devcovenant test` is no longer a public root command
   - every public command accepts universal per-invocation `--quiet`,
     `--normal`, and `--verbose` overrides
   - command output behavior is owned by the shared output/runtime layer
     rather than bespoke per-command verbosity branches
   - workflow runtime timestamps stay UTC-only under one canonical field name
   - command-group schema uses `commands` only instead of parallel
     `command`/`commands` execution payloads
   - enabled policies do not implicitly plug into `run`
   - runtime no longer special-cases `tests`; richer behavior is exposed
     through generic run hooks/metadata instead
   - every allowed runner kind and success-contract kind is actually supported
   - profile run metadata no longer leaks command-alias ownership
   - AGENTS, docs, CI, and gate messages all teach the same workflow
   - any remaining references to `devcovenant test` are historical only

9. [not done] De-Spaghettize Core Workflow Architecture.
   Goal:
   - realign the core module layout with the actual ownership boundaries that
     the `run` / workflow-session redesign introduced
   - stop leaving workflow truth split across policy-era carryovers,
     crowded `core/services` modules, and duplicated validation surfaces
   - make the code layout describe the architecture we actually want to keep
     after the first SemVer-governed public line
   Why this matters:
   - the `run` redesign is large enough that the architecture should move
     with it instead of staying frozen in pre-redesign folder boundaries
   - `core/services` has grown into a crowded mixed-responsibility area
     instead of a narrow home for true shared services
   - `devflow_run_gates`, `devcov_integrity_guard`, and
     `devcov_structure_guard` still read partly like policy-era carryovers
     from the time when these concepts lived closer to normal policy shapes
   - if the code keeps those legacy placements and duplicated logic islands,
     the redesign will continue to feel stitched together even after the
     public command surface is cleaned up
   Design decisions for this item:
   - workflow truth should have one authoritative home, centered around
     `core/flow` and `core/runtime`, with contracts and schemas remaining in
     `core/contracts`
   - `core/services` should shrink back to true shared services rather than
     acting as the drawer where any hard-to-place core logic accumulates
   - `devflow_run_gates` should dissolve into shared flow/runtime
     workflow-validation logic instead of surviving as a standalone
     invariant-style logic island
   - `devcov_integrity_guard` and `devcov_structure_guard` should be
     re-evaluated as thin validators, merged concepts, or relocated modules
     instead of staying as unquestioned policy-era carryovers
   - the schema-tightening decisions from Item 8 are part of this
     architectural cleanup in implementation terms:
     UTC-only `last_run_utc`, `commands`-only command groups, explicit
     run-freshness contracts, and explicit policy participation need one
     clean module ownership story, not just good field names
   - generic run-event/reporting infrastructure should stop carrying
     `test_events` / `TestEvent*` naming once it is the shared workflow-run
     reporting system for all run types
   - registry/runtime ownership should split by both ephemerity and contract
     ownership, not just by one axis:
     tracked core-owned state, tracked extension-owned state, runtime
     core-owned state, and runtime policy-owned state should not all keep
     sharing one generic registry implementation module
   - generic run-reporting hooks belong to the workflow/runtime ownership
     story as well:
     special richer reporting must be run-declarative and reusable, not
     hidden inside one tests-only branch
   Work packages in dependency order:
   1. Core ownership audit.
      File scope:
      - all modules under `devcovenant/core/**`
      Work to do:
      - classify each module as primarily:
        - flow
        - runtime
        - contract/schema
        - service
        - validation/integrity
        - compatibility carryover
      - identify modules whose folder placement no longer matches their real
        responsibility after the `run` redesign
      Done when:
      - the repo has an explicit ownership map for the current core tree
      - drift candidates are named instead of hand-waved

   2. Workflow-truth consolidation.
      File scope:
      - `devcovenant/core/flow/**`
      - `devcovenant/core/runtime/**`
      - dissolution path for `devflow_run_gates*`
      Work to do:
      - move, merge, rename, or dissolve modules so workflow truth is not
        implemented in multiple disconnected places
      - absorb `devflow_run_gates` behavior into the flow/runtime ownership
        story instead of keeping a second major implementation island
      - keep gate behavior, required-run validation, workflow session
        recording, and rerun guidance centered around one coherent flow/runtime
        story
      Done when:
      - workflow truth is not split across a dissolved legacy invariant island
        and a separate flow/runtime system

   3. Guard-module re-hash.
      File scope:
      - `devcov_integrity_guard`
      - `devcov_structure_guard`
      - `devflow_run_gates`
      Work to do:
      - decide for each whether it remains:
        - a thin validator
        - a moved/renamed module
        - a merged concept
        - or a deleted compatibility carryover
      - explicitly dissolve `devflow_run_gates` into shared flow/runtime
        validation code
      - strip stale workflow/schema assumptions out of
        `devcov_integrity_guard` so it validates the final UTC-only runtime
        state instead of legacy `last_run` / test-command contracts
      Done when:
      - the three guard/invariant-era modules are justified by present
        architecture rather than by history

   4. `core/services` reduction.
      File scope:
      - `devcovenant/core/services/**`
      Work to do:
      - move misplaced flow/runtime logic out of `core/services`
      - merge paper-thin wrappers that only preserve old layering myths
      - split overloaded modules when one file is acting as several domains at
        once
      - keep only true cross-cutting shared services there
      Done when:
      - `core/services` is no longer the default parking area for unrelated
        core logic

   5. Registry split by ephemerity and ownership.
      File scope:
      - `devcovenant/core/services/registry.py`
      - runtime-registry helpers
      - tracked-registry helpers
      - any callers that currently rely on the mixed registry facade
      Work to do:
      - separate tracked and runtime registry concerns instead of keeping one
        broad registry module for both
      - further separate ownership concerns so core-owned tracked/runtime
        state and extension-owned tracked/runtime state do not blur into one
        implementation bucket
      - make path helpers, registry serializers, and ownership-specific
        helpers live where their contract actually belongs
      Done when:
      - tracked versus runtime state is explicit in code structure
      - ownership boundaries are explicit in code structure
      - one generic `registry.py` no longer carries all registry meanings

   6. Schema and runtime cleanup.
      File scope:
      - workflow-session runtime state
      - workflow-contract parsing
      - any supporting serializers/deserializers
      Work to do:
      - implement the final UTC-only timestamp contract with
        `last_run_utc` as the canonical field
      - remove duplicated same-value aliases such as `last_run`
      - implement the final `commands`-only command-group payload contract
      - keep policy participation explicit rather than implicit in runtime
        orchestration
      - move richer per-run reporting onto generic run hooks/metadata so
        special reporting is reusable by any run
      - finish generalizing the run-event/reporting subsystem so names such
        as `test_events`, `TestEvent`, and related counters no longer pretend
        the shared contract belongs only to the `tests` run
      - keep file-dependent success checks generic, including explicit
        absolute/relative path resolution controls
      - formalize whether workflow evidence paths are fixed runtime-owned
        paths or configurable contract surfaces, and make both docs and code
        tell the same story
      Done when:
      - the runtime/session schema is non-duplicative and matches the plan's
        final contract
      - generic run reporting no longer wears test-only names by accident

   7. Documentation, registry, and test rewrite for the new architecture.
      File scope:
      - `devcovenant/docs/architecture.md`
      - `devcovenant/docs/workflow.md`
      - `devcovenant/docs/registry.md`
      - `PLAN.md`
      - core architecture tests and workflow-contract tests
      Work to do:
      - rewrite architecture explanations to reflect the final ownership map
      - remove stale service/invariant myths from docs and test expectations
      - ensure registry/runtime docs describe one truthful ownership model
      - document generic run-reporting hooks and generic file-dependent
        success checks as reusable workflow features instead of tests-only
        exceptions
      Done when:
      - docs and tests describe the post-de-spaghettized architecture instead
        of the policy-era carryover layout

   Done when:
   - workflow truth has one coherent implementation story
   - `core/services` is reduced to true services
   - `devflow_run_gates` disappears as a standalone major implementation and
     its behavior lives in the core flow/runtime story
   - the guard modules are justified by current architecture instead of
     historical inertia
   - the runtime/session schema is non-duplicative
   - registry code is split by both ephemerity and ownership
   - richer run behavior is generic and declarative, not hardcoded to
     `tests`
   - run-event/reporting internals no longer remain misleadingly test-only
     once they are shared workflow runtime machinery
   - the code layout looks like the architecture DevCovenant actually claims
     to have

10. [not done] Prepare The First Real Release Candidate.
   Goal:
   - start the real release-candidate cut only after the external-grade
     remediation audit is clean, the `run` migration is complete, and the
     follow-up architecture cleanup is no longer deferred.
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
  2. `devcovenant run`
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
  3. start-gate carry-forward failure tests for unresolved required runs
  4. end-gate closure tests for required declared runs
  5. run-runner tests for each supported runner kind in scope
  6. success-contract tests for each supported success-contract kind in scope
  7. `devcovenant run` orchestration tests for ordered required-run execution
  8. root-command tests that `devcovenant test` is retired from the public CLI
     once the migration lands
  9. universal output-mode override tests for all command families in scope
  10. policy-state ownership tests so mutable policy-local state stays out of
     tracked or packaged source surfaces unless explicitly declared

- For core architecture cleanup work, also run:
  1. ownership-map tests or direct assertions that moved modules now live
     under the right core subdomain
  2. regression tests for any renamed or relocated guard/validation modules
  3. workflow-session schema tests covering `last_run_utc` as the canonical
     timestamp field
  4. command-group schema tests covering `commands`-only execution payloads
  5. architecture/doc contract tests that the new ownership map is described
     consistently across docs and registry/runtime surfaces

- Until Item 8 lands, ordinary governed development in this repo still uses the
  current live workflow command surface.
- Item 8 itself must migrate the repo, docs, and CI to the `run` surface
  coherently in one contract-aligned slice rather than leaving a mixed model.
