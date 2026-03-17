# DevCovenant Architecture Contracts
**Last Updated:** 2026-03-16
**Project Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Program Vocabulary](#program-vocabulary)
- [Evidence Artifact Flow](#evidence-artifact-flow)
- [Workflow](#workflow)
- [Output Governance Contract](#output-governance-contract)
- [Contract Surface Matrix](#contract-surface-matrix)
- [Core Runtime Invariants](#core-runtime-invariants)
- [Policy Runtime Invariants](#policy-runtime-invariants)
- [Quality Invariants](#quality-invariants)

## Overview
This document is the stable architecture contract for DevCovenant.
DevCovenant is a Repository Governance Framework.
It is an SDLC policy and evidence engine, AI-resilient by design and usable
without AI.

It captures behavior that should stay consistent across refactors. Detailed
operational procedures stay in the other docs in this folder.

## Program Vocabulary
Core user-facing nouns (for example `gate session`, `check`, `policy`,
`profile`, `translator`, `evidence artifact`, and `registry`) are defined in
`devcovenant/README.md` under `Glossary (Canonical Terms)`.
This section adds runtime and architecture vocabulary used by implementation
contracts.

- `output boundary`:
  one runtime interface for all user-visible output.
- `output mode`:
  command output contract level (`normal` concise, `quiet` minimal,
  `verbose` detailed).
- `tests output mode`:
  test-command output/progress contract (`normal` concise,
  `quiet` minimal, `verbose` detailed).
- `test event`:
  normalized lifecycle event emitted by test adapters.
- `assertion signal`:
  meaningful assertion proving behavior in related tests; tautologies are
  excluded unless fixture-annotated.
- `deterministic execution`:
  DevCovenant self-runs rely on explicit configuration, stable metadata,
  and reproducible session state.

## Evidence Artifact Flow
Evidence artifacts are a first-class output of the runtime, not an incidental
debug byproduct. The runtime translates source files into shared internal
units, policies evaluate those units, and command/gate flows record evidence
artifacts that prove what happened.

Conceptual flow:

```text
repo files
  -> translator runtime (language-profile selected)
  -> normalized internal units
  -> policy runtime evaluation (check/gate orchestration)
  -> evidence artifacts
       - concise gate session ledger (gate_status.json)
       - companion session snapshot (session_snapshot.json)
       - per-run log folder (run.json, summaries, stdout/stderr, tail)
       - closure-proof references in tracked docs (PLAN/CHANGELOG)
```

Translator boundary clarification:
- translators are the language-aware boundary between repository source and
  policy runtime inputs
- policies stay language-agnostic by consuming normalized units rather than
  language-specific parser details
- this boundary is a key differentiator: evidence artifacts can remain stable
  while language coverage expands through translators

## Workflow
Runtime architecture is coupled to the enforced gate sequence.
`gate --start` establishes session scope, `gate --mid` runs a
non-lifecycle mutating preflight, `test` records command execution, and
`gate --end` closes the session with clean-hook metadata and closure
evidence.

## Output Governance Contract
Output-sink governance is implemented by
`no-print-outside-output-runtime` as a metadata-driven policy.

Architecture ownership split:
- policy script:
  generic enforcement engine (no hardcoded language sink inventory).
- language profiles:
  define sink inventories through `sink_call_targets`,
  `sink_attr_targets`, and `sink_macro_targets`.
- repository profiles:
  define scope and boundary allowances through selectors,
  `allowed_file_globs`, `allowed_symbol_targets`,
  and `allow_waiver_comment`.

Language handling:
- translator runtime arbitrates one language translator per file.
- sink checks run against resolved language metadata.
- Python sink detection is AST-based; non-Python uses language-aware text
  matching until richer translator facts are introduced.

Invariant:
- direct-output sink policy behavior is profile/config driven.
- policy code remains contract-stable while metadata evolves.

## Contract Surface Matrix
- Tier A: user contract (CLI behavior, config schema, managed doc formats).
- Tier B: extension contract (policy/profile/translator interfaces).
- Tier C: data contract (tracked registry schema and runtime status payloads).
- Tier D: layered kernel modules under
  `devcovenant/core/{flow,runtime,services,lib,contracts}` with direct
  submodule imports and no lazy package-export compatibility indirection.

## Core Runtime Invariants
### Runtime and Parsing
- Runtime policy input is the AGENTS managed policy block.
- Tracked registry state is deterministic governance data and AGENTS
  compile source.
- Policy registry entries record `origin` as `builtin` or `custom`.
- `check` is the default read-only audit command; gate commands own refresh,
  autofix orchestration, and lifecycle state writes for the same checking
  routine.
- Gate-managed autofix requests read `engine.auto_fix_enabled` from repo
  config and default to disabled when the key is absent.
- `upgrade` normalizes and reports semantic-version comparison (including
  partial and `v`-prefixed versions), then always reconciles the full
  `devcovenant/` package from source (`devcovenant/*.py`, `core/`, `builtin/`)
  while preserving repo-local runtime/custom state.
- Upgrade preserves user custom policy trees under
  `devcovenant/custom/policies/**` and user custom profile trees under
  `devcovenant/custom/profiles/**` by design.
- Upgrade prunes known repo-only custom payload directories leaked by older
  installs (`devcov_raw_string_escapes`, `managed_doc_assets`,
  `readme_sync`, repository-only custom profiles) before refresh.
- When a custom script has a missing/invalid descriptor, refresh/upgrade keeps
  custom files but fails with the same descriptor-missing/invalid contract as
  core policies until descriptor metadata is fixed.
- Managed-doc descriptors are schema-validated before refresh rendering:
  descriptors must declare ordered keys
  (`title`, `doc_id`, `doc_type`, `project_version`, `last_updated`,
  `devcovenant_version`, `managed_block`, `body`, optional `workflow_block`);
  multiline `managed_block`/`body`/`workflow_block` values must use YAML
  literal block scalar style so generated markdown remains deterministic.
- `devcovenant/core/runtime/run_logging.py` provides the shared per-run log
  substrate (run-folder allocation, artifact metadata, and latest-run pointer
  updates under `devcovenant/logs/`) while command layers own integration.
- CLI dispatch now owns top-level run-context lifecycle (create/adopt on
  entry, finalize on success/failure, and pointer emission) so all root
  commands can share one run-folder contract.
- CLI unhandled exceptions are normalized through
  `devcovenant/core/runtime/errors.py` into typed explicit errors
  (`devcovenant/core/contracts/errors.py`) before process exit, while full
  traceback detail is preserved in run-log artifacts.
- The run-logging substrate is intended to remain full-fidelity even when
  command layers later change console verbosity or suppression behavior.
- Output mode is resolved from `devcovenant/config.yaml -> engine.output_mode`
  (`normal|quiet|verbose`) and defaults to `verbose` when unset or invalid.
- tests output mode resolves from
  `devcovenant/config.yaml -> engine.tests_output_mode`. Keep the key
  explicit so test output behavior is not inferred from `engine.output_mode`.
- `test` resolves required commands through the
  `devflow-run-gates` policy runtime action
  (`resolve-required-test-commands`) and executes exactly the returned
  command chain; runtime does not inject hidden alternate command lists.
- managed-environment orchestration is policy-owned:
  `managed-environment` runtime action `resolve-stage` prepares
  stage-scoped environment state (`start`/`test`/`end`/`command`), and
  CLI dispatch re-execs DevCovenant commands in the resolved interpreter
  when current and managed interpreters differ.
  Lifecycle bootstrap/teardown commands
  (`install`, `deploy`, `undeploy`, `uninstall`) bypass managed re-exec.
- when a resolved managed interpreter path exists but is not executable,
  CLI dispatch emits an explicit managed-environment error and stops so the
  interpreter contract can be repaired directly.
- Normal-mode `devcovenant test` keeps status output concise, suppresses
  flood-prone test child output in console, captures full child output in
  run-log artifacts, and emits sparse deterministic start/completion markers
  for each required command (for example `▶ [n/total] <command>` plus
  completion/failure lines).
- Progress-bar parsing/rendering is removed from the DevCovenant runtime so
  CI and agent terminals do not receive redraw/noise spam.
- Runtime subprocess helpers and gate rerun helpers capture command
  stdout/stderr into the active run-log context so full-fidelity artifacts do
  not depend on console verbosity mode.
- Gate recovery-start reconcile test runs invoke `devcovenant test` without
  end-buffering subprocess stdout/stderr so concise normal-mode liveness
  markers remain visible during recovery.
- Gate status records `tests_output_mode` and
  `tests_required_commands_key` with each test run so end-gate validation
  can replay the exact command contract used at test time.
- Each required test command also emits a `test_event` with schema version
  `1.0` (from `EVENT_SCHEMA_VERSION` in
  `devcovenant/core/services/event.py`). `session_snapshot.json` stores the
  full `test_events` payload list, while `gate_status.json` keeps the concise
  `test_events_count` summary field.
- `devcovenant test` also writes informational per-run profiling artifacts
  (`test_profile.json`, `test_profile.txt`) in the active run-log folder with
  module/group aggregation and slowest-command duration breakdowns for the
  resolved command chain (supports two or more commands).
- test summary metadata includes stable command-duration aggregation fields
  (`duration_seconds_min_command`, `duration_seconds_avg_command`,
  `duration_seconds_max_command`, `duration_events_count`) so duration trends
  remain queryable across runs.
- Adapter-load failures no longer fail silently. Runtime stores adapter-load
  warnings in `devcovenant/core/services/event.py` and emits them through the
  output boundary before command execution continues.

### Metadata and Activation
- Activation authority is `config.yaml -> policy_state` for standard
  enable/disable toggles.
- `severity: critical` policies remain enforced even when a config toggle in
  `policy_state` attempts to disable them; runtime emits an explicit
  diagnostic and continues enforcement.
- Current initial critical rollout set:
  `devflow-run-gates`, `devcov-integrity-guard`,
  `devcov-structure-guard`.
- Metadata precedence is fixed:
  descriptor defaults -> profile overlays -> autogen overlays ->
  user overlays -> autogen overrides -> user overrides -> policy_state.
- Policy registry entries now persist per-key `metadata_resolution` trace and
  structured `metadata_warnings` so descriptor/profile/config precedence can
  be audited without reading runtime code or guessing from final values.
- Policy registry entries also persist typed
  `runtime_metadata_options`, `runtime_config_overrides`, and
  `runtime_effective_options` views so runtime-facing policy option behavior
  can be inspected without reconstructing `PolicyCheck.get_option(...)`
  manually.
- Trace payloads may also show runtime-owned layers such as
  `runtime_defaults`, `runtime_identity`, and `derived_selectors` when the
  effective value is filled or normalized by runtime rather than directly by a
  descriptor/profile/config layer.
- Pseudo-empty sentinel tokens are not part of active metadata contracts.
  Empty metadata must use typed YAML empties (`''`, `[]`, `{}`).
- Refresh rewrites a full alphabetical `policy_state` map:
  - preserve existing booleans
  - seed new IDs from resolved descriptor defaults
  - remove stale IDs
  - keep user-entered booleans even when runtime will ignore a critical
    disable toggle

### Profiles and Translators
- Profiles provide overlays, cleanup overlays, assets, selectors, and hook
  fragments.
- Profiles do not activate policies.
- Only language profiles declare translators.
- Policies remain language-agnostic and request translation via runtime.
- Translator runtime resolves by extension from active language profiles.

### CLI and Command Placement
- Public commands are:
  `check`, `clean`, `gate`, `test`, `install`, `deploy`, `refresh`,
  `upgrade`, `undeploy`, `uninstall`, `update_lock`.
- CLI examples default to on-PATH `devcovenant ...` usage.
- `python3 -m devcovenant ...` remains a supported alternate launcher form for
  source checkouts.
- CLI-facing command scripts stay at package root.
- Active kernel ownership now lives under `devcovenant/core/flow`,
  `devcovenant/core/runtime`, `devcovenant/core/services`,
  `devcovenant/core/lib`, and `devcovenant/core/contracts`.
- `devcovenant/core/flow/clean.py` orchestrates cleanup selection/reporting,
  records clean-summary metadata for run artifacts, while
  `devcovenant/core/services/cleanup.py` resolves config/profile targets,
  honors explicit per-key override clearing, and enforces non-overridable
  protection fences.
- Bundled policy/profile sources are canonical under
  `devcovenant/builtin/policies` and `devcovenant/builtin/profiles`.
- Legacy bundled policy/profile source trees are removed; runtime resolves
  bundled checks/profiles from builtin.
- Managed-environment CLI re-exec is single-hop guarded to prevent loops.

### Gate Contract
- `gate --start` is blocking: non-zero pre-commit exit fails the command and
  does not record start metadata.
- managed-environment defaults remain disabled in builtin/global descriptors
  and
  templates; repositories opt in through
  `config.yaml -> policy_state.managed-environment`.
- when `managed-environment` is enabled, gate stages run stage-scoped
  `managed_commands` (`start`/`end`) before pre-commit, then execute
  Python-launcher gate commands with the resolved managed interpreter.
- managed-environment resolution requires local policy registry metadata.
  Missing registry state now fails explicitly and requires
  `devcovenant refresh`.
- managed-environment command stages are metadata-driven:
  `start`, `test`, `end`, `command`, and `all`.
- managed-environment interpreter detection preserves virtualenv launcher
  paths (for example `.venv/bin/python`) instead of collapsing symlinks to
  system interpreter paths.
- if a non-start stage is invoked before interpreter creation, runtime runs
  explicit `start=>...` managed commands once as stage bootstrap.
- managed-environment stage bootstrap state is tracked in
  `DEVCOV_MANAGED_STAGE_RUNS` so `start` commands are not rerun after CLI
  managed-interpreter re-exec.
- managed-environment stage resolution honors explicit base environments, so
  empty base-env inputs isolate stage tracking from ambient process state.
- managed-environment stage command subprocess output honors runtime output
  mode and command policy: normal/quiet suppress managed child bursts
  (for example managed `pip install` steps), while verbose mode streams
  full managed-child output; all variants preserve full lines in active
  run logs.
- Start baseline metadata is created only on successful start-gate completion.
- Start gate clears stale end-phase pre-commit evidence so ordering checks
  align to the active session.
- Start gate records AGENTS hash metadata (`agents_full_sha256`,
  `agents_workflow_sha256`, `agents_non_workflow_sha256`) in gate status so
  workflow reread discipline can detect non-workflow AGENTS changes.
- `gate --end` records closure timestamps only after successful convergence.
- `gate --end` writes closure fields only after successful hook/test
  convergence; failing end runs must keep the session open and preserve the
  prior closure metadata.
- `gate --start` cannot silently overwrite a closed-session baseline:
  - when no post-end edits are detected, start follows the normal path
  - when post-end edits are detected, start runs reconcile checks before
    baseline rewrite
  - malformed status payloads use the same reconcile discipline instead of
    silent baseline reset
- `gate --end` is explicit-loop oriented: it does not rerun hooks/tests
  internally when hooks mutate files or tests are stale; instead it fails
  with instructions to run `devcovenant test` and rerun
  `devcovenant gate --end`.
- `gate --end` fail-fast: if pre-commit surfaces blocking, non-autofixed
  DevCovenant violations, end fails immediately without rerunning tests.
- `gate --end` failure messages should lead with explicit next-step commands
  (`fix`, `devcovenant test` when required, then rerun
  `devcovenant gate --end`) instead of non-actionable "no reruns" wording.
- `gate --mid` reuses the gate-owned pre-commit/DevCovenant mutating check
  path inside an open session, but does not write lifecycle timestamps or
  change `session_state` in gate status.
- gate pre-commit file targeting is phase-consistent: `start`, `mid`, and
  `end` all derive the same snapshot-backed file list, so newly created files
  are enforced before any lifecycle transition and cannot bypass one phase.
- `gate --mid` resolves managed-environment prep through the generic
  `command` stage so repositories can opt into a mid-session wrapper/setup
  path without conflating lifecycle `start`/`end` stages.
- gate commands never run tests internally (start recovery/reconcile and end
  closure paths both require explicit operator `devcovenant test` runs;
  `gate --mid` is a pre-test hook sweep, not a test substitute).
- recovery-start now evaluates existing explicit test evidence and only keeps
  blocking when tests are stale/missing for the current unsessioned edits.
- `devflow-run-gates` keeps edit sessions strict and allows one narrow audit
  relaxation: closed-session no-change `devcovenant check` runs do not block
  solely because recorded tests are newer than recorded end.
- Runtime snapshot/session helper ownership lives in
  `devcovenant/core/runtime/session_snapshot.py`.
- `devcovenant/core/flow/session.py` exports explicit session helper symbols
  (`capture_current_numstat_snapshot`, `session_delta_paths`, and related
  snapshot helpers) rather than wildcard runtime imports.
- Command execution and managed-environment orchestration live in
  `devcovenant/core/runtime/execution.py`.
- AGENTS policy-block rendering lives in
  `devcovenant/core/services/policy_block_refresh.py`.
- AGENTS policy parser/model helpers live in
  `devcovenant/core/services/policy_parse.py`.
- Policy metadata parsing treats only non-indented `key:` rows as new keys, so
  indented continuation values can safely contain `:` tokens (for example URL
  prefixes and long-line marker tokens).
- Registry metadata block parsing uses the same non-indented `key:` rule so
  AGENTS refresh/registry round-trips keep colon-containing continuation
  values stable.
- Policy check orchestration lives in
  `devcovenant/core/services/policy_engine.py`. The stable service surface is
  `DevCovenantEngine.check()` returning `CheckResult`, with result helper
  methods used by command layers for blocking/sync decisions.
- Core package `__init__` modules now act as simple namespace markers.
  Internal callers import concrete submodules directly, and extracted helper
  seams under `devcovenant/core/services/policy_*.py` remain internal
  implementation modules unless a plan slice explicitly promotes one.
- Cleanup orchestration in `devcovenant/core/flow/clean.py` treats
  `devcovenant clean` as a post-session maintenance command: it checks the
  runtime gate-status file first and fails explicitly when a gate session is
  still open, so runtime registry and log cleanup cannot erase live session
  evidence. The cleanup service also derives safe build-artifact release-tree
  targets from repo/manifest project names and removes repo-root unpacked
  directories shaped like `<project>-<version>/`.
- Policy-engine summary status messaging now resolves against the configured
  `engine.fail_threshold` so printed status text matches actual blocking
  behavior.
- `line-length-limit` keeps default max-length enforcement but now supports
  optional metadata escape hatches across all selected file types:
  `allow_long_url_lines` + `url_prefixes`, and `allow_long_lines` with
  `long_lines_contain` plus `long_lines_between` (`left=>right` pairs).
- `TranslatorRuntime` keeps bounded run-scoped caches for `can_handle`
  arbitration results and translated immutable `LanguageUnit` payloads,
  using context object identity where needed, to reduce repeated work across
  policies without changing result ordering.
  methods `has_violations()` and `has_sync_issues()`.
- Policy runtime actions also dispatch through
  `devcovenant/core/services/policy_engine.py` via
  `run_policy_runtime_action(...)` and policy-level
  `PolicyCheck.run_runtime_action(...)`.
- `policy_engine.py` now delegates policy script loading and runtime-action
  dispatch helpers to
  `devcovenant/core/services/policy_runtime_actions.py`, while preserving the
  `policy_engine` wrapper functions as the stable service import surface.
- `policy_engine.py` also delegates violation/sync reporting and fail-threshold
  blocking helpers to `devcovenant/core/services/policy_reporting.py` while
  preserving `DevCovenantEngine` reporting methods as the stable output
  contract surface.
- `policy_engine.py` also delegates repository file-scope helpers (config
  ignore pattern normalization, core exclusion path resolution, profile-based
  suffix/ignore merges, and repository file collection) to
  `devcovenant/core/services/policy_file_scope.py` while preserving engine
  methods as the stable call surface for callers and tests.
- `policy_engine.py` also delegates autofixer discovery/execution helpers
  (bundled fixer loading plus auto-fix run-loop messaging/results) to
  `devcovenant/core/services/policy_autofix.py` while preserving engine
  wrapper methods as the stable call surface for command flows and tests.
- `policy_engine.py` also delegates change-state and check-context assembly
  (gate-session snapshot interpretation and `CheckContext` construction) to
  `devcovenant/core/services/policy_check_context.py` while preserving
  engine wrapper methods for callers/tests that patch engine internals.
- `policy_engine.py` also delegates policy execution-loop helpers
  (critical-disable enforcement, option extraction, and per-policy execution
  counting/error-to-violation conversion) to
  `devcovenant/core/services/policy_check_runner.py` while preserving
  engine wrapper methods and count-mutating semantics for command flows.
- Profile discovery/merge registry runtime lives in
  `devcovenant/core/services/profile_registry.py`.
- Profile discovery validates manifest template references before registry
  output is built: `assets[*].template`, `gitignore_template`, and
  `governance_template` must resolve within the profile `assets/` tree so
  refresh/registry paths fail explicitly on profile asset drift.

### Refresh and Registry
- Full refresh runs in `refresh`, `deploy`, `upgrade`, and gate pre-commit
  phases via gate-owned check orchestration (`gate --start`,
  required non-lifecycle `gate --mid`, and `gate --end`).
- Refresh regenerates:
  - the tracked `devcovenant/registry/registry.yaml` document
  - AGENTS managed policy block
  - managed docs and generated config sections
  - generated `.pre-commit-config.yaml` and `.gitignore`
  - generated `.github/workflows/governance-and-test.yml` with literal
    workflow trigger key `on` preserved and trigger events rendered in
    canonical form (`push:`, `pull_request:` without `null` values)
- `.gitignore` is generated from:
  - global template fragments
  - active profile manifest fragments (`gitignore_fragments` or `ignore_dirs`)
  - `config.gitignore.overlays`
  - preserved user block entries
- global template ignores runtime artifacts under `devcovenant/logs/**`
  while re-including `devcovenant/logs/` and
  `devcovenant/logs/README.md`
- core manifest/structure guard now requires `devcovenant/logs` and the
  tracked `devcovenant/logs/README.md` skeleton without requiring any policy
  inventory to exist
- runtime subprocess execution exports `PYTHONPYCACHEPREFIX` when
  `engine.pycache_prefix_enabled` is active so repo-local DevCovenant child
  Python commands write bytecode caches outside the repo tree while
  preserving bytecode generation fidelity.
- source-checkout top-level `python3 -m devcovenant ...` launches can still
  write launcher-process bytecode before DevCovenant runtime code gains
  control; shell/CI `PYTHONPYCACHEPREFIX` owns that zero-drift boundary
  instead of repo-root startup hooks or in-package bootstrap tricks.
- Runtime gate state file is `devcovenant/registry/runtime/gate_status.json`.
- `gate --status` reads gate-state and latest-run-log pointers through a
  short, read-only status path and does not mutate lifecycle state.
- `devcovenant/core/flow/gate_status_helpers.py` owns read-only status-line
  assembly and owned latest-run pointer resolution for `gate --status`.
- `devcovenant/core/flow/gate_changelog_helpers.py` owns gate-start
  changelog top-entry fingerprint and document-exemption option resolution.
- changelog helper default header-key resolution aligns with generated doc
  headers: `Last Updated`, `Project Version`, `DevCovenant Version`.
- Gate/runtime helper extraction remains explicit: command-facing modules may
  call dedicated helper modules, but package-level compatibility-export
  indirection is removed and internal callers import concrete modules
  directly.
- gate-start document exemption baselines now capture DEVCOV-managed block
  fingerprints for non-doc text files (for example generated YAML/YML
  assets) so changelog coverage can ignore managed-only regenerations
  during gate-session checks.
- managed/header exemption fingerprinting is centralized in
  `devcovenant/core/lib/document_exemptions.py`; runtime session baseline
  capture (`session_snapshot`) and the `changelog-coverage` policy consume
  the same canonical helper functions to avoid behavior drift.
- `devcovenant/builtin/policies/last_updated/last_updated.yaml` now carries
  the neutral package-doc baseline (`devcovenant/README.md`,
  package README surfaces, and `devcovenant/docs/**/*.md`) so installed
  repos inherit safe `Last Updated` defaults before profile overlays add
  repo-specific root docs or maps.
- top-level CLI run-log pointer emission is centralized in
  `devcovenant/core/runtime/execution.py`; normal-mode test runs can emit
  the same standard `Run logs:` pointer early for artifact-first triage
  without duplicating the final CLI pointer line. `uninstall` is the one
  deliberate exception because it removes `devcovenant/` and cannot preserve
  a durable run-log folder under that path.
- run-log retention is runtime-owned in the same layer and prunes older
  per-run directories after command finalization using
  `engine.logs_keep_last` (`0` = unlimited retention).
- runtime console emission is line-flushed by the shared output boundary so
  long-running command status/progress messages stay live while command
  output streams continuously.
- runtime subprocess streaming helpers also emit a low-rate normal-mode
  heartbeat (`Please wait. In progress...`) during long silent waits while
  preserving existing phase/start lines.
  Heartbeat scheduling remains sub-second so short silent steps can still emit
  deterministic liveness lines when heartbeat output is configured.
- runtime subprocess helpers use a PTY-backed stream path on POSIX when
  console emission is enabled so child-tool output flushes live instead of
  accumulating in subprocess buffers; helpers fall back to pipe streaming
  when PTY is unavailable or normal-mode suppression hides child output.
- child command routing is centralized through
  `run_child_command_with_output_policy` in
  `devcovenant/core/runtime/execution.py`, with channel plans resolved via
  `resolve_child_output_plan_for_channel` so gate/test/managed paths share one
  output pipeline.
- normal mode streams gate pre-commit hook output, suppresses
  flood-prone managed/test child channels, and still emits deterministic
  progress/liveness lines through the shared output boundary without
  duplicate per-command completion lines.
- quiet mode suppresses routine stdout child output across channels while
  preserving stderr error/violation surfaces and full run-log artifacts.
- policy-engine reporting routes violation/sync output to stderr in quiet mode
  so failures stay visible while routine stdout remains suppressed.
- verbose mode keeps full child-output streaming through the same runtime
  helper path for every channel.
- CLI run logs (`run.json`) record interpreter provenance (`invoked_python`,
  `effective_python`, `managed_environment_active`,
  `managed_reexec_applied`) so managed-environment re-exec behavior is
  inspectable from evidence artifacts.
- retention pruning preserves the active finalized run, the runtime pointer at
  `devcovenant/registry/runtime/latest.json`, and the tracked
  `devcovenant/logs/README.md` skeleton while removing older run folders only.
- Changelog and session scoping use gate-session snapshots
  (`session_start_snapshot`, optional `session_baseline_snapshot`,
  `session_end_snapshot`, `last_run_snapshot`).
- Gate-session snapshots now use the current filesystem-hash row format only;
  older snapshot payloads are rejected explicitly and require a fresh
  `devcovenant gate --start`.
- `session_snapshot.json` stores the targeted
  `session_start_snapshot` baseline mapping so `changelog-coverage` can scope
  deleted-file evidence to the active session without relying on HEAD-wide git
  deletions.
- `gate_status.json` stays slim by storing lifecycle state plus
  `session_snapshot_file` / `session_snapshot_updated_*` pointer metadata
  instead of the heavy snapshot payloads themselves.
- Filesystem snapshot helpers are centralized in
  `devcovenant/core/runtime/session_snapshot.py`, with runtime consumers
  treating that module as the canonical snapshot-helper home.
- Core policy/runtime flow avoids git `HEAD`/working-tree diff dependence for
  bundled session behavior.
- Session-scoped policy checks evaluate an empty scope during normal
  `gate --start`; reconcile-on-start checks evaluate unsessioned delta before
  writing a fresh start baseline.
- Reconcile-on-start must pass pre-commit policy checks and test execution
  before start baseline metadata is rewritten.
- Existing-file session scope is snapshot-diff based and includes only paths
  changed since baseline after applying config `ignore.patterns`; deleted-file
  coverage for changelog validation is derived from `session_start_snapshot`.
- Default global config excludes `devcovenant/config.yaml` from session delta
  and unsessioned-edit detection.
- Universal filesystem noise is layered intentionally:
  shared editor/build/runtime artifacts live in the global baseline
  (`engine.ignore_dirs`, `ignore.patterns`, and generated `.gitignore`),
  builtin policy descriptors carry policy-specific universal skip fences,
  and repo-local overlays are reserved for genuinely repository-specific
  exclusions.
- Missing or invalid session metadata is a hard error.
- Read-only `check` keeps a narrow bootstrap exception:
  missing gate status with an empty scoped delta is non-blocking.
- Policy runtime validates `session_id`, `session_state`, and end-epoch
  invariants before exposing session scope to checks.
- Read-only status rendering may report malformed gate-state payloads, but it
  does not rewrite `gate_status.json` during inspection.
- `changelog-coverage` tolerates out-of-scope files in changelog `Files:`
  blocks (skipped selectors and managed/header-only exempt deltas) while
  still enforcing exact coverage for in-scope changed files.

## Policy Runtime Invariants
- Every policy ships descriptor prose and metadata defaults.
- Descriptor keys remain schema declarations even when values are empty
  placeholders; active profiles own operational defaults (for example
  line-length limits and gate/session path metadata).
- `devcov-integrity-guard` path defaults (`policy_definitions`,
  `registry_file`, `gate_status_file`) are resolved from profile overlays
  while descriptor keys remain declared placeholders.
- Runtime executes resolved policy definitions from AGENTS.
- `devcovenant/core/services/metadata.py` is the canonical metadata
  normalization/decoding layer: it resolves list-valued metadata, renders the
  AGENTS/registry string-map form, and provides shared typed decoding helpers
  for runtime option consumers.
- Local policy registry metadata remains a string-map persistence contract for
  stable diffs/audits, while runtime helpers may consume the shared typed view
  derived from that stored map.
- Same-ID custom policy scripts override core scripts fully.
- Autofix helpers are optional and must follow autofix contracts when present.
- Selector metadata keys are shared policy contract keys.
- Session-bound policies read gate-session state from
  `devcovenant/registry/runtime/gate_status.json` and fail explicitly when the
  session ledger is missing or invalid.
- Bundled runtime scope is no longer metadata-switchable (`session_scope` is
  not used by core policy helpers); bundled checks consume gate-session state
  directly.
- `tests-coverage` is structural: it validates assertion signals across
  related tests for in-scope modules via source-to-test relationships and
  reads related test files directly at check time (no gate-status evidence
  payload).
  Assertion helper runtime lives in
  `devcovenant/builtin/policies/tests_coverage/assertion_signal.py`.
  Assertion semantics are metadata-driven by language profiles
  (`assertion_signal_patterns`, `tautology_patterns`,
  `fixture_marker_pattern`), and symbol-fidelity checks are controlled by
  `symbol_kinds`, `symbol_name_min_length`, `symbol_assertion_window`, and
  `enforce_symbol_fidelity`.
- `modules-need-tests` mirror enforcement is metadata-driven:
  `mirror_roots` defines source/test roots, while
  `mirror_test_name_templates` (`language=>template`) defines expected mirror
  filenames; stale mirrors are flagged when they do not map to any active
  module-derived expectation.
  Repository module inventory for this policy uses shared runtime snapshot
  scanning (not git index/HEAD queries) so policy scope stays gate-consistent.
- `raw-string-escapes` is language-aware: Python scanning uses tokenizer
  spans, while non-Python scanning uses metadata-driven literal and escape
  patterns with language suffix routing (`language_suffixes`,
  `literal_patterns`, `raw_literal_patterns`,
  `suspicious_escape_patterns`).
- `no-raw-errors` enforces explicit error surfaces for Python source by
  flagging bare `except`, broad `except Exception` handlers, generic
  `raise Exception(...)`, and silent `except Exception: pass` handlers in
  selected scope.
  Broad-handler waivers are explicit through marker comments and marker
  regions (`broad_exception_waiver_markers`,
  `broad_exception_waiver_between`).
- `read-only-directories` is opt-in by include scope. Empty typed include
  selectors (`[]`) disable enforcement until explicit include metadata is
  configured.
- `dependency-license-sync` and `update_lock` remain metadata-driven,
  including dependency selector metadata for mixed repositories and generated
  generic license artifacts under `licenses/`.
- lock refresh runtime for dependency governance is policy-owned in
  `devcovenant/builtin/policies/dependency_license_sync/` with
  `dependency_lock_runtime.py`.
- dependency selector modeling supports role taxonomy for mixed ecosystems:
  `intent`, `resolved`, and `package_manifest` mapped with
  `role=>selector` metadata entries.
- version-sync extractor taxonomy is role-driven and format-aware:
  `manifest_project_version` handles TOML/JSON/YAML manifests while
  `project_version_line` and `changelog_header_version` cover canonical
  docs/changelog surfaces plus any opted-in legal text, and version-sync
  remains a consistency-only policy that delegates parsing/comparison to
  version-governance.
- version-governance owns version-format validation, scheme-aware bump
  progression, and optional SemVer release-scope validation when enabled.
- `devcovenant/builtin/policies/version_governance/version_governance.py`
  owns the shared changelog/version-file orchestration and scheme registry,
  while sibling modules (`semver.py`, `calver.py`, `integer.py`,
  `pep440.py`, `custom_regex.py`, `custom_adapter.py`) implement
  scheme-specific parsing, comparison, and extra release rules.
- `custom_regex.py` is the strict validation-only escape hatch for exotic
  formats that have no trustworthy ordering semantics.
- `custom_adapter.py` is the strict repo-local extension path for arbitrary
  ordering logic; it loads one repo-relative Python module and expects that
  module to export `SCHEME` with the same version-governance adapter
  interface used by builtin schemes.
- dependency-license-sync validates artifact targets as repository-relative
  paths and rejects out-of-repo traversal for both checks and autofix.
- dependency-license-sync autofix is idempotent: synchronized artifacts are
  left unchanged on repeated runs.
- dependency-license-sync autofix rewrites the configured license-report
  section deterministically from current dependency-change inputs and prunes
  stale report references instead of appending indefinitely.
- Dependency governance is split into two architecture domains:
  - `repo_dependency_compliance`: repository dependency-change hygiene and
    synchronized legal artifacts.
  - `package_distribution_compliance`: legal artifacts included in published
    distributions (sdist/wheel/binary).
- Passing repository dependency compliance does not, by itself, certify
  package-distribution legal completeness; packaging contracts remain the
  authority for shipped artifacts.
- Tooling dependencies and product dependencies are distinct semantics:
  both may exist in repository manifests, but DevCovenant itself is treated as
  a repository tooling dependency by default in governed repositories.
- Changelog coverage keeps session-level prepend-entry semantics and accepts
  header/managed-block exemptions via lightweight
  `document_exemption_baseline` records in `session_snapshot.json` without
  storing whole-repo session signature inventories in `gate_status.json`.

## Quality Invariants
- Refresh output is deterministic for identical inputs.
- CLI output is structured and actionable.
- Tests validate current behavior only.
- Removed modules require removed stale tests.
- Security-sensitive behavior is policy-enforced and test-covered.
