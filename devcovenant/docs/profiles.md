# Profiles
**Last Updated:** 2026-03-31
**Project Version:** 1.0.1

## Overview
Profiles tell DevCovenant what kind of repository it is working in and which
reusable behavior should come with that setup.

A profile can contribute:
1. metadata overlays
2. workflow runs
3. managed assets
4. pre-commit fragments
5. suffix inventories
6. translator declarations
7. CI fragments through `ci_and_test`
8. ignore-directory hints that feed generated `.gitignore` and pre-commit
   excludes

Profiles do not directly turn policies on or off.
Policy activation still lives in `policy_state`.

## Profile Types
The common profile categories are:
- `global` and `defaults` as the shared base
- `devcovuser` as the normal user-repository layer
- `github` as the opt-in GitHub Actions layer
- language profiles
- framework or tooling profiles
- custom profiles

The normal pattern is:
1. keep the base profiles active
2. keep `devcovuser` active for an ordinary repository using DevCovenant
3. add `github` when the repository wants a generated GitHub Actions workflow
4. add the needed language or stack profiles
5. add a repo-specific custom profile on top when the repository needs its own
   rules, assets, or workflow additions

Use direct overlays when you only need a very small local tweak.
Use a custom profile when the repository has real repeatable behavior of its
own.

## What Profiles Should Own
Profiles are the right place for reusable behavior.
That includes:
1. dependency file roles for a language ecosystem
2. managed-environment expectations for a stack
3. generated asset templates
4. translator declarations for a language
5. documentation routes for a reusable repo family
6. extra CI jobs that should apply to a repo family instead of every
   DevCovenant repository
7. declared workflow runs that should be required for repositories of the same
   shape

If the behavior should apply to more than one repository of the same shape, it
probably belongs in a profile instead of local config.

The built-in `defaults` profile seeds a plain Python `.venv` starting point:
- expected paths and interpreters
- required commands for the target environment
- manual guidance that uses `{current_python}` and `{managed_python}`

That is a starting point, not a promise that every repository should use
`.venv`.
Repositories that use bench or another environment should declare that
environment through their active profile stack or metadata overlays instead of
relying on the defaults to guess it.

The built-in `devcovuser` profile is the normal user-repository layer.
It keeps DevCovenant's own shipped runtime files out of ordinary app-code
checks while still keeping `devcovenant/custom/**` in scope for repo-owned
extensions.

Profiles may also contribute `ignore_dirs` for disposable local outputs that
should stay out of generated `.gitignore` and out of pre-commit's all-files
scan.
Typical examples are proof roots such as `.proof-wheel` and `.proof-sdist`,
support-floor environments such as `.proof-py310`, or runner cache roots such
as `.gha-pycache` when a CI profile needs them.

A repo-specific custom profile can then strengthen the standard stack.
For example, it may add `managed_commands`, extra assets, or CI proof that
belongs to that repository or repo family.

## Assets And Managed Docs
Profiles can ship assets, including managed-document templates.

`devcovenant asset FILE.ext [OUTPUTNAME.ext]` is the command for those shipped
assets.
It can resolve both:
- manifest-declared profile assets
- descriptor-backed managed docs such as `SPEC.md`

Resolution works like this:
- exact target-path matches beat basename matches
- active profiles are considered first in active-profile order
- remaining discovered profiles are considered afterward in profile-name order
- if the winning profile still exposes multiple basename matches,
  DevCovenant stops and asks for an exact target path

The command writes Desktop copies only.
It uses the same rendering code that refresh and deploy use.

Managed-doc descriptor ownership follows profile precedence by target path:
- the global profile provides the baseline descriptor set
- active profiles may add new target docs
- active profiles may override a global descriptor by shipping the same target
  path
- later active profiles win over earlier ones for the same target path

## Translators
Translators are owned by language profiles.
They let policies work with a normalized view of source files instead of making
every policy understand every language directly.

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
Profiles are the preferred place for reusable stack-specific settings.
Examples include:
1. dependency-management selectors
2. version-sync file roles
3. documentation-growth routes
4. no-print sink metadata from language profiles
5. reusable workflow runs such as a stack's `tests` run
6. reusable `ci_and_test` fragments for repo-family CI jobs
7. managed-environment roots that cleanup and other services need to respect

The CI boundary matters.
The builtin `github` workflow template should stay generic.
It should bootstrap DevCovenant from the shipped
`devcovenant/requirements.lock`, not from the repository's own
dependency files.
If a repo family needs extra proof or extra project dependency setup, that
extension belongs in the relevant profile instead of in the builtin base
workflow.

The same split helps config stay readable.
The global config asset lists the full `project-governance` key set and the
allowed values.
Profiles and local config can then tighten or extend behavior without
making the shared base too repo-specific.

If a language or stack has a standard run, the profile should declare it
through `workflow_runs`.
That keeps shared run definitions in one place.
In the built-in Python profile, the standard `tests` run lives there and uses
`python3 -m unittest discover -v` as the default Python test command.

## Workflow Runs
`workflow_runs` is the public profile authoring model for extra run steps.
Each run may declare:
- `id`
- ordering fields `after`, `before`, and `order`
- `runner`
- `success_contract`
- `freshness`
- `recording`

Ordering is real behavior, not decorative metadata.
- `after` and `before` may reference reserved anchors: `start`, `mid`, `end`
- `after` and `before` may also reference other declared run ids
- DevCovenant validates those references
- DevCovenant rejects cycles instead of silently keeping broken rules
- when multiple runs are eligible at the same time, `order`, then owner id,
  then run id break ties

Supported runner kinds are:
- `command_group`
- `runtime_action`
- `policy_command`
- `manual_attestation`

Supported success-check kinds are:
- `all_commands_exit_zero`
- `runtime_action_success`
- `policy_command_success`
- `manual_attested`
- `external_artifact_check`
