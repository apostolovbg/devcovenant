# Workflow
**Last Updated:** 2026-03-21
**Project Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Program Vocabulary](#program-vocabulary)
- [Required Sequence](#required-sequence)
- [90-Second Evidence Ritual](#90-second-evidence-ritual)
- [Step Details](#step-details)
- [Session State Model](#session-state-model)
- [Recovery and Reconcile](#recovery-and-reconcile)
- [Changelog and Delta Scope Rules](#changelog-and-delta-scope-rules)
- [CI (continuous integration) Mapping](#ci-continuous-integration-mapping)
- [Operator Checklist](#operator-checklist)

## Overview
DevCovenant workflow is a hard contract, not a suggestion:

```bash
gate --start -> gate --mid loop (rerun until clean) -> test -> gate --end
```

The sequence exists to guarantee three things:
- baseline integrity at session start
- execution evidence for required tests
- clean, recorded closure state

The sequence applies to governed code and documentation changes.
Default `ignore.patterns` excludes `devcovenant/config.yaml`, so config-only
edits do not trigger session-delta or changelog-coverage nagging.
Layered kernel modules now live under
`devcovenant/core/{flow,runtime,services,lib,contracts}`.
Namespace scaffolds under `devcovenant/builtin/{policies,profiles}` are the
canonical bundled stock paths.
The lifecycle-metadata contract that feeds AGENTS, SPEC, PLAN, CHANGELOG, and
registry outputs is documented in `devcovenant/docs/project_governance.md`.

Use this document when you need to answer questions like:
- "Which command should I run next?"
- "Why does DevCovenant insist on `gate --mid` before tests?"
- "What is the difference between `check`, `gate --status`, and the gate
  commands?"
- "Why did the tool ask me to rerun part of the sequence?"

## Program Vocabulary
- `gate session`:
  one workflow slice between successful `gate --start` and `gate --end`
- `session baseline`:
  the timestamp/snapshot boundary used to compute in-scope changed files
- `session delta`:
  files changed after baseline
- `output boundary`:
  runtime API (application programming interface) for all command-visible
  output
- `output mode`:
  `verbose`, `normal`, or `quiet` command output contract
- `tests output mode`:
  `verbose`, `normal`, or `quiet` test-command output/progress contract
- `test event`:
  normalized test lifecycle event emitted by adapters
- `assertion signal`:
  meaningful assertion used by tests-coverage checks

## Required Sequence
Canonical commands:

```bash
devcovenant gate --start
# edit files and clear complaints while working
# required pre-test mutating preflight; rerun until clean
devcovenant gate --mid
devcovenant test
devcovenant gate --end
```

If CLI (command-line interface) is unavailable:

```bash
python3 -m devcovenant gate --start
python3 -m devcovenant gate --mid
python3 -m devcovenant test
python3 -m devcovenant gate --end
```

On Windows, `py -m devcovenant ...` is a common equivalent launcher form.
This equivalent launcher form does not change exact-token validation for
`devflow-run-gates.required_commands` test evidence.

Required execution order:
1. on the first session in a new conversation, read full `AGENTS.md`
2. on every session, reread the `DEVCOV-WORKFLOW` block in `AGENTS.md`
3. if AGENTS non-workflow hash changed since prior session, reread full
   `AGENTS.md`
4. build active-policy model from `enabled: true` policies
5. run `gate --start` before edits
6. clear start-gate complaints before editing
7. edit while proactively following policy contracts
8. if complaints appear, clear them before continuing
9. run `gate --mid` before tests to surface hook/devcov
   mutations and blocking complaints early; rerun `gate --mid` until clean
10. run `test`
11. run `gate --end`
12. rerun required steps if end gate reports new changes/violations

`devcovenant clean` is intentionally outside the active gate lifecycle.
Run cleanup only after `gate --end`; an open gate session blocks `clean`
because registry/log cleanup would destroy the session's own runtime evidence.

Quick command-choice guide:
- use `check` when you want a read-only audit
- use `gate --status` when you want to inspect the current gate session
- use `gate --start` / `gate --mid` / `test` / `gate --end` when you are
  doing real repository work
- use `clean` only after the gate session is closed

## 90-Second Evidence Ritual
Use this ritual when you want a fast proof that DevCovenant is working and
producing evidence artifacts, without running a full gate lifecycle first.

Canonical ritual commands:

```bash
devcovenant check
devcovenant test
```

Why this ritual is the canonical quick proof:
- it uses explicit commands from the real command surface (no demo wrapper)
- it demonstrates `check` as read-only audit behavior
- it demonstrates command-run evidence artifacts and `Run logs:` pointers
- it demonstrates quick, live command feedback without running full lifecycle

Stable cues to verify (avoid exact timestamp matching):
1. `check` prints a standard `Run logs:` pointer and completes without opening
   or closing a gate session.
2. `test` prints a standard `Run logs:` pointer, records test command
   evidence, and keeps full output in run artifacts.
3. If a workflow command fails and you need lifecycle inspection, run
   `gate --status` to view `Gate Status:` and a `Latest Relevant Logs:`
   pointer (when run artifacts exist).

Artifact-first inspection order:
1. `summary.txt`
2. `tail.txt` (if present)
3. `stderr.log` / `stdout.log`

Scope note:
- this ritual is a quick confidence check, not a substitute for the required
  development workflow
- for repository work, use the full gate sequence:
  `devcovenant gate --start` -> `devcovenant gate --mid` loop ->
  `devcovenant test` -> `devcovenant gate --end`
- `devcovenant clean` is a maintenance command for disposable build, cache,
  runtime-registry, and log residue; it does not replace the gate workflow
  for actual repository work

## Step Details
Shared gate hook targeting:
- `gate --start`, `gate --mid`, and `gate --end` resolve pre-commit targets
  from the current snapshot path set before hook execution.
- when the configured hook command uses `--all-files`, gate runtime rewrites it
  to explicit `--files <snapshot-paths...>` for phase-consistent coverage,
  including newly created files not yet staged in git.

`gate --start` responsibilities:
- bootstrap local policy registry metadata when missing so managed-environment
  contracts can resolve on clean clones before pre-commit
- run managed-environment `start` commands when policy is enabled
- run pre-commit hooks for baseline validation
- block baseline recording if hooks fail
- record session start timestamps and concise lifecycle metadata in
  `gate_status.json`
- clear stale end-gate pre-commit evidence so ordering checks stay
  session-bound
- record changelog top-entry fingerprint for fresh-entry enforcement
- capture document exemption baselines, recovery baselines, and gate-start
  snapshot data in `devcovenant/registry/runtime/session_snapshot.json`
- resolve changelog/session-baseline helper logic through
  `devcovenant/core/flow/gate_changelog_helpers.py` so metadata parsing and
  top-entry fingerprint behavior stay centralized
- default changelog exemption header keys align with generated doc headers:
  `Last Updated`, `Project Version`, and `DevCovenant Version`
- the resolved `project-governance` service can add `Project Stage`,
  `Development Stance`, `Versioning Mode`, `Project Codename`, and
  `Build Identity` to opted-in managed docs; changelog helper logic resolves
  active release headings from the same service so
  intentionally unversioned repos can use `## Unreleased`
- fail with explicit retry instructions (run `devcovenant test`, then rerun
  `devcovenant gate --start`) when recovery/reconcile requires fresh test
  evidence; start gate performs no internal test runs

`gate --mid` responsibilities:
- require an active open gate session (`gate --start` already completed)
- run managed-environment `command` stage preparation when policy is enabled
- run pre-commit hooks with the same gate-owned refresh/autofix orchestration
  used by lifecycle gate phases
- surface blocking, non-autofixed DevCovenant violations with explicit
  `gate --mid` retry guidance before tests
- remain non-lifecycle: do not record start/end timestamps or change gate
  session state in `gate_status.json`

`test` responsibilities:
- run managed-environment `test` commands when policy is enabled
- execute Python-launcher commands with the resolved managed interpreter
- resolve canonical command metadata from `required_commands`
- consume typed-empty metadata values directly; no sentinel pseudo-empty token
  path is part of active runtime behavior
- execute commands in declared order without hidden alternate command
  injection
- record execution timestamp and command chain in gate status
- record tests mode and selected command-metadata key in gate status
- record normalized schema-version `1.0` test events and the last test
  snapshot in `devcovenant/registry/runtime/session_snapshot.json`
- keep `gate_status.json` concise by storing `test_events_count` there
  instead of the full event payload list
- emit adapter-load warnings through output runtime before running commands
- command runtime actions (for example `update_lock`) dispatch through policy
  contracts using `PolicyCheck.run_runtime_action(...)`

`gate --end` responsibilities:
- run managed-environment `end` commands when policy is enabled
- run pre-commit hooks
- fail fast with explicit fix-and-rerun guidance when pre-commit reports
  blocking, non-autofixed DevCovenant violations
- fail with explicit retry instructions when hooks mutate files or tests are
  stale for the current tree (`devcovenant test`, then
  `devcovenant gate --end`)
- record session closure only after successful checks, with the end snapshot
  stored in `devcovenant/registry/runtime/session_snapshot.json`

Install/upgrade boundary:
- `upgrade` normalizes and reports DevCovenant package-version
  comparison before copying the new core into place; this comparison is
  about DevCovenant's own release version, not the governed repo version
  scheme
- `install` is a cold bootstrap command and does not preserve existing
  managed runtime state
- `install` may record compatible pre-authored managed docs
  (`SPEC.md`, `README.md`, `PLAN.md`, and peers) so the first
  `refresh`/`deploy` adopts their authored content while updating generated
  headers and managed blocks to the active runtime
- that adoption and preservation contract is now owned by the shared
  managed-doc runtime service instead of being split between separate
  install-time and refresh-time document helpers
- `install` seeds user-repo defaults, including `developer_mode: false` and
  `install.config_reviewed: false`, so bootstrap starts in normal user scope
  with deploy still blocked pending explicit config review
- `deploy` requires `install.config_reviewed: true` before it activates
  managed docs, registries, and other generated artifacts
- think of that first install/deploy boundary like this:
  - `install` is setup
  - config review is the human decision point
  - `deploy` is activation
  - the first start -> mid -> test -> end cycle is the proof that activation
    succeeded
- managed-doc selection now comes from `doc_assets.autogen` plus descriptor
  lookup from the global managed-doc assets and any active profile asset
  roots:
  keep `AGENTS.md`, remove builtin docs there to turn them off for one repo,
  and add custom docs there only after creating matching descriptors
- in this repository, `README.md` is the authored source and
  `devcovenant/README.md` is the synced packaged projection with repo-only
  sections stripped by `readme-sync`
- document preservation rules are exact:
  - missing docs may be created from assets/templates
  - empty docs may be replaced fully
  - one-line docs may be replaced fully
  - otherwise only managed header lines and explicit `<!-- DEVCOV* -->`
    blocks may change
- install/deploy bootstrap cases therefore work like this:
  - empty repo: deploy creates the managed baseline
  - seeded DevCovenant-shaped docs: deploy adopts and upgrades them
  - existing repo with ordinary docs/files: deploy preserves real authored
    content and adds managed regions around it
- `install` exits and points to `upgrade` when DevCovenant is already present
- source-checkout `install` copies tracked package skeletons only; it skips
  source runtime logs, source runtime registry files, and tracked
  `registry.yaml` output before seeding a fresh tracked registry in the
  target repo
- `clean` resolves active-profile `clean_overlays` plus repo
  `clean.overlays`/`clean.overrides`, requires an explicit `--all`,
  `--build`, `--cache`, `--registry`, or `--logs` scope, writes cleanup
  details into `summary.txt`/`summary.json`, and keeps tracked files such as
  `.git`, `.venv`, `devcovenant/registry/registry.yaml`,
  `devcovenant/registry/README.md`, and `devcovenant/logs/README.md`
- `upgrade` preserves runtime-local `devcovenant/registry/runtime/` and
  `devcovenant/logs/`, plus repository `devcovenant/config.yaml`, during
  core replacement before running refresh
- `refresh` and `upgrade` recreate missing tracked
  `devcovenant/registry/registry.yaml` explicitly, but they do not fabricate
  runtime registry session files when those are absent
- refresh keeps the generated local `devcovenant` pre-commit hook explicit in
  `.pre-commit-config.yaml`; when fragments omit it, refresh injects the
  default local hook payload instead of treating it as compatibility state
- refresh renders the compact managed header set for ordinary docs and can
  add project-governance header lines to any opted-in managed doc when the
  descriptor requests them
- AGENTS remains the one explicit special-case doc: refresh also renders its
  dedicated managed `Project Governance` section after the workflow block so
  agents can read the resolved repo lifecycle state directly before the
  generated policy block
- refresh writes final per-policy metadata snapshots to
  `devcovenant/registry/registry.yaml` and now also records per-key
  `metadata_resolution` trace plus `metadata_warnings` for destructive
  override replacement, so workflow debugging can start from registry
  evidence instead of ad-hoc guesswork
- the same registry also records `runtime_metadata_options`,
  `runtime_config_overrides`, and `runtime_effective_options` so policy
  option debugging can use the exact typed runtime surface rather than only
  the raw string-map metadata block
- `upgrade` preserves user payload trees under
  `devcovenant/custom/policies/<policy-id>/` and
  `devcovenant/custom/profiles/<profile-id>/`
- `upgrade` prunes known repo-only custom payload paths leaked by older
  installs (`devcov_raw_string_escapes`, `managed_doc_assets`,
  `readme_sync`, and repository-only custom profiles) before refresh
- `upgrade` and `refresh` may replace known old generic `PLAN.md` /
  `SPEC.md` scaffolds, but only by exact body fingerprint after generated
  headers and the first managed block are stripped from the comparison
- orphan custom policy scripts still fail with the same descriptor contract as
  core policies; fix the descriptor and rerun
- refresh validates managed-doc descriptor schema before rendering docs:
  descriptors must declare ordered keys
  (`title`, `target_path`, `doc_id`, `doc_type`, `project_version`,
  `last_updated`, `devcovenant_version`, optional managed-doc booleans,
  optional `legacy_generic_body_fingerprints`, `managed_block`, `body`,
  optional `workflow_block`);
  multiline `managed_block`/`body`/`workflow_block` fields must use
  YAML (YAML Ain't Markup Language) literal block style (`|`/`|-`) for
  stable markdown output
- refresh preserves user carve-outs wrapped in
  `DEVCOV-USER-PRESERVE:BEGIN/END` anywhere in managed docs
- `upgrade` reconciles the full `devcovenant/` package from source on every
  run (including `devcovenant/*.py`, `core/`, and `builtin/`) regardless of
  version ordering

`gate --status` responsibilities:
- read gate session state without mutating lifecycle files
- report short session status and last known phase
- point to the latest relevant run-log artifacts for summary-first triage
- resolve status-line rendering and owned latest-run pointer artifacts through
  `devcovenant/core/flow/gate_status_helpers.py` so read-only status behavior
  remains isolated from lifecycle writes
- align CLI help wording with the same contract
  (`devcovenant check --help` = audit-only,
  `devcovenant gate --help` = lifecycle phases + `gate --mid` +
  short read-only `gate --status`)
- support inspection-first recovery loops without rerunning gate commands
  just to read lifecycle state
- keep audit-only no-change `devcovenant check` runs non-blocking for stale
  end-vs-test ordering in closed sessions with no post-end edits
- discover policy scripts from `devcovenant/builtin/policies` and
  `devcovenant/custom/policies` only
- keep profile discovery and merge inventory resolved from
  `devcovenant/core/services/profile_registry.py`

Output behavior:
- `engine.output_mode: verbose` prints detailed stage/step messages
- `engine.output_mode: normal` uses concise runtime command output
- `engine.output_mode: quiet` suppresses routine stdout output and keeps
  errors/violations on stderr
- runtime console messages are line-flushed by default so status/progress
  lines remain visible during long-running commands instead of appearing only
  at process exit
- `engine.tests_output_mode` controls `devcovenant test` console-detail and
  child-output suppression behavior
- `devcovenant/core/runtime/run_logging.py` provides a shared per-run logging
  substrate for command-run artifact folders under `devcovenant/logs/`;
  CLI dispatch now allocates/finalizes top-level run folders and emits a
  deterministic standard `Run logs:` pointer on success and failure paths,
  except for `uninstall`, which removes `devcovenant/` and therefore cannot
  leave a durable run-log folder
- `devcovenant/core/flow/clean.py` now refuses to run while
  `devcovenant/registry/runtime/gate_status.json` records an open session,
  keeping cleanup commands outside live gate ownership; build cleanup also
  prunes repo-root unpacked release trees named like
  `<project>-<version>/` for the repo or manifest project name
- CLI unhandled exceptions are normalized to explicit typed errors through
  `devcovenant/core/runtime/errors.py` and
  `devcovenant/core/contracts/errors.py`; console output stays explicit while
  full traceback detail remains in run-log artifacts
- broad exception handlers at intentional process/plugin boundaries must be
  explicitly marked (`DEVCOV_ALLOW_BROAD_ONCE` or configured waiver
  regions) to satisfy `no-raw-errors` governance
- operators should treat the printed `Run logs:` path as the canonical
  debug entrypoint for command-run evidence artifacts
- `engine.logs_keep_last` controls how many recent run-log folders remain in
  `devcovenant/logs/` after each command (`0` keeps all); logging itself is
  not a disableable runtime feature
- artifact-first triage order for run evidence artifacts is: `summary.txt`,
  then `tail.txt` (if
  present), then full logs (`stderr.log`/`stdout.log`)
- when run artifacts are available, prefer status updates and final
  results over verbose live-streaming, and use summaries/tails first for
  failure triage
- prefer low-frequency polling for long-running commands instead of tight
  polling loops
- use the documented polling cadence internally, but do not narrate
  polling steps/cadence in routine progress updates unless asked
- avoid ad-hoc output redirects for DevCovenant commands when official
  run artifacts already exist
- the logging substrate preserves artifact fidelity independently of console
  verbosity choices
- `check` is read-only by default; gate pre-commit phases own refresh/autofix
  orchestration for the shared checking routine
- read-only `check` remains usable before the first gate session:
  when gate status is missing and no session-scoped changes are present,
  session-only checks stay non-blocking
- gate session lifecycle evidence is stored in the concise ledger
  `devcovenant/registry/runtime/gate_status.json`
- heavy session baseline/snapshot evidence is stored in
  `devcovenant/registry/runtime/session_snapshot.json`
- command-run evidence is stored in
  `devcovenant/logs/<run-id>-<command>/`
- gate-managed autofix requests honor `engine.auto_fix_enabled` from
  `devcovenant/config.yaml` (disabled globally by default)
- runtime subprocess helpers for explicit `test` runs and gate-managed
  subprocess execution capture full command output into run artifacts while
  console verbosity remains a separate concern
- runtime subprocess helpers emit `Please wait. In progress...` during long
  silent waits in normal mode while preserving existing phase/start lines
  and use sub-second heartbeat polling so short silent commands still emit
  deterministic liveness updates when heartbeat output is configured
- refresh-owned `devcovenant/config.yaml` guidance comments (for example
  `fail_threshold` and `auto_fix_enabled`) are emitted from refresh runtime
  source logic, not hand-maintained in repo-local generated config files
- `engine.tests_output_mode: normal` keeps status lines concise while
  suppressing test command child output, emits deterministic
  start/failure markers (for example `▶ [n/total] <command>` and
  `[n/total] FAILED: <command> (exit n)`), and still writes full output
  to run-log artifacts
- `engine.tests_output_mode: quiet` suppresses routine test stdout chatter
  and child output while preserving stderr failures/violations and full
  run-log artifacts
- `devcovenant test` writes informational profiling artifacts per run
  (`test_profile.json` and `test_profile.txt`) with module/group and slowest-
  command duration breakdowns for the resolved command chain
- test-run summary metadata now includes stable command-duration fields
  (`duration_seconds_min_command`, `duration_seconds_avg_command`,
  `duration_seconds_max_command`, `duration_events_count`) for trend tracking
- gate commands never run tests internally (including recovery/reconcile
  paths); they fail with explicit `devcovenant test` retry instructions
- normal mode streams gate pre-commit hook output, suppresses
  flood-prone managed/test child channels, and preserves deterministic
  liveness heartbeats plus bounded failure tails when suppression applies
- quiet mode suppresses routine stdout child output across channels and keeps
  error/violation surfaces on stderr; verbose mode keeps full child streaming
- progress-bar rendering is removed from the DevCovenant runtime; normal
  mode no longer emits redraw noise in terminals or CI logs
- normal-mode live streaming can be acceptable when it stays concise, but
  verbose streaming can consume significant tokens
- runtime console-emitting subprocesses use
  PTY (pseudoterminal)-backed streaming on
  POSIX (Portable Operating System Interface) systems by default so hook/test
  output flushes live without process-end buffering; pipe streaming becomes
  the alternate transport when PTY is unavailable or when normal-mode
  suppression hides child output
- gate/test/managed child commands route through one runtime helper
  (`run_child_command_with_output_policy`) with channel plans resolved by
  `resolve_child_output_plan_for_channel`; this keeps mode behavior aligned
  across all command families
- prefer run artifacts and summaries/tails before switching to verbose
  streaming or ad-hoc redirects
- keep operator progress updates concise: report what changed, what
  passed/failed, and the next step; avoid narrating routine waits or
  polling steps/cadence or obvious command progress
- normal-mode live streaming is acceptable for routine progress visibility;
  reserve verbose streaming for explicit request, missing run artifacts, or
  interactive I/O needs
- recommended polling cadence for long-running commands is:
  `5s`, `15s`, `30s`, `45s`, `60s`, `90s`, `120s`, `150s`, `180s`, `240s`,
  then every `60s`
- `engine.pycache_prefix_enabled: true` routes Python bytecode caches via
  `PYTHONPYCACHEPREFIX` for DevCovenant-managed child commands, preserving
  bytecode generation fidelity while avoiding repo-local `__pycache__/` drift
- generated CI governance workflows still set `PYTHONPYCACHEPREFIX` at job
  scope for managed child commands and stable CI behavior
- source-checkout top-level `python -m devcovenant ...` launches keep the
  repo clean by suppressing later cache-file writes and removing the
  package-import cache Python may emit before CLI startup
- gate-session changelog coverage uses a gate-start exemption baseline that
  includes DEVCOV-managed blocks in non-doc text files (for example generated
  YAML/YML assets), so managed-only regen noise does not require new
  changelog entries
- the shared exemption fingerprint implementation now lives in
  `devcovenant/core/lib/document_exemptions.py`, and both gate-session
  baseline capture and changelog-coverage checks call that same helper path
  to reduce drift risk

Managed-environment scope split:
- core/global defaults keep `managed-environment` disabled.
- each repository opts in by setting
  `devcovenant/config.yaml -> policy_state.managed-environment: true`.
  Critical-severity policy disable attempts are still ignored by runtime,
  with explicit diagnostics, even though `policy_state` remains the config
  control surface.
- when enabled, any DevCovenant CLI command re-execs under the managed
  interpreter automatically when invoked from a different interpreter, except
  lifecycle bootstrap/teardown commands (`install`, `deploy`, `undeploy`,
  `uninstall`).
- non-executable managed interpreter paths emit an explicit
  managed-environment error and stop execution so the interpreter contract
  can be fixed directly.
- stage command prefixes are `start`, `test`, `end`, `command`, and `all`.
- if non-start commands run before interpreter creation, runtime executes
  explicit `start=>...` bootstrap commands once before failing.
- managed-environment stage bootstrap progress is tracked in
  `DEVCOV_MANAGED_STAGE_RUNS` so stage commands are not repeated after CLI
  re-exec into the managed interpreter.
- managed-environment stage bootstrap/output commands honor runtime output
  mode: normal mode suppresses bootstrap command bursts, quiet mode keeps
  routine stdout hidden, and verbose mode streams full child output.
- scope exclusions: when `developer_mode` is false, normal repos ignore
  `profiles.generated.devcov_core_paths`, which represent DevCovenant's own
  source/runtime paths rather than the user's project files.
- managed-environment guidance expands tokenized manual commands with
  resolved paths; missing values render explicit placeholders like
  `<managed_python>`.

## Session State Model
Session metadata is persisted in:
- `devcovenant/registry/runtime/gate_status.json` for concise lifecycle
  state and companion-pointer metadata
- `devcovenant/registry/runtime/session_snapshot.json` for bulky baseline,
  snapshot, and test-event payloads

Conceptual state machine:
1. `closed` (or absent) -> run `gate --start` -> `open`
2. `open` -> run `test` as needed during the slice
3. `open` -> successful `gate --end` -> `closed`

Important rules:
- a new start is rejected while a session is `open`
- end requires an active open session
- `gate --status` is read-only and does not change session state
- failed end does not mark session closed
- baseline/session keys must be valid for session-aware checks
- start records AGENTS section hashes:
  `agents_full_sha256`, `agents_workflow_sha256`,
  `agents_non_workflow_sha256`

Session scope behavior:
- policy checks use gate-session delta
- during normal start, delta is empty after baseline capture
- during recovery start, reconciled unsessioned edits are included in scope
- config `ignore.patterns` are applied before unsessioned/session checks

## Recovery and Reconcile
Start gate includes guardrails against silent baseline resets.

When start detects unsessioned edits after the previous closed session:
1. it opens a recovery session
2. it runs pre-commit against that unsessioned delta
3. it fails with explicit instructions to run `devcovenant test` and rerun
   `devcovenant gate --start` (no internal test execution)
4. it records a fresh baseline only after a later explicit retry succeeds when
   test evidence was stale or missing
5. if explicit test evidence is already fresh for the current unsessioned
   edits, the retry can succeed without another redundant test run

When start detects malformed/invalid status payload:
- it opens recovery behavior from current baseline rather than silently
  discarding state

This behavior protects changelog/session checks from hidden drift.

## Changelog and Delta Scope Rules
`changelog-coverage` is session-aware:
- it compares current top entry fingerprint against start fingerprint
- each change slice needs a fresh top changelog entry
- validations are scoped to files changed in the active session delta
- default config excludes `devcovenant/config.yaml` from this scope

Session baseline keys:
- `session_start_snapshot`:
  normal session baseline snapshot in `session_snapshot.json`
- `session_baseline_snapshot`:
  optional recovery baseline snapshot in `session_snapshot.json` that
  includes unsessioned edits
- `session_end_snapshot`:
  closed-session snapshot in `session_snapshot.json` used for
  unsessioned-edit detection
- `last_run_snapshot`:
  explicit test snapshot in `session_snapshot.json` used for end-gate
  freshness checks
- `document_exemption_baseline`:
  changelog-exemption baseline in `session_snapshot.json`
- `session_snapshot_file`:
  repo-relative companion pointer recorded in `gate_status.json`
- older gate snapshot row formats are not migration-bridged; if they are
  encountered, DevCovenant fails explicitly and requires a fresh
  `devcovenant gate --start`

Policy scope contract:
- missing or invalid session metadata outside start phase is an explicit error
- gate-aware checks read session ledger state directly
- session delta is computed from runtime snapshot helpers, not ad-hoc git
  commands
- deleted-file coverage is scoped to the active session via the
  `session_start_snapshot` gate-start baseline in `session_snapshot.json`,
  so older staged deletions do not leak into new slices
- normal `gate --start` validates an empty session delta and does not import
  HEAD-wide deleted paths from prior slices
- runtime snapshot/session helper ownership now lives in
  `devcovenant/core/runtime/session_snapshot.py`, while
  `devcovenant/core/runtime/execution.py` is the layered command-facing
  execution module
- `devcovenant/core/flow/session.py` keeps the session-helper surface
  explicit and auditable for flow-layer callers
- AGENTS policy-block rendering is isolated in
  `devcovenant/core/services/policy_block_refresh.py`, and AGENTS policy
  parser/model helpers are isolated in
  `devcovenant/core/services/policy_parse.py`

Test-policy alignment rules:
- `modules-need-tests` enforces source-to-test structural alignment
- `tests-coverage` enforces assertion signal quality
- tautological assertions do not count unless fixture-marked with
  `DEVCOV_FIXTURE_OK: <reason>`

## CI (continuous integration) Mapping
Primary governance workflow:
- `.github/workflows/governance-and-test.yml`
- generated by refresh from template + profile/config overlays
- tracked in this repository as refresh output; change inputs, then refresh
- installs CI tooling from `requirements.lock` to keep versions reproducible
- runs start -> test -> end sequence
- normalizes trigger rendering to canonical GitHub syntax:
  `on:`, `push:`, and `pull_request:` (no quoted `on` / `null` trigger values)
- sets `PYTHONPYCACHEPREFIX` in job env to `.gha-pycache` so CI bytecode
  artifacts stay out of source trees

Repository-maintained workflows (not refresh-generated):
- `build.yml`:
  build validation after successful governance workflow completion, including
  pre-build artifact cleanup plus isolated wheel + sdist install smoke
  (`python -m devcovenant --help`)
- `publish.yml`:
  manual release workflow (`workflow_dispatch`) with the same cleanup and
  wheel + sdist install smoke in its build job before upload/publish

Use local gates to match CI expectations and reduce late failures.

## Operator Checklist
Before edits:
1. read `AGENTS.md` and active policies
2. run `devcovenant gate --start`

During edits:
1. keep changelog and docs aligned with behavior changes
2. clear complaints before continuing

After edits:
1. run `devcovenant test`
2. run `devcovenant gate --end`
3. if end gate reports hook-induced changes or stale tests, rerun
   `devcovenant test` and then `devcovenant gate --end` until clean
4. stage all changed files for the completed slice
