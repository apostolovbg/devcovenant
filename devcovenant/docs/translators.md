# Translators
**Last Updated:** 2026-02-27
**Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Declaration Schema](#declaration-schema)
- [Runtime Resolution](#runtime-resolution)
- [LanguageUnit Shape](#languageunit-shape)
- [Translator Boundaries](#translator-boundaries)
- [Failure Modes](#failure-modes)
- [Workflow](#workflow)

## Overview
Translators keep policy logic language-agnostic.

Instead of embedding parser logic into each policy, language profiles declare
translator behavior once. Policies then consume normalized language units from
runtime resolution.

Separation of concerns:
- translators:
  normalize source files into shared policy-consumable units
- policy scripts:
  evaluate normalized units against policy contracts
- profile metadata:
  declares which translator owns which extensions

Test-event adapters are related but separate:
- declared in profile metadata (`test_events`)
- loaded by event runtime for `devcovenant test`
- not part of translator selection logic

## Declaration Schema
Translator declarations live in language profile manifests.

Typical fields:
- `id`:
  stable translator identifier
- `extensions`:
  dotted lowercase suffixes handled by the translator
- `can_handle`:
  gate function used to confirm applicability
- `translate`:
  entrypoint that returns normalized language-unit payload

Declaration guidance:
- keep extension ownership explicit and unambiguous
- prefer one canonical translator per extension per active profile stack
- keep entrypoints profile-contained and importable in runtime context

## Runtime Resolution
Per-file resolution flow:
1. identify file extension
2. collect translators from active language profiles that declare the extension
3. evaluate translator `can_handle` logic
4. require exactly one translator
5. execute `translate` and return a normalized unit

Resolution outcomes:
- zero matches:
  no translator available for this file
- one match:
  success
- multiple matches:
  ambiguous ownership violation

Runtime enforces entrypoint containment so translator references cannot escape
declaring profile roots.

## LanguageUnit Shape
A language unit is the common payload consumed by policies and autofix helpers.

The exact payload can vary by language, but it should provide deterministic
information needed by policy logic, such as:
- structural elements (for example functions/classes)
- symbol names and locations
- node/call references used by policy checks

Design intent:
- policy authors write one cross-language rule style
- language-specific parsing remains isolated in translator implementations

## Translator Boundaries
Translator ownership rules:
- only language profiles should declare translators
- framework/ops/tooling profiles may contribute policy metadata, not language
  translators
- overlapping extension declarations across active profiles must resolve to one
  effective owner

Extension strategy for mixed repos:
1. keep broad ownership in base language profiles
2. use `can_handle` for fine-grained disambiguation
3. avoid duplicate extension declarations unless disambiguation is explicit and
   deterministic

When adding new language support:
1. create or update a language profile
2. add translator declaration and implementation
3. add tests that prove resolution and payload correctness
4. validate downstream policy behavior on translated units

## Failure Modes
High-frequency translator failures:
- extension not covered by any active language profile
- multiple candidates remain after `can_handle` checks
- invalid declaration shape or missing entrypoint callable
- entrypoint path traversal/root-escape violations
- translator returns malformed/non-normalized payload

Troubleshooting pattern:
1. verify `profiles.active` includes expected language profile
2. inspect profile translator declarations for duplicate ownership
3. verify translator entrypoint import path and callable signature
4. add or update targeted translator tests

## Workflow
1. Add or update translator declaration in a language profile manifest.
2. Implement or modify translator entrypoint code.
3. Add mirrored tests under `tests/devcovenant/builtin/profiles/<profile>/`.
4. Run policy tests that depend on translated output.
5. Run `devcovenant test`.
6. Run `devcovenant gate --end`.
