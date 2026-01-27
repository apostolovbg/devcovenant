# DevCovenant Development Guide
<!-- DEVCOV:BEGIN -->
**Doc ID:** AGENTS
**Doc Type:** policy-source
**Managed By:** DevCovenant

# Message from Human, do not edit:

Read `README.md` and `devcovenant/README.md` first for architecture and
workflow. This file is the canonical policy source of truth.

Taking development notes is effectively obligatory; treat it as required.
The editable notes section starts immediately after `<!-- DEVCOV:END -->`.
When installing DevCovenant into a repo, preserve any existing notes and
place them in the editable section below. If none exist, insert a reminder
to record decisions there.
#


<a id="editable-notes-record-decisions-here"></a>
### Editable notes (repo-specific)


Just below the DEVCOV:END marker after this paragraph is the editable section
that the installer and repo maintainers use for working memory. Keep any
existing notes entered by previous maintainers, or replace the text with new
decision logs when installing into a new repo. Because the rest of `AGENTS.md`
below is managed by DevCovenant, do not move or overwrite anything after the
`DEVCOV:BEGIN` marker when documenting repo-specific decisions here. The
editable section is after the `DEVCOV:END` below and before the `DEVCOV:BEGIN`
after it. It is marked by `# EDITABLE SECTION` if `AGENTS.md` is not present
in the repo at DevCovenant installation. If a user `AGENTS.md` is present,
its contents are preserved in the editable section. It is strongly advised
that they be revised right after installation, so there are no conflicting
instructions with DevCovenant, its applied policies (and in general).
<!-- DEVCOV:END -->

# EDITABLE SECTION

<!-- DEVCOV:BEGIN -->
## Operational Orientation
Running DevCovenant uses a fixed sequence: begin with
`python3 tools/run_pre_commit.py --phase start`, make edits, run
`python3 tools/run_tests.py`, and finish with
`python3 tools/run_pre_commit.py --phase end`. The `devflow-run-gates`
policy records those commands; any deviation blocks progress. Discussion-only
turns may skip tests, yet triggering the start gate still snapshots the repo
state.

Follow the `managed-environment` metadata (virtualenv, bench, conda, poetry,
etc.) for interpreters, paths, and command hints. If a change requires
services (web servers, APIs, databases, data pipelines, etc.), launch them
before the test gate so the suite exercises the running stack. Stock policies
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
- Run `python3 tools/run_pre_commit.py --phase start` before editing files,
  perform your work, execute `python3 tools/run_tests.py`, and close with
  `python3 tools/run_pre_commit.py --phase end`.
- When policy text changes, mark `updated: true`, refresh scripts/tests, run
  `devcovenant update-policy-registry`, then reset the flag to keep the registry aligned
  with policy prose.
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
- Optional docs (`SPEC.md`, `PLAN.md`) remain untouched unless
  `--include-spec` / `--include-plan` is supplied.
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
  `devcovenant/registry/local/policy_registry.yaml` via `devcovenant update-policy-registry` before
  releasing.
- Build artifacts locally (`python -m build`, `twine check dist/*`) and verify
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

## Policy: DevCovenant Self-Enforcement

```policy-def
id: devcov-self-enforcement
status: active
severity: error
auto_fix: false
updated: false
applies_to: devcovenant/**
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
applies_to: *
enforcement: active
apply: true
custom: false
profile_scopes: global
```

Ensure the DevCovenant repo keeps the required structure and tooling files.

---

## Policy: Dependency License Sync

```policy-def
id: dependency-license-sync
status: active
severity: error
auto_fix: true
updated: false
applies_to: *
enforcement: active
apply: true
custom: false
profile_scopes: python
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
dependency_files: requirements.in,requirements.lock,pyproject.toml
third_party_file: THIRD_PARTY_LICENSES.md
licenses_dir: licenses
report_heading: ## License Report
```

Maintain the third-party license table alongside `requirements.in`,
`requirements.lock`, and `pyproject.toml`. The policy points reviewers to the
`licenses/` directory and its `## License Report` section so every dependency
change touches both the license text and the cited manifest.

---

## Policy: Policy Text Presence

```policy-def
id: policy-text-presence
status: active
severity: error
auto_fix: false
updated: false
applies_to: AGENTS.md
enforcement: active
apply: true
custom: false
profile_scopes: global
policy_definitions: AGENTS.md
```

Every policy definition must include descriptive text immediately after the
`policy-def` block. Empty policy descriptions are not allowed.

---

## Policy: Stock Policy Text Sync

