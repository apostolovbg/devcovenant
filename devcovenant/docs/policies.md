# Policies
**Last Updated:** 2026-03-23
**Project Version:** 1.0.0

## Overview
This document is the normative home for the policy descriptor contract.
Use it together with `devcovenant/docs/contracts.md` when you need the stable
boundary between configurable policy behavior, autofix, commands, and core
invariants.

Policies are the customizable enforcement units in DevCovenant.
Each policy combines descriptor metadata, runtime check logic, and optional
autofix support.

Policies are different from core invariants.
Policies are repository-governance surfaces.
Core invariants are DevCovenant-owned runtime boundaries.

## What A Policy Contains
A normal policy directory contains:

- a descriptor YAML file

- a runtime check file

- optional autofix helpers

- optional assets

The descriptor declares metadata and human-facing prose.
The runtime code enforces the rule.

## Activation And Metadata
Policy activation is controlled by `config.policy_state`.
Profile overlays and config overrides then tune how enabled policies behave.

That means the usual control split is:

- config decides whether a customizable policy is on or off

- profiles and metadata decide how it behaves

- runtime enforces the result

## Checks, Autofix, And Commands
The boundary here is important:

- checks inspect and report

- autofixers mutate during autofix-enabled check flows

- explicit policy commands perform deliberate operator actions

Checks should not mutate files directly.
That keeps the runtime honest and makes side effects easier to reason about.

## Policy Runtime Actions
A policy can expose runtime actions.
Those actions are the reusable operational surface a policy command or autofix
can call.

For example, the dependency-management policy can expose refresh actions that:

- refresh lock state

- refresh dependency and license artifacts

- refresh the whole dependency-management output set

The same runtime action can then be used by:

- an autofixer

- a manual policy command

The managed-environment policy also exposes runtime-owned environment context
that other services can consume safely.
One example is cleanup protection: cleanup may ask the managed-environment
runtime which roots should stay protected, using explicit
`cleanup_protected_paths` metadata first and falling back to `expected_paths`
when no custom cleanup roots are declared.

## Policy Commands
DevCovenant now supports namespaced policy commands.
The intended shape is:

```bash
devcovenant policy <policy-id> <command>
```

That keeps policy-owned operations explicit and prevents the CLI from turning
into a pile of unrelated one-off top-level commands.

Dependency management now uses only the namespaced policy command surface.

## Dependency Management
Dependency management is now one coherent policy surface.
It owns dependency refresh, dependency inventory, and license/report
synchronization together instead of splitting those behaviors across separate,
loosely connected commands or policies.

That gives custom repositories one policy to customize rather than several
half-overlapping surfaces.

## Version-Governance Adapter Contract
Version-governance adapters define how version schemes are parsed,
validated, normalized, and compared.
They are part of the stable extension surface because repositories can choose
scheme behavior that is stricter than raw string equality.

## Custom Policies
Custom policies live under `devcovenant/custom/policies/<id>/` and use the
same descriptor-plus-runtime model as builtin ones.
They should follow the same boundary discipline:

- checks report

- autofixers fix

- commands run explicit operations

## Practical Guidance
When changing a policy, update all of the following together:

1. descriptor prose and metadata
2. runtime code
3. tests
4. user-facing docs when behavior changes

That is what keeps the policy surface readable instead of turning it into code
that only the runtime understands.
