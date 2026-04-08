# Policy Map
**Doc ID:** POLICY_MAP
**Doc Type:** reference-map
**Project Version:** 1.0.1b2
**Last Updated:** 2026-04-07
**DevCovenant Version:** 1.0.1b2

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
This map lists the shipped policies and who owns them.

## Global Rules
- Policy activation authority is `config.policy_state` only.
- Policy descriptors are the canonical prose and metadata defaults.
- AGENTS policy block is compiled from resolved metadata and parsed at
  runtime.
- Local registry stores synchronized hash and metadata diagnostics.
- Same-id custom policy fully shadows the builtin policy with that id.
- When a custom policy shadows a builtin one, the builtin policy is ignored
  instead of being merged.
- Engine-owned runtime checks such as workflow validation, integrity
  validation, and structure validation are documented in
  `devcovenant/docs/workflow.md` and `devcovenant/docs/architecture.md`,
  not in this policy inventory.

## Builtin Policies
- `changelog-coverage`: requires one fresh top changelog entry per work
  session, with Change/Why/Impact summary lines and file list coverage;
  DEVCOV managed-block-only edits are excluded for any file, and
  doc header-only edits are excluded when they touch only configured header
  keys inside the configured top-of-file header scan window. Generated
  governance targets (`.gitignore`, `.pre-commit-config.yaml`,
  `.github/workflows/ci.yml`) are excluded by default.
- `dependency-management`: requires lock/dependency changes to stay aligned
  with `THIRD_PARTY_LICENSES.md` and `licenses/` artifacts (including
  generated `licenses/README.md`) using metadata-driven selectors. This
  policy enforces repository dependency compliance; distribution-package
  legal scope is handled by packaging rules.
- `docstring-and-comment-coverage`: requires explanatory docs/comments for
  in-scope source files.
- `documentation-growth-tracking`: enforces docs-update expectations and
  quality gates for user-facing changes.
- `last-updated`: enforces top-level `Last Updated` placement and
  updates date values for managed docs.
- `line-length-limit`: warns when in-scope files exceed configured line
  limit.
- `no-raw-errors`: blocks raw Python error anti-patterns (bare `except`,
  generic `raise Exception(...)`, and silent `except Exception: pass`) in
  selector-scoped files.
- `no-print-outside-output-runtime`: enforces metadata-driven output sinks.
  Language profiles declare sink targets, while repository profiles define
  selectors and allowed output-boundary files and symbols.
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
  warnings with metadata-driven literal and escape patterns.
- `read-only-directories`: blocks writes to declared read-only paths.
- `security-scanner`: blocks risky patterns (`eval`, `exec`, shell risks).
- `version-governance`: optional version-format validation, scheme-aware
  forward-bump enforcement, and adapter-specific release-rule alignment.
- `version-sync`: enforces consistency across role-targeted version surfaces
  only.

## Custom Policies
- `devcov-raw-string-escapes`: repo-only raw-string warning guard.
- `managed-doc-assets`: validates managed-doc descriptor and asset
  consistency.

## Builtin Package-Facing Policies
- `package-doc-sync`: syncs package-facing docs from repository source
  docs, strips configured repo-only marker blocks, and rewrites public
  repo-relative links from package metadata for PyPI-safe rendering.
- `package-artifact-mirror`: keeps package-shipped exact mirrors such as
  `LICENSE => devcovenant/licenses/LICENSE` synchronized from their
  canonical repo-root sources.

## Language-Aware Policies
Policies that may request translation through shared translator runtime:
- `docstring-and-comment-coverage`
- `modules-need-tests`
- `name-clarity`
- `security-scanner`
- `tests-coverage`
- `no-print-outside-output-runtime`

## Metadata Families
Activation and severity:
- `enabled`, `severity`, `enforcement`

Selectors:
- `include_*`, `exclude_*`, `force_include_*`, `selector_roles`

Workflow and session:
- `gate_status_file`, `workflow_session_file`, pre-commit command and epoch
  keys
- workflow and runtime path and command knobs live in ordinary config
  sections such as `paths.*` and `workflow.*`, not `policy_state`

Runtime note:
- workflow runs are resolved from tracked workflow-definition data, not from
  ad hoc command lists
- `run_events` payloads are runtime-owned workflow-run event metadata
  from profiles and are not policy descriptor metadata keys

Dependency and license:
- `dependency_files`, `dependency_globs`, `dependency_dirs`
- `dependency_roles`, `dependency_role_files`, `dependency_role_globs`,
  `dependency_role_dirs`
- `third_party_file`, `licenses_dir`, `report_heading`

Versioning:
- `version_file`, `changelog_file`, `changelog_header_prefix`,
  `target_roles`
- `role_extractors`, `target_role_files`, `target_role_globs`,
  `target_role_dirs`
- semantic-scope metadata: `version_file`, `changelog_file`,
  `ignored_prefixes`

Docs quality:
- user-facing selectors, required headings, word-count, mention constraints
- `doc_routes`

Overlay and override layers:
- `autogen_metadata_overlays`, `user_metadata_overlays`
- `autogen_metadata_overrides`, `user_metadata_overrides`

Output-boundary sinks:
- `sink_call_targets`, `sink_attr_targets`, `sink_macro_targets`
- `allowed_symbol_targets`, `allowed_file_globs`,
  `allow_waiver_comment`

Raw-error policy:
- `forbid_bare_except`, `forbid_raise_exception`,
  `forbid_silent_exception_pass`
