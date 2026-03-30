# Policies

## Overview
Use this doc for the repository-facing enforcement model.
Keep the distinction between customizable policies and DevCovenant-owned core
invariants explicit.
For the full contract taxonomy, keep `devcovenant/docs/contracts.md` nearby.

This page should make it easy to answer three questions:
what is customizable, what is enforced as a core engine boundary, and where a
new behavior belongs when it needs checks, autofix, or an explicit operator
command.

## What This Doc Should Cover
Explain:

- what a policy is

- descriptor metadata and runtime code

- read-only checks versus autofix versus explicit policy commands

- policy runtime actions

- which policies are runtime/workflow plugs versus session-evidence or
  artifact-contract policies

- namespaced policy commands

- dependency-management as one coherent policy surface

- the `requirements.lock` contract for normalized resolution content versus
  environment-specific pip source options

- version-governance adapter expectations

- custom policy guidance

## Writing Rules
Avoid drowning readers in descriptor bookkeeping.
Explain the boundary clearly enough that a maintainer can reason about where a
new behavior belongs and which mutation path, if any, is allowed.
The clean mental model is:

- core invariants are engine-owned boundaries

- runtime/workflow plugs change how commands execute

- session-evidence policies depend on gate/workflow session state

- artifact-contract policies require files or synchronized artifacts to exist

Call out session-scoped policy contracts when they matter. For example,
`changelog-coverage` should be described as gate-session scoped rather than
git-scoped, with the prior top entry preserved by fingerprint anywhere below
the fresh session entry instead of in a hard-coded slot.

## Custom Policy Guidance
In a normal repository, do not seed repo-specific custom policies before the
first reviewed baseline activation.
Start with `install`, config review, and `deploy`, prove that baseline, and
then add custom policies once the normal repo contract is already working.
Keep policy docs explicit when a builtin policy changes how it consumes
tracked registry metadata or workflow-owned command stages.
Builtin policy runtimes now resolve descriptor metadata and script locations
through the dedicated `policy_registry.py` helper layer instead of through a
mixed registry service surface.
The managed-environment policy now also speaks in one execution-environment
contract: reuse the current interpreter when it already satisfies metadata,
bootstrap the selected target only when it is still missing or invalid, and
let gate hooks fall back to `python -m ...` when a Python console-script shim
is absent.
That makes `managed-environment` the clearest runtime/workflow plug on the
policy side of the boundary, while policies such as `modules-need-tests`,
`tests-coverage`, and `dependency-management` remain artifact-contract
policies enforced by the governed check flow.
Namespaced policy-command parsing and runtime-action dispatch now live under
`devcovenant/core/runtime/`, which keeps `devcovenant policy ...` on the same
execution boundary as `run`.
