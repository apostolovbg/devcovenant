# Policies
**Project Version:** 1.0.1.dev1

## Overview
Policies are the named rule units in DevCovenant.
Each policy combines human-readable guidance, metadata, runtime checks, and,
when needed, explicit repair actions.

Use this page when you need to answer questions like these:
- should this behavior be a policy at all?
- should it only report problems, or should it also know how to repair them?
- should the action happen automatically, or only when a human asks for it?

Built-in engine checks such as workflow validation, integrity validation, and
structure validation are separate from repository-facing policies.
This page is about the policies a repository can enable, configure, and extend.

## What A Policy Contains
A normal policy directory contains:
- a descriptor YAML file
- a runtime check file
- optional autofix helpers
- optional assets or support files

The descriptor explains the rule and declares its metadata.
The runtime code enforces the rule.

## Turning Policies On And Tuning Them
`config.policy_state` decides which configurable policies are enabled.
Profiles and config overlays then shape how those enabled policies behave.

That gives a clear split:
- config turns a policy on or off
- profile metadata shapes how it behaves
- runtime code enforces the result

## Checks, Autofix, And Commands
The boundary matters:
- checks inspect and report
- autofixers repair during autofix-enabled check flows
- explicit policy commands perform deliberate operator actions

Checks should not quietly edit files.
That keeps the CLI honest and makes side effects easier to understand.
One good example is `changelog-coverage`: it works from the active gate slice,
not from raw git history. When the top changelog version changes during an
open slice, it expects a new version section above the preserved previous top
section, and it expects the preserved pre-session top entry to stay first in
that older section instead of relabeling old entries. It tracks that
preserved entry by fingerprint, so the rule does not depend on bump wording
inside the entry text.
If you intentionally rebuild changelog history, run
`devcovenant policy changelog-coverage reset-baseline` during the open
session. That command relaxes only the preserved-old-entry requirement for the
active session. It does not relax the normal date, summary, or file-coverage
rules.

## Policy Runtime Actions
A policy can expose reusable runtime actions.
Those actions give policy commands and autofix flows a shared implementation
path instead of duplicating logic.

For example, dependency management can expose refresh actions that update:
- lock state
- dependency reports
- license files
- the full dependency-management output set

The managed-environment policy also exposes the selected execution
environment so other runtime code can use the same target interpreter.
It resolves one target environment, reuses it when it already matches, and
runs `managed_commands` only when the target environment is missing or invalid.
For Python-owned tools such as the pre-commit gate hook, execution uses
`python -m ...` through the selected interpreter instead of depending on a
console-script shim.
Command templates may use `{current_python}` / `{current_bin}` for the running
interpreter and `{managed_python}` / `{managed_bin}` / `{managed_root}` for the
selected target environment.

## Policy Commands
DevCovenant supports namespaced policy commands:

```bash
devcovenant policy <policy-id> <command>
```

That keeps policy-owned operations explicit and stops the CLI from turning into
an unrelated pile of top-level commands.
The parser and dispatcher live under `devcovenant/core/runtime/`, so policy
commands run through the same execution boundary as the rest of the CLI.

## Dependency Management
Dependency management is one policy area, not a loose group of unrelated
scripts.
It owns dependency refresh, dependency inventory, and license/report sync
as one job.

For Python repositories, `requirements.lock` is meant to store normalized
resolution content, not environment-local pip control lines.
Refresh strips environment-specific directives from comparison and from the
written lock body so repositories keep package-source behavior in metadata and
config instead of baking it into the lock file.
Dependency-management metadata is now surface-based.
It uses one typed metadata model:
- scalars stay scalars
- lists stay lists
- mappings stay mappings
- lists of mappings with stable `id` values merge by `id`

That means repositories should express one concept in one metadata shape.
Do not mix a structured `surfaces` list with separate flat fallback keys for
the same dependency surface model.

Each surface owns:
- one `lock_file`
- its direct dependency inputs
- the dependency selectors that should trigger report/license refresh
- one `third_party_file`
- one `licenses_dir`
- optional hash-lock targets

That means the policy can own more than one dependency surface at once.
For example:
1. `root_workspace`
2. `package_runtime`
3. `devcovenant_runtime`

There is no special root-versus-auxiliary split anymore.
Repositories can declare additional surfaces the same way when they need them.

When one surface enables `generate_hashes`, `dependency-management refresh-all`
does not try to patch a host-local `pip-compile` result.
Instead it resolves the full configured target closure from that surface's
`hash_targets`, then writes one hash-locked result that covers those targets
or fails explicitly.
That keeps hash mode target-aware instead of GitHub-specific or
host-platform-specific.

The shipped defaults are:
1. `root_workspace`: non-hash mode
2. `package_runtime`: non-hash mode
3. `devcovenant_runtime`: hash mode in the builtin `github` profile

Most governed repositories only work directly with `root_workspace` and,
when they ship their own Python package, `package_runtime`.
`devcovenant_runtime` is DevCovenant's bundled bootstrap/runtime surface for
the package-maintained GitHub bootstrap path rather than a surface ordinary
adopters usually maintain themselves.

For the seeded Python stack, `root_workspace` starts from
`requirements.in`, and that seeded file includes the shipped
`devcovenant/runtime-requirements.lock`.
`dependency-management refresh-all` then writes the resolved
`requirements.lock` and the matching license artifacts for that surface.
Resolved locks are policy-owned outputs, not starter profile assets.

If a repository overrides one of those surfaces, do it in the profile or
config layer for that surface id instead of inventing a second metadata shape.

## Version-Governance Adapters
Version-governance adapters define how version schemes are parsed,
validated, normalized, and compared.
They are part of the supported extension model because repositories may need
stricter rules than plain string equality.
For the built-in `pep440` adapter, the format and canonical spelling still
follow PEP 440, while repo progression may reopen the same base version with a
`.devN` review line above an older final section.

## Custom Policies
Custom policies live under `devcovenant/custom/policies/<id>/` and use the
same descriptor-plus-runtime structure as built-in policies.
They should keep the same boundary discipline:
- checks report
- autofixers fix
- commands run explicit operations

Custom policies that inspect managed docs should expect the generated header
model for docs that opt into those headers.
Custom policies that sync package-facing docs should also keep release targets
truthful. If a packaged README rewrites repo-relative links or images, those
links should point at release-stable tagged URLs instead of a moving branch.

## Practical Rule
When policy behavior changes, update all of these together:
1. descriptor prose and metadata
2. runtime code
3. tests
4. user-facing docs when behavior changes

That keeps policy docs readable instead of turning them into code that only the
runtime understands.
