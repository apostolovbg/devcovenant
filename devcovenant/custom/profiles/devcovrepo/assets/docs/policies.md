# Policies
**Project Version:** 1.0.0

## Overview
This document is the normative home for the policy descriptor contract.
Policies are the configurable enforcement units in DevCovenant.
Each policy combines descriptor metadata, runtime check logic, and optional
runtime actions.

Use this page when you need to decide whether a behavior belongs in a policy
at all and, if it does, whether it should surface as a check, an autofixer,
a runtime action, or an explicit policy command.

Built-in runtime checks such as workflow validation, integrity validation,
and structure validation are separate engine behavior.
This page is about repository-facing policy surfaces.

## What A Policy Contains
A normal policy directory contains:

- a descriptor YAML file
- a runtime check file
- optional autofix helpers
- optional assets or support files

The descriptor declares metadata and human-facing prose.
The runtime code enforces the rule.

## Activation And Metadata
Policy activation is controlled by `config.policy_state`.
Profile overlays and config overrides then tune how enabled policies behave.

That means the usual control split is:

- config decides whether a policy is on or off
- profiles and metadata decide how it behaves
- runtime enforces the result

## Checks, Autofix, And Commands
The boundary here is important:

- checks inspect and report
- autofixers mutate during autofix-enabled check flows
- explicit policy commands perform deliberate operator actions

Checks should not mutate files directly.
That keeps the runtime honest and makes side effects easier to reason about.
One important example is `changelog-coverage`: it is gate-session scoped, not
git-scoped.

## Policy Runtime Actions
A policy can expose runtime actions.
Those actions are the reusable operational surface a policy command or
autofix can call.

For example, dependency management can expose refresh actions that update:

- lock state
- dependency reports
- license artifacts
- the whole dependency-management output set

The managed-environment policy also exposes runtime-owned environment context
that other services can consume safely.
It resolves one target execution environment, reuses it when it already
satisfies the contract, and only runs `managed_commands` when the selected
environment is missing or invalid.
For Python-owned tools such as the gate hook, execution prefers the
environment's console script and resolves `python -m ...` through the same
interpreter when the shim is absent.

## Policy Commands
DevCovenant supports namespaced policy commands.
The intended shape is:

```bash
devcovenant policy <policy-id> <command>
```

That keeps policy-owned operations explicit and prevents the CLI from turning
into a pile of unrelated top-level commands.
The command-definition parser and runtime-action dispatcher live under
`devcovenant/core/runtime/` so policy commands run through the same execution
boundary as the rest of the CLI.

## Dependency Management
Dependency management is one coherent policy surface.
It owns dependency refresh, dependency inventory, and license/report
synchronization together instead of splitting them across loosely connected
commands or policies.

For Python repositories, `requirements.lock` follows a stricter contract:
it represents normalized dependency-resolution content, not environment-local
pip control lines.
Refresh strips environment-specific directives from both semantic comparison
and the written lock body so repositories keep package-source behavior in
metadata/config instead of baking it into the lock file.

## Version-Governance Adapter Contract
Version-governance adapters define how version schemes are parsed,
validated, normalized, and compared.
They are part of the stable extension surface because repositories can choose
scheme behavior that is stricter than raw string equality.

## Custom Policies
Custom policies live under `devcovenant/custom/policies/<id>/` and use the
same descriptor-plus-runtime model as builtin policies.
They should follow the same boundary discipline:

- checks report
- autofixers fix
- commands run explicit operations

Custom policies that inspect managed docs should treat the generated header
model as a stable contract.
That means header-aware checks need to expect the current project-governance
header set when a document opts into those headers.

## Practical Guidance
When changing a policy, update all of the following together:

1. descriptor prose and metadata
2. runtime code
3. tests
4. user-facing docs when behavior changes

That is what keeps the policy surface readable instead of turning it into
code that only the runtime understands.
