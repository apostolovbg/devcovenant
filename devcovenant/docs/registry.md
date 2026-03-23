# Registry
**Last Updated:** 2026-03-23
**Project Version:** 1.0.0

## Overview
This document is the normative home for the registry contract.
Use it together with `devcovenant/docs/contracts.md` when you need the stable
meaning of tracked registry state versus runtime-local registry state.

DevCovenant uses `devcovenant/registry/` for generated state.
Some of that state is tracked and durable.
Some of it is runtime-local and disposable.

The safest working rule is simple:
read the registry when you need to understand resolved state,
but do not hand-edit generated registry files.

## Tracked Registry
`devcovenant/registry/registry.yaml` is the tracked registry.
It stores deterministic governance state such as:

1. resolved policy metadata

2. resolved core-invariant metadata

3. active profile inventory

4. managed-doc and generation state

5. profile-provided generation fragments, including reusable
   `ci_and_test` additions

6. resolution traces used for auditing and debugging

Commit tracked-registry changes when they are the result of real repo changes.

## Runtime Registry
`devcovenant/registry/runtime/` stores runtime-local state such as:

- `gate_status.json`

- latest-run pointers

- session snapshot companions

This state is about the current or recent command history, not about the
stable repo contract.

## Gate Status
`gate_status.json` is the short session ledger.
It records lifecycle state for the current gate session and the latest test
run that belongs to it.

That is why `gate --status` is often the right first command when you need to
know where a slice stands.

## When To Read Which Surface
Read `registry.yaml` when you need to understand:

1. resolved metadata

2. active profiles

3. generated policy or invariant state

4. why one configuration value won over another

5. which profile contributed an extra generated workflow fragment or other
   resolved generation input

Read `registry/runtime/` when you need to understand:

- whether a gate session is open

- what the last relevant run was

- where the latest evidence artifacts live

## What Not To Do
Do not use the registry as a casual editing surface.
If the registry looks wrong, change the config, profile, descriptor, or other
owning input and then refresh.
