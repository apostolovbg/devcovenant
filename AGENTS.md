# DevCovenant Development Guide
**Last Updated:** 2026-02-14
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

## Working Notepad (Live Development Spec)

### Update Habit (Do Not Skip)
- Note-to-self: update this section frequently so notes never grow beards.
- Note-to-self: if a decision changes, update this section in the same session.
- Note-to-self: when PLAN/SPEC changes, mirror the operational impact here.
- Note-to-self: stale notes are drift; treat stale notes as a bug.
- Note-to-self: prefer short, factual entries over long narrative text.

### Current Direction (0.2.6)
- API freeze means contract semantics are stable.
- Additive extensions are allowed; silent behavior flips are not.
- Policy activation authority is config `policy_state`.
- Policy lifecycle `status` metadata is retired.
- Profiles do not activate policies.
- Profiles supply overlays, assets, selectors, and hooks.
- AGENTS policy block is runtime-parsed source for active behavior.
- Registry remains diagnostic/hash state and AGENTS compile source.
- Refresh must keep AGENTS policy block synchronized.
- Forward-only implementation is the baseline stance.

### Forward-Only Rules
- Do not add legacy fallbacks unless explicitly requested.
- Do not add anti-legacy policing logic unless explicitly requested.
- Do not keep dead compatibility code "just in case".
- When architecture changes, remove obsolete paths.
- When modules are replaced, remove old tests for removed modules.
- Prefer direct target-state code over migration scaffolding.
- If migration glue is unavoidable, mark it temporary and remove quickly.
- Spec-first changes must ship with reality-aligned code.

### Policy Activation Rules
- `policy_state` is the single source for enabled/disabled state.
- Policy descriptors may still carry default `enabled` for seeding.
- Refresh rewrites full alphabetical `policy_state` map.
- Existing user boolean values are preserved on refresh.
- New policy IDs are seeded from resolved defaults.
- Stale policy IDs are removed during materialization.
- Profiles must not be used as policy toggles.
- Policy replacements migrate `policy_state` keys during `upgrade`.
- Replacement migration skips keys that have custom policy overrides.

### Profile Contract Rules
- Core/custom origin is inferred by path location.
- No dedicated `custom` type key is needed.
- Profiles are explicit; no inheritance machinery in this pass.
- Profile manifests define metadata overlays only.
- Profile manifests define assets only.
- Profile manifests define hook fragments only.
- Profile manifests define selection metadata only.
- Keep manifest shape deterministic and readable.

### Translator Contract Rules
- Translators are declared by language profiles.
- Translator declarations live in profile YAML.
- Translator declaration fields: `id`, `extensions`, `can_handle`, `translate`.
- `extensions` are normalized to lowercase dotted values.
- `can_handle` must define strategy and entrypoint.
- `translate` must define strategy and entrypoint.
- Non-language profiles must not declare translators.
- Routing is resolved from active language declarations.
- No per-policy extension-to-adapter hardcoding in target architecture.

### Runtime Parsing Rules
- Runtime policy parsing reads AGENTS policy block.
- Parser must stay scoped to managed policy markers.
- Avoid reading policy-like text outside managed block.
- Keep parser behavior deterministic across runs.
- Keep parser behavior independent of formatting noise.

### Refresh and Registry Rules
- Full refresh is expected in check/deploy/upgrade/refresh workflows.
- Refresh regenerates local policy/profile registries.
- Refresh syncs managed docs and managed blocks.
- Refresh updates generated config sections.
- User-configurable settings should remain preserved.
- Generated config sections should be clearly separated.
- Refresh output should be informative, not ambiguous.

### Managed Docs Rules
- Managed markers are generated, not copied from body prose.
- Editable content outside managed blocks is preserved.
- Managed block content should be deterministic.
- AGENTS has special policy block semantics.
- Keep workflow guidance consistent with actual command behavior.
- Keep document headers and metadata coherent.

### CLI and Lifecycle Rules
- CLI-exposed scripts stay on package root.
- Root command scripts are real scripts, not shims.
- Helper/library code belongs under `devcovenant/core`.
- Avoid duplicate command logic across modules.
- Keep command contracts minimal and explicit.
- `check` supports `--nofix`, `--norefresh`.
- `gate` supports `--start`, `--end`.
- Unneeded flags are removed when they create drift.

### Testing Rules
- Tests validate current behavior, not retired behavior.
- If module changes, matching tests must be updated.
- If module is removed, matching tests must be removed.
- Python tests should be `unittest` style.
- Pytest remains execution layer in test command.
- Tests tree mirrors intended structure contracts.
- Avoid stale placeholder tests where real coverage is expected.

### Drift Never-Do-Agains
- Never reintroduce stock-policy-text restore infrastructure.
- Never reintroduce reset-to-stock lifecycle paths.
- Never hardcode profile activation in profile manifests.
- Never hardcode path logic when metadata is the contract.
- Never keep duplicate modules with near-identical purpose.
- Never split one responsibility into random tiny sprawl files.
- Never patch over architecture issues with temporary shims.
- Never let PLAN say done while reality is not done.

