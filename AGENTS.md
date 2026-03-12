# DevCovenant Development Guide
**Doc ID:** AGENTS
**Doc Type:** policy-source
**Project Version:** 1.0.0
**Last Updated:** 2026-03-09
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
# Message from DevCovenant's Human (Read First)

This document is the canonical law of this repository for both humans and AI.
If you do not follow it, commits will fail, development quality will drift, and
the project in this repository will be compromised.

Read this entire file end-to-end before doing any work: this managed message,
the editable section, the workflow block, and the active policies.

Follow the required gate workflow. If you read this document carefully, you
will get to know everything about it.

Build an active-policy mental model from policies marked `enabled: true` and
follow those policies proactively while writing, not after violations appear.

Use the editable section as a live repo-specific notepad. Keep notes short,
factual, and current so they do not grow beards. When decisions change, update
notes in the same session. When operational behavior changes, update notes so
future sessions do not run on stale assumptions. Treat stale notes as drift and
clear them.

Never edit content inside managed `<!-- DEVCOV* -->` blocks in any file.
Read `README.md` for project context and `devcovenant/README.md` for lifecycle
and command behavior.
<!-- DEVCOV:END -->

# EDITABLE SECTION

## Editable-Section Hygiene
- Keep this section focused on repo-specific direction and constraints.
- Do not restate standard workflow steps that are already defined elsewhere.
- Update notes in the same session when decisions change.
- Remove stale notes immediately; stale notes are drift.

## Public Baseline Notes
- This repository now treats `1.0.0` as the public baseline.
- Preserve command/runtime contracts unless an explicit plan item changes them.
- Keep implementation ownership layered under
  `devcovenant/core/{flow,runtime,services,lib,contracts}`.
- Keep product-operation docs in `devcovenant/docs/*` and keep repo-internal
  release notes out of package docs.

## Release Control Notes
- Human-controlled release operations remain manual.
- Destructive history operations require explicit human direction.
- Keep CI/governance checks green before publish decisions.

## Hygiene Rules
- Keep this section short, factual, and current.
- Remove stale temporary notes in the same session.
- Prefer explicit failures over silent fallbacks.

<!-- DEVCOV-WORKFLOW:BEGIN -->

## Workflow Contract
This block defines the mandatory execution contract for repository work.
Use it as the operational checklist for every session.

