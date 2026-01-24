# DevCovenant Development Guide
**Last Updated:** 2026-01-23
**Version:** 0.2.6

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

- 2026-01-22: Removed `DEVCOVENANT.md` and `CITATION.cff`; documentation now
  lives in `README.md` and `devcovenant/README.md`, and citation support is
  fully removed from the CLI and assets.
- 2026-01-22: SPEC/PLAN are optional docs; they are created only when
  `--include-spec` or `--include-plan` is supplied, and policies treat them as
  optional when absent.
- 2026-01-22: Update runs overwrite `devcovenant/` docs while preserving
  editable notes and managed blocks in repo-level docs.
<!-- DEVCOV:BEGIN -->
## Table of Contents
1. [Overview](#overview)
2. [Program Overview](#program-overview)
3. [Install and First-Run Guidance](#install-and-first-run-guidance)
4. [Severity Baseline](#severity-baseline)
5. [Editable Notes](#editable-notes-record-decisions-here)
6. [Workflow](#workflow)
7. [Installer Behavior Reference](#installer-behavior-reference)
8. [Policy Management and
   Enforcement](#devcovenant-policy-management-and-enforcement)

## Overview
This document is the single source of truth for DevCovenant policy. Every
rule that the engine enforces is written here in plain language with a
structured policy block beneath it.

## Program Overview
DevCovenant is a policy engine that binds documentation to enforcement. The
parser reads policy blocks, the registry stores hashes, and the engine runs
policy scripts while the CLI coordinates checks and fixes. Policies are
implemented in two layers: built-in scripts in
`devcovenant/core/policies/<policy>/<policy>.py` (with fixers in
`devcovenant/core/policies/<policy>/fixers`), repo-specific scripts in
`devcovenant/custom/policies/<policy>/<policy>.py`, and repo-specific
fixers in `devcovenant/custom/policies/<policy>/fixers`. A custom policy
script with the same id fully overrides the core policy, and core fixers
are skipped for that override.

DevCovenant core lives under `devcovenant/core`. User repos must keep core
exclusion enabled via `devcov_core_include: false` in `devcovenant/config.yaml`
so the engine can update itself safely. Only the DevCovenant repo should set
`devcov_core_include: true`.

## Install and First-Run Guidance
Always install DevCovenant on a fresh branch. Start with error-level blocking
only, clear all error-level violations, then ask the human owner whether to
address warnings or raise the block level.

## Severity Baseline
Use error severity for drift-critical policies (version sync, last-updated,
changelog coverage, devflow gates, and registry checks). Use warning severity
for code style and documentation quality. Use info severity for growth-only
reminders. Default block level should be `error` during initial adoption.

## Workflow
When you edit policy blocks, set `updated: true`, update scripts/tests, run
`devcovenant update-hashes`, then reset `updated: false`.
Finally, run the pre-commit and test gates in order.

Any change in the repo—code, configuration, or documentation—must still run
through the gated workflow (
`tools/run_pre_commit.py --phase start`, tests,
`tools/run_pre_commit.py --phase end`).
Whenever dependency manifests such as `requirements.in`, `requirements.lock`,
or `pyproject.toml` are updated, refresh `THIRD_PARTY_LICENSES.md` along with
the `licenses/` directory before committing so the dependency-license-sync
policy remains satisfied. Treat the workflow as mandatory for every commit,
even when only documentation or metadata is touched.

Keep the “Last Updated” fields and changelog headers on the current date
before running the gates; the `no-future-dates` policy blocks timestamps
set later than today, so double-check the dates before you touch those docs.


## Installer Behavior Reference
DevCovenant installs and updates standard docs in a predictable way.
Use the Install Behavior Reference in `devcovenant/README.md` when
preparing new repos or upgrades. Key defaults:
- `AGENTS.md` is replaced by the template; editable notes are
  preserved under `# EDITABLE SECTION`.
- `README.md` is preserved, headers refreshed, and the managed block
  inserted when required sections are missing.
- `CHANGELOG.md` and `CONTRIBUTING.md` are backed up to `*_old.*` and
  replaced by the standard assets and managed blocks.
- `SPEC.md` and `PLAN.md` are optional. When present, their content is
  preserved and headers are refreshed.
- `.gitignore` is regenerated from global, profile, and OS fragments,
  then merged with user entries under a preserved block.
## Release Readiness Review
- Confirm the gate sequence (pre-commit start → tests → pre-commit end)
  runs cleanly whenever changes touch docs, policies, or code. The updated
  `devflow-run-gates` policy will catch any skipped steps.
- Whenever dependency manifests change, update `THIRD_PARTY_LICENSES.md`,
  refresh the `licenses/` directory, and confirm the dependency-license-sync
  policy reports no violations before tagging a release. The policy looks for a
  `## License Report` section that mentions every touched manifest.
- The changelog must record every touched file, and
  `devcovenant/registry/registry.json` must be refreshed via
  `devcovenant update-hashes` before tagging a release.
- Build artifacts locally (`python -m build`, `twine check dist/*`) and verify
  the `publish.yml` workflow publishes using the `PYPI_API_TOKEN` secret before
  pushing the release tag.

# DO NOT EDIT FROM HERE TO END UNLESS EXPLICITLY REQUESTED BY A HUMAN!

# DevCovenant Policy Management and Enforcement

This section is managed by DevCovenant and captures the workflow and
enforcement expectations used by the policy engine. For architecture and
installer details, see `devcovenant/README.md`.

**Managed environment rule (metadata-driven).**
When `managed-environment` is active, run tooling inside the environment
declared in its metadata (`expected_paths`, `expected_interpreters`,
`required_commands`, `command_hints`). Examples include virtualenv, bench,
conda, poetry/pipx, or containerized Python. Use the provided command
hints in that policy.

**Required workflow**
- Start each session: `python3 tools/run_pre_commit.py --phase start`
- Run tests: `python3 tools/run_tests.py`
- End session: `python3 tools/run_pre_commit.py --phase end`
- When policy text changes, set `updated: true`, run
  `devcovenant update-hashes`, then reset the flag.

**Session checklist**
- Log decisions in the editable section above.
- Keep `AGENTS.md` as the canonical policy source.
- Sync policy text, scripts, and tests before committing.

**Standard commands**
Use `python3 -m devcovenant` if the `devcovenant` console script is not on
your PATH.
- `devcovenant check`
- `devcovenant check --mode pre-commit`
- `devcovenant check --fix`
- `devcovenant install --target <repo>`
- `devcovenant update --target <repo>`
- `devcovenant uninstall --target <repo>`
- `devcovenant restore-stock-text --policy <id>`

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
registry_file: devcovenant/registry/registry.json
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
stock_texts_file: devcovenant/registry/stock_policy_texts.yaml
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
test_status_file: devcovenant/registry/test_status.json
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
allowed_globs: README.md,AGENTS.md,CONTRIBUTING.md,CHANGELOG.md
  SPEC.md,PLAN.md
  devcovenant/README.md
allowed_files:
allowed_suffixes:
required_files:
required_globs: README.md,AGENTS.md,CONTRIBUTING.md,CHANGELOG.md
  SPEC.md,PLAN.md
  devcovenant/README.md
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
custom: false
profile_scopes: python
include_suffixes: .py
include_prefixes: devcovenant
exclude_prefixes: build,dist,node_modules,tests,devcovenant/core/tests
  devcovenant/core/profiles,devcovenant/custom/profiles
exclude_globs:
watch_dirs: tests,devcovenant/core/tests
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
exclude_prefixes: devcovenant/core/tests
user_facing_prefixes: devcovenant,tools,.github
user_facing_exclude_prefixes: devcovenant/core/tests,tests
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
