# Refresh Behavior

## Overview
Use this doc for the regeneration boundary.
It should explain what refresh owns, when it runs, and how managed docs are
preserved or replaced.

This page should answer a practical maintainer question: if a generated file
changed, which input owns that change and what kind of rewrite is DevCovenant
allowed to perform? Keep the answer concrete enough that someone can tell when
a manual edit will survive refresh and when it will be replaced.

## What This Doc Should Cover
Explain:

- what refresh regenerates

- when full refresh runs

- managed-doc descriptors

- preservation rules

- seeded-doc adoption

- custom managed docs from profiles

- failure modes and validation

## Writing Rules
Keep the ownership questions obvious.
Readers should leave knowing what input owns a generated output, what kind of
mutation refresh is allowed to make, and when a full rerender is expected
rather than surprising.
