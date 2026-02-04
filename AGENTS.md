# DevCovenant Development Guide
**Last Updated:** 2026-02-04
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** AGENTS
**Doc Type:** policy-source
**Managed By:** DevCovenant

# Message from DevCovenant's Human, read first and do not edit:

This document is the absolute source of truth for everyone who works in
this repository—human and AI alike. Think of it as the Law of the Land:
the canonical policy source for this repo, and the policies it holds are
managed by DevCovenant. Failing to follow the instructions here will
cause commits to fail.

After `AGENTS.md`, read `README.md` to learn about the project that
lives in this repository and what it aims to solve.

When you are ready to interact with DevCovenant itself, open
`devcovenant/README.md`. It can be finicky at first, but that is the
price of keeping docs, code, and features in sync under AI-assisted
development.

Taking development notes below is effectively obligatory. Updating them
frequently to describe current hurdles and events is good practice.

The editable notes section starts immediately after this message and
after the `DEVCOV:END` marker, up to the next `DEVCOV:BEGIN`.
When installing DevCovenant into a repo, the installer preserves any
existing `AGENTS.md` content in that section. Never edit between
`DEVCOV*:BEGIN` and `DEVCOV*:END` markers in any file, regardless of how
they are styled.

Have a productive session and read the docs end-to-end. Always run the
gate commands in the right order - ALWAYS start your edits session with
`start`, do your edits, then run your tests if any, then `end`. This
ensures devflow policy compliance and accepted commits. Read this entire
document and you will get it!
<!-- DEVCOV:END -->

# EDITABLE SECTION

- 2026-01-22: Removed `DEVCOVENANT.md` and `CITATION.cff`; documentation now
  lives in `README.md` and `devcovenant/README.md`, and citation support is
  fully removed from the CLI and assets.
- 2026-01-22: SPEC/PLAN are managed alongside the other profile-driven doc
  assets. There is no include flag; profiles, policies, and config decide when
  to refresh them.
- 2026-01-22: Update runs overwrite `devcovenant/` docs while preserving
  editable notes and managed blocks in repo-level docs.
- 2026-01-26: Noted repo tests live under `/tests` outside the package and are
  driven by metadata selectors (e.g., `tests_watch_dirs`), so policy/profile
  suites can move freely without hard-coded paths.
- 2026-01-26: PLAN/SPEC now describe the scanner roadmap, the science profile
  (including a `CITATION.md` asset), the additional framework/API/database
  profiles, and the upcoming 0.2.7 metadata-driven DSL for stock policies while
  keeping custom policy prose editable in AGENTS.
- 2026-01-27: Reordered AGENTS sections and markers as intended; the
  policy block remains a special DevCovenant-managed area that general block
  automation should avoid until we flesh out the policy handling workflow.

<!-- DEVCOV:BEGIN -->

## THE DEV COVENANT

- We are human and AI developers working on this project together.
- We obey every AGENTS.md and DevCovenant instruction.
- We maintain flawless repo hygiene to prevent drift and keep integrity strong.
- We never edit anything inside managed `<!-- DEVCOV* -->` blocks.
- We read AGENTS.md on every task so we stay current with the development
  policies.
- We follow the documented workflow precisely and read README/SPEC/PLAN after
  AGENTS.md before we start editing.
- We proactively follow policies while working and stay happy when DevCovenant
  is happy after edits.
- We treat any change to repository content as an edit that must obey our
  gates.

## Obligatory Workflow
Running DevCovenant uses a fixed sequence: begin with
`python3 devcovenant/run_pre_commit.py --phase start`,
_only then make any edits_, then run
`python3 devcovenant/run_tests.py`, and finish with
`python3 devcovenant/run_pre_commit.py --phase end`. The `devflow-run-gates`
policy records those commands; any deviation blocks progress. Discussion-only
turns may skip tests, yet triggering the start gate still snapshots the repo
state.

This workflow is non-negotiable. Failing to follow it causes failed commits,
extra gate reruns, and major non-compliance with repository policy.

Multiple violations degrade team culture, so stay polite and courteous;
follow the rules, keep the repository clean, and ask for help instead of
looping whenever you cannot clear the gates.

## Managed Environment
If your project lives in a managed environment, work and run DevCovenant
from that environment (the pre-commit hook uses the devcovenant config by
default).

Follow the `managed-environment` metadata (virtualenv, bench, conda, poetry,
etc.) for interpreters, paths, and command hints.

_WARNING: IMPORTANT BEHAVIOR REMINDER:_