```policy-def
id: stock-policy-text-sync
status: active
severity: warning
auto_fix: false
updated: false
applies_to: AGENTS.md
enforcement: active
apply: true
custom: false
profile_scopes: global
policy_definitions: AGENTS.md
stock_texts_file: devcovenant/registry/global/stock_policy_texts.yaml
```

If a built-in policy text is edited from its stock wording, DevCovenant must
raise a warning and instruct the agent to either restore the stock text or
mark the policy `custom: true` and provide a matching custom implementation.

---

## Policy: DevFlow Run Gates

```policy-def
id: devflow-run-gates
status: active
severity: error
auto_fix: false
updated: false
applies_to: *
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
  python -m unittest discover
require_pre_commit_start: true
require_pre_commit_end: true
pre_commit_command: pre-commit run --all-files
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

## Policy: Managed Environment

```policy-def
id: managed-environment
status: active
severity: error
auto_fix: false
updated: false
applies_to: *
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


## Policy: Changelog Coverage

```policy-def
id: changelog-coverage
status: active
severity: error
auto_fix: false
updated: false
applies_to: *
enforcement: active
apply: true
custom: false
profile_scopes: global
main_changelog: CHANGELOG.md
skipped_files: CHANGELOG.md,.gitignore,.pre-commit-config.yaml
collections: __none__
```

Every substantive change must be recorded in the changelog entry for the
current version. This policy prevents untracked updates and keeps release
notes aligned with repository changes.

---

## Policy: Version Synchronization

```policy-def
id: version-sync
status: active
severity: error
auto_fix: false
updated: false
applies_to: *
enforcement: active
apply: true
custom: false
profile_scopes: global
  docs
  data
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
  terraform
  docker
  kubernetes
version_file: VERSION
readme_files: README.md,AGENTS.md,CONTRIBUTING.md,SPEC.md
  PLAN.md
  devcovenant/README.md
optional_files: SPEC.md,PLAN.md
pyproject_files: pyproject.toml
license_files: LICENSE
runtime_entrypoints: __none__
runtime_roots: __none__
changelog_file: CHANGELOG.md
changelog_header_prefix: ## Version
readme_file:
pyproject_file:
```

All version-bearing files must match the canonical `VERSION` value, and
version bumps must move forward. Files listed under `optional_files` are
only enforced when present (for example, SPEC/PLAN in user repos). The
policy also flags hard-coded runtime versions and ensures changelog
releases reflect the current version.

---

## Policy: Semantic Version Scope

```policy-def
id: semantic-version-scope
status: active
severity: error
auto_fix: false
updated: false
applies_to: *
enforcement: active
apply: false
custom: false
profile_scopes: global
version_file: VERSION
changelog_file: CHANGELOG.md
ignored_prefixes:
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

## Policy: Last Updated Placement

```policy-def
id: last-updated-placement
status: active
severity: error
auto_fix: true
updated: false
applies_to: *.md
enforcement: active
apply: true
custom: false
profile_scopes: global
  docs
  data
include_suffixes: .md
allowed_globs: README.md,AGENTS.md,CONTRIBUTING.md,SPEC.md
  PLAN.md
  devcovenant/README.md
allowed_files:
allowed_suffixes:
required_files:
required_globs:
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
applies_to: *
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
  kotlin
  scala
  groovy
  dotnet
  csharp
  fsharp
  php
  ruby
  swift
  dart
  terraform
  docker
  kubernetes
  ansible
max_length: 79
include_suffixes: .py,.md,.rst,.txt,.yml,.yaml,.json,.toml,.cff
exclude_prefixes: build,dist,node_modules
exclude_globs: devcovenant/core/profiles/global/assets/LICENSE_GPL-3.0.txt
include_prefixes:
include_globs:
exclude_suffixes:
force_include_globs:
```

Keep lines within the configured maximum so documentation and code remain
readable. Reflow long sentences or wrap lists rather than ignoring the limit.

---

## Policy: Docstring and Comment Coverage

```policy-def
id: docstring-and-comment-coverage
status: active
severity: error
auto_fix: false
updated: false
applies_to: *.py
enforcement: active
apply: true
custom: false
profile_scopes: python
include_suffixes: .py
exclude_prefixes: build,dist,node_modules
include_prefixes:
include_globs:
exclude_suffixes:
exclude_globs:
force_include_globs:
```

Python modules, classes, and functions must include a docstring or a nearby
explanatory comment. This keeps intent visible even as code evolves.

---

## Policy: Name Clarity

```policy-def
id: name-clarity
status: active
severity: warning
auto_fix: false
updated: false
applies_to: *.py
enforcement: active
apply: true
custom: false
profile_scopes: python
exclude_prefixes: build,dist,node_modules
include_suffixes:
include_prefixes:
include_globs:
exclude_suffixes:
exclude_globs:
force_include_globs:
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
applies_to: *
enforcement: active
apply: true
custom: true
updated: false
profile_scopes: python
include_suffixes: .py
include_prefixes: devcovenant
exclude_prefixes:
  - build
  - dist
  - node_modules
  - tests
  - devcovenant/core/profiles
  - devcovenant/custom/profiles
