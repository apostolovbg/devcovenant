# DevCovenant (Repository Guide)
**Last Updated:** 2026-01-24
**Version:** 0.2.6

**DevCovenant Version:** 0.2.6
**Status:** Active Development
**License:** DevCovenant License v1.0

<!-- DEVCOV:BEGIN -->
**Doc ID:** DEVCOVENANT-README
**Doc Type:** devcovenant-guide
**Managed By:** DevCovenant
<!-- DEVCOV:END -->

This file is installed into a target repository at `devcovenant/README.md`.
It explains how to use DevCovenant inside that repo. The root `README.md`
should remain dedicated to the repository's actual project.

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Workflow](#workflow)
4. [CLI Entry Points](#cli-entry-points)
5. [CLI Command Reference](#cli-command-reference)
6. [Install Modes and Options](#install-modes-and-options)
7. [Install Behavior Reference](#install-behavior-reference)
8. [Installer Behavior (File by File)](#installer-behavior-file-by-file)
9. [Install Manifest](#install-manifest)
10. [Managed Documentation Blocks](#managed-documentation-blocks)
11. [Editable Notes in AGENTS](#editable-notes-in-agents)
12. [Core Exclusion and Config](#core-exclusion-and-config)
13. [Language Profiles](#language-profiles)
14. [Check Modes and Exit Codes](#check-modes-and-exit-codes)
15. [Auto-Fix Behavior](#auto-fix-behavior)
16. [Policy Registry and Stock Text](#policy-registry-and-stock-text)
17. [Policy Scripts and Fixers](#policy-scripts-and-fixers)
18. [Core Policy Guide](#core-policy-guide)
19. [DevFlow Gates and Test Status](#devflow-gates-and-test-status)
20. [Dependency and License Tracking](#dependency-and-license-tracking)
21. [Templates and Packaging](#templates-and-packaging)
22. [Uninstall Behavior](#uninstall-behavior)
23. [CI and Automation](#ci-and-automation)
24. [Troubleshooting](#troubleshooting)

## Overview
DevCovenant enforces the policies written in `AGENTS.md`. It parses those
policies, validates them against their scripts, and reports violations with
clear severity levels. The system is designed to keep policy text,
enforcement logic, and documentation synchronized.

## Quick Start
If DevCovenant is installed, start with (use `python3` unless `python`
already points to Python 3):
```bash
pip install devcovenant

devcovenant install --target .

python3 tools/run_pre_commit.py --phase start
python3 tools/run_tests.py
python3 tools/run_pre_commit.py --phase end
```

If you built DevCovenant locally, `pip install dist/devcovenant-*` before
running `devcovenant install --target .` so the wheel files are reused.

## Workflow
DevCovenant requires the gated workflow for every change, including
documentation updates:
1. `python3 tools/run_pre_commit.py --phase start`
2. `python3 tools/run_tests.py`
3. `python3 tools/run_pre_commit.py --phase end`

When policy text changes, set `updated: true`, update scripts/tests, run
`devcovenant update-hashes`, then reset the flag.

## CLI Entry Points
DevCovenant ships both a console script and a module entry:
```bash
devcovenant --help
python3 -m devcovenant --help
```

Use the module entry if the console script is not on your PATH.

## CLI Command Reference
The primary commands are:
- `devcovenant check` (default enforcement)
- `devcovenant check --mode startup|lint|pre-commit|normal`
- `devcovenant check --fix` (apply auto-fixes when allowed)
- `devcovenant sync` (startup sync check)
- `devcovenant test` (runs `pytest devcovenant/core/tests/`)
- `devcovenant update-hashes` (refresh `devcovenant/registry/registry.json`)
- `devcovenant normalize-metadata` (insert missing metadata keys)
- `devcovenant restore-stock-text --policy <id>`
- `devcovenant restore-stock-text --all`
- `devcovenant install --target <path>`
- `devcovenant update --target <path>`
- `devcovenant uninstall --target <path>`

Normalize-metadata uses `devcovenant/core/templates/global/AGENTS.md`
as the schema.
Empty metadata values (blank strings or empty lists) are treated as unset,
so defaults still apply. Use `--schema` to point at a different AGENTS file
and `--no-set-updated` to avoid flipping `updated: true` on changed policy
blocks.

Selector roles
--------------
Policies can declare `selector_roles` to enable standardized selector
triplets. Each role name produces `role_globs`, `role_files`, and
`role_dirs` metadata keys. Custom role names are allowed and interpreted
by the policy script. Normalization infers roles from legacy selector
keys (for example, `include_suffixes` or `guarded_paths`) and inserts
the triplets without overwriting existing values.
Documentation-growth-tracking defaults to the roles `user_facing`,
`user_visible`, and `doc_quality`, with legacy selector keys mapped into
role triplets during normalization.

The `tools/*.py` scripts support the repo workflow (pre-commit/test gates).

## Install Modes and Options
Install is for new repos. Use `devcovenant update` to refresh existing
installs. Install supports:
- `--mode auto`: infer new vs. existing and refuse if already installed
  unless you approve auto-uninstall.
- `--mode empty`: treat the repo as new.
- `--mode existing`: reserved for update flows.

Docs, config, and metadata handling defaults are derived from the mode.
Use `devcovenant update` when DevCovenant is already installed.
- `--docs-mode preserve|overwrite`
- `--config-mode preserve|overwrite`
- `--metadata-mode preserve|overwrite|skip`

Updates default to preserve docs/config/metadata, append missing policies,
and run metadata normalization.
- `--policy-mode preserve|append-missing|overwrite`

Targeted overrides:
- `--license-mode inherit|preserve|overwrite|skip`
- `--version-mode inherit|preserve|overwrite|skip`
- `--pyproject-mode inherit|preserve|overwrite|skip`
- `--ci-mode inherit|preserve|overwrite|skip`
- `--docs-include README,AGENTS,...` (limit overwrites to named docs)
- `--docs-exclude CONTRIBUTING,...` (omit docs from overwrite targets)
- `--include-spec` / `--include-plan` (create optional SPEC/PLAN docs)
- `--preserve-custom` / `--no-preserve-custom`
- `--force-docs` / `--force-config`
- `--disable-policy id1,id2` to set `apply: false` on listed policies.
- `--auto-uninstall` to uninstall when existing artifacts are detected.
- `--version <x.x|x.x.x>` to set the initial VERSION (defaults to 0.0.1
  when no VERSION/pyproject version is found and prompting is skipped).
Doc selectors use extension-less names like `README` or `AGENTS`.

## Install Behavior Reference
The installer keeps repo content intact by default and only
overwrites when explicitly instructed. Summary:
- `AGENTS.md`: replaced by template; editable notes preserved.
- `README.md`: content preserved; headers refreshed; managed block added.
- `CHANGELOG.md` / `CONTRIBUTING.md`: always replaced on install with
  `*_old.md` backups; updates only refresh managed blocks.
- `SPEC.md` / `PLAN.md`: optional; created only with `--include-spec` or
  `--include-plan`, otherwise preserved if they already exist.
- `.gitignore`: regenerated from global, profile, and OS fragments,
  then merged with a preserved user block.
- Config files: preserved unless `--config-mode overwrite` (or forced).

## Installer Behavior (File by File)
Install targets new repositories. Use `devcovenant update` for existing
repos; it preserves content by default and refreshes managed blocks.

- `devcovenant/`: core engine always installs; `custom/` scripts and fixers
  are preserved by default on updates.
- `tools/run_pre_commit.py`, `tools/run_tests.py`,
  `tools/update_test_status.py`: always overwritten from the package.
- `.pre-commit-config.yaml`, `.github/workflows/ci.yml`: preserved when
  `--config-mode preserve`, otherwise overwritten. Use `--ci-mode skip` to
  skip CI installs.
- `.gitignore`: regenerated from global, profile, and OS fragments,
  then merged with existing user entries under a preserved block.
- `AGENTS.md`: always replaced by the template. If an existing file is found,
  the editable section content is preserved under `# EDITABLE SECTION`.
- `README.md`: existing content is preserved, headers are refreshed, and the
  managed block is inserted to add missing sections.
- `SPEC.md`, `PLAN.md`: optional; existing content is preserved while
  headers refresh. Use `--include-spec` / `--include-plan` to create
  them when missing.
- `CHANGELOG.md`, `CONTRIBUTING.md`: always replaced on install with
  `*_old.md` backups; updates only refresh managed blocks.
- `--docs-include` / `--docs-exclude` limit overwrites for other docs;
  they do not bypass the install defaults for CHANGELOG/CONTRIBUTING.
- `VERSION`: created on demand. The installer prefers an existing VERSION,
  otherwise falls back to a version found in `pyproject.toml`, otherwise
  prompts. If prompting is skipped, it defaults to `0.0.1`. The `--version`
  flag overrides detection and accepts `x.x` or `x.x.x` (normalized to
  `x.x.0`).
- `LICENSE`: created from the GPL-3.0 template if missing. Overwritten only
  when the license mode requests it, and the original is backed up first.
- `pyproject.toml`: preserved or overwritten based on `--pyproject-mode`.
- `devcovenant/registry/manifest.json`: always written or refreshed by install,
  update, or first-run checks.

All `Last Updated` headers are stamped with the UTC install date.

Any file that is overwritten or merged during install is backed up
as `*_old.*`, and the installer prints the backup list at the end.

## Install Manifest
The installer writes `devcovenant/registry/manifest.json` with:
- `schema_version`: manifest schema version.
- `updated_at`: ISO timestamp in UTC.
- `mode`: `install` or `update`.
- `core`: required core directories and files.
- `docs`: doc paths grouped by type (`core`, `optional`, `custom`).
- `custom`: allowed user-writable paths (`devcovenant/custom/**`).
- `generated`: generated files such as registries or test status.
- `profiles`: active profiles and the catalog snapshot recorded at install.
- `policy_assets`: policy-scoped asset mappings recorded by install or
  update for audit and cleanup. Profile assets are resolved from profile
  manifests under `templates/profiles/`.
- `installed`: lists of installed paths by group (`core`, `config`, `docs`).
- `doc_blocks`: list of docs that received managed blocks.
- `options`: resolved install options (docs/config/metadata modes, version,
  core inclusion, preservation flags, disabled policies, and auto-uninstall
  settings).

Use this file to audit what DevCovenant changed in the target repo. The
structure guard reads it to validate core layout and managed docs. If the
manifest is missing (manual migration), the first DevCovenant run creates
it automatically.

Manifest schema (summary):
```json
{
  "schema_version": 2,
  "updated_at": "2026-01-22T00:00:00Z",
  "mode": "install|update",
  "core": {
    "dirs": ["devcovenant/core"],
    "files": ["devcovenant/cli.py"]
  },
  "docs": {
    "core": ["AGENTS.md"],
    "optional": ["SPEC.md"],
    "custom": []
  },
  "custom": {
    "dirs": ["devcovenant/custom"],
    "files": []
  },
  "generated": {
    "dirs": [],
    "files": ["devcovenant/registry/registry.json"]
  },
  "profiles": {
    "active": [],
    "catalog": []
  },
  "policy_assets": {
    "global": [],
    "policies": {}
  },
  "installed": {
    "core": [],
    "config": [],
    "docs": []
  },
  "doc_blocks": ["AGENTS.md"],
  "options": {
    "policy_mode": "append-missing",
    "disable_policies": [],
    "auto_uninstall": false
  }
}
```

## Managed Documentation Blocks
DevCovenant-managed blocks are wrapped as:
```
<!-- DEVCOV:BEGIN -->
**Doc ID:** README
**Doc Type:** repo-readme
**Managed By:** DevCovenant

... managed content ...
<!-- DEVCOV:END -->
```

## Policy Replacement Workflow
DevCovenant can retire core policies via the replacement map in
`devcovenant/registry/policy_replacements.yaml`. During `devcovenant update`:
- Enabled replaced policies (`apply: true`) are moved to
  `devcovenant/custom/`, marked `custom: true`, and flagged
  `status: deprecated`. Their last-known core scripts/fixers are
  copied into the custom folders.
- Disabled replaced policies are removed from `AGENTS.md` and any custom
  scripts/fixers for that policy are deleted.
- Newly added stock policies are appended (default update behavior) and
  reported in the update notices.

Update notices are printed to stdout and appended to
`devcovenant/registry/manifest.json` under `notifications`. Deprecated policies
are not enforced by default; set them back to `status: active` if you
need to keep enforcing legacy behavior.

Every managed doc receives a top-of-file block just below the standard header
lines (`Last Updated`, `Version`, and any additional header markers). The
installer inserts or replaces these blocks while leaving surrounding text
untouched. Policies like `documentation-growth-tracking` and
`policy-text-presence` depend on these markers, so do not edit them manually
outside of the DevCovenant workflow.

## Editable Notes in AGENTS
`AGENTS.md` contains a dedicated editable section, located just below the
first `<!-- DEVCOV:END -->` marker and labeled `# EDITABLE SECTION` when the
file is installed. The installer preserves any existing notes in that region
and reinserts them on subsequent installs. Use this area for repo-specific
working memory, decisions, and constraints.

## Core Exclusion and Config
User repos should keep DevCovenant core excluded from enforcement so updates
remain safe. The installer sets this automatically in
`devcovenant/config.yaml`:
```yaml
devcov_core_include: false
devcov_core_paths:
  - devcovenant/core
  - devcovenant/__init__.py
  - devcovenant/__main__.py
  - devcovenant/cli.py
  - tools/run_pre_commit.py
  - tools/run_tests.py
  - tools/update_test_status.py
```

Only the DevCovenant repo should set `devcov_core_include: true`.

### Config schema (profile-generated)
`devcovenant/config.yaml` is generated from global defaults plus the
active profiles. The installer writes `profiles.active` and a computed
`profiles.generated.file_suffixes` list so the config reflects the
active profile selection. Global sections provide knobs that apply to
every repo:

- `profiles`: active profiles and generated suffixes.
- `paths`: policy definitions, registry, manifest, template roots.
- `docs`: managed block markers and optional doc toggles.
- `install` / `update`: default behaviors for CLI commands.
- `engine`: scanning defaults, thresholds, and ignore dirs.
- `hooks`, `reporting`, `ignore`, `self_enforcement`: runtime toggles.
- `policies`: per-policy overrides (apply, severity, selectors).

When multiple profiles are active, the generated suffix list is the
union of each profile's catalog suffixes. Profile manifests can also
supply policy metadata overlays that are merged into `config.yaml`.

## Profiles and Scopes
DevCovenant uses install profiles to tailor policy applicability and assets.
Profiles are discovered from template folders and summarized in the generated
catalog at `devcovenant/registry/profile_catalog.yaml`. That catalog is
regenerated on install/update, so treat it as read-only output.

Each profile can ship a profile manifest at
`devcovenant/core/templates/profiles/<profile>/profile.yaml`. The manifest
lists profile assets and per-policy metadata overlays. Custom profile
manifests in `devcovenant/custom/templates/profiles/<profile>/profile.yaml`
override the core manifest when both exist. See the template indexes for
layout and examples:
- `devcovenant/core/templates/README.md`
- `devcovenant/core/templates/profiles/README.md`
- `devcovenant/core/templates/policies/README.md`

Install prompts for one or more active profiles and stores the selection in
`devcovenant/config.yaml` under `profiles.active`. Active profiles:
- extend `engine.file_suffixes` with catalog suffixes,
- gate policies via `profile_scopes` metadata,
- install profile assets declared in profile manifests,
- apply profile metadata overlays into `config.yaml`.

Example configuration:
```yaml
profiles:
  active:
    - python
    - docs
    - data
```

Mixed repos can list multiple profiles. Global policies set
`profile_scopes: global` and always apply, while profile-scoped policies
apply only when one of their scopes matches an active profile.

### Creating a custom profile (exhaustive)
Custom profiles are optional and live entirely inside the repo's
`devcovenant/custom/` tree. They let you ship profile-specific assets and
metadata without editing DevCovenant core.

1) Define the profile manifest:
`devcovenant/custom/templates/profiles/frappe/profile.yaml`
```yaml
version: 1
profile: frappe
category: framework
suffixes:
  - .py
  - .json
  - .js
assets:
  - path: requirements.in
    template: requirements.in
    mode: merge
policy_overlays:
  dependency-license-sync:
    dependency_files:
      - requirements.in
```

2) Add the templates themselves (including optional `.gitignore` fragments):
```
devcovenant/custom/templates/profiles/frappe/requirements.in
devcovenant/custom/templates/profiles/frappe/.gitignore
```

3) If a policy needs custom assets, add
`devcovenant/custom/templates/policies/<policy>/policy_assets.yaml` and any
referenced templates under the same policy folder.

4) Activate the profile in `devcovenant/config.yaml`:
```yaml
profiles:
  active:
    - frappe
    - docs
```

Notes:
- Template resolution always prefers custom templates over core templates.
- Profiles are additive: multiple active profiles can contribute assets and
  metadata overlays at once.
- `devcovenant/custom/templates/global/` exists to override global templates
  (for example, a repo-specific AGENTS.md or README.md). Use it when a repo
  needs to deviate from the stock global assets while still keeping updates.
## Check Modes and Exit Codes
Run checks through the CLI:
```bash
devcovenant check

devcovenant check --mode startup

devcovenant check --mode pre-commit
```

- `startup` is used at session start to detect drift early.
- `lint` focuses on faster checks and avoids heavy operations.
- `pre-commit` matches the gating workflow.
- `normal` is the default for full enforcement.

`check` exits non-zero if blocking violations or sync issues exist. Use
`devcovenant check --fix` to apply auto-fixes when available.

## Auto-Fix Behavior
Policies that declare `auto_fix: true` may include fixers. When `--fix` is
supplied, DevCovenant applies fixers in place and then reruns the checks.
Fixer logic lives under `devcovenant/core/fixers/`, and custom fixers can
live under `devcovenant/custom/fixers/`.

## Policy Registry and Stock Text
Policy definitions in `AGENTS.md` are hashed into
`devcovenant/registry/registry.json`. When policy text changes, set
`updated: true`, update scripts and tests, then run:
```bash
devcovenant update-hashes
```

Stock policy wording is stored in
`devcovenant/registry/stock_policy_texts.yaml`.
Restore it with:
```bash
devcovenant restore-stock-text --policy <id>
```

## Policy Scripts and Fixers
Policy scripts resolve in this order:
1. `devcovenant/custom/policy_scripts/`
2. `devcovenant/core/policy_scripts/`

Custom scripts fully replace the built-in policy. Built-in fixers live under
`devcovenant/core/fixers`, custom fixers live under
`devcovenant/custom/fixers`, and core fixers are skipped whenever a custom
policy override exists.

### Creating a custom policy (override or brand-new)
Custom policies are defined in `AGENTS.md` with `custom: true` and implemented
under `devcovenant/custom/`. Overrides replace core policies; brand-new
policies live only in custom.

1) Add the policy block to `AGENTS.md` (set `custom: true`):
```policy-def
id: my-policy
status: active
severity: warning
auto_fix: false
updated: false
apply: true
custom: true
```

2) Implement the checker:
```
devcovenant/custom/policy_scripts/my-policy.py
```

3) (Optional) add a fixer:
```
devcovenant/custom/fixers/my-policy.py
```

4) (Optional) attach assets with a per-policy manifest:
`devcovenant/custom/templates/policies/my-policy/policy_assets.yaml`
```yaml
assets:
  - path: docs/README.md
    template: README.md
    mode: replace
```

5) Provide the templates alongside the manifest:
```
devcovenant/custom/templates/policies/my-policy/README.md
```

Custom policy assets are applied only when the policy is active
(`apply: true`) and its `profile_scopes` intersect the active profiles.

## Core Policy Guide
DevCovenant ships a default policy set that enforces disciplined workflows
without requiring per-repo scripting. Each policy is metadata-driven in
`AGENTS.md` so repos can tune scope or disable a policy with `apply: false`.
The summary below explains intent, defaults, and impact.

### DevCovenant Self-Enforcement
Keeps `devcovenant/registry/registry.json` synchronized with the policy
blocks in `AGENTS.md`. Default severity is `error` with `apply: true` so
drift in policy
text or hashes cannot go unnoticed.

### DevCovenant Structure Guard
Validates the core DevCovenant layout using the manifest, ensuring required
core files and managed docs are present. This keeps updates safe by detecting
missing or altered core assets early.

### Dependency License Sync
Tracks dependency manifests (`requirements.in`, `requirements.lock`,
`pyproject.toml`) and ensures license artifacts are refreshed. Default config
expects `THIRD_PARTY_LICENSES.md` plus the `licenses/` directory so dependency
changes always carry their license audit trail.

### Policy Text Presence
Requires each policy block to include descriptive prose immediately after the
metadata. This keeps `AGENTS.md` readable and makes future policy edits
intentional.

### Stock Policy Text Sync
Warns when the built-in policy text diverges from the stock wording stored
in `devcovenant/registry/stock_policy_texts.yaml`. Use it to keep the
prose aligned with the core implementation unless a custom rewrite is
intended.

### DevFlow Run Gates
Enforces the session workflow (pre-commit start, tests, pre-commit end) by
reading `devcovenant/registry/test_status.json`. Default required commands are
`pytest` and `python -m unittest discover`, with timestamps compared against
recent code changes.

### Changelog Coverage
Requires every changed file to be listed in the latest changelog entry.
Defaults target `CHANGELOG.md`, skipping the changelog file itself so release
notes stay complete and traceable.

### Version Synchronization
Keeps `VERSION`, docs, and other version-bearing files aligned with the latest
changelog header. It prevents backward or mismatched version bumps so repo
metadata never drifts.

### Semantic Version Scope (optional)
Validates that the latest changelog entry declares one SemVer scope tag
(`semver:major`, `semver:minor`, or `semver:patch`) and that the bump
matches the change from the previous version. Use `major` for
API-breaking releases, `minor` for backward-compatible feature work, and
`patch` for bug fixes or docs-only adjustments. The policy ships disabled
(`apply: false`) and should only be enabled when release discipline is
required.

### Last Updated Placement
Ensures documentation files listed in the metadata carry a `Last Updated`
header near the top. Defaults allow only approved docs and auto-fix the date
when needed.

### Line Length Limit
Keeps lines within the configured max length (default 79) for readability.
Scopes are metadata-driven so teams can tighten or relax limits per file type.

### Docstring and Comment Coverage
Requires docstrings or adjacent explanatory comments for Python modules,
classes, and functions. Defaults focus on `.py` files and skip vendor output.

### Name Clarity
Warns on vague identifiers in code. It encourages descriptive naming without
blocking commits unless the repo raises its severity threshold.

### New Modules Need Tests
Ensures new modules are accompanied by tests. Defaults watch Python files
outside test directories and require matching `test_*.py` entries.

### Documentation Growth Tracking
When user-facing files change, requires updates to the documentation set. It
uses selector roles (`user_facing`, `user_visible`, `doc_quality`) so policies
can identify API-facing paths and enforce minimum doc depth.

### Read-Only Directories
Protects declared directories from edits. Defaults to no protected paths, but
teams can list vendor or dataset folders to make them immutable.

### No Future Dates
Guards against future timestamps in docs and changelogs. Auto-fix rewrites
invalid dates to the current UTC day.

### Security Scanner
Flags risky Python constructs like `eval`, `exec`, or `shell=True`. Defaults
scan `.py` files outside tests to keep unsafe patterns out of production
code.

### Managed Environment (optional)
Enforces usage of a declared managed environment (venv, bench, conda, etc.).
This policy is shipped off by default; enable it only after filling in
`expected_paths`, `expected_interpreters`, and `command_hints`.
`required_commands` should list the tooling that must be on PATH.
When enabled, DevCovenant emits warnings if the metadata is incomplete or
required commands are missing so teams refine their setup guidance.

## DevFlow Gates and Test Status
DevCovenant enforces the gate sequence for every change:
1. `python3 tools/run_pre_commit.py --phase start`
2. `python3 tools/run_tests.py`
3. `python3 tools/run_pre_commit.py --phase end`

The status file at `devcovenant/registry/test_status.json` records
timestamps and commands. The `devflow-run-gates` policy reads it to enforce
the workflow.

## Dependency and License Tracking
Runtime dependencies are recorded in `requirements.in`, pinned in
`requirements.lock`, and mirrored in `pyproject.toml`. When those files
change, update `THIRD_PARTY_LICENSES.md` and the license texts in `licenses/`.
The dependency-license-sync policy checks that the license report includes
all touched manifests under `## License Report`.

## Templates and Packaging
DevCovenant ships templates under `devcovenant/core/templates/` with
three layers: `global/` (shared docs/config/tools),
`profiles/<profile>/` (profile-specific assets), and
`policies/<policy>/` (policy-scoped assets). Each profile folder can
include a `profile.yaml` manifest that declares assets and policy
overlays. Custom overrides live under `devcovenant/custom/templates/`
with the same layout, including `custom/templates/global/` for
overriding global templates.

Use the template indexes for detailed structure and examples:
- `devcovenant/core/templates/README.md`
- `devcovenant/core/templates/profiles/README.md`
- `devcovenant/core/templates/policies/README.md`

Asset selection is driven by per-policy `policy_assets.yaml` manifests,
compiled into `devcovenant/registry/policy_assets.yaml`, plus profile
manifests under `templates/profiles/`. Assets for disabled policies or
inactive profiles are skipped.

### Template precedence and resolution
When DevCovenant resolves a template path, it checks in this order:
1) `devcovenant/custom/templates/policies/<policy>/...`
2) `devcovenant/custom/templates/profiles/<profile>/...`
3) `devcovenant/custom/templates/global/...`
4) `devcovenant/core/templates/policies/<policy>/...`
5) `devcovenant/core/templates/profiles/<profile>/...`
6) `devcovenant/core/templates/global/...`

If the template path already includes `profiles/` or `policies/`, the path is
resolved directly against the custom and core template roots. This lets
policy assets and profile assets point to their template files explicitly
without needing additional rewrites.

## Uninstall Behavior
Uninstall removes DevCovenant-managed blocks and, when requested, deletes
installed docs. Use:
```bash
devcovenant uninstall --target /path/to/repo

devcovenant uninstall --target /path/to/repo --remove-docs
```

## CI and Automation
The recommended CI workflow runs the same gate sequence used locally. Ensure
PyYAML and semver are installed so policy scripts and dependency checks run
cleanly. For tagged releases, run `python -m build` and `twine check dist/*`
before publishing.

## Troubleshooting
- Missing console script: use `python3 -m devcovenant`.
- Policy drift: run `devcovenant update-hashes`.
- Missing scripts: confirm the policy id matches the script filename.
- Unexpected violations: review policy metadata and custom overrides.
