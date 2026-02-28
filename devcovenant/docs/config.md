# Configuration
**Last Updated:** 2026-02-27
**Version:** 1.0.0

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
Runtime still requires valid YAML; parse/load errors in config remain
blocking command failures.
The template source
`devcovenant/builtin/profiles/global/assets/config.yaml` also carries detailed
inline comments and should be treated as part of the configuration contract.

## Ownership Model
Autogen-owned sections:
- `profiles.generated`
- `autogen_metadata_overlays`
- `autogen_metadata_overrides`

User-owned sections:
- `profiles.active`
- `user_metadata_overlays`
- `user_metadata_overrides`
- `policy_state`
- `install.generic_config`
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
  `dependency-license-sync` and `version-sync`.

When runtime behavior or policy contracts change, update template comments in
the same session so generated configs remain self-explanatory.

## Top-Level Sections
- `profiles.active`: selected profiles for this repository.

- `profiles.generated`: refresh-generated profile metadata summary
  (`file_suffixes`, `devcov_core_paths`).

- `doc_assets`: managed-doc routing for autogen and user selections.

- `autogen_metadata_overlays`: generated additive overlay layer.

- `user_metadata_overlays`: user additive overlay layer.

- `autogen_metadata_overrides`: generated replace layer.

- `user_metadata_overrides`: user replace layer (highest metadata authority).

- `policy_state`: authoritative activation map for every policy ID.
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

- `engine.fail_threshold`: severity threshold that blocks checks.

- `engine.auto_fix_enabled`: gate-managed auto-fix toggle (`true|false`).

- `engine.output_mode`: runtime command output contract
  (`normal|quiet|verbose`).

- `engine.tests_output_mode`: test-command output contract
  (`normal|quiet|verbose`), independent from runtime command output.
  If unset, runtime falls back to `engine.output_mode` for compatibility.
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

- `devflow-run-gates.required_commands`: canonical test command chain.
  `engine.tests_output_mode` changes output presentation only; it does not
  select a different command list.

- `install.generic_config`: deploy guard for first-time activation flow.

- `managed-environment.expected_paths|expected_interpreters`: metadata-driven
  managed interpreter roots and explicit interpreter candidates.

- `managed-environment.manual_commands`: human-run guidance commands that are
  never auto-executed.

- `managed-environment.managed_commands`: stage-scoped auto commands using
  `stage=>command` entries (`start|test|end|command|all`).

- `managed-environment.managed_rerun_commands`: stage-scoped wrapper rerun
  commands using `stage=>command` entries (`start|test|end|command|all`).

- managed-environment command behavior:
  when active, CLI commands automatically re-exec under the resolved managed
  interpreter when the current interpreter differs, or through configured
  wrapper rerun commands when direct interpreter execution is unavailable.
  Lifecycle bootstrap/teardown commands (`install`, `deploy`, `undeploy`,
  `uninstall`) are excluded from managed re-exec.

- `paths.policy_definitions`: policy prose source read by runtime.

- `paths.registry_file`: local policy hash registry destination.

- `devcov_core_include`: toggles user-repo scope vs full DevCovenant scope.

- `profiles.generated.devcov_core_paths`: autogen list of DevCovenant
  internal paths excluded when `devcov_core_include` is false, including
  builtin and core trees plus root CLI scripts.

Baseline profile guidance:
- keep `global` first
- `defaults` provides common repo-layout metadata defaults
- use custom profiles (or config metadata layers) for repo-specific layout
  changes

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

## Policy Activation
`policy_state` is the activation authority for normal policy toggles.
`severity: critical` policies are the exception: runtime keeps them enforced
and emits a diagnostic when a config attempts to disable them.
This repository's initial critical set is:
- `devflow-run-gates`
- `devcov-integrity-guard`
- `devcov-structure-guard`
Intentional changes to those policies require tracked metadata changes or a
builtin-to-custom policy replacement; temporary `policy_state: false` toggles
do not disable them.

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
- `semantic-version-scope` stays `false` outside release slices.
- `raw-string-escapes` stays optional and can be enabled when repositories
  want language-aware suspicious-escape checks beyond repo-specific custom
  policies.

## Workflow
1. Update user-owned config keys for desired behavior.
2. Run `devcovenant refresh`.
3. Inspect generated sections and AGENTS policy block output.
4. Run `devcovenant test`.

Autofix workflow note:
- `devcovenant check` is always read-only audit mode.
- `engine.auto_fix_enabled` controls whether gate-managed check runs request
  autofix during `gate --start` / `gate --end`.
- `engine.logs_keep_last` controls how many recent run-log folders remain
  under `devcovenant/logs/` after each command completes (`0` keeps all).
- `engine.pycache_prefix_enabled` + `engine.pycache_prefix` route bytecode
  caches away from the repo tree for DevCovenant-managed Python subprocesses
  while preserving bytecode generation fidelity.
- For fallback launcher runs (`python3 -m devcovenant ...`), set
  `PYTHONPYCACHEPREFIX` in the shell/CI environment before Python starts if
  you need to prevent repo-local launcher-process `__pycache__` writes.

## Practical Recipes
Disable one shipped policy:
```yaml
policy_state:
  semantic-version-scope: false
```

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
user_metadata_overrides:
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
    managed_rerun_commands:
      - command=>bench exec -- devcovenant {command_argv}
```

Managed command token contract:
- `{repo_root}`: absolute repository root.
- `{managed_python}`: resolved managed interpreter path.
- `{managed_bin}`: managed interpreter directory.
- `{managed_root}`: managed environment root (for example `.venv` or bench
  env directory).
- `{command}` / `{command_name}`: DevCovenant command token (for example
  `gate`).
- `{command_args}`: standalone token that expands to command args.
- `{command_argv}`: standalone token that expands to
  `{command_name} + {command_args}`.
- `{command_string}`: shell-escaped command string for wrapper arguments.

Scope split contract:
- default global descriptor/template state keeps `managed-environment` off.
- repository-level enablement is controlled by `policy_state` in each repo's
  `devcovenant/config.yaml`.
- CLI commands run from non-managed interpreters are automatically re-executed
  in the managed interpreter when this policy is active, excluding
  `install`, `deploy`, `undeploy`, and `uninstall`.
- when direct managed interpreter resolution fails, runtime can rerun
  DevCovenant through `managed_rerun_commands` wrapper metadata.

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
  dependency-license-sync:
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
`policy_overlays` for your repository structure.

## Common Mistakes
- Trying to activate policies through profile manifests.
- Editing autogen sections directly and expecting persistence.
- Using overrides when overlays are sufficient for additive behavior.
- Skipping refresh after profile/descriptor contract edits.
