# Policies
**Last Updated:** 2026-02-28
**Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Program Vocabulary](#program-vocabulary)
- [Policy Structure](#policy-structure)
- [Descriptor and Metadata](#descriptor-and-metadata)
- [Descriptor Authoring Convention](#descriptor-authoring-convention)
- [Runtime Execution](#runtime-execution)
- [Output Governance Policy](#output-governance-policy)
- [Core Policy Deep Dives](#core-policy-deep-dives)
- [Autofix Model](#autofix-model)
- [Custom Policy Overrides](#custom-policy-overrides)
- [Workflow](#workflow)
- [Testing Expectations](#testing-expectations)

## Overview
Policies are executable governance rules.
Each policy combines prose (`text`), metadata defaults, and runtime check code.

Policy activation is controlled by `config.policy_state` for standard
enable/disable toggles.
`severity: critical` policies remain enforced even when a config toggle
attempts to disable them, and runtime emits an explicit diagnostic.
Profiles and metadata layers influence behavior, not on/off activation.

Initial critical policy set in this repository (conservative rollout):
- `devflow-run-gates` (gate/test/gate evidence workflow integrity)
- `devcov-integrity-guard` (policy/registry/prose integrity)
- `devcov-structure-guard` (required repo/core/tooling structure safety)
These policies require tracked metadata changes (or builtin-to-custom
replacement) for intentional behavior divergence; `policy_state` toggles do
not disable them.

## Program Vocabulary
- `output boundary`:
  one runtime interface for all user-visible output.
- `output mode`:
  command output contract level (`normal` concise, `quiet` minimal,
  `verbose` detailed).
- `test event`:
  normalized lifecycle event emitted by test adapters.
  Events follow schema version `1.0` (see
  `devcovenant/core/services/event.py`) and are recorded into the gate status
  payload (`test_events`) for downstream tooling to consume.
- `assertion signal`:
  meaningful assertion proving behavior in related tests; tautologies are
  excluded unless fixture-annotated.
- `deterministic execution`:
  DevCovenant self-runs rely on explicit configuration, stable metadata,
  and reproducible session state.

## Policy Structure
Builtin policy path:
- `devcovenant/builtin/policies/<policy-id>/`

Custom policy path:
- `devcovenant/custom/policies/<policy-id>/`

Expected files:
- `<policy-id>.yaml` descriptor
- `<policy-id>.py` check script
- optional `autofix/`
- optional `assets/`
- optional directories are contract-optional: do not commit placeholder-only
  folders
- `.gitkeep` placeholder files are not part of policy layout contracts;
  create `assets/` or `autofix/` only when real files exist

## Descriptor and Metadata
Descriptor metadata defines default behavior.
Resolved metadata is computed from descriptor/profile/config layers and then
rendered into AGENTS managed policy block and local policy registry.
The canonical resolver/decoder lives in
`devcovenant/core/services/metadata.py`.
It now exposes a typed companion resolved-metadata view for internal runtime
use while preserving the registry's persisted string-map contract for audit
stability.
Runtime policy option loading (including runtime-action metadata reads) uses
the shared decoder so bool/list/number parsing stays consistent across code
paths.

Shared metadata families include:
- severity and enforcement controls
- selectors (`include_*`, `exclude_*`, `force_include_*`)
- session-ledger references (for policies that validate gate sessions)
- policy-specific options (for example changelog verbs, dependency files,
  version-sync targets)

## Descriptor Authoring Convention
Use minimal policy descriptor metadata and prefer profile overlays for
operational values when behavior is profile-dependent.

Metadata shape conventions:
- keep scalars unquoted when safe
- use single quotes when quoting is required
- use `''` for empty string placeholders
- use `[]` for empty list placeholders
- use `{}` for empty object placeholders
- prefer typed empty values only; do not use sentinel pseudo-empty values
  such as `__none__`
- keep policy-level defaults minimal and move stack/layout defaults to profiles
  (for example changelog paths/header keys, version/changelog targets, and
  test watch roots)

Descriptor keys remain part of the contract schema even when values are
profile-populated. Runtime checks should raise explicit violations when
required metadata remains unresolved after merge.
When authoring or debugging metadata, treat the registry/AGENTS forms as
canonical persisted strings and the shared metadata decoder as the canonical
typed interpretation layer for runtime code.

## Runtime Execution
Runtime source for policy definitions is AGENTS policy block.
Execution flow:
1. parse AGENTS policy definitions
2. load policy scripts from builtin/custom paths
3. apply activation and metadata
4. run checks
5. run autofix helpers if allowed and available
6. rerun checks when autofix helpers changed files

Output mode contract:
- runtime output mode is selected by
  `devcovenant/config.yaml -> engine.output_mode`
- tests output mode is selected by
  `devcovenant/config.yaml -> engine.tests_output_mode` and falls back to
  `engine.output_mode` when unset
- allowed values are `normal`, `quiet`, and `verbose`
- default is `verbose` when key is unset or invalid
- tests `normal` mode keeps status lines concise, suppresses flood-prone test
  child output in console, and emits deterministic `[n/total] <command>`
  markers plus summary hints while full child output remains in run logs
- tests `quiet` mode suppresses routine stdout chatter and child output while
  preserving stderr failure surfaces and full run-log artifacts

High-impact runtime contracts:
- `changelog-coverage` requires a fresh top entry per gated session and keeps
  validation scoped to paths changed after gate start via session snapshots
  (`session_start_snapshot`, optional `session_baseline_snapshot` for recovery
  starts, plus `session_end_snapshot` / `last_run_snapshot` for lifecycle
  checks). Missing or invalid required snapshot metadata is a hard error.
  Deleted-file coverage is scoped with the gate-start
  `session_start_snapshot` baseline so older staged deletions do not leak
  into later slices, and start-phase validation does not import HEAD-wide
  deleted paths.
  Header/managed-block changelog exemptions use lightweight
  `document_exemption_baseline` records from gate start instead of whole-repo
  snapshot inventories, and the fingerprint algorithm is shared with
  gate-session baseline capture via
  `devcovenant/core/lib/document_exemptions.py`.
  By default, generated governance files (`.gitignore`,
  `.pre-commit-config.yaml` and `.github/workflows/governance-and-test.yml`)
  are excluded from changelog coverage.
  Deleted in-scope files remain valid `Files:` entries and are treated as
  real change evidence even after the path no longer exists on disk.
  Out-of-scope files (skipped metadata selectors and managed/header-only
  exempt deltas) are tolerated when humans list them in `Files:` blocks, but
  only in-scope files satisfy required coverage.
  Top-level read-only `devcovenant check` without an open gate session
  (`missing_gate_status` and empty phase) uses an empty scope instead of
  hard-failing bootstrap checks.
- `devflow-run-gates` enforces the start -> test -> end sequence and validates
  the latest `test` evidence against resolved required command metadata
  (`required_commands`). Gate status stores the tests mode and selected
  command key for deterministic end-gate validation.
  Required command validation is exact-token based against recorded command
  entries; substring matches do not satisfy required command evidence.
  For audit-only no-change `devcovenant check` runs in a closed session with
  no post-end edits, stale end-vs-test ordering does not emit a blocking
  violation; edit-session and unsessioned-edit enforcement remains strict.
  Missing gate status also stays non-blocking only for top-level read-only
  `check` bootstrap (`missing_gate_status` with empty phase).
- `devcov-structure-guard` enforces repo-local bytecode hygiene when
  enabled by profile/config metadata, flagging `__pycache__/` and `*.py[cod]`
  artifacts under `devcovenant/`, and it validates the tracked
  `devcovenant/logs` skeleton via the core manifest without requiring any
  policy inventory.
- `line-length-limit` excludes transient runtime log artifacts under
  `devcovenant/logs/**` so generated summaries and tails do not create
  warning noise during gated runs.
  Descriptor keys remain declared, while default values are profile-owned
  (`defaults` for max-length/URL escape-hatch defaults and
  `global` for runtime log-artifact excludes).
  It also supports optional escape-hatch metadata for long lines:
  `allow_long_url_lines` + `url_prefixes` (URL-like marker prefixes),
  plus `allow_long_lines` with `long_lines_contain` and
  `long_lines_between` (`left=>right` pairs).
  These escape hatches are general and apply to any selected file type,
  not documentation only.
- `read-only-directories` enforces only when include selectors are explicitly
  configured. Empty typed selectors (`[]`) keep the policy scope disabled.
- `managed-environment` is metadata-driven and stage-aware:
  `manual_commands` are operator guidance only, while
  `managed_commands` (`stage=>command`) are executable runtime preparation
  steps for `gate --start`, `test`, `gate --end`, and general command
  dispatch (`command` stage).
  Runtime tracks completed stage preparation in
  `DEVCOV_MANAGED_STAGE_RUNS` so stage bootstrap commands are not repeated
  across managed-interpreter CLI re-exec hops.
  Stage resolution honors explicit base environments so empty overrides
  isolate stage tracking from ambient process state.
  Managed command subprocess output now routes through the shared runtime
  child-command gateway
  (`run_child_command_with_output_policy` in
  `devcovenant/core/runtime/execution.py`) with per-channel plans resolved
  by `resolve_child_output_plan_for_channel`.
  Normal mode suppresses managed/test child channels while keeping gate
  pre-commit hook output visible; quiet mode suppresses routine stdout child
  output across channels; verbose mode keeps full child streaming for every
  channel.
  Long silent waits can emit `Please wait. In progress...` through the
  shared runtime heartbeat.
  `managed_rerun_commands` (`stage=>command`) provide wrapper-based command
  rerun adapters (for example bench or other external environment runners)
  when the managed interpreter cannot be executed directly.
  Active policy state also enables CLI interpreter auto re-exec into the
  managed interpreter; command-run `run.json` artifacts record interpreter
  provenance for audit/debug use.
  Empty managed-environment metadata emits explicit expected-path/interpreter
  guidance warnings; missing manual-command hint warnings are not emitted
  unless an actual environment mismatch requires remediation guidance.
- `dependency-license-sync` and `update_lock` operate from resolved metadata
  (descriptor + profiles + config layers), with role selectors as the
  primary contract (`dependency_role_*` via `role=>selector`) and no
  hardcoded manifest lists.
  Command runtime dispatch uses policy contract actions through
  `PolicyCheck.run_runtime_action(...)`.
- `documentation-growth-tracking` can enforce hard doc-route mappings so
  user-facing code changes must touch specific documentation targets.
  By default, documentation-only suffixes are not treated as user-facing;
  include them explicitly only when a repository wants doc edits to trigger
  route checks.
  Dot-prefixed glob triggers (for example `.github/workflows/*.yml`) are
  matched as literal dot-prefixed paths.
- `modules-need-tests` enforces source-to-test alignment, bans placeholder
  tests, and removes stale mirror-path tests using profile-owned
  `mirror_test_name_templates` metadata (with translator template fallback).
  Repository module inventory uses the shared snapshot scanner
  (`capture_current_snapshot_paths`) instead of git index commands so policy
  scope stays snapshot-driven.
  Language-specific test-style requirements are metadata-driven through
  `test_style_requirements` (`language=>rule` tokens).
  UTF-8 decode/read failures in module or test files are emitted as explicit
  deterministic violations instead of aborting policy execution.
- `security-scanner` reads source via UTF-8 and emits explicit read/decode
  violations when files are unreadable, instead of raising runtime
  exceptions.
- `raw-string-escapes` is language-aware and metadata-driven: Python literals
  use tokenizer spans for precise detection and autofix context, while other
  languages use configurable suffix, literal, raw-prefix, and escape-pattern
  metadata (`language_suffixes`, `literal_patterns`,
  `raw_literal_patterns`, `suspicious_escape_patterns`).
- `no-raw-errors` enforces explicit error surfaces in Python source by
  flagging bare `except`, generic `raise Exception(...)`, and silent
  `except Exception: pass` handlers through selector-driven scope metadata.
- `tests-coverage` is structural and validates assertion signals across related
  tests for each in-scope module that already has related tests.
  It reads related test files directly (no gate-status evidence payload) and
  uses profile-owned assertion metadata (`assertion_signal_patterns`,
  `tautology_patterns`, `fixture_marker_pattern`) plus symbol-fidelity keys
  (`symbol_kinds`, `symbol_name_min_length`, `symbol_assertion_window`,
  `enforce_symbol_fidelity`) to enforce function/class coverage
  deterministically.
  Assertion signal helpers are policy-owned under
  `devcovenant/builtin/policies/tests_coverage/assertion_signal.py`.
- session-bound checks (for example changelog coverage) consume the
  gate-session ledger from
  `devcovenant/registry/local/gate_status.json`; `gate --start` records
  baseline snapshots, checks run against post-start snapshot deltas, and
  missing/invalid session metadata is an explicit error. Start cannot reset a
  closed-session baseline when post-end edits exist; reconcile-on-start must
  clear policy checks and test execution before baseline rewrite. End closure
  timestamps/snapshots are written only after a successful end gate and never
  from failing end runs.
- bundled policy helpers do not expose metadata-driven `session_scope`
  switching; bundled session checks read runtime session state directly.
- bundled session checks share centralized snapshot helpers from
  `devcovenant/core/runtime/session_snapshot.py`, with command-facing
  compatibility re-exports from `devcovenant/core/runtime/execution.py`.
- `last-updated-placement` scopes stale-date checks to session-changed files
  from runtime context only (no git fallback scanning).
- `version-sync` stays consistency-only; semver bump progression and release
  scope enforcement are handled by `semantic-version-scope`.
- `semantic-version-scope` activation follows
  `config.yaml -> policy_state`; descriptor text should stay neutral and not
  hardcode an enabled/disabled deployment assumption.
- runtime change-state naming uses `current_snapshot_*` for full current
  snapshot data and `session_*` for gate-scoped deltas.
- `version-sync` uses role-based selectors
  (`target_role_files`/`target_role_globs`/`target_role_dirs`) and
  `role_extractors` mappings (`role=>extractor`) to keep target-version
  checks format-aware without file-type bucket metadata.
- policy descriptors keep contract keys, while global/profile overlays provide
  operational defaults for `changelog-coverage`, `last-updated-placement`,
  `semantic-version-scope`, `version-sync`, `modules-need-tests`,
  and `tests-coverage`.
- `devcov-integrity-guard` keeps its path keys declared in the descriptor,
  while `global` profile overlays provide default values for
  `policy_definitions`, `registry_file`, and `gate_status_file`.

## Output Governance Policy
`no-print-outside-output-runtime` is now a metadata-driven output-sink policy.
The policy script stays generic while profiles own operational values.

### Metadata Ownership Model
- descriptor:
  owns contract keys and neutral defaults only.
- language profiles:
  own sink declarations (`sink_call_targets`, `sink_attr_targets`,
  `sink_macro_targets`) using `language=>target` entries.
- repository profiles:
  own selection scope (`include_*`, `exclude_*`) and boundary allowances
  (`allowed_file_globs`, `allowed_symbol_targets`,
  `allow_waiver_comment`).
- activation:
  remains `config.yaml -> policy_state` for standard toggles; critical
  severity enforcement immunity still applies.
  The current initial critical set is `devflow-run-gates`,
  `devcov-integrity-guard`, and `devcov-structure-guard`.

### Enforcement Model
1. Build scope from resolved selector metadata.
2. Resolve one translator/language per file through translator runtime.
3. Load sink targets for that language (plus wildcard `*` targets).
4. Detect sink calls:
   Python uses AST; non-Python uses language-aware textual matching.
5. Allow only hits covered by boundary metadata
   (`allowed_file_globs`, `allowed_symbol_targets`, waiver marker).
6. Emit violations for remaining direct-output sinks.

### Metadata Contract (Output Sinks)
- `sink_call_targets`: `language=>call_target` entries.
- `sink_attr_targets`: `language=>attribute_target` entries.
- `sink_macro_targets`: `language=>macro_target` entries.
- `allowed_symbol_targets`: `language=>symbol_name` entries.
- `allowed_file_globs`: path globs where sinks are allowed by boundary.
- `allow_waiver_comment`: line marker for explicit reviewed waivers.

### no-print-outside-output-runtime
The policy does not hardcode language sink lists or repository paths.
It enforces only what resolved metadata declares for the active profile stack.

## Core Policy Deep Dives
### dependency-license-sync
`dependency-license-sync` is metadata-driven and profile-driven:
- dependency inputs are resolved primarily from role-based selectors:
  `dependency_role_files`/`dependency_role_globs`/`dependency_role_dirs`
  with `role=>selector` tokens
- generic selectors (`dependency_files`/`dependency_globs`/
  `dependency_dirs`) remain available when role taxonomy is unnecessary
- canonical roles are:
  - `intent`
  - `resolved`
  - `package_manifest`
- selector keys are generic by design and may include both manifests and
  lock/resolution files
- `update_lock` resolves lock refresh targets from `resolved` role file
  selectors
- no language-specific manifest list is hardcoded in policy logic
- mixed-language repositories are supported by profile overlays and config
  metadata layers

Role selector examples:
- `intent=>requirements.in`
- `resolved=>requirements.lock`
- `package_manifest=>pyproject.toml`
- `intent=>services/*/package.json`

Compliance domains:
- `repo_dependency_compliance`: repository dependency changes (tooling and
  product dependency inputs present in the repository) must update legal
  artifacts consistently.
- `package_distribution_compliance`: package-level legal artifacts shipped in
  sdists/wheels/binaries; this scope is defined by packaging contracts and is
  not enforced by `dependency-license-sync` alone.

Boundary rule:
- Passing `dependency-license-sync` means repository artifacts are synchronized
  for changed dependency inputs; it does not certify distribution-package legal
  completeness by itself.

Package-distribution contract for this repository:
- `pyproject.toml` uses SPDX `project.license` and PEP 639
  `project.license-files`.
- `MANIFEST.in` includes the same license-source artifacts for sdist inputs.
- required shipped legal artifacts are:
  - `LICENSE`
  - `licenses/THIRD_PARTY_LICENSES.md`
  - `licenses/*.txt` dependency license texts
- build-time validation is enforced by
  `tests/devcovenant/test_install.py`.

Default artifact contract:
- `licenses/THIRD_PARTY_LICENSES.md` for the report document
- `licenses/README.md` for generated, generic maintenance guidance
- `licenses/` for per-dependency license texts/notices
- no legacy marker artifacts are required in `licenses/`

Operational behavior:
- when dependency manifests change, the policy requires synchronized updates to
  both the report document and the license directory
- `devcovenant update_lock` delegates lock refresh/runtime orchestration while
  this policy enforces the license artifact contract
- lock refresh handlers are policy-owned under
  `devcovenant/builtin/policies/dependency_license_sync/`
  (`dependency_lock_runtime.py`) and invoked through policy runtime action
  dispatch
- autofix is scoped to configured artifacts only (`third_party_file` and
  `licenses_dir/README.md`) and rejects out-of-repo metadata paths
- refresh/fix rewrites the configured `## License Report` section
  deterministically from the current dependency-change set; stale report
  entries are pruned automatically
- refresh/fix behavior remains idempotent when report and README already
  match the expected deterministic content

### version-sync
`version-sync` is role-based:
- declare role names in `target_roles`
- map each role to one extractor in `role_extractors` (`role=>extractor`)
- attach selectors with `target_role_files` / `target_role_globs` /
  `target_role_dirs` (`role=>selector`)
- all declared role targets are required; there is no optional-target mode
- extractor set is explicit (`doc_header_version`,
  `changelog_header_version`, `manifest_project_version`, `semver_token`)
- `manifest_project_version` is format-aware and resolves version fields from
  TOML/JSON/YAML manifest files using the same role mapping contract
- semver bump progression and scope tagging are enforced separately by
  `semantic-version-scope` when that policy is enabled
- target-role metadata is expected to be profile-driven, with final values
  resolved by standard metadata precedence
  (descriptor -> active profiles -> config overlays -> config overrides)

`devflow-run-gates` required command metadata is canonical:
- descriptor default may be empty
- active profiles may contribute commands through `required_commands`
- config overlay/override layers can append or replace
- runtime executes exactly what resolves, in declared order

Documentation route metadata:
- `doc_routes`: list of `trigger => doc1, doc2` mappings
- trigger supports prefix (`path/`) and glob (`**/*.py`) forms
- route, mention, and quality violations use the policy's single `severity`
- malformed `doc_routes` entries emit explicit configuration violations

## Autofix Model
Autofix helpers are optional.
When present, they live under `autofix/`.
Do not keep empty placeholder `autofix/` directories.

Routing behavior:
- use language-specific autofix helper when available
- fall back to `autofix/global.py` otherwise

Some policies intentionally ship without autofix helpers.

## Custom Policy Overrides
Custom policy with same ID fully overrides builtin policy and suppresses
builtin autofix helpers for that ID.

Override policy still participates in the same metadata resolution and
`policy_state` activation flow.

## Workflow
1. Update descriptor text/metadata and check script together.
2. Run `devcovenant refresh` if descriptor metadata changed.
3. Update mirrored tests.
4. Run `devcovenant test` and `gate --end`.

## Testing Expectations
Policy changes require mirrored tests under:
- `tests/devcovenant/builtin/policies/<policy-id>/...`
- `tests/devcovenant/custom/policies/<policy-id>/...` for custom policies

Tests validate current behavior only. Remove stale tests for removed behavior.
Placeholder test stubs are not allowed; tests must encode behavioral or
contract assertions.
