# DevCovenant Development Guide
**Last Updated:** 2026-01-11
**Version:** 0.1.1

# Message from Human, do not edit:
Read `DEVCOVENANT.md` first for architecture and workflow. This file is the
canonical policy source of truth.
#

Edit and write here.

# DO NOT EDIT FROM HERE TO END UNLESS EXPLICITLY REQUESTED BY A HUMAN!

# DEVELOPMENT POLICY (DevCovenant and Laws)

**IMPORTANT: READ FROM HERE TO THE END OF THE DOCUMENT AT THE BEGINNING OF
EVERY DEVELOPMENT SESSION**

DevCovenant is self-enforcing. Use this workflow:
- `python tools/run_pre_commit.py --phase start`
- `python tools/run_tests.py`
- `python tools/run_pre_commit.py --phase end`

When policy blocks change, set `updated: true`, run
`python devcovenant/update_hashes.py`, then reset the flag to `false`.

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
waiver: false
policy_definitions: AGENTS.md
registry_file: devcovenant/registry.json
```

DevCovenant must keep its registry synchronized with policy definitions.

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
waiver: false
status_file: devcovenant/test_status.json
required_commands: pre-commit run --all-files,pytest
  python -m unittest discover
code_extensions: .py,.md,.rst,.txt,.yml,.yaml,.json,.toml,.cff
require_pre_commit_start: true
require_pre_commit_end: true
pre_commit_command: pre-commit run --all-files
pre_commit_start_epoch_key: pre_commit_start_epoch
pre_commit_end_epoch_key: pre_commit_end_epoch
pre_commit_start_command_key: pre_commit_start_command
pre_commit_end_command_key: pre_commit_end_command
```

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
waiver: false
main_changelog: CHANGELOG.md
skipped_files: CHANGELOG.md,.gitignore,.pre-commit-config.yaml
collections: __none__
```

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
waiver: false
version_file: VERSION
readme_files: README.md,AGENTS.md,DEVCOVENANT.md,CONTRIBUTING.md,PLAN.md
  devcovenant/README.md,devcovenant/waivers/README.md
citation_file: CITATION.cff
pyproject_files: pyproject.toml
license_files: LICENSE
runtime_entrypoints: __none__
runtime_roots: __none__
changelog_file: CHANGELOG.md
changelog_header_prefix: ## Version
```

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
waiver: false
include_suffixes: .md
allowed_globs: README.md,AGENTS.md,DEVCOVENANT.md,CONTRIBUTING.md,PLAN.md
  devcovenant/README.md,devcovenant/waivers/README.md
```

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
waiver: false
max_length: 79
include_suffixes: .py,.md,.rst,.txt,.yml,.yaml,.json,.toml,.cff
exclude_prefixes: build,dist,node_modules
exclude_globs: CHANGELOG.md,devcovenant/registry.json
```

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
waiver: false
include_suffixes: .py
exclude_prefixes: build,dist,node_modules
```

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
waiver: false
exclude_prefixes: build,dist,node_modules
```

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
waiver: false
include_suffixes: .py
include_prefixes: devcovenant
exclude_prefixes: build,dist,node_modules,tests,devcovenant/tests
exclude_globs: devcovenant_check.py
watch_dirs: tests,devcovenant/tests
```

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
waiver: false
include_prefixes: devcovenant,tools
exclude_prefixes: devcovenant/tests
user_visible_files: README.md,DEVCOVENANT.md,CONTRIBUTING.md,AGENTS.md
  PLAN.md,devcovenant/README.md
```

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
waiver: false
include_globs: __none__
```

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
waiver: false
```

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
waiver: false
```
