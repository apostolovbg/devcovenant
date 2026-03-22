# Registry

## Overview
Use this doc to explain the difference between tracked registry state and
runtime-local session state.

A reader should be able to tell which registry surface belongs in version
control, which one only exists to support local workflow evidence, and when to
inspect each one during debugging.
Keep the explanation grounded in the actual files DevCovenant writes so a
maintainer can move from a confusing registry entry to the right source of
truth without having to reverse-engineer the runtime first.

## What This Doc Should Cover
Explain:

- `registry.yaml`

- `registry/runtime/`

- `gate_status.json`

- latest-run pointers

- when to inspect each surface

- why generated registry files should not be hand-edited

## Writing Rules
Keep the distinction between durable and disposable state plain.
This doc should help someone debug resolved state quickly instead of teaching a
new layer of jargon or making the registry sound more mysterious than it is.
