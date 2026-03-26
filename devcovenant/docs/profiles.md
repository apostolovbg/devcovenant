# Profiles
**Last Updated:** 2026-03-26
**Project Version:** 1.0.0

## Overview
Profiles describe repository shape.
They tell DevCovenant what kind of repository this is and what reusable stack
behavior should come with that shape.

A profile can contribute refresh-generated output and reusable stack
metadata. A profile can contribute:

1. metadata overlays

2. workflow phases

3. managed assets

4. pre-commit fragments

5. suffix inventories

6. translator declarations

7. CI-and-test workflow fragments through `ci_and_test`

8. core-invariant metadata overlays where DevCovenant exposes that contract

Profiles do not directly turn policies on or off.
Policy activation remains config-driven through `policy_state`.

## Profile Types
The common profile categories are:

- global and defaults baselines

- language profiles

- framework or tooling profiles

- repo-specific custom profiles

The normal pattern is to keep `global` active, add the needed language or
stack profiles, and then use config overrides only for repository-specific
changes.

## What Profiles Should Own
Profiles are the right place for reusable stack behavior.
That includes things like:

1. dependency file roles for a language ecosystem

2. managed-environment expectations for a stack

3. generated asset templates

4. translator declarations for a language

5. documentation routes for a reusable repo profile

6. extra CI jobs that should apply to a repo family instead of every
   DevCovenant repository

7. declared workflow phases that should be required for repositories of the
   same stack shape

If the behavior should apply to many repositories of the same shape, it
probably belongs in a profile instead of local config.

## Assets And Managed Docs
Profiles can ship assets.
Those assets can include managed-document templates.

That matters for Item 5 directly:
profile assets should not be thin scaffolds that push every repository back
into vague, terse, hard-to-read starter docs.
They should generate useful, substantial starting documents whose structure and
formatting already reflect the intended documentation quality.

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

5. reusable workflow phases such as a stack's `tests` phase

6. reusable `ci_and_test` fragments for repo-family CI jobs

7. managed-environment roots that other engine services may need to respect,
   such as cleanup-safe environment paths

The CI boundary is important.
The global workflow template should stay generic.
If a repo family needs additional CI proof, that extension belongs in the
relevant profile instead of in the builtin global workflow.
The usual shape is to extend the main `ci-and-test` job with repo-family
steps and, if needed, add one dependent verification job such as this
repository's `build-and-install-test` job for real built-artifact proof.
In this repository, that generated workflow now uses the visible workflow
name `CI`, while the specific job names stay descriptive underneath it.
The repo-specific verification job should prove the public install story from
the actual wheel, sdist, and `pipx` path, not from shallow `--help` or
`--status` checks alone.
That repo-specific proof should also keep its shell structure simple enough
that inline activation helpers stay parse-stable in GitHub Actions.
If a repo family needs a reviewed temporary scanner exception because an
upstream advisory has no fix release yet, that exception belongs here too,
not in the generic global workflow template.

Use config overrides after that for repository-specific deltas.

The same profile boundary helps with config readability.
The global config asset is where DevCovenant now lists the full
`project-governance` key set, the default allowed `stage` values, the default
allowed `maintenance_stance` values, the legal
`compatibility_policy` values, and the two legal `versioning_mode` values
directly in the generated config comments.
The same boundary also matters for cleanup:
the global profile can seed reusable cleanup targets, but it should not
hardcode one language-specific managed environment path such as `.venv`.
Managed-environment protection belongs with the managed-environment metadata so
other environment types can participate through the same contract.

The same ownership split now matters for workflow itself.
If a language or stack has a standard required phase, the profile should
declare it through `workflow_phases`.
That keeps the engine-facing workflow contract explicit instead of smuggling
workflow structure through core-invariant metadata.
In the built-in Python profile, the standard `tests` phase now lives there and
declares its runner commands and success contract, while core owns the public
`run` and `phase run <id>` command surfaces used to execute it.

The same asset ownership shows up in managed docs.
Profile README descriptors can intentionally keep a managed block empty.
That is the correct contract for the root `README.md` and packaged
`devcovenant/README.md` here: the `<!-- DEVCOV -->` block stays present but
empty by design, so profile assets do not inject DevCovenant runtime prose at
the top of user-facing README surfaces.

## Builtin And Custom Profiles
Builtin profiles are the shipped reusable stack surface.
Custom profiles let a repository add its own reusable behavior without editing
DevCovenant core files.

A custom profile is a good fit when a repository needs:

1. custom managed docs

2. recurring selectors

3. repo-specific metadata overlays

4. repo-specific pre-commit fragments

5. repo-specific reference-map assets that explain local custom behavior
   cleanly

It is not a good fit for a one-off local toggle that belongs in config.
In a normal repository, it is also not the first step.
Reach the first reviewed DevCovenant baseline first, then add repo-specific
custom profiles after the initial `install` -> config review -> `deploy`
activation has already proven the base contract.

A repo-specific custom profile can own reference assets such as
`POLICY_MAP.yaml`.
Those assets can describe local policy behavior, including packaged README
sync that rewrites public links from package metadata instead of hardcoding
one upstream URL into shared runtime code.

## Example Profile Shapes
A repository can combine general stack profiles with narrower tooling or API
profiles.
For example, an API-oriented profile can seed docs such as API, auth, and
error contracts without hardcoding that documentation shape into core runtime
code.

Those examples matter because they show how profile-owned assets and metadata
can shape documentation and policy behavior while staying reusable across more
than one repository.

## Working Rules
Good profile design stays disciplined:

- keep reusable stack behavior in profiles

- keep repo-only choices in config

- keep translator ownership in language profiles

- keep assets substantial and readable

- avoid embedding unrelated business logic in profiles