_If a change requires services (web servers, APIs, databases,_
_data pipelines, etc.), launch them before the test gate so the suite_
_exercises the running stack!_

Stock policies
such as `devflow-run-gates`, `version-sync`, `dependency-license-sync`,
`changelog-coverage`, and `managed-environment` guard critical invariants;
consult `devcovenant/README.md` for the broader command catalog, architecture
notes, profile guidance, and release steps before customizing their metadata.

DevCovenant’s own tests live under `tests/devcovenant/...` (mirroring
`devcovenant/core` and `devcovenant/custom`) and stay outside the installable
package. Selector metadata (`selector_roles`, `tests_watch_dirs`, etc.) routes
policies to those suites, so relocate tests by editing metadata instead of
hard-coding paths.

## Table of Contents
1. [Overview](#overview)
2. [Program Overview](#program-overview)
3. [Workflow](#workflow)
4. [Installer Behavior Reference](#installer-behavior-reference)
5. [Release Readiness Review](#release-readiness-review)
6. [Policy Management and Enforcement](#policy-management-and-enforcement)

## Overview
DevCovenant translates policy prose into executable checks. This document is
the canonical source of policy definitions and the instructions for working
with them.

## Program Overview
The engine loads policy modules under `devcovenant/core/policies/<policy>`
with optional overrides under `devcovenant/custom/policies/<policy>`. Assets,
adapters, and fixers sit beside the scripts, and profiles configure suffixes,
commands, and metadata through their manifests.

## Workflow
- Run `python3 devcovenant/run_pre_commit.py --phase start` before editing
  files, perform your work, execute `python3 devcovenant/run_tests.py`, and
  close with `python3 devcovenant/run_pre_commit.py --phase end`.
- Use `python3 -m devcovenant` instead of `devcovenant` when the console
  script is not on your PATH.
- When policy text changes, mark `updated: true`, refresh scripts/tests, run
  `devcovenant update-policy-registry`, then reset the flag to keep the
  registry aligned with policy prose.
- Update `THIRD_PARTY_LICENSES.md` and the `licenses/` directory whenever
  dependency manifests (`requirements.in`, `requirements.lock`,
  `pyproject.toml`) change so the dependency-license-sync policy passes.
- Keep each managed doc’s “Last Updated” header current and log your work
  in the current `CHANGELOG.md` entry before closing the gates; the
  `no-future-dates` policy rejects post-dated timestamps.

## Installer Behavior Reference
- `AGENTS.md` comes from this template while preserving the editable section
  created per repo.
- `README.md` preserves user content, gains the standard header, and receives
  a managed block for DevCovenant details.
- `CHANGELOG.md` and `CONTRIBUTING.md` refresh their managed blocks on install
  and are backed up as `*_old.*`.
- Managed docs (`SPEC.md`, `PLAN.md`, etc.) remain under profile/metadata
  control.
- `.gitignore` merges generated fragments with user entries under a preserved
  block, while installs record chosen profiles plus the immovable `global`,
  `data`, `docs`, and `suffixes` profiles.

## Release Readiness Review
- Keep the gate sequence (pre-commit start → tests → pre-commit end) clean
  whenever docs, policies, or code change; `devflow-run-gates` will flag
  deviations.
- Update `THIRD_PARTY_LICENSES.md`, refresh `licenses/`, and cite touched
  manifests in the `## License Report` before tagging a release.
- Log every touched file in the current `CHANGELOG.md` entry and refresh
  `devcovenant/registry/local/policy_registry.yaml` via
  `devcovenant update-policy-registry` before releasing.
- Build artifacts locally (`python3 -m build`, `twine check dist/*`) and verify
  `.github/workflows/publish.yml` publishes with `PYPI_API_TOKEN`.

## Policy Management and Enforcement
This section is managed by DevCovenant; installers and updates refresh it
automatically. It describes the enforced workflow, managed-environment
expectations, and points to `devcovenant/README.md` for commands, profiles, and
release guidance. Detailed policy blocks follow.
**Managed blocks**
Managed sections are wrapped with `<!-- DEVCOV:BEGIN -->` and
`<!-- DEVCOV:END -->`. Install/update/uninstall scripts refresh those
blocks while leaving surrounding content intact.


<!-- DEVCOV:END -->
<!-- DEVCOV-POLICIES:BEGIN -->
## Policy: Changelog Coverage

```policy-def
id: changelog-coverage
severity: error
auto_fix: False
enforcement: active
apply: True
custom: False
profile_scopes: global
main_changelog: CHANGELOG.md
skipped_files: CHANGELOG.md
  .gitignore
  .pre-commit-config.yaml
collections: __none__
selector_roles: skipped
skipped_globs:
skipped_dirs:
```

Every change must be logged in the latest changelog entry dated today,
under the current version, with every touched path listed in its Files
block. Collection prefixes (when enabled) must be logged in their own
changelog; prefixed files may not appear in the root changelog. This keeps
release notes daily, file-complete, and traceable.


---

## Policy: Dependency License Sync

```policy-def
id: dependency-license-sync
status: active
severity: error
auto_fix: true
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: python
  javascript
  typescript
  java
  csharp
  php
  ruby
  go
  rust
  swift
  dart
  flutter
  fastapi
  frappe
  objective-c
dependency_files: requirements.in
  requirements.lock
  pyproject.toml
third_party_file: THIRD_PARTY_LICENSES.md
licenses_dir: licenses
report_heading: ## License Report
selector_roles: dependency
dependency_globs:
dependency_dirs:
```

Maintain the third-party license table alongside `requirements.in`,
`requirements.lock`, and `pyproject.toml`. The policy points reviewers to the
`licenses/` directory and its `## License Report` section so every dependency
change touches both the license text and the cited manifest.


---

## Policy: Devcov Parity Guard

```policy-def
id: devcov-parity-guard
status: active
severity: warning
auto_fix: false
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: global
policy_definitions: AGENTS.md
```

Ensure the policy text recorded in AGENTS matches the descriptor text
shipped alongside each policy (core or custom). When the two drift,
DevCovenant warns so the policy prose and its implementation stay aligned.


---

## Policy: Devcov Raw String Escapes

```policy-def
id: devcov-raw-string-escapes
status: active
severity: warning
auto_fix: false
updated: false
enforcement: active
apply: true
custom: true
freeze: false
profile_scopes: devcovrepo
```

Warn when DevCovenant repo Python strings contain bare backslashes.
This repo-only policy keeps the raw-string guidance active without
forcing it on user repos.


---

## Policy: DevCovenant Self-Enforcement

```policy-def
id: devcov-self-enforcement
status: active
severity: error
auto_fix: false
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: global
policy_definitions: AGENTS.md
registry_file: devcovenant/registry/local/policy_registry.yaml
```

DevCovenant must keep its registry synchronized with policy definitions.


---

## Policy: DevCovenant Structure Guard

```policy-def
id: devcov-structure-guard
status: active
severity: error
auto_fix: false
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: global
```

Ensure the DevCovenant repo keeps the required structure and tooling files.


---

## Policy: DevFlow Run Gates

```policy-def
id: devflow-run-gates
status: active
severity: error
auto_fix: false
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: global
  python
  javascript
  typescript
  java
  kotlin
  scala
  groovy
  dotnet
  csharp
  fsharp
  php
  ruby
  go
  rust
  swift
  dart
  flutter
  elixir
  erlang
  haskell
  clojure
  julia
  ocaml
  crystal
test_status_file: devcovenant/registry/local/test_status.json
required_commands: pytest
  python3 -m unittest discover
require_pre_commit_start: true
require_pre_commit_end: true
pre_commit_command: python3 -m pre_commit run --all-files
pre_commit_start_epoch_key: pre_commit_start_epoch
pre_commit_end_epoch_key: pre_commit_end_epoch
pre_commit_start_command_key: pre_commit_start_command
pre_commit_end_command_key: pre_commit_end_command
code_extensions:
```

DevCovenant must record and enforce the standard workflow: pre-commit start,
tests, then pre-commit end. The policy reads the status file to ensure each
gate ran and that no required command was skipped.
This check is enforced for every repository change (including
documentation-only updates) so the gate sequence cannot be skipped.


---

## Policy: Docstring and Comment Coverage

```policy-def
id: docstring-and-comment-coverage
status: active
severity: error
auto_fix: false
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: python
  javascript
  typescript
  go
  rust
  java
  csharp
include_suffixes:
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

Python modules, classes, and functions must include a docstring or a nearby
explanatory comment. This keeps intent visible even as code evolves.


---

## Policy: Documentation Growth Tracking

```policy-def
id: documentation-growth-tracking
status: active
severity: info
auto_fix: false
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: global
  docs
  data
  python
  javascript
  typescript
  go
  rust
  java
  csharp
  php
  ruby
  swift
  dart
  terraform
  docker
  kubernetes
  sql
  fastapi
  frappe
  flutter
  objective-c
selector_roles: user_facing
  user_visible
  doc_quality
include_prefixes: devcovenant
  tools
  .github
exclude_prefixes: tests
user_facing_prefixes: devcovenant
  tools
  .github
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
user_facing_files: devcovenant/cli.py
  devcovenant/__main__.py
  .pre-commit-config.yaml
  pyproject.toml
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
doc_quality_files: README.md
  CONTRIBUTING.md
  AGENTS.md
  SPEC.md
  PLAN.md
  devcovenant/README.md
required_headings: Table of Contents
  Overview
  Workflow
require_toc: true
min_section_count: 3
min_word_count: 120
quality_severity: warning
require_mentions: true
mention_severity: warning
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
include_globs: devcovenant/**
  tools/**
  .github/**
exclude_suffixes:
exclude_globs: tests/**
force_include_globs:
user_facing_exclude_globs:
user_facing_exclude_suffixes:
user_facing_dirs: devcovenant/**
  tools/**
  .github/**
user_visible_globs:
user_visible_dirs:
doc_quality_globs:
doc_quality_dirs:
include_files:
include_dirs:
exclude_files:
exclude_dirs:
user_facing_exclude_files:
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
of contents, and minimum depth.


---

## Policy: Last Updated Placement

```policy-def
id: last-updated-placement
status: active
severity: error
auto_fix: true
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: global
  docs
  data
include_suffixes: .md
allowed_globs: >
  README.md
  AGENTS.md
  CONTRIBUTING.md
  CHANGELOG.md
  SPEC.md
  PLAN.md
  devcovenant/README.md
  devcovenant/core/profiles/global/assets/*.yaml
allowed_files:
allowed_suffixes:
required_files:
required_globs: README.md
  AGENTS.md
  CONTRIBUTING.md
  CHANGELOG.md
  SPEC.md
  PLAN.md
  devcovenant/README.md
selector_roles: include
  allowed
  required
include_globs: *.md
include_files:
include_dirs:
allowed_dirs:
required_dirs:
```

Docs must include a `Last Updated` header near the top so readers can trust
recency. The auto-fix keeps timestamps current while respecting allowed
locations.


---

## Policy: Line Length Limit

```policy-def
id: line-length-limit
status: active
severity: warning
auto_fix: false
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: global
  docs
  data
  python
  javascript
  typescript
  go
  rust
  java
  csharp
  php
  ruby
  swift
  dart
  terraform
  docker
  kubernetes
  sql
  fastapi
  frappe
  flutter
  objective-c
max_length: 79
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
exclude_globs: devcovenant/core/profiles/global/assets/*.yaml
  devcovenant/core/stock_policy_texts.json
  build/**
  dist/**
  node_modules/**
include_prefixes:
include_globs: *.>
  *.py
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
include_files:
include_dirs:
exclude_files:
exclude_dirs:
force_include_files:
force_include_dirs:
```

Keep lines within the configured maximum so documentation and code remain
readable. Reflow long sentences or wrap lists rather than ignoring the limit.


---

## Policy: Managed Doc Assets

```policy-def
id: managed-doc-assets
severity: error
auto_fix: false
enforcement: active
apply: true
custom: true
profile_scopes: devcovrepo
```

Ensure AGENTS.md, README.md, PLAN.md, SPEC.md, CHANGELOG.md, and
CONTRIBUTING.md remain the authoritative sources for their managed-block
descriptors under `devcovenant/core/profiles/global/assets/` so documentation
generation is deterministic.


---

## Policy: Managed Environment

```policy-def
id: managed-environment
status: active
severity: error
auto_fix: false
updated: false
enforcement: active
apply: false
custom: false
profile_scopes: global
expected_paths:
expected_interpreters:
required_commands:
command_hints:
```

DevCovenant must run from the managed environment described in this
policy's metadata. Use expected_paths for virtualenv or bench roots,
expected_interpreters for explicit interpreter locations, and
required_commands or command_hints to guide contributors. When enabled
with empty metadata, the policy emits a warning so teams fill the
required context.


---

## Policy: Name Clarity

```policy-def
id: name-clarity
status: active
severity: warning
auto_fix: false
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: python
  javascript
  typescript
  go
  rust
  java
  csharp
exclude_prefixes: build
  dist
  node_modules
include_suffixes:
include_prefixes:
include_globs:
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

## Policy: New Modules Need Tests

```policy-def
id: new-modules-need-tests
status: active
severity: error
auto_fix: false
updated: false
enforcement: active
apply: true
custom: true
profile_scopes: python
  fastapi
  frappe
  javascript
  typescript
  go
  rust
  java
  csharp
include_suffixes:
include_prefixes: devcovenant
exclude_prefixes: build
  dist
  node_modules
  tests
  devcovenant/core/profiles
exclude_globs: devcovenant/core/profiles/**
watch_dirs: tests
tests_watch_dirs: tests
include_globs:
exclude_suffixes:
force_include_globs:
watch_files:
```

New or modified modules in the watched locations must have corresponding
tests. Test modules (files starting with `test_`) are exempt from the rule.

The `tests_watch_dirs` metadata keeps `tests/` as the default watch list,
so the policy covers `tests/devcovenant/core/profiles/` and the
`tests/devcovenant/custom/profiles/` suites that mirror the package layout.


---

## Policy: No Future Dates

```policy-def
id: no-future-dates
status: active
severity: error
auto_fix: true
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: global
```

Dates in changelogs or documentation must not be in the future. Auto-fixers
should correct accidental placeholders to today’s date.


---

## Policy: Policy Text Presence

```policy-def
id: policy-text-presence
status: active
severity: error
auto_fix: false
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: global
policy_definitions: AGENTS.md
```

Every policy definition must include descriptive text immediately after the
`policy-def` block. Empty policy descriptions are not allowed.


---

## Policy: Raw String Escapes

```policy-def
id: raw-string-escapes
status: active
severity: warning
auto_fix: false
updated: false
enforcement: active
apply: false
custom: false
freeze: false
profile_scopes: python
```

Policy description pending.


---

## Policy: Read-Only Directories

```policy-def
id: read-only-directories
status: active
severity: error
auto_fix: false
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: global
include_globs: __none__
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

## Policy: README Sync

```policy-def
id: readme-sync
status: active
severity: error
auto_fix: true
updated: false
enforcement: active
apply: true
custom: true
freeze: true
profile_scopes: global
```

Ensure `devcovenant/README.md` mirrors `README.md` with repository-only
sections removed via the `<!-- REPO-ONLY:BEGIN -->` /
`<!-- REPO-ONLY:END -->` markers. Auto-fix rewrites the packaged guide from
the repo README.


---

## Policy: Security Scanner

```policy-def
id: security-scanner
status: active
severity: error
auto_fix: false
updated: false
exclude_globs: tests/**
  **/tests/**
enforcement: active
apply: true
custom: false
profile_scopes: python
  fastapi
  frappe
  javascript
  typescript
  go
  rust
  java
  csharp
include_suffixes:
include_prefixes:
include_globs:
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

Scan Python files for risky constructs like `eval`, `exec`, or `shell=True`.
Use the documented allow-comment only when a security review approves the
exception.


---

## Policy: Semantic Version Scope

```policy-def
id: semantic-version-scope
status: active
severity: error
auto_fix: false
updated: false
enforcement: active
apply: false
custom: false
profile_scopes: global
version_file: VERSION
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
must match the bump from the previous version, and `VERSION` must be
updated whenever the changelog declares a release scope. The policy ships
disabled (`apply: false`) and should only be enabled for release
processes that enforce SemVer discipline.


---

## Policy: Track Test Status

```policy-def
id: track-test-status
status: active
severity: warning
auto_fix: false
updated: false
enforcement: active
apply: true
custom: false
freeze: false
profile_scopes: global
```

Policy description pending.


---

## Policy: Version Synchronization

```policy-def
id: version-sync
status: active
severity: error
auto_fix: false
updated: false
enforcement: active
apply: true
custom: false
profile_scopes: global
  docs
  data
  suffixes
  python
  javascript
  typescript
  java
  csharp
  php
  ruby
  go
  rust
  swift
  dart
  flutter
  terraform
  docker
  kubernetes
  sql
  fastapi
  frappe
  objective-c
version_file: VERSION
readme_files: README.md
  AGENTS.md
  CONTRIBUTING.md
  SPEC.md
  PLAN.md
  devcovenant/README.md
optional_files: SPEC.md
  PLAN.md
pyproject_files: pyproject.toml
license_files: LICENSE
runtime_entrypoints: __none__
runtime_roots: __none__
changelog_file: CHANGELOG.md
changelog_header_prefix: ## Version
readme_file:
pyproject_file:
selector_roles: readme
  optional
  pyproject
  license
readme_globs:
readme_dirs:
optional_globs:
optional_dirs:
pyproject_globs:
pyproject_dirs:
license_globs:
license_dirs:
```

All version-bearing files must match the canonical `VERSION` value, and
version bumps must move forward. Files listed under `optional_files` are
only enforced when present (for example, SPEC/PLAN in user repos). The
policy also flags hard-coded runtime versions and ensures changelog
releases reflect the current version.
<!-- DEVCOV-POLICIES:END -->
