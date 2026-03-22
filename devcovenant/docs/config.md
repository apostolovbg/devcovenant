# Configuration
**Last Updated:** 2026-03-22
**Project Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Ownership Model](#ownership-model)
- [Template Comment Contract](#template-comment-contract)
- [Top-Level Sections](#top-level-sections)
- [Metadata Resolution Order](#metadata-resolution-order)
- [Policy Activation](#policy-activation)
- [Workflow](#workflow)
- [Practical Recipes](#practical-recipes)
- [Common Mistakes](#common-mistakes)

## Overview
`devcovenant/config.yaml` is the repository runtime contract.

Refresh rebuilds autogen sections and preserves user-owned sections.
The file is intentionally explicit so policy and profile behavior can be
audited without reading runtime code.
Default global config includes `ignore.patterns:
devcovenant/config.yaml`, so config-only edits are excluded from
session-delta governance and related policy nagging.
That same global baseline also ignores ubiquitous editor, packaging,
coverage, and DevCovenant runtime artifacts such as `.vscode/**`,
`.idea/**`, `*.egg-info/**`, `pip-wheel-metadata/**`, `.coverage*`,
`devcovenant/logs/**`, and `devcovenant/registry/runtime/**`.
Runtime still requires valid YAML (YAML Ain't Markup Language); parse/load
errors in config remain blocking command failures.
The template source
`devcovenant/builtin/profiles/global/assets/config.yaml` also carries detailed
inline comments and should be treated as part of the configuration contract.
For the dedicated lifecycle-metadata contract, see
`devcovenant/docs/project_governance.md`.
This is the primary home for config ownership, review, and runtime control
surface details. Use `devcovenant/docs/installation.md` for lifecycle order,
`devcovenant/docs/policies.md` for policy behavior, and
`devcovenant/docs/profiles.md` for profile-supplied metadata.
It is also the normative home for the public `devcovenant/config.yaml`
contract. Use `devcovenant/docs/contracts.md` for the contract index and use
this document for the exact stable public config surface.

Practical mental model:
- `install` gives you this file plus the DevCovenant runtime
- your review of this file decides how the repo should behave
- `deploy` is blocked until that review is done
- after that, `refresh`, `deploy`, gates, and tests all read this file as the
  repo's active operating contract

First-pass reading order for this file:
- most users should start with `developer_mode`, `profiles.active`,
  `doc_assets`, `core_invariants`, `policy_state`, and the `engine` settings
- most users should leave generated sections alone
- if you are unsure whether a key is a policy choice, a repo-lifecycle
  choice, or generated state, read `Ownership Model` before editing

## Ownership Model
Autogen-owned sections:
- `profiles.generated`
- `autogen_metadata_overlays`
- `autogen_metadata_overrides`
- `install.import_managed_docs`

User-owned sections:
- `profiles.active`
- `clean.overlays`
- `clean.overrides`
- `core_invariants`
- `user_metadata_overlays`
- `user_metadata_overrides`
- `policy_state`
- `install.config_reviewed`
- `engine.fail_threshold`
- `engine.auto_fix_enabled`
- `engine.output_mode`
- `engine.tests_output_mode`
- `engine.logs_keep_last`
- `engine.pycache_prefix_enabled`
- `engine.pycache_prefix`
- `governance_and_test.overlays`
- `governance_and_test.overrides`
- `pre_commit.overlays`
- `pre_commit.overrides`
- `gitignore.overlays`
- `gitignore.overrides`

Autogen sections are regenerated each full refresh. User sections are kept.
User-owned sections are human authority. Do not modify them without explicit
human request (including `engine.fail_threshold`, `engine.output_mode`,
`engine.tests_output_mode`, `engine.logs_keep_last`,
`engine.pycache_prefix_enabled`, `engine.pycache_prefix`, and
`engine.auto_fix_enabled`).
Operational rule: config-only edits to `devcovenant/config.yaml` are
intentionally out of governance scope by default via `ignore.patterns`, so
they can be adjusted without changelog/session formalities.

## Template Comment Contract
Template comments are intentionally detailed and normative.
They should explain:
- key ownership boundaries (human-owned vs refresh-owned);
- merge semantics (overlay vs override);
- generation behavior for managed files (`.gitignore`, pre-commit config,
  governance workflow);
- required edit-session gate flow (`gate --start` -> `gate --mid` -> `test`
  -> `gate --end`);
- concise output-mode semantics for `engine.output_mode` and
  `engine.tests_output_mode`;
- role-based metadata conventions for policies such as
  `dependency-management` and `version-sync`.

When runtime behavior or policy contracts change, update template comments in
the same session so generated configs remain self-explanatory.

## Top-Level Sections
- `profiles.active`: selected profiles for this repository.

- `profiles.generated`: refresh-generated profile metadata summary
  (`file_suffixes`, `devcov_core_paths`).

- `doc_assets`: managed-doc selection for builtin docs, optional custom docs,
  and per-repo exclusions.

- `project-governance`: first-class repo lifecycle metadata for public
  project identity (`project_name`, `project_description`), stage,
  development stance, versioning mode, optional codename/build identity,
  displayed unversioned label, and unreleased changelog heading.

- `autogen_metadata_overlays`: generated additive overlay layer.

- `user_metadata_overlays`: user additive overlay layer.

- `autogen_metadata_overrides`: generated replace layer.

- `user_metadata_overrides`: user replace layer (highest metadata authority).

- `core_invariants`: first-class metadata for DevCovenant-owned runtime
  invariants such as gate evidence, registry integrity, and required
  DevCovenant runtime structure. These are not normal policy toggles.

- `policy_state`: authoritative activation map for every policy
  ID (identifier).
  `severity: critical` policies remain enforced even if a config toggle sets
  them to `false`; runtime emits an explicit diagnostic instead of silently
  honoring the disable attempt.

- `governance_and_test.overlays`: additive governance workflow patches.

- `governance_and_test.overrides`: replacement governance workflow payload.

- `pre_commit.overlays`: additive pre-commit payload patches.

- `pre_commit.overrides`: replacement pre-commit payload.

- `gitignore.overlays`: additive entries appended to generated `.gitignore`.

- `gitignore.overrides`: replacement list for generated
  base/profile/os entries.

- `ignore.patterns`: global glob-style exclusions for universal editor,
  packaging, coverage, and runtime artifacts that should stay outside
  `CheckContext` file collections across policies.

- `engine.fail_threshold`: severity threshold that blocks checks.

- `engine.auto_fix_enabled`: gate-managed auto-fix toggle (`true|false`).

- `engine.output_mode`: runtime command output contract
  (`normal|quiet|verbose`).

- `engine.tests_output_mode`: test-command output contract
  (`normal|quiet|verbose`), independent from runtime command output.
  Keep this key explicit in config so test behavior does not inherit
  `engine.output_mode` implicitly.
  Normal mode keeps status output concise, shows gate hook output, suppresses
  flood-prone managed/test child output, emits deterministic
  `[n/total] <command>` markers, and preserves full output in run logs.
  Quiet mode suppresses routine stdout chatter and child output while keeping
  error/violation surfaces on stderr and preserving full output in run logs.

- `engine.logs_keep_last`: run-log retention count (`0` = unlimited, `1` =
  keep only the latest run folder, `N` = keep the latest `N` run folders).
  Logging stays enabled by design; this key controls retention only and
  pruning happens after top-level command run finalization.

- `engine.pycache_prefix_enabled`: enable Python bytecode cache routing via
  `PYTHONPYCACHEPREFIX` for DevCovenant-managed Python subprocesses.

- `engine.pycache_prefix`: path used for `PYTHONPYCACHEPREFIX` when routing is
  enabled. Use `''` for an auto-selected stable repo-specific temp path;
  relative paths resolve from repo root and absolute paths are used as-is.

- `clean.overlays`: additive cleanup targets merged after active profile
  `clean_overlays`, including per-scope lists for build, cache,
  runtime-registry, logs, and protected paths.

- `clean.overrides`: replacement cleanup lists for repositories that need
  full ownership of one resolved cleanup key. Template defaults use `{}` so
  no replacement is implied; explicit per-key `[]` values intentionally clear
  inherited lists for that key, including all-empty override blocks.
  Runtime still protects tracked files such as
  `devcovenant/registry/registry.yaml` and `devcovenant/logs/README.md`.

- `core_invariants.devflow-run-gates.required_commands`: canonical test
  command chain.
  `engine.tests_output_mode` changes output presentation only; it does not
  select a different command list.

- `install.config_reviewed`: explicit post-install config-review guard for
  first-time activation flow. `install` leaves this as `false`. Change it to
  `true` only after a human has reviewed `developer_mode`,
  `profiles.active`, `core_invariants`, `policy_state`, and the key `engine`
  settings.

- `install.import_managed_docs`: refresh-owned install memory that records
  compatible pre-authored managed docs discovered during `install` so the
  first `refresh`/`deploy` can adopt seeded `SPEC.md`, `README.md`,
  `PLAN.md`, and similar DevCovenant-shaped docs instead of overwriting
  their authored body content.

- `managed-environment.expected_paths|expected_interpreters`: metadata-driven
  managed interpreter roots and explicit interpreter candidates.

- `managed-environment.manual_commands`: human-run guidance commands that are
  never auto-executed.

- `managed-environment.managed_commands`: stage-scoped auto commands using
  `stage=>command` entries (`start|test|end|command|all`).

- managed-environment command behavior:
  when active, CLI (command-line interface) commands automatically re-exec
  under the resolved managed interpreter when the current interpreter
  differs. Missing or non-executable managed interpreters now fail
  explicitly.
  Lifecycle bootstrap/teardown commands (`install`, `deploy`, `undeploy`,
  `uninstall`) are excluded from managed re-exec.

- `paths.policy_definitions`: policy prose source read by runtime.

- `paths.registry_file`: local policy hash registry destination.

- `developer_mode`: use `false` in a normal repository that is using
  DevCovenant as a tool. Use `true` only when the repository itself is being
  used to develop DevCovenant.

- `profiles.generated.devcov_core_paths`: autogen list of DevCovenant
  source/runtime paths hidden from normal repository scans when
  `developer_mode` is false. This is part of how normal repos avoid taking
  ownership of DevCovenant's own source tree and repo-only development
  surfaces.

Baseline profile guidance:
- keep `global` first
- `defaults` provides common repo-layout metadata defaults
- `global` owns the shared ignore/gitignore baseline for ubiquitous
  editor/build/runtime artifact noise; repo-local config should only add
  truly repository-specific exclusions on top
- `global` and stack-specific profiles may also contribute `clean_overlays`
  for disposable build/cache targets; repository config should add only
  repo-specific cleanup targets or deliberate replacements
- use custom profiles (or config metadata layers) for repo-specific layout
  changes

Practical `developer_mode` rule:
- set `developer_mode: false` for ordinary application/library repos that
  merely use DevCovenant
- set `developer_mode: true` only in the DevCovenant source repo or another
  repo intentionally used to develop DevCovenant itself
- when `developer_mode: false`, `deploy` prunes repo-only DevCovenant
  development paths such as `devcovenant/custom/policies/**`,
  `devcovenant/custom/profiles/<repo-only-profile>/**`, and
  `tests/devcovenant/core/**`

Practical first-review checklist:
1. decide whether this is a normal repo using DevCovenant or a repo used to
   develop DevCovenant itself, then set `developer_mode`
2. confirm the active profile stack in `profiles.active`
3. confirm `core_invariants` metadata such as required test commands and
   gate-status paths
4. confirm which policies should be on or off in `policy_state`
5. confirm the important `engine` settings:
   - `fail_threshold`
   - `output_mode`
   - `tests_output_mode`
   - `auto_fix_enabled`
5. confirm the managed-doc list in `doc_assets`
6. then flip `install.config_reviewed: true`

What `install.config_reviewed` is not:
- not a technical runtime cache
- not a hidden deploy switch
- not something refresh should guess for you

It is simply the repo's explicit statement that a human has reviewed the
starting config and is ready to let `deploy` activate it.

What most repositories change first:
- `profiles.active`
- `policy_state`
- `doc_assets`
- `engine.output_mode`
- `engine.tests_output_mode`

What most repositories should not change casually:
- generated sections such as `profiles.generated`
- runtime memory such as `install.import_managed_docs`
- low-level path references unless the repo structure genuinely differs from
  the normal layout

## Metadata Resolution Order
Resolved policy metadata is computed in this order:
1. descriptor defaults
2. active profile overlays
3. autogen metadata overlays
4. user metadata overlays
5. autogen metadata overrides
6. user metadata overrides
7. policy_state activation application

Overlay semantics:
- lists append with de-duplication
- scalars replace previous scalar values
- empty metadata must use typed YAML empties (`''`, `[]`, `{}`); sentinel
  pseudo-empty tokens are not part of active runtime behavior

Override semantics:
- targeted keys are replaced
- upstream overlay/default values for that key are omitted
- replacement intent is explicit: use overrides when you want full authority
  over one key, not when you want additive extension
- refresh records per-key resolution trace in
  `devcovenant/registry/registry.yaml` under
  `metadata_resolution`
- when an override replaces inherited non-empty values, refresh also records
  a structured `metadata_warnings` entry for that policy key so destructive
  replacement is visible during audits

## Policy Activation
`policy_state` is the activation authority for normal policy toggles.
`severity: critical` policies are the exception: runtime keeps them enforced
and emits a diagnostic when a config attempts to disable them.
Core invariants are not part of `policy_state`.
They use the first-class `core_invariants` section instead.
That keeps normal policy activation separate from DevCovenant's own
non-optional runtime contracts.

Refresh behavior:
- rewrites full alphabetical map of effective policy IDs
- preserves existing booleans
- seeds new policy IDs from resolved defaults
- removes stale policy IDs no longer present
- does not delete user-entered `false` toggles for critical policies;
  enforcement immunity is runtime behavior, not config rewrite coercion
  (the preserved toggle is evidence of intent, not an effective disablement)

Profiles do not activate policies.

Notable activation defaults in this repository:
- `version-governance` stays `false` in the global config template until a
  repository explicitly opts in.
- `version-sync` stays `false` in the global config template by default.
- `raw-string-escapes` stays optional and can be enabled when repositories
  want language-aware suspicious-escape checks beyond repo-specific custom
  policies.

## Workflow
Use this document when the question is "what does this key mean?" or
"who owns this section?".
For the exact gate sequence, use `devcovenant/docs/workflow.md`.

Normal config-change loop:
1. Update user-owned config keys for desired behavior.
2. Run `devcovenant refresh`.
3. Inspect generated sections and AGENTS policy block output.
4. Run the normal gate workflow from `devcovenant/docs/workflow.md`.

Autofix workflow note:
- `devcovenant check` is always read-only audit mode.
- `engine.auto_fix_enabled` controls whether gate-managed check runs request
  autofix during `gate --start` / `gate --end`.
- `engine.logs_keep_last` controls how many recent run-log folders remain
  under `devcovenant/logs/` after each command completes (`0` keeps all).
- `engine.pycache_prefix_enabled` + `engine.pycache_prefix` route bytecode
  caches away from the repo tree for DevCovenant-managed Python subprocesses
  while preserving bytecode generation fidelity.
- For source-checkout alternate launcher runs (`python3 -m devcovenant ...`),
  DevCovenant keeps the repo clean by suppressing later cache-file writes
  and removing the package-import cache Python may emit before CLI startup.

## Practical Recipes
Configure a normal repository that uses DevCovenant as a tool:
```yaml
developer_mode: false

install:
  config_reviewed: true
```

Configure a repository that is being used to develop DevCovenant itself:
```yaml
developer_mode: true

install:
  config_reviewed: true
```

Disable one shipped policy:
```yaml
policy_state:
  version-governance: false
```

Configure version governance for a SemVer repository:
```yaml
policy_state:
  version-governance: true

user_metadata_overrides:
  version-governance:
    scheme: semver
    version_file: VERSION
    changelog_file: CHANGELOG.md
    changelog_header_prefix: '## Version'
    enforce_bumping: true
    semver_scope_tags_required: true
```

Configure version governance for a CalVer repository:
```yaml
policy_state:
  version-governance: true

user_metadata_overrides:
  version-governance:
    scheme: calver
    version_file: VERSION
    changelog_file: CHANGELOG.md
    changelog_header_prefix: '## Version'
    enforce_bumping: true
```

Configure version governance for a Python package using
PEP (Python Enhancement Proposal) 440:
```yaml
policy_state:
  version-governance: true

user_metadata_overrides:
  version-governance:
    scheme: pep440
    version_file: VERSION
    changelog_file: CHANGELOG.md
    changelog_header_prefix: '## Version'
    enforce_bumping: true
    canonical_versions_required: true
    pep440_allow_prereleases: true
    pep440_allow_dev_releases: true
    pep440_allow_post_releases: false
```

Configure version governance for a format-only custom scheme:
```yaml
policy_state:
  version-governance: true

user_metadata_overrides:
  version-governance:
    scheme: custom_regex
    version_file: VERSION
    changelog_file: CHANGELOG.md
    changelog_header_prefix: '## Version'
    enforce_bumping: false
    custom_regex_pattern: '[IVXLC]+'
```

Configure version governance for a fully custom repo-local adapter:
```yaml
policy_state:
  version-governance: true

user_metadata_overrides:
  version-governance:
    scheme: custom_adapter
    version_file: VERSION
    changelog_file: CHANGELOG.md
    changelog_header_prefix: '## Version'
    enforce_bumping: true
    custom_adapter_path: \
      devcovenant/custom/policies/version_governance/roman_scheme.py
```

Choose `version-governance.scheme` explicitly whenever the policy is
enabled; there is no implicit SemVer fallback.
`custom_regex` is validation-only and should keep `enforce_bumping: false`.
`custom_adapter` expects the referenced repo-relative Python file to export
`SCHEME` with the same parse/compare/release interface used by builtin
version-governance adapters.
`enforce_bumping` stays generic across schemes: the version must move
forward under the selected ordering rules.
`canonical_versions_required` is enforced only by schemes that define a
canonical string form, such as integer and PEP 440.
CalVer intentionally keeps repo-chosen formatting instead of inventing one.

Keep repository equality under CalVer while requiring Python package
manifests to satisfy PEP 440:
```yaml
policy_state:
  version-governance: true
  version-sync: true

user_metadata_overrides:
  version-governance:
    scheme: calver
    version_file: VERSION
    changelog_file: CHANGELOG.md
    changelog_header_prefix: '## Version'
    enforce_bumping: true
  version-sync:
    role_legality_schemes:
      - package_manifest=>pep440
```

`role_legality_schemes` uses the same `role=>scheme` mapping style as other
role-based metadata. It adds stricter ecosystem legality for selected
surfaces after `version-sync` has already read and compared them through the
active repo-level `version-governance` scheme.

Configure orthogonal project governance for a versioned repository:
```yaml
project-governance:
  project_name: DevCovenant
  project_description: DevCovenant is a Repository Governance Framework.
  stage: stable
  development_stance: active-development
  versioning_mode: versioned
  codename: atlas

policy_state:
  version-governance: true
  version-sync: true
```

Use project governance for an intentionally unversioned repository:
```yaml
project-governance:
  project_name: Project Name
  project_description: >
    Describe the project this repository ships: what it does, who it helps,
    and what problem it solves.
  stage: beta
  development_stance: experimental
  versioning_mode: unversioned
  unversioned_label: Unversioned
  unreleased_heading: '## Unreleased'

policy_state:
  version-governance: false
  version-sync: false
```

`project-governance` does not replace `version-governance`; it governs
project identity, phase, and stance metadata through the dedicated top-level
config section. `project_name` and `project_description` feed managed README
surfaces and package metadata surfaces that DevCovenant owns or
synchronizes. When `versioning_mode` is `unversioned`, managed docs keep the
`Project Version` line but render the configured non-version label, and
`CHANGELOG.md` uses the configured unreleased heading.

Fresh installs start from this same unversioned pattern so refresh
never fabricates a placeholder numbered release such as `0.0.0`.

Add extra changelog verbs without replacing defaults:
```yaml
user_metadata_overlays:
  changelog-coverage:
    summary_verbs:
      - verify
      - validated
```

Default changelog exclusions already skip generated governance targets:
`.gitignore`, `.pre-commit-config.yaml`, and
`.github/workflows/governance-and-test.yml`.

Adjust which document header-only edits are ignored by changelog coverage:
```yaml
user_metadata_overrides:
  changelog-coverage:
    header_doc_suffixes:
      - .md
      - .rst
      - .txt
    header_keys:
      - Last Updated
      - Version
    header_scan_lines: 4
```

Replace the required test command chain:
```yaml
core_invariants:
  devflow-run-gates:
    required_commands:
      - python3 -m unittest discover -v
      - pytest
```

Configure managed-environment stage automation with explicit manual guidance:
```yaml
policy_state:
  managed-environment: true

user_metadata_overrides:
  managed-environment:
    expected_paths:
      - .venv
    expected_interpreters:
      - .venv/bin/python
      - .venv/Scripts/python.exe
    manual_commands:
      - python3 -m venv .venv
      - '{managed_python} -m pip install -r requirements.lock'
    managed_commands:
      - start=>python3 -m venv .venv
      - start=>{managed_python} -m pip install -r requirements.lock
      - command=>{managed_python} -m pip install -r requirements.lock
```

Managed command token contract:
- `{repo_root}`: absolute repository root.
- `{managed_python}`: resolved managed interpreter path.
- `{managed_bin}`: managed interpreter directory.
- `{managed_root}`: managed environment root (for example `.venv` or bench
  env directory).

Scope split contract:
- default global descriptor/template state keeps `managed-environment` off.
- repository-level enablement is controlled by `policy_state` in each repo's
  `devcovenant/config.yaml`.
- CLI commands run from non-managed interpreters are automatically re-executed
  in the managed interpreter when this policy is active, excluding
  `install`, `deploy`, `undeploy`, and `uninstall`.
- if a resolved managed interpreter path exists but is not executable,
  runtime emits an explicit managed-environment error and stops so the
  environment contract can be repaired directly.

Keep repository blocking at `error` while downgrading `tests-coverage` findings
to warning:
```yaml
engine:
  fail_threshold: error

user_metadata_overrides:
  tests-coverage:
    severity: warning
```

Switch command output to concise normal mode:
```yaml
engine:
  output_mode: normal
  tests_output_mode: normal
```

Switch command output to quiet mode (errors/violations only):
```yaml
engine:
  output_mode: quiet
  tests_output_mode: quiet
```

Keep only the latest 20 DevCovenant run-log folders in this repo:
```yaml
engine:
  logs_keep_last: 20
```

Route Python bytecode caches away from the repo tree while preserving
bytecode generation:
```yaml
engine:
  pycache_prefix_enabled: true
  pycache_prefix: ''
```

Configure output-sink governance at config layer:
```yaml
policy_state:
  no-print-outside-output-runtime: true

user_metadata_overlays:
  no-print-outside-output-runtime:
    allowed_file_globs:
      - devcovenant/core/runtime/execution.py
    allow_waiver_comment: 'DEVCOV_ALLOW_OUTPUT:'
```

`tests-coverage` now reads related test files directly and does not require
gate-status evidence settings. For fixture-only assertion placeholders, use the
in-test marker `DEVCOV_FIXTURE_OK: <reason>` immediately above the assertion.
Language-specific assertion semantics are metadata-driven through
`assertion_signal_patterns` and `tautology_patterns` (`language=>regex`
tokens), while symbol-fidelity controls use `symbol_kinds`,
`symbol_name_min_length`, `symbol_assertion_window`, and
`enforce_symbol_fidelity`.

Append repo-specific `.gitignore` entries without editing generated sections:
```yaml
gitignore:
  overlays:
    - "*.cache-local"
    - "tmp/dev/"
```

Replace generated gitignore fragments entirely (keep preserved user block):
```yaml
gitignore:
  overrides:
    - ".custom-cache/"
    - ".tool-state/"
```

Append one extra step to generated governance workflow:
```yaml
governance_and_test:
  overlays:
    jobs:
      governance-and-test:
        steps:
          - name: Extra validation
            run: echo "extra"
```

Replace generated pre-commit payload entirely:
```yaml
pre_commit:
  overrides:
    repos:
      - repo: local
        hooks:
          - id: devcovenant
            name: enforce repository policies (DevCovenant)
            entry: python3 -m devcovenant.cli check
            language: python
            pass_filenames: false
            always_run: true
```

Add strict-ish documentation route reminders for source changes:
```yaml
user_metadata_overlays:
  documentation-growth-tracking:
    doc_routes:
      - "src/**/*.py => docs/architecture.md"
      - "src/**/*.py => docs/workflow.md"
      - "src/policies/**/*.py => docs/policies.md"
      - "pyproject.toml => docs/installation.md"
      - "MANIFEST.in => docs/installation.md"
```
When `doc_routes` is configured, every user-facing changed file must match at
least one route and touch all mapped docs.
Route globs are path-segment aware: `devcovenant/*.py` targets only files
directly under `devcovenant/`; use `**` when recursive matching is intended.
All documentation-growth-tracking findings inherit the policy's single
`severity`; there are no per-subcheck severity keys.
Route requirements are validated against the effective `user_visible_files`
set; keep that set aligned with route targets such as
`devcovenant/docs/architecture.md`.
By default, docs suffixes are not in user-facing scope, so files like
`CHANGELOG.md` are not route-checked unless you opt in via policy metadata.

Replace dependency role selectors completely:
```yaml
user_metadata_overrides:
  dependency-management:
    dependency_role_files:
      - intent=>requirements.in
      - resolved=>requirements.lock
      - package_manifest=>pyproject.toml
    dependency_role_globs:
      - intent=>services/*/package.json
    dependency_role_dirs:
      - resolved=>apps/web
```
Dependency selector model:
- `defaults` profile provides generic dependency-license output targets.
- language/framework profiles add dependency selectors when active.
- role selectors are preferred:
  (`dependency_role_files`, `dependency_role_globs`,
  `dependency_role_dirs`) using `role=>selector` tokens.

Replace shipped layout defaults with your own profile:
```yaml
profiles:
  active:
    - global
    - mylayout
    - python
    - docs
```
Create `devcovenant/custom/profiles/mylayout/mylayout.yaml` by copying
`devcovenant/builtin/profiles/defaults/defaults.yaml`, then tailor
`policy_overlays` and `core_invariant_overlays` for your repository
structure.

## Common Mistakes
- Trying to activate policies through profile manifests.
- Editing autogen sections directly and expecting persistence.
- Using overrides when overlays are sufficient for additive behavior.
- Skipping refresh after profile/descriptor contract edits.
