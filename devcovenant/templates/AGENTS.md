# DevCovenant Development Guide
<!-- DEVCOV:BEGIN -->
# Message from Human, do not edit:

Read `DEVCOVENANT.md` first for architecture and workflow. This file is the
canonical policy source of truth.

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
## Table of Contents
1. [Overview](#overview)
2. [Program Overview](#program-overview)
3. [Install and First-Run Guidance](#install-and-first-run-guidance)
4. [Severity Baseline](#severity-baseline)
5. [Editable Notes](#editable-notes-record-decisions-here)
6. [Workflow](#workflow)
7. [Installer Behavior Reference](#installer-behavior-reference)
8. [Development Policy](#development-policy-devcovenant-and-laws)

## Overview
This document is the single source of truth for DevCovenant policy. Every
rule that the engine enforces is written here in plain language with a
structured policy block beneath it.

## Program Overview
DevCovenant is a policy engine that binds documentation to enforcement. The
parser reads policy blocks, the registry stores hashes, and the engine runs
policy scripts while the CLI coordinates checks and fixes. Policies are
implemented in three layers: built-in scripts in
`devcovenant/core/policy_scripts` (with built-in fixers in
`devcovenant/core/fixers`), repo-specific scripts in
`devcovenant/custom/policy_scripts`, and patch scripts in
`devcovenant/common_policy_patches` (Python preferred; JSON/YAML supported).

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
Use the Install Behavior Cheat Sheet in `README.md` and the full
details in `devcovenant/README.md` when preparing new repos or
upgrades. Key defaults:
- `AGENTS.md` is replaced by the template; editable notes are
  preserved under `# EDITABLE SECTION`.
- `README.md` is preserved, headers refreshed, and the managed block
  inserted when required sections are missing.
- `DEVCOVENANT.md`, `CHANGELOG.md`, and `CONTRIBUTING.md` are backed
  up to `*_old.*` and replaced by the standard templates.
- `SPEC.md` and `PLAN.md` keep content with updated headers, or are
  created if missing.
- `.gitignore` is regenerated and merges user entries under a
  preserved block.
## Release Readiness Review
- Confirm the gate sequence (pre-commit start → tests → pre-commit end)
  runs cleanly whenever changes touch docs, policies, or code. The updated
  `devflow-run-gates` policy will catch any skipped steps.
- Whenever dependency manifests change, update `THIRD_PARTY_LICENSES.md`,
  refresh the `licenses/` directory, and confirm the dependency-license-sync
  policy reports no violations before tagging a release. The policy looks for a
  `## License Report` section that mentions every touched manifest.
- The changelog must record every touched file, and
  `devcovenant/registry.json` must be refreshed via
  `devcovenant update-hashes` before tagging a release.
- Build artifacts locally (`python -m build`, `twine check dist/*`) and verify
  the `publish.yml` workflow publishes using the `PYPI_API_TOKEN` secret before
  pushing the release tag.

# DO NOT EDIT FROM HERE TO END UNLESS EXPLICITLY REQUESTED BY A HUMAN!

# DEV(COVENANT) DEVELOPMENT POLICY MANAGEMENT AND ENFORCEMENT

**IMPORTANT: READ FROM HERE TO THE END OF THE DOCUMENT AT THE BEGINNING OF
EVERY DEVELOPMENT SESSION**

**Workflow primer**
- Start each session with `python3 tools/run_pre_commit.py --phase start`.
- Run `python3 tools/run_tests.py` after work concludes.
- Finish with `python3 tools/run_pre_commit.py --phase end`.
- Updating policy text? Set `updated: true`, sync hashes via
  `devcovenant update-hashes`, then reset the flag.
- Treat this gate sequence as obligatory for every repo change, even doc-only
  edits; if no tests exist, run the script that would normally cover them and
  note that in the session checklist.

**Session checklist**
- Document decisions inside the editable section above `<!-- DEVCOV:BEGIN -->`.
- Keep `AGENTS.md` as the canonical policy source and link to it from derived
  docs.
- Preserve human-authored prose around the managed blocks; only edit automation
  guidance through the installer or the CLI.
- All policy changes must have matching script/test updates before the commit.

**DevCovenant sessions**
- AI agents run `python3 devcov_check.py check --mode startup` at session start
  to detect policy-text drift and sync issues. Fix them before doing any other
  work.
- Developers revisit this section after receiving sync issues or policy
  warnings so the workflow remains consistent across repos.

**Standard commands**
Use `python3 -m devcovenant` if the `devcovenant` console script is not on
your PATH.
- `devcovenant check` – full validation.
- `devcovenant check --mode pre-commit`.
- `devcovenant check --fix` when auto-fixes are available.
- `devcovenant install --target <repo>` installs DevCovenant.
- `devcovenant uninstall --target <repo>`.
- `devcovenant restore-stock-text --policy <id>` when policy
  prose diverges from code.

**DevCovenant enforcement**
1. Policies defined here are parsed by `devcovenant/core/parser.py` and hashed
   into `devcovenant/registry.json`.
2. `devcovenant/core/engine.py` runs the checks and auto-fixers.
3. `devcovenant/core/fixers/` hosts auto-fix logic for built-in policies.
   Legacy imports can continue using the compatibility wrappers there.
   Repo-specific fixers may live under `devcovenant/custom/fixers`.
4. Built-in policies live in `devcovenant/core/policy_scripts/`.
   Custom policies go in `devcovenant/custom/policy_scripts/`, and patches
   live under `devcovenant/common_policy_patches/`.

**Sync expectations**
- When a policy block changes, DevCovenant highlights the diff and records an
  `updated: true` status. Update the corresponding script/test before resetting
  the flag.
- The `policy-text-presence` policy enforces that every policy block includes
  descriptive prose immediately after the metadata.
- The `stock-policy-text-sync` reminder prevents drifting from the canonical
  wording located in `devcovenant/core/stock_policy_texts.json`.

**Documentation blocks**
- Managed sections are wrapped with
  `<!-- DEVCOV:BEGIN -->` / `<!-- DEVCOV:END -->`.
- Install/update/uninstall scripts inject those blocks while leaving other
  content untouched.
- Policy reminders (e.g., `documentation-growth-tracking`,
  `policy-text-presence`, `last-updated-placement`) point authors back to
  these blocks whenever updates are required.

---

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
policy_definitions: AGENTS.md
registry_file: devcovenant/registry.json
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
policy_definitions: AGENTS.md
stock_texts_file: devcovenant/core/stock_policy_texts.json
```

If a built-in policy text is edited from its stock wording, DevCovenant must
raise a warning and instruct the agent to either restore the stock text or
patch the policy implementation to match the new meaning.

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
status_file: devcovenant/test_status.json
required_commands: pytest
  python -m unittest discover
require_pre_commit_start: true
require_pre_commit_end: true
pre_commit_command: pre-commit run --all-files
pre_commit_start_epoch_key: pre_commit_start_epoch
pre_commit_end_epoch_key: pre_commit_end_epoch
pre_commit_start_command_key: pre_commit_start_command
pre_commit_end_command_key: pre_commit_end_command
```

DevCovenant must record and enforce the standard workflow: pre-commit start,
tests, then pre-commit end. The policy reads the status file to ensure each
gate ran and that no required command was skipped.
This check is enforced for every repository change (including
documentation-only updates) so the gate sequence cannot be skipped.

---

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
version_file: VERSION
readme_files: README.md,AGENTS.md,DEVCOVENANT.md,CONTRIBUTING.md,SPEC.md
  PLAN.md
  devcovenant/README.md
  devcovenant/common_policy_patches/README.md
  devcovenant/custom/policy_scripts/README.md
citation_file: CITATION.cff
pyproject_files: pyproject.toml
license_files: LICENSE
runtime_entrypoints: __none__
runtime_roots: __none__
changelog_file: CHANGELOG.md
changelog_header_prefix: ## Version
```

All version-bearing files must match the canonical `VERSION` value, and
version bumps must move forward. The policy also flags hard-coded runtime
versions and ensures changelog releases reflect the current version.

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
include_suffixes: .md
allowed_globs: README.md,AGENTS.md,DEVCOVENANT.md,CONTRIBUTING.md,SPEC.md
  PLAN.md
  devcovenant/README.md
  devcovenant/common_policy_patches/README.md
  devcovenant/custom/policy_scripts/README.md
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
max_length: 79
include_suffixes: .py,.md,.rst,.txt,.yml,.yaml,.json,.toml,.cff
exclude_prefixes: build,dist,node_modules
exclude_globs: CHANGELOG.md,devcovenant/registry.json
  devcovenant/core/stock_policy_texts.json
  tools/templates/LICENSE_GPL-3.0.txt
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
include_suffixes: .py
exclude_prefixes: build,dist,node_modules
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
exclude_prefixes: build,dist,node_modules
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
include_suffixes: .py
include_prefixes: devcovenant
exclude_prefixes: build,dist,node_modules,tests,devcovenant/core/tests
exclude_globs: devcov_check.py
watch_dirs: tests,devcovenant/core/tests
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
include_prefixes: devcovenant,tools,.github
exclude_prefixes: devcovenant/core/tests
user_facing_prefixes: devcovenant,tools,.github
user_facing_exclude_prefixes: devcovenant/core/tests,tests
user_facing_suffixes: .py,.js,.ts,.tsx,.vue,.go,.rs,.java,.kt,.swift,.rb
  .php,.cs,.yml,.yaml,.json,.toml
user_facing_files: devcov_check.py,.pre-commit-config.yaml,pyproject.toml
user_facing_globs: .github/workflows/*.yml,.github/workflows/*.yaml
user_facing_keywords: api,endpoint,endpoints,route,routes,routing,service
  services,controller,controllers,handler,handlers,client,clients,webhook
  webhooks,integration,integrations,sdk,cli,ui,view,views,page,pages,screen
  screens,form,forms,workflow,workflows
user_visible_files: README.md,DEVCOVENANT.md,CONTRIBUTING.md,AGENTS.md
  SPEC.md,PLAN.md,devcovenant/README.md
  devcovenant/common_policy_patches/README.md
  devcovenant/custom/policy_scripts/README.md
doc_quality_files: README.md,DEVCOVENANT.md,CONTRIBUTING.md,AGENTS.md
  SPEC.md,PLAN.md,devcovenant/README.md
  devcovenant/common_policy_patches/README.md
  devcovenant/custom/policy_scripts/README.md
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
include_globs: __none__
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
```

Scan Python files for risky constructs like `eval`, `exec`, or `shell=True`.
Use the documented allow-comment only when a security review approves the
exception.

---

<!-- DEVCOV:END -->