### Operational Discipline
- Before edits: run `python3 -m devcovenant gate --start`.
- After edits: run `python3 -m devcovenant test`.
- Finalize: run `python3 -m devcovenant gate --end`.
- Every substantive change gets CHANGELOG coverage.
- Keep file lists in changelog accurate.
- Consult SPEC before implementing PLAN items.
- Update PLAN status as work is completed.
- Stage all changes after each completed work slice.

### Near-Term Backlog Memory
- Item 4 translator schema: completed.
- Item 5 centralized translator runtime: next major step.
- Item 6 shared `LanguageUnit`: required for policy migration.
- Item 7 migrate language-aware policies to shared runtime.
- Item 8 pre-commit ownership cleanup by profile.
- Item 9 Tier C registry/state contract tests: completed.
- Item 10 core responsibility consolidation and parser fold: completed.
- Item 11 SPEC-vs-reality closure audit: next.
- Item 12 final SPEC-vs-reality closure audit.
- 2026-02-14: Added Tier C contract tests for policy/profile registry schema,
  registry synchronization invariants, and gate/test-status payload schema.
- 2026-02-14: Folded AGENTS policy parsing into `policy_runtime.py` and
  removed standalone `core/parser.py` plus stale mirrored parser tests.
- 2026-02-13: Workflow split is now explicit: `gate` owns start/end
  pre-commit orchestration, while `check` owns policy evaluation and may
  skip startup refresh via `--norefresh` when explicitly requested.

### Self-Checks Before Claiming Completion
- Does behavior match SPEC text exactly?
- Is old logic removed instead of hidden?
- Are tests aligned with new behavior?
- Is changelog entry complete and specific?
- Is PLAN item status updated?
- Is AGENTS notepad updated with key lessons?
- Are there any unexplained generated artifacts?
- Is the worktree staged for user-controlled commit/push?

<!-- DEVCOV-WORKFLOW:BEGIN -->
## THE DEV COVENANT

- We are human and AI developers working on this project together.
- We obey every AGENTS.md and DevCovenant instruction.
- We maintain clean repository hygiene and avoid unmanaged drift.
- We never edit content inside managed `<!-- DEVCOV* -->` blocks.

## Obligatory Workflow
Run DevCovenant gates in this sequence for repository edits:
1. `python3 -m devcovenant gate --start`
2. `python3 -m devcovenant test`
3. `python3 -m devcovenant gate --end`

## Managed Environment
If a managed environment is configured, run DevCovenant from that environment.
Start required services before the test gate so runtime checks execute against
the active stack.

