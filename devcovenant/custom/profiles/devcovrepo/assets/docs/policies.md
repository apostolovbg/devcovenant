# Policies

## Overview
Use this doc for the repository-facing enforcement model.
Keep the distinction between customizable policies and DevCovenant-owned core
invariants explicit.

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