## Table of Contents
1. [Overview](#overview)
2. [The Dev Covenant](#the-dev-covenant)
3. [Workflow](#workflow)
4. [Execution Order (Mandatory)](#execution-order-mandatory)
5. [Managed Environment](#managed-environment)
6. [Command Form](#command-form)
7. [Policy Block Contract](#policy-block-contract)

## Overview
DevCovenant converts policy prose into executable checks. This file is the
canonical policy source and operational guide for the repository.

## THE DEV COVENANT
- We are human and AI developers working on this project together.
- We obey every AGENTS.md and DevCovenant instruction.
- We maintain clean repository hygiene and avoid unmanaged drift.
- We never edit content inside managed `<!-- DEVCOV* -->` blocks.

## Workflow
Use the mandatory execution order below for all repository changes,
including documentation-only edits.
Treat DevCovenant run artifacts as the primary debug surface for command
results. Prefer summary/tail/log inspection first. Normal-mode live
streaming is acceptable when concise, but verbose streaming can consume
significant tokens. Keep operator progress updates concise: report what
changed, what passed/failed, and the next step; avoid routine narration
during command waits.

## Execution Order (Mandatory)
1. On the first session in a new conversation, read the entire `AGENTS.md`
   before running work commands, including policy metadata and policy text.
2. On every session, reread this workflow block
   (`<!-- DEVCOV-WORKFLOW:* -->`) before any repository edits.
3. If `AGENTS.md` non-workflow content changed since the previous gate
   session, reread the entire `AGENTS.md` before work commands.
4. Build an active-policy mental model from policies marked `enabled: true`
   and follow those policies proactively while writing.
5. If a managed environment is configured, activate/use it first. Run
   DevCovenant commands and tests in that environment. Installing
   DevCovenant in that environment is recommended.
6. Run `devcovenant gate --start` before any repository edits. For
   long-running commands, use non-PTY execution for non-interactive
   DevCovenant commands, prefer low-frequency polling, and avoid verbose
   or large-output streaming by default.
   Polling cadence for long waits: 5s, 15s, 30s, 45s, 60s, 90s, 120s,
   150s, 180s, 240s, then every 60s.
   Do not narrate polling steps or cadence in routine progress updates
   unless the human explicitly asks.
7. Before applying edits, clear start-gate complaints. Blocking violations
   must be cleared; preferred behavior is to clear all complaints. When
   DevCovenant run artifacts are available, inspect summaries/tails/logs
   before rerunning commands.
8. Apply edits while following policy text and metadata proactively.
9. If any DevCovenant complaint appears (error, warning, or info), stop
   the requested task and clear blocking violations first. Use the latest
   `Run logs:` path and summary artifacts as the primary debug
   entrypoint.
10. Preferred behavior: clear all DevCovenant complaints before continuing,
   unless the human explicitly requests otherwise.
11. Run `devcovenant gate --mid` before tests to surface hook-induced
   mutations and blocking DevCovenant complaints early. `gate --mid`
   requires an open session, does not record lifecycle state, and may
   need an explicit rerun until hooks converge.
12. Run `devcovenant test`. For long runs, report status/phase updates
   and final result, and prefer run-artifact summaries/tails before
   escalating to verbose streaming. Long silent waits in normal mode
   should surface `Please wait. In progress...`.
13. Run `devcovenant gate --end`. Use the same artifact-first output
   discipline as test runs. Gate commands do not run tests internally.
14. If end-gate hooks or checks produce additional changes or violations,
   use `devcovenant gate --status` for lifecycle inspection and inspect
   the latest run artifacts before rerunning required commands until the
   repository is clean. When gates require tests, run `devcovenant test`
   explicitly and rerun the gate command.
15. Stage all changes after each completed work slice.

Audits are not a separate workflow mode. The same gate discipline applies.
Use `check` as the default read-only audit command. Gate commands own
refresh/autofix orchestration; lifecycle state writes are limited to
`gate --start` / `gate --end`; `gate --mid` is non-lifecycle.
Gate commands never run tests internally.
When DevCovenant run artifacts are available, inspect `summary.txt`,
then `tail.txt` (if present), then full logs before using ad-hoc
redirects or verbose streaming. Normal-mode live streaming can be
acceptable when it stays concise, but verbose streaming can consume many
tokens. Prefer normal-mode streaming plus artifact-first inspection for
routine work. Reserve verbose streaming for explicit human request, no
DevCovenant run artifacts, or interactive I/O needs. Keep operator
updates concise (what changed, what passed/failed, next step) instead of
narrating routine waits, polling steps, or obvious command progress.

## Managed Environment
If a managed environment is configured, run DevCovenant from that
environment and run all tests there as well.
Start required services before the test gate so runtime checks execute
against the active stack.

## Command Form
Primary command examples use on-PATH `devcovenant ...`.
If the CLI is unavailable from source checkout, use
`python3 -m devcovenant ...`.
On Windows, `py -m devcovenant ...` is a common equivalent launcher form.

## Policy Block Contract
The policy block below is generated by DevCovenant from policy descriptors
and runtime metadata resolution. Treat it as managed and do not edit it
directly.
<!-- DEVCOV-WORKFLOW:END -->

<!-- DEVCOV-POLICIES:BEGIN -->
## Policy: Changelog Coverage

```policy-def
id: changelog-coverage
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: false
main_changelog: CHANGELOG.md
skipped_files: devcovenant/config.yaml
  CHANGELOG.md
  .gitignore
  .pre-commit-config.yaml
  .github/workflows/governance-and-test.yml
skipped_globs:
skipped_prefixes:
summary_labels: Change
  Why
  Impact
summary_verbs: add
  added
  address
  addressed
  adjust
  adjusted
  align
  aligned
  amend
  amended
  automate
  automated
  bootstrap
  build
  built
  bump
  bumped
  cache
  clean
  cleaned
  clarify
  clarified
  consolidate
  consolidated
  configure
  correct
  corrected
  create
  created
  define
  defined
  deserialize
  deprecate
  deprecated
  detect
  document
  documented
  drop
  dropped
  enable
  enabled
  enforce
  enforced
  expand
  expanded
  extract
  fix
  fixed
  harden
  hardened
  implement
  improve
  improved
  instrument
  integrate
  introduce
  introduced
  invalidate
  lock
  materialize
  merge
  migrate
  migrated
  normalize
  normalized
  optimize
  pin
  preserve
  prevent
  profile
  publish
  reconcile
  regenerate
  refactor
  refactored
  release
  remove
  removed
  rename
  renamed
  replace
  replaced
  resolve
  restructure
  restructured
  revert
  revise
  revised
  sanitize
  scaffold
  serialize
  simplify
  simplified
  split
  stabilize
  stabilized
  streamline
  streamlined
  support
  supported
  sync
  tune
  unpin
  update
  updated
  upgrade
  upgraded
  validate
  validated
  verify
  verified
  wrap
  wrapped
  allow
  allowed
  analyze
  analyzed
  annotate
  annotated
  assess
  assessed
  audit
  audited
  calculate
  calculated
  check
  checked
  choose
  chosen
  close
  closed
  collect
  collected
  compare
  compared
  complete
  completed
  compose
  composed
  constrain
  constrained
  convert
  converted
  copy
  copied
  cover
  covered
  delete
  deleted
  derive
  derived
  describe
  described
  design
  designed
  diagnose
  diagnosed
  disable
  disabled
  ensure
  ensured
  estimate
  estimated
  evaluate
  evaluated
  execute
  executed
  explain
  explained
  expose
  exposed
  finalize
  finalized
  make
  made
  map
  mapped
  mark
  marked
  measure
  measured
  organize
  organized
  prioritize
  prioritized
  promote
  promoted
  prune
  pruned
  prove
  proved
  record
  recorded
  reduce
  reduced
  reject
  rejected
  repair
  repaired
  report
  reported
  reset
  restore
  restored
  retain
  retained
  review
  reviewed
  rewrite
  rewrote
  select
  selected
  sequence
  sequenced
  show
  showed
  sort
  sorted
  stage
  staged
  standardize
  standardized
  strengthen
  strengthened
  suppress
  suppressed
  test
  tested
gate_status_file: devcovenant/registry/local/gate_status.json
collections:
header_doc_suffixes: .md
  .rst
  .txt
header_keys: Last Updated
  Project Version
  DevCovenant Version
header_scan_lines: 4
required_globs: README.md
  AGENTS.md
  CONTRIBUTING.md
  CHANGELOG.md
  SPEC.md
  PLAN.md
selector_roles: skipped
  header_doc
  required
skipped_dirs:
header_doc_globs: *.md
  *.rst
  *.txt
header_doc_files:
header_doc_dirs:
required_files:
required_dirs:
```

Every change must be logged in a new changelog entry dated today, under the
current version, with a three-line summary labeled Change/Why/Impact. Each
summary line must include an action verb listed in the summary_verbs
metadata and a Files block that lists only the touched paths for this
change. The policy compares the top changelog entry against the gate-start
top-entry fingerprint to require a fresh entry for each work session, while
resolving changed paths from the active gate session. Collection prefixes
(when enabled) must be logged in their own changelog; prefixed files may not
appear in the root changelog. This keeps release notes daily, file-complete,
and traceable.


---

## Policy: Dependency License Sync

```policy-def
id: dependency-license-sync
severity: error
auto_fix: true
enforcement: active
enabled: true
custom: false
dependency_files:
dependency_globs:
dependency_dirs:
dependency_roles: intent
  resolved
  package_manifest
dependency_role_files: intent=>requirements.in
  resolved=>requirements.lock
  package_manifest=>pyproject.toml
dependency_role_globs:
dependency_role_dirs:
third_party_file: licenses/THIRD_PARTY_LICENSES.md
licenses_dir: licenses
report_heading: ## License Report
selector_roles: dependency
```

Maintain third-party license artifacts alongside dependency changes.
This policy governs repository dependency compliance only: when dependency
inputs in this repository change, repository license artifacts must be kept
synchronized. It does not, by itself, define or guarantee package-
distribution legal compliance for sdists/wheels/binaries.
Dependency input modeling supports role-based taxonomy for mixed ecosystems:
`intent`, `resolved`, and `package_manifest`.
Role selectors are metadata-driven via
(`dependency_role_files`, `dependency_role_globs`,
`dependency_role_dirs`) using `role=>selector` tokens.
Dependency selectors are metadata-driven
(`dependency_files`, `dependency_globs`, `dependency_dirs`) and may include
both manifest files and lock/resolution files so mixed-language repositories
can define their own layout. Every dependency change must keep the
configured report file (`third_party_file`) and configured license directory
(`licenses_dir`) synchronized, including the configured `report_heading`.
Autofix is restricted to those configured artifacts and must remain
deterministic/idempotent.


---

## Policy: Devcov Integrity Guard

```policy-def
id: devcov-integrity-guard
severity: critical
auto_fix: false
enforcement: active
enabled: true
custom: false
policy_definitions: AGENTS.md
registry_file: devcovenant/registry/local/policy_registry.yaml
gate_status_file: devcovenant/registry/local/gate_status.json
watch_dirs:
watch_files:
selector_roles: watch
  watch_files
watch_globs:
watch_files_globs:
watch_files_files:
watch_files_dirs:
```

Enforce DevCovenant policy integrity: every policy must include descriptive
text, AGENTS prose must match policy descriptors, the policy registry must
stay synchronized, and gate-status metadata must validate when configured.


---

## Policy: Devcov Raw String Escapes

```policy-def
id: devcov-raw-string-escapes
severity: warning
auto_fix: false
enforcement: active
enabled: true
custom: true
include_suffixes: .py
  .pyi
  .pyw
selector_roles: include
include_globs: *.py
  *.pyi
  *.pyw
include_files:
include_dirs:
```

Warn when DevCovenant repo Python strings contain bare backslashes.
This repo-only policy keeps the raw-string guidance active without
forcing it on user repos.


---

## Policy: Devcov Structure Guard

```policy-def
id: devcov-structure-guard
severity: critical
auto_fix: false
enforcement: active
enabled: true
custom: false
```

Ensure the DevCovenant repo keeps the required structure and tooling files.


---

## Policy: Devflow Run Gates

```policy-def
id: devflow-run-gates
severity: critical
auto_fix: false
enforcement: active
enabled: true
custom: false
gate_status_file: devcovenant/registry/local/gate_status.json
required_commands: python3 -m unittest discover -v
  pytest
require_pre_commit_start: true
require_pre_commit_end: true
pre_commit_command: python3 -m pre_commit run --all-files
pre_commit_start_epoch_key: pre_commit_start_epoch
pre_commit_end_epoch_key: pre_commit_end_epoch
pre_commit_start_command_key: pre_commit_start_command
pre_commit_end_command_key: pre_commit_end_command
code_extensions:
skipped_globs: devcovenant/registry/local/**
selector_roles: skipped
skipped_files:
skipped_dirs:
```

DevCovenant must record and enforce the standard workflow: pre-commit start,
tests, then pre-commit end. The policy reads the status file to ensure each
gate ran and that no required command was skipped.
This check is enforced for every repository change (including
documentation-only updates) so the gate sequence cannot be skipped.
Changelog-only edits remain gate-scoped but do not require a fresh test
rerun by themselves.


---

## Policy: Docstring And Comment Coverage

```policy-def
id: docstring-and-comment-coverage
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: false
include_suffixes: .py
exclude_prefixes: build
  dist
  node_modules
include_prefixes:
include_globs: *.py
exclude_suffixes:
exclude_globs: build/**
  dist/**
  node_modules/**
force_include_globs:
selector_roles: include
  exclude
  force_include
include_files:
include_dirs:
exclude_files:
exclude_dirs:
force_include_files:
force_include_dirs:
```

Source files must include a docstring or nearby explanatory comment so
intent stays visible even as code evolves. Adapters decide how each
language satisfies the requirement.


---

## Policy: Documentation Growth Tracking

```policy-def
id: documentation-growth-tracking
severity: warning
auto_fix: false
enforcement: active
enabled: true
custom: false
selector_roles: user_facing
  user_visible
  doc_quality
include_prefixes:
exclude_prefixes:
user_facing_prefixes:
user_facing_exclude_prefixes: tests
user_facing_suffixes: .py
  .js
  .ts
  .tsx
  .vue
  .go
  .rs
  .java
  .kt
  .swift
  .rb
  .php
  .cs
  .yml
  .yaml
  .json
  .toml
user_facing_files: .pre-commit-config.yaml
  pyproject.toml
  devcovenant/cli.py
  devcovenant/__main__.py
user_facing_globs: .github/workflows/*.yml
  .github/workflows/*.yaml
  *.py
  *.js
  *.ts
  *.tsx
  *.vue
  *.go
  *.rs
  *.java
  *.kt
  *.swift
  *.rb
  *.php
  *.cs
  *.yml
  *.yaml
  *.json
  *.toml
user_facing_keywords: api
  endpoint
  endpoints
  route
  routes
  routing
  service
  services
  controller
  controllers
  handler
  handlers
  client
  clients
  webhook
  webhooks
  integration
  integrations
  sdk
  cli
  ui
  view
  views
  page
  pages
  screen
  screens
  form
  forms
  workflow
  workflows
user_visible_files: README.md
  CONTRIBUTING.md
  AGENTS.md
  SPEC.md
  PLAN.md
  devcovenant/README.md
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/policies.md
  devcovenant/docs/translators.md
  devcovenant/docs/registry.md
  devcovenant/docs/refresh.md
  devcovenant/docs/workflow.md
  devcovenant/docs/troubleshooting.md
doc_quality_files: README.md
  CONTRIBUTING.md
  AGENTS.md
  SPEC.md
  PLAN.md
  devcovenant/README.md
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/policies.md
  devcovenant/docs/translators.md
  devcovenant/docs/registry.md
  devcovenant/docs/refresh.md
  devcovenant/docs/workflow.md
  devcovenant/docs/troubleshooting.md
required_headings: Table of Contents
  Overview
  Workflow
require_toc: true
min_section_count: 3
min_word_count: 120
doc_routes: devcovenant/builtin/policies/ => devcovenant/docs/policies.md
  devcovenant/builtin/policies/ => devcovenant/docs/architecture.md
  devcovenant/builtin/profiles/*/*.yaml => devcovenant/docs/profiles.md
  devcovenant/*/profiles/*/*translator.py=> devcovenant/docs/translators.md
  devcovenant/builtin/profiles/**/config.yaml => devcovenant/docs/config.md
  devcovenant/*/profiles/*/assets/*.yaml=> devcovenant/docs/profiles.md
  devcovenant/*/profiles/*/assets/*.yml=> devcovenant/docs/profiles.md
  devcovenant/*/profiles/**/assets/**/*.yaml=> devcovenant/docs/profiles.md
  devcovenant/*/profiles/**/assets/**/*.yml=> devcovenant/docs/profiles.md
  devcovenant/custom/profiles/__init__.py => devcovenant/docs/profiles.md
  devcovenant/custom/profiles/*.py => devcovenant/docs/profiles.md
  devcovenant/custom/profiles/**/*.py => devcovenant/docs/profiles.md
  devcovenant/custom/profiles/**/*.yaml => devcovenant/docs/profiles.md
  devcovenant/custom/policies/**/*.yaml => devcovenant/docs/policies.md
  devcovenant/custom/policies/**/*.py => devcovenant/docs/policies.md
  devcovenant/core/flow/*.py => devcovenant/docs/workflow.md
  devcovenant/core/flow/*.py => devcovenant/docs/architecture.md
  devcovenant/core/runtime/*.py => devcovenant/docs/workflow.md
  devcovenant/core/runtime/*.py => devcovenant/docs/architecture.md
  devcovenant/core/services/*.py => devcovenant/docs/architecture.md
  devcovenant/core/lib/*.py => devcovenant/docs/architecture.md
  devcovenant/core/contracts/*.py => devcovenant/docs/architecture.md
  devcovenant/*.py => devcovenant/docs/installation.md
  devcovenant/*.py => devcovenant/docs/workflow.md
  pyproject.toml => devcovenant/docs/installation.md
  MANIFEST.in => devcovenant/docs/installation.md
  devcovenant/config.yaml => devcovenant/docs/config.md
  .github/workflows/*.yml => devcovenant/docs/workflow.md
require_mentions: true
mention_min_length: 3
mention_stopwords: devcovenant
  tools
  common
  custom
  policy
  policies
  script
  scripts
  py
  js
  ts
  json
  yml
  yaml
  toml
  md
  readme
  plan
  spec
include_suffixes:
include_globs:
exclude_suffixes:
exclude_globs:
force_include_globs:
user_facing_exclude_globs: tests/**
user_facing_exclude_suffixes:
user_facing_dirs:
user_visible_globs:
user_visible_dirs: devcovenant/docs
doc_quality_globs:
doc_quality_dirs: devcovenant/docs
include_files:
include_dirs:
exclude_files:
exclude_dirs:
user_facing_exclude_files: devcovenant/config.yaml
user_facing_exclude_dirs: tests/**
force_include_files:
force_include_dirs:
```

When user-facing files change (as defined by the user-facing selectors and
keywords), the documentation set listed here must be updated. User-facing
includes API surfaces, integration touchpoints, and any behavior that affects
the user's experience or workflow. Updated docs should mention the relevant
components by name so readers can find changes quickly. The policy also
enforces documentation quality standards such as required headings, a table
of contents, and minimum depth. When `doc_routes` is configured, each
user-facing change must match at least one route and touch all mapped docs.


---

## Policy: Last Updated

```policy-def
id: last-updated
severity: error
auto_fix: true
enforcement: active
enabled: true
custom: false
include_suffixes: .md
allowed_globs: README.md
  AGENTS.md
  CONTRIBUTING.md
  CHANGELOG.md
  SPEC.md
  PLAN.md
  PROFILE_MAP.md
  POLICY_MAP.md
  devcovenant/README.md
  devcovenant/core/README.md
  devcovenant/custom/README.md
  devcovenant/registry/README.md
  devcovenant/builtin/policies/README.md
  devcovenant/builtin/profiles/README.md
  devcovenant/custom/policies/README.md
  devcovenant/custom/profiles/README.md
  devcovenant/docs/*.md
  devcovenant/docs/**/*.md
allowed_files:
allowed_suffixes:
required_files:
required_globs: README.md
  AGENTS.md
  CONTRIBUTING.md
  CHANGELOG.md
  SPEC.md
  PLAN.md
  PROFILE_MAP.md
  POLICY_MAP.md
  devcovenant/README.md
  devcovenant/core/README.md
  devcovenant/custom/README.md
  devcovenant/registry/README.md
  devcovenant/builtin/policies/README.md
  devcovenant/builtin/profiles/README.md
  devcovenant/custom/policies/README.md
  devcovenant/custom/profiles/README.md
  devcovenant/docs/*.md
  devcovenant/docs/**/*.md
selector_roles: include
  allowed
  required
include_globs: *.md
include_files:
include_dirs:
allowed_dirs:
required_dirs:
```

Docs must include a `Last Updated` header in the generated header zone so
readers can trust recency. The auto-fix updates UTC dates for touched
allowlisted docs while respecting allowlist selectors.


---

## Policy: Line Length Limit

```policy-def
id: line-length-limit
severity: warning
auto_fix: false
enforcement: active
enabled: true
custom: false
max_length: 79
allow_long_url_lines: True
url_prefixes: https://
  http://
  ftp://
  ftps://
  sftp://
  ssh://
  ws://
  wss://
  file://
  git://
  svn://
  mailto:
  tel:
  magnet:
  torrent:
  data:
  urn:
allow_long_lines: True
long_lines_contain:
long_lines_between:
include_suffixes: .py
  .md
  .rst
  .txt
  .yml
  .yaml
  .json
  .toml
  .cff
exclude_prefixes: build
  dist
  node_modules
exclude_globs: devcovenant/builtin/profiles/global/assets/*.yaml
  devcovenant/registry/**
  *.egg-info/**
  **/*.egg-info/**
  build/**
  dist/**
  node_modules/**
include_prefixes:
include_globs: *.py
  *.md
  *.rst
  *.txt
  *.yml
  *.yaml
  *.json
  *.toml
  *.cff
exclude_suffixes:
force_include_globs:
selector_roles: include
  exclude
  force_include
url_globs: https:/**
  http:/**
  ftp:/**
  ftps:/**
  sftp:/**
  ssh:/**
  ws:/**
  wss:/**
  file:/**
  git:/**
  svn:/**
  mailto:/**
  tel:/**
  magnet:/**
  torrent:/**
  data:/**
  urn:/**
url_files:
url_dirs:
include_files:
include_dirs:
exclude_files:
exclude_dirs:
force_include_files:
force_include_dirs:
```

Keep lines within the configured maximum so documentation and code remain
readable. Reflow long sentences or wrap lists rather than ignoring the limit.
Optional metadata escape hatches can allow long lines for URL-heavy content
or explicit marker patterns when repositories need targeted flexibility.


---

## Policy: Managed Doc Assets

```policy-def
id: managed-doc-assets
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: true
```

Ensure AGENTS.md, README.md, PLAN.md, SPEC.md, CHANGELOG.md, and
CONTRIBUTING.md remain the authoritative sources for their managed-block
descriptors under `devcovenant/builtin/profiles/global/assets/` so
documentation
generation is deterministic.


---

## Policy: Managed Environment

```policy-def
id: managed-environment
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: false
expected_paths: .venv
expected_interpreters: .venv/bin/python
  .venv/Scripts/python.exe
required_commands: python3
  pre-commit
  pytest
manual_commands: python3 -m venv .venv
  {managed_python} -m pip install -r requirements.lock
managed_commands: start=>python3 -m venv .venv
  start=>{managed_python} -m pip install -r requirements.lock
managed_rerun_commands:
```

DevCovenant must run from the managed environment described in this
policy's metadata. Use expected_paths for virtualenv or bench roots,
expected_interpreters for explicit interpreter locations, and
required_commands with `manual_commands`, stage-scoped
`managed_commands`, and stage-scoped `managed_rerun_commands` to define
guidance, runtime preparation, and wrapper rerun adapters.
Active managed-environment policy now also re-executes DevCovenant CLI
commands in the managed interpreter automatically when the current
interpreter does not match. Stage-scoped `managed_commands` accept
`start`, `test`, `end`, `command`, and `all` prefixes; non-start
commands reuse `start` bootstrap commands once when the interpreter is
still missing. `managed_rerun_commands` uses the same stage prefixes and
can rerun commands through wrapper environments (for example bench or
other adapters) when managed interpreters are not directly executable.
When enabled with empty metadata, the policy emits a warning so teams
fill the required context.


---

## Policy: Modules Need Tests

```policy-def
id: modules-need-tests
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: false
include_suffixes: .py
include_prefixes:
exclude_prefixes: build
  dist
  node_modules
  tests
exclude_globs: devcovenant/builtin/profiles/**/assets/**
  build/**
  dist/**
  node_modules/**
  tests/**
watch_dirs: tests
tests_watch_dirs: tests
mirror_roots: devcovenant=>tests/devcovenant
mirror_test_name_templates: python=>test_{stem}.py
  python=>{stem}_test.py
test_style_requirements: python=>python_unittest
include_globs: *.py
exclude_suffixes:
force_include_globs:
watch_files:
placeholder_test_methods: test_placeholder
placeholder_text_markers: placeholder-marker-alpha
  placeholder-marker-beta
  placeholder-marker-gamma
selector_roles: include
  exclude
  watch
  tests_watch
  force_include
include_files:
include_dirs:
exclude_files:
exclude_dirs:
watch_globs:
tests_watch_globs:
tests_watch_files:
force_include_files:
force_include_dirs:
```

In-scope non-test modules must have corresponding tests under configured
test roots. The rule is metadata-driven and supports mirror enforcement for
selected source roots. The policy enforces structural source-to-test
alignment and rejects stale mirrored tests. Placeholder tests are not
allowed. Python test files must use unittest.TestCase-style definitions;
pytest still runs as an execution layer.


---

## Policy: Name Clarity

```policy-def
id: name-clarity
severity: warning
auto_fix: false
enforcement: active
enabled: true
custom: false
exclude_prefixes: build
  dist
  node_modules
include_suffixes: .py
include_prefixes:
include_globs: *.py
exclude_suffixes:
exclude_globs: build/**
  dist/**
  node_modules/**
force_include_globs:
selector_roles: exclude
  include
  force_include
exclude_files:
exclude_dirs:
include_files:
include_dirs:
force_include_files:
force_include_dirs:
```

Identifiers should be descriptive enough to communicate intent without
reading their implementation. Avoid cryptic or overly short names unless
explicitly justified.


---

## Policy: No Future Dates

```policy-def
id: no-future-dates
severity: error
auto_fix: true
enforcement: active
enabled: true
custom: false
```

Dates in changelogs or documentation must not be in the future. Auto-fixers
should correct accidental placeholders to today’s date.


---

## Policy: No Print Outside Output Runtime

```policy-def
id: no-print-outside-output-runtime
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: false
selector_roles: include
  exclude
  force_include
allowed_file_files:
allowed_file_dirs:
include_suffixes: .py
include_prefixes:
include_globs: devcovenant/**/*.py
  *.py
exclude_suffixes:
exclude_prefixes:
exclude_globs: devcovenant/builtin/profiles/**/assets/**
  tests/**
force_include_globs:
include_files:
include_dirs:
exclude_files:
exclude_dirs:
force_include_files:
force_include_dirs:
sink_call_targets: python=>print
  python=>builtins.print
sink_attr_targets:
sink_macro_targets:
allowed_symbol_targets:
allowed_file_globs: devcovenant/core/runtime/execution.py
allow_waiver_comment: DEVCOV_ALLOW_OUTPUT:
```

Enforce metadata-driven direct-output sink boundaries across configured
languages. Language sink definitions come from profile overlays, while
repository profiles define in-scope selectors and boundary allowlists.


---

## Policy: No Raw Errors

```policy-def
id: no-raw-errors
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: false
selector_roles: include
  exclude
  force_include
include_suffixes: .py
include_prefixes:
include_globs: *.py
exclude_suffixes:
exclude_prefixes: build
  dist
  node_modules
exclude_globs: build/**
  dist/**
  node_modules/**
force_include_globs:
include_files:
include_dirs:
exclude_files:
exclude_dirs:
force_include_files:
force_include_dirs:
forbid_bare_except: True
forbid_raise_exception: True
forbid_broad_exception_handlers: True
forbid_silent_exception_pass: True
broad_exception_waiver_markers: DEVCOV_ALLOW_BROAD_ONCE
broad_exception_waiver_between: DEVCOV_BROAD_BEGIN=>DEVCOV_BROAD_END
```

Enforce explicit error surfaces and block raw exception anti-patterns.
This policy flags bare `except`, broad `except Exception` handlers,
generic `raise Exception(...)`, and silent `except Exception: pass`
handlers in selected source files. Broad-handler waivers are explicit
through marker comments or marker regions.


---

## Policy: Raw String Escapes

```policy-def
id: raw-string-escapes
severity: warning
auto_fix: false
enforcement: active
enabled: false
custom: false
include_suffixes: .py
  .pyi
  .pyw
  .js
  .jsx
  .ts
  .tsx
  .go
  .rs
  .java
  .cs
  .kt
  .swift
  .php
  .rb
selector_roles: include
  exclude
  force_include
include_globs: *.py
  *.pyi
  *.pyw
  *.js
  *.jsx
  *.ts
  *.tsx
  *.go
  *.rs
  *.java
  *.cs
  *.kt
  *.swift
  *.php
  *.rb
include_files:
include_dirs:
exclude_globs:
exclude_files:
exclude_dirs:
force_include_globs:
force_include_files:
force_include_dirs:
language_globs:
language_files:
language_dirs:
language_suffixes:
literal_patterns:
raw_literal_patterns:
suspicious_escape_patterns:
```

Warn when in-scope string literals contain suspicious bare backslashes.
Detection is language-aware: Python uses tokenizer spans, while other
languages use metadata-driven literal and escape patterns.


---

## Policy: Read Only Directories

```policy-def
id: read-only-directories
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: false
include_globs:
include_suffixes:
include_prefixes:
exclude_suffixes:
exclude_prefixes:
exclude_globs:
force_include_globs:
selector_roles: include
  exclude
  force_include
include_files:
include_dirs:
exclude_files:
exclude_dirs:
force_include_files:
force_include_dirs:
```

Protect declared read-only directories from modification. If a directory must
be editable, update this policy definition first.


---

## Policy: Readme Sync

```policy-def
id: readme-sync
severity: error
auto_fix: true
enforcement: active
enabled: true
custom: true
```

Ensure `devcovenant/README.md` mirrors `README.md` with repository-only
sections removed via the `<!-- REPO-ONLY:BEGIN -->` /
`<!-- REPO-ONLY:END -->` markers. Auto-fix rewrites the packaged guide from
the repo README.


---

## Policy: Security Scanner

```policy-def
id: security-scanner
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: false
exclude_globs: tests/**
  **/tests/**
include_suffixes: .py
include_prefixes:
include_globs: *.py
exclude_suffixes:
exclude_prefixes:
force_include_globs:
selector_roles: exclude
  include
  force_include
exclude_files:
exclude_dirs:
include_files:
include_dirs:
force_include_files:
force_include_dirs:
```

Scan source files for risky constructs like `eval`, `exec`, or
`shell=True`. Use the documented allow-comment only when a security
review approves the exception.


---

## Policy: Semantic Version Scope

```policy-def
id: semantic-version-scope
severity: error
auto_fix: false
enforcement: active
enabled: false
custom: false
version_file: devcovenant/VERSION
changelog_file: CHANGELOG.md
ignored_prefixes:
selector_roles: ignored
ignored_globs:
ignored_files:
ignored_dirs:
```

When enabled, the latest changelog entry must include exactly one
`[semver:major|minor|patch]` tag that matches the version bump. Use
`major` for API-breaking releases, `minor` for backward-compatible feature
work, and `patch` for bug fixes or documentation-only updates. The tag
must match the bump from the previous version, and the configured
version file must be updated whenever the changelog declares a release
scope. Activation is controlled by `config.yaml -> policy_state` and
should only be enabled for release processes that enforce SemVer
discipline.


---

## Policy: Tests Coverage

```policy-def
id: tests-coverage
severity: warning
auto_fix: false
enforcement: active
enabled: true
custom: false
enforce_symbol_fidelity: True
symbol_kinds: function
  class
symbol_name_min_length: 3
symbol_assertion_window: 2
fixture_marker_pattern: \bDEVCOV_FIXTURE_OK:\s*(?P<reason>\S.*)
assertion_signal_patterns: *=>\bassert\b
  python=>\bassert\b
  python=>\bself\.assert[A-Za-z_]*\s*\(
tautology_patterns: *=>^\s*assert\s*\(\s*true\s*\)\s*;?\s*$
  *=>^\s*assert\s+true\s*;?\s*$
  rust=>^\s*assert!\s*\(\s*true\s*\)\s*;?\s*$
  python=>^\s*assert\s+True\s*$
  python=>^\s*self\.assertTrue\s*\(\s*True\s*\)\s*$
include_suffixes: .py
include_prefixes:
exclude_prefixes: build
  dist
  node_modules
  tests
exclude_globs: build/**
  dist/**
  node_modules/**
  tests/**
watch_dirs: tests
tests_watch_dirs: tests
include_globs: *.py
exclude_suffixes:
force_include_globs:
watch_files:
selector_roles: include
  exclude
  watch
  tests_watch
  force_include
include_files:
include_dirs:
exclude_files:
exclude_dirs:
watch_globs:
tests_watch_globs:
tests_watch_files:
force_include_files:
force_include_dirs:
```

In-scope modules with related tests must include assertion signals in those
related test files. This policy enforces assertion-quality coverage for
structural source-to-test relationships, while modules-need-tests enforces
source-to-test structural alignment itself.
Tautological assertions (for example always-true checks) do not count as
assertion signal unless explicitly annotated as fixture-only using comment
marker `DEVCOV_FIXTURE_OK: <reason>` immediately above the assertion.


---

## Policy: Version Sync

```policy-def
id: version-sync
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: false
version_file: devcovenant/VERSION
target_roles: docs
  changelog
  legal
  package_manifest
role_extractors: docs=>doc_header_version
  changelog=>changelog_header_version
  legal=>semver_token
  package_manifest=>manifest_project_version
target_role_files: docs=>README.md
  docs=>AGENTS.md
  docs=>CONTRIBUTING.md
  docs=>SPEC.md
  docs=>PLAN.md
  changelog=>CHANGELOG.md
  legal=>LICENSE
  docs=>CHANGELOG.md
  docs=>PROFILE_MAP.md
  docs=>POLICY_MAP.md
  docs=>devcovenant/README.md
  docs=>devcovenant/core/README.md
  docs=>devcovenant/custom/README.md
  docs=>devcovenant/registry/README.md
  docs=>devcovenant/builtin/policies/README.md
  docs=>devcovenant/builtin/profiles/README.md
  docs=>devcovenant/custom/policies/README.md
  docs=>devcovenant/custom/profiles/README.md
  package_manifest=>pyproject.toml
target_role_globs: docs=>devcovenant/docs/**/*.md
target_role_dirs: docs=>devcovenant/docs
changelog_file: CHANGELOG.md
changelog_header_prefix: ## Version
selector_roles: target
target_globs:
target_files:
target_dirs:
```

All version-bearing targets must match the canonical version file (default
`VERSION` or a configured override).
Target selection is role-based via `target_roles` and role selectors
(`target_role_files`, `target_role_globs`, `target_role_dirs`) with
`role=>selector` entries. Version extraction is role-driven via
`role_extractors` and explicit extractor names
(`doc_header_version`, `changelog_header_version`,
`manifest_project_version`, `semver_token`). Manifest extraction remains
format-aware (TOML/JSON/YAML) while selector routing stays role-based.
Semantic bump progression and release-scope enforcement are handled by
`semantic-version-scope`.
<!-- DEVCOV-POLICIES:END -->
