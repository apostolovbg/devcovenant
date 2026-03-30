# Profiles
**Last Updated:** 2026-03-30
**Project Version:** 1.0.1

## Overview
Profiles describe repository shape.
They tell DevCovenant what kind of repository this is and what reusable stack
behavior should come with that shape.

A profile can contribute refresh-generated output and reusable stack metadata.
A profile can contribute:
1. metadata overlays
2. workflow runs
3. managed assets
4. pre-commit fragments
5. suffix inventories
6. translator declarations
7. CI fragments through `ci_and_test`
8. ignore-directory hints that feed generated `.gitignore` and the shared
   pre-commit exclude contract

For the built-in `global` profile, that includes the canonical
`workflow.pre_commit_command` value `pre-commit run --all-files`, while the
managed-environment runtime launches pre-commit through the selected
interpreter so gate execution stays portable across local work, CI, and proof
repositories.

Profiles do not directly turn policies on or off.
Policy activation remains config-driven through `policy_state`.
Reach the first reviewed DevCovenant baseline first.
Add custom profiles after the initial `install`, config review, `deploy`, and
full gate cycle prove the normal contract is already working.

## Profile Types
The common profile categories are:
- global and defaults baselines
- language profiles
- framework or tooling profiles
- custom profiles

The normal pattern is to keep `global` active, add the needed language or
stack profiles, and then use config overrides only for repository-specific
deltas.

## What Profiles Should Own
Profiles are the right place for reusable stack behavior.
That includes things like:
1. dependency file roles for a language ecosystem
2. managed-environment expectations for a stack
3. generated asset templates
4. translator declarations for a language
5. documentation routes for a reusable repo family
6. extra CI jobs that should apply to a repo family instead of every
   DevCovenant repository
7. declared workflow runs that should be required for repositories of the
   same stack shape

If the behavior should apply to many repositories of the same shape, it
probably belongs in a profile instead of local config.

The built-in `defaults` profile now seeds the baseline `.venv`
managed-environment contract for ordinary repos:
- `expected_paths` / `expected_interpreters`
- `required_commands` for the target env
- manual guidance that uses `{current_python}` and `{managed_python}`

Profiles may also contribute `ignore_dirs` for disposable local outputs that
should stay out of generated `.gitignore` and out of pre-commit's all-files
surface. That is the right place for repo-family proof or scratch directories,
not for durable source paths.

Repo profiles can then strengthen that baseline.
One repo profile may add `managed_commands` so `gate --start` can materialize
the repo-owned environment automatically, while the built-in `global` CI asset
keeps shared runner-runtime choices in the generic workflow layer.

## Assets And Managed Docs
Profiles can ship assets.
Those assets can include managed-document templates.

`devcovenant asset FILE.ext [OUTPUTNAME.ext]` is the operator surface for
those shipped assets.
It resolves both:
- manifest-declared profile assets
- descriptor-backed managed docs such as `SPEC.md`

Resolution is deterministic:
- exact target-path matches beat basename matches
- active profiles are considered first in resolved active-profile order
- remaining discovered profiles are considered afterward in deterministic
  profile-name order
- builtin versus custom is not a special tie-breaker after profiles are
  discovered
- if the winning profile still exposes multiple basename matches,
  DevCovenant fails and asks for an exact asset target path

The command writes Desktop copies only.
It reuses the same rendering machinery that normal refresh and deploy use:
plain profile assets go through the shared profile-asset renderer, while
managed docs go through the managed-doc descriptor renderer.

Managed-doc descriptor ownership follows profile precedence by target path:
- the global profile provides the baseline descriptor set
- active profiles may add new target docs
- active profiles may override a global descriptor by shipping the same target
  path
- later active profiles win over earlier ones for the same target path

That precedence model is what lets one repo family replace a generalized
global trust doc such as `SECURITY.md` with a repo-specific version without
adding a second managed-doc system.

## Translators
Translators are owned by language profiles.
They keep policy logic language-agnostic by translating files into normalized
units instead of forcing policies to understand each language directly.

A translator declaration normally includes:
- a stable translator id
- handled file extensions
- a `can_handle` entrypoint
- a `translate` entrypoint

Practical resolution flow:
1. identify the file extension
2. collect candidate translators from the active language profiles
3. run `can_handle`
4. require one effective translator
5. return one normalized language unit

Framework and tooling profiles should not become alternate language owners.
Translator ownership belongs with language profiles.

## Metadata Overlays
Profiles are the preferred place for operational metadata that depends on stack
shape.
Examples include:
1. dependency-management selectors
2. version-sync file roles
3. documentation-growth routes
4. no-print sink metadata from language profiles
5. reusable workflow runs such as a stack's `tests` run
6. reusable `ci_and_test` fragments for repo-family CI jobs
7. managed-environment roots that other engine services may need to respect,
   such as cleanup-safe environment paths

The CI boundary is important.
The global workflow template should stay generic.
If a repo family needs additional CI proof, that extension belongs in the
relevant profile instead of in the builtin global workflow.

The same profile boundary helps with config readability.
The global config asset is where DevCovenant lists the full
`project-governance` key set, the allowed lifecycle values, the legal
`compatibility_policy` values, and the legal `versioning_mode` values directly
in the generated config comments.
Repo overlays can then tighten that compatibility policy.
That same config surface marks ownership section-by-section as human-owned,
refresh-owned, or mixed ownership so a repository can tell at a glance which
settings it owns directly and which state refresh writes for visibility.

The same ownership split matters for workflow itself.
If a language or stack has a standard run, the profile should declare it
through `workflow_runs`.
That keeps the engine-facing workflow contract explicit.
In the built-in Python profile, the standard `tests` run lives there and
declares its runner commands and success contract, while core owns the public
`run` command surface used to execute it.
That default Python run uses `python3 -m unittest discover -v` as the single
Python test command, so the repo keeps one structural Python test pass without
a second launcher executing the same suites.
That same declaration can also carry `recording` hooks such as:
- `output_mode_config_field`
- `event_adapter_group`
- `write_runtime_profile`

Those hooks let a profile opt specific runs into richer reporting without
reintroducing hardcoded executor behavior for a special run id.

## Workflow Run Contract
`workflow_runs` is a public profile-authoring contract.
Each run may declare:
- `id`
- ordering fields `after`, `before`, and `order`
- `runner`
- `success_contract`
- `freshness`
- `recording`

Ordering is executable contract, not decorative metadata.
- `after` and `before` may reference reserved anchors: `start`, `mid`, `end`
- `after` and `before` may also reference other declared run ids
- DevCovenant validates those references during contract resolution
- DevCovenant rejects cyclic positioning rules instead of preserving them as
  inert metadata
- when multiple runs are simultaneously eligible, `order`, then owner id,
  then run id break ties deterministically

Supported runner kinds are:
- `command_group`
- `runtime_action`
- `policy_command`
- `manual_attestation`

Supported success-contract kinds are:
- `all_commands_exit_zero`
- `runtime_action_success`
- `policy_command_success`
- `manual_attested`
- `external_artifact_check`
