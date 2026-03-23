# Policy Map
**Doc ID:** POLICY_MAP
**Doc Type:** reference-map
**Project Version:** 1.0.0
**Last Updated:** 2026-03-23
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use `POLICY_MAP.md` to track policy inventory and ownership below this block.
<!-- DEVCOV:END -->

## Table of Contents
1. [Purpose](#purpose)
2. [Global Rules](#global-rules)
3. [Builtin Policies](#builtin-policies)
4. [Custom Policies](#custom-policies)
5. [Language-Aware Policies](#language-aware-policies)
6. [Metadata Families](#metadata-families)

## Purpose
This map documents shipped policy contracts and ownership for 1.0.0.

## Global Rules
- Policy activation authority is `config.policy_state` only.
- Policy descriptors are the canonical prose and metadata defaults.
- AGENTS policy block is compiled from resolved metadata and parsed at runtime.
- Local registry stores synchronized hash and metadata diagnostics.
- Same-id custom policy overrides same-id builtin policy.

## Builtin Policies
- `changelog-coverage`: requires one fresh top changelog entry per work
  session, with Change/Why/Impact summary lines and file list coverage;
  DEVCOV managed-block-only edits are excluded for any file, and
  doc header-only edits are excluded when they touch only configured header
  keys inside the configured top-of-file header scan window. Generated
  governance targets (`.gitignore`, `.pre-commit-config.yaml`,
  `.github/workflows/ci-and-test.yml`) are excluded by default.
- `dependency-management`: requires lock/dependency changes to stay aligned
  with `THIRD_PARTY_LICENSES.md` and `licenses/` artifacts (including
  generated `licenses/README.md`) using metadata-driven selectors. This
  policy enforces repository dependency compliance; distribution-package legal
  scope is handled by packaging contracts.
- `devcov-integrity-guard`: validates descriptor/registry/runtime consistency.
- `devcov-structure-guard`: enforces required repository shape constraints.
- `devflow-run-gates`: enforces gate start -> test -> gate end evidence and
  validates required-command and pre-commit execution records.
- `docstring-and-comment-coverage`: requires explanatory docs/comments for
  in-scope source files.
- `documentation-growth-tracking`: enforces docs-update expectations and
  quality gates for user-facing changes.
- `last-updated`: enforces top-level `Last Updated` placement and
  updates date values for managed docs.
- `line-length-limit`: warns when in-scope files exceed configured line limit.
- `no-raw-errors`: blocks raw Python error anti-patterns (bare `except`,
  generic `raise Exception(...)`, and silent `except Exception: pass`) in
  selector-scoped files.
- `no-print-outside-output-runtime`: enforces metadata-driven output sinks.
  Language profiles declare sink targets, while repository profiles define
  selectors and allowed output-boundary files/symbols.
- `managed-environment`: optional managed-runtime environment guard.
- `modules-need-tests`: enforces structural source-to-test alignment and
  mirror-root correctness using metadata-driven mirror templates, and bans
  placeholder test scaffolds.
- `tests-coverage`: enforces structural assertion-quality coverage across
  related tests with metadata-driven assertion semantics and symbol-level
  fidelity checks.
- `name-clarity`: warns on unclear identifiers in in-scope code.
- `no-future-dates`: blocks future dates in docs/changelog contexts.
- `raw-string-escapes`: optional language-aware suspicious backslash escape
  warnings with metadata-driven literal/escape patterns.
- `read-only-directories`: blocks writes to declared read-only paths.
- `security-scanner`: blocks risky patterns (`eval`, `exec`, shell risks).
- `version-governance`: optional version-format validation, scheme-aware
  forward-bump enforcement, and adapter-specific release-rule alignment.
- `version-sync`: enforces consistency across role-targeted version surfaces
  only.

## Custom Policies
- `devcov-raw-string-escapes`: repo-only raw-string warning guard.
- `managed-doc-assets`: validates managed-doc descriptor/asset consistency.
- `readme-sync`: syncs packaged README from repository README.

## Language-Aware Policies
Policies that may request translation through shared translator runtime:
- `docstring-and-comment-coverage`
- `modules-need-tests`
- `name-clarity`
- `security-scanner`
- `tests-coverage`
- `no-print-outside-output-runtime`

## Metadata Families
Activation/severity:
- `enabled`, `severity`, `enforcement`

Selectors:
- `include_*`, `exclude_*`, `force_include_*`, `selector_roles`

Gate/session:
- `gate_status_file`, `required_commands`, pre-commit command/epoch keys

Runtime note:
- `required_commands` executes in resolved metadata order without runtime
  fallback command injection.
- `test_events` payloads are runtime-owned test evidence from profile metadata
  and are not policy descriptor metadata keys.

Dependency/license:
- `dependency_files`, `dependency_globs`, `dependency_dirs`,
- `dependency_roles`, `dependency_role_files`, `dependency_role_globs`,
  `dependency_role_dirs`,
  `third_party_file`, `licenses_dir`, `report_heading`

Versioning:
- `version_file`, `changelog_file`, `changelog_header_prefix`, `target_roles`
- `role_extractors`, `target_role_files`, `target_role_globs`,
  `target_role_dirs`
- semantic-scope metadata: `version_file`, `changelog_file`,
  `ignored_prefixes`

Docs quality:
- user-facing selectors, required headings, word-count, mention constraints
- `doc_routes`

Overlay/override layers:
- `autogen_metadata_overlays`, `user_metadata_overlays`
- `autogen_metadata_overrides`, `user_metadata_overrides`

Output-boundary sinks:
- `sink_call_targets`, `sink_attr_targets`, `sink_macro_targets`
- `allowed_symbol_targets`, `allowed_file_globs`,
  `allow_waiver_comment`

Raw-error policy:
- `forbid_bare_except`, `forbid_raise_exception`,
  `forbid_silent_exception_pass`
