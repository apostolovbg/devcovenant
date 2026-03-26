# Registry
**Project Version:** 1.0.0

## Overview
This document is the normative home for the registry contract.
Keep `devcovenant/docs/contracts.md` nearby when you need the stable document
map for the rest of the package surfaces.

DevCovenant uses `devcovenant/registry/` for generated state.
Some of that state is tracked and durable.
Some of it is runtime-local and disposable.
Use this page when you need to answer one practical debugging question:
is the thing I am looking at part of the repository's resolved contract, or is
it only local evidence about recent command runs?

Working rule:
read the registry when you need to understand resolved state,
but do not hand-edit generated registry files.

## Tracked Registry
`devcovenant/registry/registry.yaml` is the tracked registry.
It stores deterministic governance state such as:

1. resolved policy metadata

2. resolved core-invariant metadata

3. active project-governance state, including stage, maintenance stance,
   compatibility policy, and versioning mode

4. active profile inventory

5. managed-doc and generation state

6. profile-provided generation fragments, including reusable
   `ci_and_test` additions

7. the resolved `workflow_contract`

8. resolution traces used for auditing and debugging

Packaging and policy-runtime changes can legitimately update tracked-registry
hashes even when the visible behavior change is elsewhere.
That is normal evidence of a real contract change, not registry noise.
In this repository, tracked registry state now also records the repo-specific
`ci_and_test` additions contributed by the active custom profile, including
the scanner steps merged into `ci-and-test` and the dependent
`build-and-install-test` proof for the built wheel, the built sdist, and the
documented `pipx` machine-install path.
That same tracked state also changes when release-facing package-data or
dependency-management semantics change, because the registry records the
resolved metadata the runtime actually uses rather than just the visible
command surface.
That tracked CI metadata can also include a reviewed temporary scanner
exception when an upstream advisory has no published fix release yet.
The tracked registry also depends on deterministic discovery order, so
profiles and policy-source inventories are sorted before refresh writes the
registry on macOS, Linux, or Windows.
That same tracked state also records the current generated workflow contract,
including the visible workflow name `CI` and the repo-specific
`build-and-install-test` verification job.
The tracked `workflow_contract` section is the workflow-owned part of that
story: it records the reserved anchors, the declared phases resolved from
active profiles, and which phase ids are currently required.
That means the tracked registry should now show required phases under
`workflow_contract`, not a legacy `devflow-run-gates.required_commands`
fallback.

Commit tracked-registry changes when they are the result of real repo changes.

## Runtime Registry
`devcovenant/registry/runtime/` stores runtime-local state such as:

- `gate_status.json`

- `workflow_session.json`

- latest-run pointers

- session snapshot companions

This state is about the current or recent command history, not about the
stable repo contract.

## Gate Status
`gate_status.json` is the short gate lifecycle ledger.
It records gate start/end state and the pre-commit evidence those anchors
require.

`workflow_session.json` records the required declared workflow phases for the
session, their pass/fail state, and the last-session/snapshot evidence used to
decide whether a phase is still fresh.

That is why `gate --status` is often the right first command when you need to
know where a slice stands.

## When To Read Which Surface
Read `registry.yaml` when you need to understand:

1. resolved metadata

2. active profiles

3. generated policy or invariant state

4. why one configuration value won over another

5. which workflow phases are required and which profile declared them

6. which profile contributed an extra generated workflow fragment or other
   resolved generation input

7. which cleanup targets came from profiles versus which protected roots came
   from runtime-owned sources such as the managed environment or the active
   clean run directory

Read `registry/runtime/` when you need to understand:

- whether a gate session is open

- whether a required workflow phase has passed for the current session

- what the last relevant run was

- where the latest evidence artifacts live

## What Not To Do
Do not use the registry as a casual editing surface.
If the registry looks wrong, change the config, profile, descriptor, or other
owning input and then refresh.

That applies to retired command surfaces too.
The tracked registry should show only the live namespaced
dependency-management command metadata and should not carry the removed
`update_lock` wrapper path or alias.

The same rule applies to cleanup protection.
The tracked registry may show reusable cleanup targets contributed by active
profiles, but it should not pretend that a language-specific managed
environment root is a global cleanup default.
Managed-environment cleanup protection belongs in the resolved
managed-environment metadata so cleanup can protect a `venv`, a bench, or
another environment type through the same runtime contract.

The same idea applies to packaged README sync.
If the tracked registry shows repo-specific `readme-sync` metadata or
diagnostics, that state should reflect package-facing link rewriting derived
from repository package metadata, not a hardcoded upstream repository URL.
