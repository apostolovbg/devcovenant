# Profiles

## Overview
Use this doc for repository-shape modeling.
Profiles describe reusable stack behavior, assets, overlays, and translator
ownership.

A strong profiles doc helps a maintainer decide where a rule belongs before
they edit anything.
It should make the boundary between reusable stack metadata and repo-local
choices obvious, because that boundary is what keeps profile growth sane.

## What This Doc Should Cover
Explain:

- profile categories and the normal active-stack model

- what profiles should own versus what config should own

- assets and managed-doc templates

- translator ownership in language profiles

- builtin versus custom profiles

- repo-local examples such as `devcovrepo` and `restapi`

## Writing Rules
Keep the explanation concrete.
Profiles are only useful when readers can tell what behavior is reusable,
what behavior is local, where to make the next change, and what kinds of
changes should not be pushed into profile metadata at all.
