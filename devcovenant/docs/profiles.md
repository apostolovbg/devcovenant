# Profiles
**Last Updated:** 2026-03-22
**Project Version:** 1.0.0

## Overview
Profiles describe repository shape.
They tell DevCovenant what kind of repository this is and what reusable stack
behavior should come with that shape.

A profile can contribute refresh-generated output and reusable stack
metadata. A profile can contribute:

- metadata overlays

- managed assets

- pre-commit fragments

- suffix inventories

- translator declarations

- core-invariant metadata overlays where DevCovenant exposes that contract

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

- dependency file roles for a language ecosystem

- managed-environment expectations for a stack

- generated asset templates

- translator declarations for a language

- documentation routes for a reusable repo profile

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

- dependency-management selectors

- version-sync file roles

- documentation-growth routes

- no-print sink metadata from language profiles

- core-invariant required test commands

Use config overrides after that for repository-specific deltas.

## Builtin And Custom Profiles
Builtin profiles are the shipped reusable stack surface.
Custom profiles let a repository add its own reusable behavior without editing
DevCovenant core files.

A custom profile is a good fit when a repository needs:

- custom managed docs

- recurring selectors

- repo-specific metadata overlays

- repo-specific pre-commit fragments

It is not a good fit for a one-off local toggle that belongs in config.

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