## Table of Contents
1. [Overview](#overview)
2. [Program Overview](#program-overview)
3. [Workflow](#workflow)
4. [Policy Management and Enforcement](#policy-management-and-enforcement)

## Overview
DevCovenant converts policy prose into executable checks. This file is the
canonical policy source and operational guide for the repository.

## Program Overview
The engine loads core policies from `devcovenant/core/policies/<policy>` and
optional overrides from `devcovenant/custom/policies/<policy>`. Profiles
provide metadata and selectors that shape enforcement behavior.

## Workflow
- Run `devcovenant gate --start`, apply edits, run tests, and finish with
  `devcovenant gate --end`.
- After policy-text changes, run `devcovenant refresh`.
- Log every change in `CHANGELOG.md` under the current version entry.

## Policy Management and Enforcement
The policy block below is generated by DevCovenant from policy descriptors and
runtime metadata resolution.
<!-- DEVCOV-WORKFLOW:END -->

<!-- DEVCOV-POLICIES:BEGIN -->
## Policy: Changelog Coverage

```policy-def
id: changelog-coverage
severity: error
auto_fix: true
enforcement: active
enabled: true
custom: false
main_changelog: CHANGELOG.md
skipped_files: CHANGELOG.md
  .gitignore
  .pre-commit-config.yaml
skipped_globs:
skipped_prefixes:
managed_docs: AGENTS.md
  README.md
  CONTRIBUTING.md
  SPEC.md
  PLAN.md
  CHANGELOG.md
  devcovenant/README.md
summary_labels: Change
  Why
  Impact
summary_verbs: add
  added
  adjust
  adjusted
  align
  aligned
  amend
  amended
  automate
  automated
  build
  built
  bump
  bumped
  clean
  cleaned
  clarify
  clarified
  consolidate
  consolidated
  correct
  corrected
  create
  created
  define
  defined
  deprecate
  deprecated
  document
  documented
  drop
  dropped
  enable
  enabled
  expand
  expanded
  fix
  fixed
  harden
  hardened
  improve
  improved
  introduce
  introduced
  migrate
  migrated
  normalize
  normalized
  refactor
  refactored
  remove
  removed
  rename
  renamed
  replace
  replaced
  restructure
  restructured
  revise
  revised
  streamline
  streamlined
  support
  supported
  update
  updated
  upgrade
  upgraded
  wrap
  wrapped
collections: __none__
required_globs: README.md
  AGENTS.md
  CONTRIBUTING.md
  CHANGELOG.md
  SPEC.md
  PLAN.md
selector_roles: skipped
  required
skipped_dirs:
required_files:
required_dirs:
```

Every change must be logged in a new changelog entry dated today, under the
current version, with a three-line summary labeled Change/Why/Impact. Each
summary line must include an action verb listed in the summary_verbs
metadata and a Files block that lists only the touched paths for this
change. Collection prefixes (when enabled) must be logged in their own
changelog; prefixed files may not appear in the root changelog. This keeps
release notes daily, file-complete, and traceable.


---

## Policy: Dependency License Sync

```policy-def
id: dependency-license-sync
severity: error
auto_fix: true
enforcement: active
enabled: true
custom: false
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

Maintain the third-party license table alongside the dependency manifests
configured by the active profiles or config overrides. The policy points
reviewers to the `licenses/` directory and its `## License Report` section so
every dependency change touches both the license text and the cited manifest.


---

## Policy: Devcov Integrity Guard

```policy-def
id: devcov-integrity-guard
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: false
policy_definitions: AGENTS.md
registry_file: devcovenant/registry/local/policy_registry.yaml
test_status_file: devcovenant/registry/local/test_status.json
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
stay synchronized, and test-status metadata must validate when configured.


---

## Policy: Devcov Raw String Escapes

```policy-def
id: devcov-raw-string-escapes
severity: warning
auto_fix: false
enforcement: active
enabled: true
custom: true
```

Warn when DevCovenant repo Python strings contain bare backslashes.
This repo-only policy keeps the raw-string guidance active without
forcing it on user repos.


---

## Policy: Devcov Structure Guard

```policy-def
id: devcov-structure-guard
severity: error
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
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: false
test_status_file: devcovenant/registry/local/test_status.json
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
severity: info
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
  .md
  .rst
  .txt
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
  *.md
  *.rst
  *.txt
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
  devcovenant/docs/README.md
  devcovenant/docs/installation.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/policies.md
  devcovenant/docs/adapters.md
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
  devcovenant/docs/README.md
  devcovenant/docs/installation.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/policies.md
  devcovenant/docs/adapters.md
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
  devcovenant/README.md
  devcovenant/core/profiles/global/assets/*.yaml
allowed_files:
allowed_suffixes:
required_files:
required_globs: devcovenant/README.md
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
recency. The auto-fix updates the UTC date for touched allowlisted docs
while respecting allowed locations.


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
include_suffixes: .md
  .rst
  .txt
  .py
exclude_prefixes: build
  dist
  node_modules
exclude_globs: devcovenant/core/profiles/global/assets/*.yaml
  devcovenant/registry/**
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
enabled: true
custom: true
```

Ensure AGENTS.md, README.md, PLAN.md, SPEC.md, CHANGELOG.md, and
CONTRIBUTING.md remain the authoritative sources for their managed-block
descriptors under `devcovenant/core/profiles/global/assets/` so documentation
generation is deterministic.


---

## Policy: Managed Environment

```policy-def
id: managed-environment
severity: error
auto_fix: false
enforcement: active
enabled: false
custom: false
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
exclude_globs: build/**
  dist/**
  node_modules/**
  tests/**
watch_dirs: tests
tests_watch_dirs: tests
mirror_roots: devcovenant=>tests/devcovenant
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

In-scope non-test modules must have corresponding tests under configured
test roots. The rule is metadata-driven and supports mirror enforcement for
selected source roots. Tests are current-behavior artifacts: when modules
change, corresponding tests must be updated, and when modules are removed,
corresponding tests must be removed as well. Python test files must use
unittest.TestCase-style definitions; pytest still runs as an execution
layer.


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

## Policy: No Spaghetti

```policy-def
id: no-spaghetti
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: true
include_globs: devcovenant/core/*.py
exclude_globs: devcovenant/core/__init__.py
max_top_level_modules: 19
min_module_lines: 120
selector_roles: include
  exclude
include_files:
include_dirs:
exclude_files:
exclude_dirs:
```

Prevent core spaghetti drift by freezing the top-level module count and
rejecting tiny top-level core modules.


---

## Policy: Raw String Escapes

```policy-def
id: raw-string-escapes
severity: warning
auto_fix: false
enforcement: active
enabled: false
custom: false
```

Policy description pending.


---

## Policy: Read Only Directories

```policy-def
id: read-only-directories
severity: error
auto_fix: false
enforcement: active
enabled: true
custom: false
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
enabled: true
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
scope. The policy ships disabled (`enabled: false`) and should only be
enabled for release processes that enforce SemVer discipline.


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

All version-bearing files must match the canonical version file (default
`VERSION` or a configured override), and version bumps must move forward.
Files listed under `optional_files` are only enforced when present. The
policy also flags hard-coded runtime versions and ensures changelog
releases reflect the current version.
<!-- DEVCOV-POLICIES:END -->
