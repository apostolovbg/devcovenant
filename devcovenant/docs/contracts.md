# Contracts
**Last Updated:** 2026-03-30
**Project Version:** 1.0.0

## Overview
This document is the contract map for the DevCovenant package docs.
Use it when you need to answer two questions cleanly:

1. what kind of contract am I looking at?
2. which document owns the explanation for that contract?

The goal is not to turn every package doc into a competing master index.
The goal is to keep one stable map of ownership and vocabulary so the rest of
package documentation can stay readable.

## Contract Kinds
DevCovenant has four distinct contract kinds.
Keeping them separate is the key to understanding how the runtime fits
together.

### 1. Core Invariants
Core invariants are DevCovenant-owned runtime boundaries.
They are not repository policies.
They are always enforced, always critical, and not repository-toggle surfaces.

Examples include:

- repository structure requirements
- descriptor and registry integrity requirements
- gate and workflow evidence requirements

Core invariants may still have invariant-specific runtime knobs, but those
knobs live in dedicated config sections such as `paths.*` and `workflow.*`.
They do not live in `policy_state`, and they do not use their own policy
activation/config section.

Canonical docs:

- `devcovenant/docs/architecture.md`
- `devcovenant/docs/workflow.md`
- `devcovenant/docs/config.md`
- `devcovenant/docs/registry.md`

### 2. Runtime And Workflow Plugs
Some behavior plugs directly into command execution rather than merely
checking repository state after the fact.
This is the most execution-sensitive integration pattern in the system.

Examples include:

- the managed-environment runtime choosing or preparing the interpreter
- the workflow invariant enforcing gate and run evidence ordering

These plugs affect how `gate` and `run` execute, which environment they use,
and which evidence must exist for the session to close.

Canonical docs:

- `devcovenant/docs/workflow.md`
- `devcovenant/docs/architecture.md`

### 3. Session-Evidence Policies
Some policies depend on gate-session state or workflow-session evidence.
They are still customizable policies, but their truth depends on the active
session, not only on a static file scan.

The clearest example is `changelog-coverage`, which compares the live session
against the gate-start snapshot instead of pretending git history alone owns
the contract.

Canonical docs:

- `devcovenant/docs/policies.md`
- `devcovenant/docs/workflow.md`

### 4. Artifact-Contract Policies
Most policies are artifact-contract policies.
They require files, companion artifacts, or synchronized state to exist and
stay aligned.

Examples include:

- `modules-need-tests`
- `tests-coverage`
- `dependency-management`
- `documentation-growth-tracking`
- `version-sync`
- `version-governance` when enabled

These policies do not plug into the executor itself.
They are enforced by the governed check flow.
If the required files or synchronized artifacts are missing or stale, the gate
fails until the repository state is corrected.

Canonical docs:

- `devcovenant/docs/policies.md`
- `devcovenant/docs/config.md`

## Document Ownership Map
The stable document ownership split is:

- `devcovenant/docs/installation.md`
  installation, deploy, upgrade, uninstall, and first-review flow

- `devcovenant/docs/workflow.md`
  gate sequence, workflow evidence, CI shape, and execution-time plugs

- `devcovenant/docs/config.md`
  public `devcovenant/config.yaml` contract and ownership model

- `devcovenant/docs/policies.md`
  customizable policy model, runtime actions, and artifact/session policy
  boundaries

- `devcovenant/docs/project_governance.md`
  repository lifecycle and compatibility metadata

- `devcovenant/docs/registry.md`
  tracked registry structure, runtime ledgers, and invariant/policy registry
  state

- `devcovenant/docs/refresh.md`
  managed-doc refresh and descriptor-driven materialization

- `devcovenant/docs/architecture.md`
  runtime layer ownership and invariant-versus-policy architecture

## Writing Rule
When behavior changes, update the owning contract page first.
Then update summaries, templates, maps, or supporting docs that point back to
that page.

That keeps the package docs honest without forcing every document to explain
every other document's job.
