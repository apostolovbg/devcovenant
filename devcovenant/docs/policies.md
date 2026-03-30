# Policies
**Last Updated:** 2026-03-30
**Project Version:** 1.0.0

## Overview
This document is the normative home for the policy descriptor contract.
Keep `devcovenant/docs/contracts.md` nearby when you need the stable document
map or the frozen boundary between configurable policy behavior, autofix,
commands, and core invariants.

Policies are the customizable enforcement units in DevCovenant.
Each policy combines descriptor metadata, runtime check logic, and optional
autofix support.
Use this page when you need to decide whether a new behavior belongs in a
policy at all, and if it does, whether it should surface as a check, an
autofixer, a runtime action, or an explicit operator command.

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
One important example is `changelog-coverage`: it is gate-session scoped, not
git-scoped. The checker compares the latest changelog entry against the
gate-start snapshot, requires a fresh top entry for the current session, and
preserves the pre-session top entry by fingerprint anywhere below that fresh
entry instead of binding it to a fixed slot.

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
The same policy now treats managed execution as one environment contract:
it first reuses the current interpreter when that interpreter already matches
metadata and its external prerequisites resolve, and only runs
`managed_commands` when the selected target environment is still missing or
invalid.
The same policy now also aligns managed command stages with the public
workflow contract: `start`, `run`, `end`, `command`, and `all`.
That keeps managed-environment orchestration aligned with `devcovenant run`
instead of preserving a special legacy `test` stage.
For Python-owned tools such as the gate hook, execution prefers the
environment's console script and can fall back to `python -m ...` through the
same interpreter when the shim is absent.
The same runtime now also persists that prepared-stage state with the same
`run` token, so managed re-exec hops no longer carry a stale internal
`test` marker after the public workflow contract moved to `run`.
The same runtime now resolves the tracked policy registry through the
tracked-registry helper layer instead of depending on the catch-all
registry service for runtime-evidence paths.
Builtin policy runtimes that need descriptor metadata or script locations now
resolve that information through the dedicated `policy_registry.py` helper
layer. That keeps dependency-management, version-governance, and other
policy-owned runtime code from reaching back into manifest-inventory or
tracked-registry ownership just to resolve policy descriptors.

## Policy Commands
DevCovenant now supports namespaced policy commands.
The intended shape is:

```bash
devcovenant policy <policy-id> <command>
```

That keeps policy-owned operations explicit and prevents the CLI from turning
into a pile of unrelated one-off top-level commands.
The command-definition parser and runtime-action dispatcher now live under
`devcovenant/core/runtime/`, which keeps `devcovenant policy ...` on the same
execution boundary as `run` while leaving policy meaning in
the service layer.

Dependency management now uses only the namespaced policy command surface.

## Dependency Management
Dependency management is now one coherent policy surface.
It owns dependency refresh, dependency inventory, and license/report
synchronization together instead of splitting those behaviors across separate,
loosely connected commands or policies.

That gives custom repositories one policy to customize rather than several
half-overlapping surfaces.
When the checker reports changed dependency manifests, the autofixer and the
`refresh-all` runtime action now preserve that same manifest set when they
rewrite `licenses/THIRD_PARTY_LICENSES.md`, so the report section stays aligned
with what the checker actually validated.
The same policy now distinguishes between artifacts that truly need a refresh
and artifacts that are already synchronized, so package-manifest edits do not
force fake license-file churn when the generated compliance surfaces are
already current.
For Python repositories, `requirements.lock` now follows a stricter contract:
it represents normalized dependency-resolution content, not environment-local
pip control lines. Refresh strips emitted directives such as index or
trusted-host options from both semantic comparison and the written lock body,
so repositories keep environment-specific package-source behavior in
dependency-management metadata/config instead of baking it into the lock file.

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

For a normal repository, do not seed repo-specific custom policies before the
first reviewed baseline activation.
Start with `install`, config review, and `deploy`, prove that baseline, and
then add custom policies once the normal repo contract is already working.
That keeps later deploy cleanup from reading like arbitrary deletion of a
supported extension surface.

Custom policies that inspect managed docs should also treat the
project-governance header model as a stable contract.
That means repository-governance header checks now need to expect
`Project Stage`, `Maintenance Stance`, `Compatibility Policy`, and
`Versioning Mode` rather than the older single `Development Stance` label.

Custom policies may also own repository-specific public-surface transforms.
In this repository, `readme-sync` strips repo-only blocks from the root
README and rewrites repo-relative public links using the repository URL from
`pyproject.toml` so the packaged `devcovenant/README.md` works on PyPI
instead of only in-tree.

## Practical Guidance
When changing a policy, update all of the following together:

1. descriptor prose and metadata
2. runtime code
3. tests
4. user-facing docs when behavior changes

That is what keeps the policy surface readable instead of turning it into code
that only the runtime understands.
