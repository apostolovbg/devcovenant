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

- version-governance adapter expectations

- custom policy guidance

## Writing Rules
Avoid drowning readers in descriptor bookkeeping.
Explain the boundary clearly enough that a maintainer can reason about where a
new behavior belongs and which mutation path, if any, is allowed.