exclude_globs:
watch_dirs:
  - tests
tests_watch_dirs:
  - tests
include_globs:
exclude_suffixes:
force_include_globs:
watch_files:
```

New or modified modules in the watched locations must have corresponding
tests. Test modules (files starting with `test_`) are exempt from the rule.

---

## Policy: Documentation Growth Tracking

```policy-def
id: documentation-growth-tracking
status: active
severity: info
auto_fix: false
updated: false
applies_to: *
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
  kotlin
  scala
  groovy
  dotnet
  csharp
  fsharp
  php
  ruby
  swift
  dart
  terraform
  docker
  kubernetes
  ansible
selector_roles: user_facing,user_visible,doc_quality
include_prefixes: devcovenant,tools,.github
exclude_prefixes: tests
user_facing_prefixes: devcovenant,tools,.github
user_facing_exclude_prefixes: tests
user_facing_suffixes: .py,.js,.ts,.tsx,.vue,.go,.rs,.java,.kt,.swift,.rb
  .php,.cs,.yml,.yaml,.json,.toml
user_facing_files: devcovenant/cli.py,devcovenant/__main__.py,
  .pre-commit-config.yaml,pyproject.toml
user_facing_globs: .github/workflows/*.yml,.github/workflows/*.yaml
user_facing_keywords: api,endpoint,endpoints,route,routes,routing,service
  services,controller,controllers,handler,handlers,client,clients,webhook
  webhooks,integration,integrations,sdk,cli,ui,view,views,page,pages,screen
  screens,form,forms,workflow,workflows
user_visible_files: README.md,CONTRIBUTING.md,AGENTS.md
  SPEC.md,PLAN.md,devcovenant/README.md
doc_quality_files: README.md,CONTRIBUTING.md,AGENTS.md
  SPEC.md,PLAN.md,devcovenant/README.md
required_headings: Table of Contents,Overview,Workflow
require_toc: true
min_section_count: 3
min_word_count: 120
quality_severity: warning
require_mentions: true
mention_severity: warning
mention_min_length: 3
mention_stopwords: devcovenant,tools,common,custom,policy,policies,script
  scripts,py,js,ts,json,yml,yaml,toml,md,readme,plan,spec
include_suffixes:
include_globs:
exclude_suffixes:
exclude_globs:
force_include_globs:
user_facing_exclude_globs:
user_facing_exclude_suffixes:
user_facing_dirs:
user_visible_globs:
user_visible_dirs:
doc_quality_globs:
doc_quality_dirs:
```

When user-facing files change (as defined by the user-facing selectors and
keywords), the documentation set listed here must be updated. User-facing
includes API surfaces, integration touchpoints, and any behavior that affects
the user's experience or workflow. Updated docs should mention the relevant
components by name so readers can find changes quickly. The policy also
enforces documentation quality standards such as required headings, a table
of contents, and minimum depth.

---

## Policy: Read-Only Directories

```policy-def
id: read-only-directories
status: active
severity: error
auto_fix: false
updated: false
applies_to: *
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
```

Protect declared read-only directories from modification. If a directory must
be editable, update this policy definition first.

---

## Policy: No Future Dates

```policy-def
id: no-future-dates
status: active
severity: error
auto_fix: true
updated: false
applies_to: *
enforcement: active
apply: true
custom: false
profile_scopes: global
```

Dates in changelogs or documentation must not be in the future. Auto-fixers
should correct accidental placeholders to today’s date.

---

## Policy: Security Scanner

```policy-def
id: security-scanner
status: active
severity: error
auto_fix: false
updated: false
applies_to: *.py
exclude_globs: tests/**,**/tests/**
enforcement: active
apply: true
custom: false
profile_scopes: python
include_suffixes:
include_prefixes:
include_globs:
exclude_suffixes:
exclude_prefixes:
force_include_globs:
```

Scan Python files for risky constructs like `eval`, `exec`, or `shell=True`.
Use the documented allow-comment only when a security review approves the
exception.

---

<!-- DEVCOV:END -->
