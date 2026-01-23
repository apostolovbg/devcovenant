# Changelog
**Last Updated:** 2026-01-23
**Version:** 0.2.6

<!-- DEVCOV:BEGIN -->
**Doc ID:** CHANGELOG
**Doc Type:** changelog
**Managed By:** DevCovenant

## How to Log Changes
Add one line for each substantive change under the current version header.
Keep entries newest-first and record dates in ISO format (`YYYY-MM-DD`).
Example entry:
- 2026-01-23: Updated dependency manifests and license report.
  Files:
  requirements.in
  requirements.lock
  THIRD_PARTY_LICENSES.md
  devcovenant/core/policy_scripts/
    documentation_growth_tracking.py
<!-- DEVCOV:END -->

## Log changes here

## Version 0.2.6
- 2026-01-23: Implemented the policy replacement workflow, added
  replacement metadata, and expanded Phase H test coverage while
  refreshing documentation and manifests. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  MANIFEST.in
  PLAN.md
  README.md
  SPEC.md
  devcov_check.py
  devcovenant/README.md
  devcovenant/config.yaml
  devcovenant/core/cli_options.py
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/metadata_normalizer.py
  devcovenant/core/policy_replacements.py
  devcovenant/core/policy_replacements.yaml
  devcovenant/core/tests/test_devcov_check.py
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_metadata_normalizer.py
  devcovenant/core/tests/test_policies/test_devcov_structure_guard.py
  devcovenant/core/tests/test_policy_replacements.py
  devcovenant/core/uninstall.py
  devcovenant/core/update.py
  devcovenant/manifest.json
  devcovenant/templates/AGENTS.md
  devcovenant/templates/devcov_check.py
- 2026-01-23: Added Phase G tests for selector-role migration, update
  refresh behavior, and structure-guard manifest validation, plus
  refreshed the plan status. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_metadata_normalizer.py
  devcovenant/core/tests/test_policies/test_devcov_structure_guard.py
- 2026-01-23: Removed the root devcov_check wrapper in favor of the
  `python3 -m devcovenant` CLI, updated installer manifests, and
  refreshed documentation/policy metadata accordingly. (AI assistant)
  Files:
  CHANGELOG.md
  AGENTS.md
  README.md
  SPEC.md
  devcov_check.py
  devcovenant/README.md
  devcovenant/config.yaml
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/tests/test_devcov_check.py
  devcovenant/core/uninstall.py
  devcovenant/manifest.json
  devcovenant/templates/AGENTS.md
  devcovenant/templates/devcov_check.py
- 2026-01-23: Unified install/update/uninstall CLI options, enforced
  install-time changelog/contributing replacement, and clarified
  version bootstrapping defaults. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/core/cli_options.py
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/metadata_normalizer.py
  devcovenant/core/tests/test_metadata_normalizer.py
  devcovenant/core/uninstall.py
  devcovenant/core/update.py
  devcovenant/manifest.json
- 2026-01-23: Marked Phases A-E as complete in the 0.2.6 plan. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-23: Switched stock policy text storage to YAML, shortened
  registry hash storage to satisfy line limits, and expanded changelog
  examples for long paths. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/policy_scripts/stock_policy_text_sync.py
  devcovenant/core/policy_texts.py
  devcovenant/core/registry.py
  devcovenant/core/stock_policy_texts.json
  devcovenant/core/stock_policy_texts.yaml
  devcovenant/core/tests/test_policies/test_stock_policy_text_sync.py
  devcovenant/manifest.json
  devcovenant/registry.json
  devcovenant/templates/AGENTS.md
- 2026-01-23: Added doc metadata blocks for managed docs, updated
  installer handling for spec/plan/changelog blocks, and refreshed
  documentation plus manifest tracking. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  CITATION.cff
  CONTRIBUTING.md
  DEVCOVENANT.md
  LICENSE
  MANIFEST.in
  PLAN.md
  README.md
  SPEC.md
  VERSION
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/common_policy_patches/README.md
  devcovenant/common_policy_patches/__init__.py
  devcovenant/config.yaml
  devcovenant/core/base.py
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/metadata_normalizer.py
  devcovenant/core/parser.py
  devcovenant/core/policy_locations.py
  devcovenant/core/policy_scripts/devcov_structure_guard.py
  devcovenant/core/policy_scripts/stock_policy_text_sync.py
  devcovenant/core/policy_scripts/version_sync.py
  devcovenant/core/stock_policy_texts.json
  devcovenant/core/tests/test_base.py
  devcovenant/core/tests/test_engine.py
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_metadata_normalizer.py
  devcovenant/core/tests/test_policies/test_devcov_structure_guard.py
  devcovenant/core/tests/test_policies/test_stock_policy_text_sync.py
  devcovenant/core/tests/test_policies/test_version_sync.py
  devcovenant/core/tests/test_policy_patches.py
  devcovenant/core/uninstall.py
  devcovenant/core/update.py
  devcovenant/custom/policy_scripts/README.md
  devcovenant/manifest.json
  devcovenant/registry.json
  devcovenant/templates/AGENTS.md
  devcovenant/templates/CONTRIBUTING.md
  devcovenant/templates/DEVCOVENANT.md
  devcovenant/templates/LICENSE_GPL-3.0.txt
  devcovenant/templates/VERSION
  devcovenant/templates/tools/install_devcovenant.py
  devcovenant/templates/tools/templates/LICENSE_GPL-3.0.txt
  devcovenant/templates/tools/uninstall_devcovenant.py
  pyproject.toml
  tools/install_devcovenant.py
  tools/templates/LICENSE_GPL-3.0.txt
  tools/uninstall_devcovenant.py
- 2026-01-22: Tracked `devcovenant/manifest.json` in-repo and added a
  manifest schema summary to devcovenant docs. (AI assistant)
  Files:
  CHANGELOG.md
  devcovenant/README.md
  devcovenant/manifest.json
- 2026-01-22: Added manifest-driven structure validation, switched
  install/update/uninstall to `devcovenant/manifest.json`, and refreshed
  docs/tests/spec to match. (AI assistant)
  Files:
  CHANGELOG.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/policy_scripts/devcov_structure_guard.py
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_policies/test_devcov_structure_guard.py
  devcovenant/core/uninstall.py
  devcovenant/registry.json
- 2026-01-22: Removed managed-blocks-only mode, set updates to append
  missing policies with automatic metadata normalization, and updated
  CLI/tests/docs to match. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/core/install.py
  devcovenant/core/update.py
  devcovenant/core/tests/test_install.py
- 2026-01-22: Migrated legacy selector metadata into selector roles and
  expanded normalization tests and docs to cover user-facing roles.
  (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/README.md
  devcovenant/core/metadata_normalizer.py
  devcovenant/core/tests/test_metadata_normalizer.py
- 2026-01-22: Confirmed Phase B by adding managed-blocks-only coverage
  in installer tests and updating the plan status. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/core/tests/test_install.py
- 2026-01-22: Filled in missing policy metadata keys, introduced empty
  metadata fallback behavior, and added selector-role defaults for
  documentation-growth-tracking. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/core/base.py
  devcovenant/core/tests/test_base.py
  devcovenant/templates/AGENTS.md
- 2026-01-22: Added selector role normalization, legacy selector migration,
  and documentation updates for selector roles. (AI assistant)
  Files:
  CHANGELOG.md
  README.md
  devcovenant/README.md
  devcovenant/core/metadata_normalizer.py
  devcovenant/core/tests/test_metadata_normalizer.py
- 2026-01-22: Marked Phase A and Phase B as not done in the plan.
  (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Noted that custom selector roles are supported in the plan.
  (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Rewrote the plan to codify target update behavior, selector
  roles, core refresh rules, and dynamic structure validation. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Documented the target update behavior, selector roles, and
  policy migration workflow in the plan. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Clarified that default updates run metadata normalization so
  core policy updates remain compatible while preserving values. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Clarified that default updates do not alter policy metadata and
  key changes require explicit normalization. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Updated the plan to migrate legacy selector keys into
  selector roles and reorder remaining phases. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Planned selector role normalization with `selector_roles` and
  globs/files/dirs triplets, including user-visible roles. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Expanded the plan to require selector-key completeness in
  metadata normalization and document the key taxonomy. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Rewrote the 0.2.6 plan to reflect policy replacement,
  managed-environment, and SemVer enablement sequencing with updated
  acceptance criteria and risks. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Expanded the plan with metadata completeness,
  policy replacement, and deprecation workflow guidance. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Documented that SemVer scope enforcement ships disabled by
  default with guidance for enabling it and keeping it on for releases.
  (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Added plan items for a unified managed-environment policy and
  SemVer scope enforcement aligned with MAJOR/MINOR/PATCH intent.
  (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Planned install defaults for CONTRIBUTING/CHANGELOG,
  version bootstrapping, and managed-block placement guidance for changelog
  updates. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
- 2026-01-22: Implemented policy-mode and managed-block-only update
  controls, plus installer logic and tests to preserve or append policy
  blocks safely during updates. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/core/install.py
  devcovenant/core/update.py
  devcovenant/core/tests/test_install.py
- 2026-01-22: Added metadata normalization tooling and CLI support to
  standardize policy blocks, plus docs and plan updates describing the
  new schema workflow. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/core/metadata_normalizer.py
  devcovenant/core/tests/test_metadata_normalizer.py
- 2026-01-22: Removed DEVCOVENANT/CITATION artifacts, made SPEC/PLAN
  optional, and updated install/update tooling plus version-sync handling
  to match the streamlined documentation flow. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  CITATION.cff
  CONTRIBUTING.md
  DEVCOVENANT.md
  LICENSE
  MANIFEST.in
  PLAN.md
  README.md
  SPEC.md
  VERSION
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/common_policy_patches/README.md
  devcovenant/common_policy_patches/__init__.py
  devcovenant/config.yaml
  devcovenant/core/base.py
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/parser.py
  devcovenant/core/policy_locations.py
  devcovenant/core/policy_scripts/devcov_structure_guard.py
  devcovenant/core/policy_scripts/stock_policy_text_sync.py
  devcovenant/core/policy_scripts/version_sync.py
  devcovenant/core/stock_policy_texts.json
  devcovenant/core/tests/test_engine.py
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_policies/test_devcov_structure_guard.py
  devcovenant/core/tests/test_policies/test_stock_policy_text_sync.py
  devcovenant/core/tests/test_policies/test_version_sync.py
  devcovenant/core/tests/test_policy_patches.py
  devcovenant/core/uninstall.py
  devcovenant/core/update.py
  devcovenant/custom/policy_scripts/README.md
  devcovenant/registry.json
  devcovenant/templates/AGENTS.md
  devcovenant/templates/CONTRIBUTING.md
  devcovenant/templates/DEVCOVENANT.md
  devcovenant/templates/LICENSE_GPL-3.0.txt
  devcovenant/templates/VERSION
  devcovenant/templates/tools/install_devcovenant.py
  devcovenant/templates/tools/templates/LICENSE_GPL-3.0.txt
  devcovenant/templates/tools/uninstall_devcovenant.py
  pyproject.toml
  tools/install_devcovenant.py
  tools/templates/LICENSE_GPL-3.0.txt
  tools/uninstall_devcovenant.py
- 2026-01-22: Consolidated 0.2.6 documentation, templates, and update
  workflow guidance to reflect custom overrides, managed-block-only updates,
  and the removal of patch-based policy artifacts. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  LICENSE
  MANIFEST.in
  PLAN.md
  README.md
  SPEC.md
  VERSION
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/common_policy_patches/README.md
  devcovenant/common_policy_patches/__init__.py
  devcovenant/config.yaml
  devcovenant/core/base.py
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/parser.py
  devcovenant/core/policy_locations.py
  devcovenant/core/policy_scripts/devcov_structure_guard.py
  devcovenant/core/policy_scripts/stock_policy_text_sync.py
  devcovenant/core/stock_policy_texts.json
  devcovenant/core/tests/test_engine.py
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_policies/test_devcov_structure_guard.py
  devcovenant/core/tests/test_policies/test_stock_policy_text_sync.py
  devcovenant/core/tests/test_policy_patches.py
  devcovenant/core/uninstall.py
  devcovenant/core/update.py
  devcovenant/custom/policy_scripts/README.md
  devcovenant/registry.json
  devcovenant/templates/AGENTS.md
  devcovenant/templates/CONTRIBUTING.md
  devcovenant/templates/LICENSE_GPL-3.0.txt
  devcovenant/templates/VERSION
  devcovenant/templates/tools/install_devcovenant.py
  devcovenant/templates/tools/templates/LICENSE_GPL-3.0.txt
  devcovenant/templates/tools/uninstall_devcovenant.py
  pyproject.toml
  tools/install_devcovenant.py
  tools/templates/LICENSE_GPL-3.0.txt
  tools/uninstall_devcovenant.py
- 2026-01-22: Refined the 0.2.6 plan and docs to describe safe update
  modes, metadata normalization, and managed-block-only refreshes.
  (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  SPEC.md
  devcovenant/README.md
- 2026-01-22: Removed legacy install/uninstall wrappers, moved the GPL
  template into `devcovenant/templates`, and updated structure checks,
  config, and docs to match the CLI-only workflow. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  LICENSE
  MANIFEST.in
  PLAN.md
  README.md
  SPEC.md
  VERSION
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/common_policy_patches/README.md
  devcovenant/common_policy_patches/__init__.py
  devcovenant/config.yaml
  devcovenant/core/base.py
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/parser.py
  devcovenant/core/policy_locations.py
  devcovenant/core/policy_scripts/devcov_structure_guard.py
  devcovenant/core/policy_scripts/stock_policy_text_sync.py
  devcovenant/core/stock_policy_texts.json
  devcovenant/core/tests/test_engine.py
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_policies/test_devcov_structure_guard.py
  devcovenant/core/tests/test_policies/test_stock_policy_text_sync.py
  devcovenant/core/tests/test_policy_patches.py
  devcovenant/core/uninstall.py
  devcovenant/core/update.py
  devcovenant/custom/policy_scripts/README.md
  devcovenant/registry.json
  devcovenant/templates/AGENTS.md
  devcovenant/templates/CONTRIBUTING.md
  devcovenant/templates/LICENSE_GPL-3.0.txt
  devcovenant/templates/VERSION
  devcovenant/templates/tools/install_devcovenant.py
  devcovenant/templates/tools/templates/LICENSE_GPL-3.0.txt
  devcovenant/templates/tools/uninstall_devcovenant.py
  pyproject.toml
  tools/install_devcovenant.py
  tools/templates/LICENSE_GPL-3.0.txt
  tools/uninstall_devcovenant.py
- 2026-01-22: Added doc-targeting flags for partial overwrites and made
  docs/tests adjusted accordingly.
  (AI assistant)
  Files:
  CHANGELOG.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/core/install.py
  devcovenant/core/update.py
  devcovenant/core/tests/test_install.py
- 2026-01-22: Simplified contributing guidance to a minimal entry point
  (AI assistant)
  Files:
  CONTRIBUTING.md
  devcovenant/templates/CONTRIBUTING.md
- 2026-01-22: Removed patch overrides in favor of custom policy overrides,
  added a dedicated update command, and refreshed installer/uninstaller
  handling, fixer resolution, and documentation to match the new flow.
  (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  LICENSE
  MANIFEST.in
  PLAN.md
  README.md
  SPEC.md
  VERSION
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/common_policy_patches/README.md
  devcovenant/common_policy_patches/__init__.py
  devcovenant/core/base.py
  devcovenant/core/engine.py
  devcovenant/core/install.py
  devcovenant/core/parser.py
  devcovenant/core/policy_locations.py
  devcovenant/core/policy_scripts/devcov_structure_guard.py
  devcovenant/core/policy_scripts/stock_policy_text_sync.py
  devcovenant/core/stock_policy_texts.json
  devcovenant/core/tests/test_engine.py
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_policies/test_devcov_structure_guard.py
  devcovenant/core/tests/test_policies/test_stock_policy_text_sync.py
  devcovenant/core/tests/test_policy_patches.py
  devcovenant/core/uninstall.py
  devcovenant/core/update.py
  devcovenant/custom/policy_scripts/README.md
  devcovenant/registry.json
  devcovenant/templates/AGENTS.md
  devcovenant/templates/VERSION
  pyproject.toml

## Version 0.2.5
- 2026-01-22: Planned a dedicated update command, stricter install
  behavior, and resilient uninstall handling for user repos.
  (AI assistant)
  Files:
  PLAN.md
- 2026-01-22: Rewrote `PLAN.md` with the 0.2.6 development plan and
  user repo update path. (AI assistant)
  Files:
  PLAN.md
- 2026-01-12: Added an install behavior cheat sheet to README and documented
  installer defaults in the managed AGENTS section so install behavior stays
  clear.
  Files:
  AGENTS.md
  CHANGELOG.md
  README.md
  devcovenant/templates/AGENTS.md
  expanded the repo guide with comprehensive installer and CLI details, and
  synced reference docs and templates to match the new behavior.
  Files:
  AGENTS.md
  CHANGELOG.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/install.py
- 2026-01-12: Expanded and harmonized documentation with current CLI and
  installer behavior, updated template docs, and corrected `devcov_check.py`
  usage guidance to match the CLI requirement.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  SPEC.md
  devcov_check.py
  devcovenant/README.md
  devcovenant/common_policy_patches/README.md
  devcovenant/custom/policy_scripts/README.md
  devcovenant/templates/AGENTS.md
  devcovenant/templates/CONTRIBUTING.md
  devcovenant/templates/devcov_check.py
- 2026-01-12: Reworked the installer to merge README headers and standard
  sections, preserve SPEC/PLAN content with updated headers, back up and
  `.gitignore`; added packaged templates, new CLI args, and installer tests.
  Files:
  AGENTS.md
  CHANGELOG.md
  MANIFEST.in
  SPEC.md
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/core/install.py
  devcovenant/core/tests/test_install.py
  devcovenant/templates/.github/workflows/ci.yml
  devcovenant/templates/.pre-commit-config.yaml
  devcovenant/templates/AGENTS.md
  devcovenant/templates/CONTRIBUTING.md
  devcovenant/templates/VERSION
  devcovenant/templates/devcov_check.py
  devcovenant/templates/tools/install_devcovenant.py
  devcovenant/templates/tools/run_pre_commit.py
  devcovenant/templates/tools/run_tests.py
  devcovenant/templates/tools/uninstall_devcovenant.py
  devcovenant/templates/tools/update_test_status.py
  devcovenant/templates/tools/templates/LICENSE_GPL-3.0.txt
- 2026-01-12: Bumped every doc/version marker to 0.2.5 so the published CLI,
  installer and policy templates remain in sync across repos; updated the
  installer to preserve existing `AGENTS.md` notes in the editable section
  instead of overwriting them.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  LICENSE
  PLAN.md
  README.md
  SPEC.md
  VERSION
  devcovenant/README.md
  devcovenant/common_policy_patches/README.md
  devcovenant/core/install.py
  devcovenant/custom/policy_scripts/README.md
  pyproject.toml
  devcovenant/registry.json

## Version 0.2.4
- 2026-02-04: Ensure the PyPI package ships the `devcovenant` module and the
  policy docs/templates so the install command and console script can run
  without `ModuleNotFoundError`.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  LICENSE
  PLAN.md
  README.md
  SPEC.md
  VERSION
  devcovenant/README.md
  devcovenant/common_policy_patches/README.md
  devcovenant/custom/policy_scripts/README.md
  pyproject.toml

## Version 0.2.3
- 2026-01-12: Bumped documentation and tooling for 0.2.3 so the published CLI
  entry point works (`devcovenant --help`) and the policy docs/regression
  instructions are up to date.
  Files:
  AGENTS.md
  README.md
  SPEC.md
  PLAN.md
  CONTRIBUTING.md
  devcovenant/README.md
  devcovenant/common_policy_patches/README.md
  devcovenant/custom/policy_scripts/README.md
  pyproject.toml
  VERSION
  LICENSE
  CHANGELOG.md
  devcovenant/registry.json
## Version 0.2.2
- 2026-02-03: Added the `devcovenant` console script entry point so pip
  installs provide the documented CLI command.
  Files:
  pyproject.toml
- 2026-02-02: Restricted package discovery to the `devcovenant` root so
  `licenses/` stays repo-only while Python packaging looks only under the
  module folder.
  Files:
  pyproject.toml
- 2026-01-31: Added pinned dependency manifests, the third-party license
  report, and the dependency-license-sync policy so PyYAML and semver stay
  documented alongside versioned metadata for 0.2.2.
  Files:
  requirements.in
  requirements.lock
  THIRD_PARTY_LICENSES.md
  licenses/PyYAML-6.0.2.txt
  licenses/semver-3.0.2.txt
  AGENTS.md
  README.md
  CONTRIBUTING.md
  SPEC.md
  PLAN.md
  pyproject.toml
  VERSION
  CHANGELOG.md
  devcovenant/README.md
  devcovenant/common_policy_patches/README.md
  devcovenant/custom/policy_scripts/README.md
  devcovenant/registry.json
- 2026-01-12: Released DevCovenant 0.2.2 after confirming the gate sequence,
  dependency-license-sync refresh, and changelog updates; publish workflow can
  run once PyPI tokens prove healthy.
  Files:
  AGENTS.md
  README.md
  SPEC.md
  PLAN.md
  CHANGELOG.md
  pyproject.toml

## Version 0.2.1
- 2026-01-11: Published follow-up release with refreshed metadata so PyPI
  surfaces the README description and the mandatory gate documentation
  remains synced.
-  Files:
-  pyproject.toml
-  VERSION
-  README.md
-  AGENTS.md
-  SPEC.md
-  PLAN.md
-  CONTRIBUTING.md
-  devcovenant/README.md
-  devcovenant/common_policy_patches/README.md
-  devcovenant/custom/policy_scripts/README.md
-  LICENSE
-  CHANGELOG.md
-  LONG_DESCRIPTION.md
-  devcovenant/registry.json

## Version 0.2.0
- 2026-01-16: Mandated the pre-commit/tests gate for every change, updated
  DevFlow run-gates policy+tests to treat docs as code, and synchronized the
  registry.
  Files:
  AGENTS.md
  SPEC.md
  devcovenant/core/policy_scripts/devflow_run_gates.py
  devcovenant/core/tests/test_policies/test_devflow_run_gates.py
  devcovenant/registry.json
  devcovenant/core/stock_policy_texts.json
- 2026-01-15: Fixed the structure guard test so it only creates each required
  directory once and no longer raises `FileExistsError`. (AI assistant)
  Files:
  devcovenant/core/tests/test_policies/test_devcov_structure_guard.py
- 2026-01-15: Ensured the CI workflow installs PyYAML so required tooling
  matches the SPEC installation guidance. (AI assistant)
  Files:
  .github/workflows/ci.yml
- 2026-01-14: Relocated the built-in fixers beside their policies, kept
  compatibility stubs, and refreshed all docs/tests to describe the new layout
  while bumping SPEC/PLAN/README/DEVCOVENANT to v0.2.0. (AI assistant)
  Files:
  README.md
  SPEC.md
  PLAN.md
  devcovenant/core/policy_scripts/fixers/dependency_license_sync.py
  devcovenant/core/policy_scripts/fixers/last_updated_placement.py
  devcovenant/core/policy_scripts/fixers/no_future_dates.py
  devcovenant/core/policy_scripts/fixers/raw_string_escapes.py
  devcovenant/core/fixers/dependency_license_sync.py
  devcovenant/core/fixers/last_updated_placement.py
  devcovenant/core/fixers/no_future_dates.py
  devcovenant/core/fixers/raw_string_escapes.py
  devcovenant/tests/test_policies/test_raw_string_escapes.py
  devcovenant/tests/test_policies/test_no_future_dates.py
- 2026-01-14: Added install/uninstall manifest coverage and
  `devcov_core_include` toggling tests to prove the CLI-driven installer
  records options properly.
  Files:
  devcovenant/core/tests/test_install.py
- 2026-01-11: Documented the workflow block in AGENTS.md and noted that
  `devcovenant/core/engine.py` now loads fixers via the new layout. (AI
  assistant)
  Files:
  AGENTS.md
  devcovenant/core/engine.py
- 2026-01-11: Bumped DevCovenant version markup and metadata files to 0.2.0 so
  the engine overrides remain consistent. (AI assistant)
  Files:
  CONTRIBUTING.md
  devcovenant/README.md
  devcovenant/common_policy_patches/README.md
  devcovenant/custom/policy_scripts/README.md
  pyproject.toml
  VERSION
  LICENSE

## Version 0.1.2
- 2026-01-13: Updated SPEC.md and PLAN.md to capture the CLI-driven install/
  uninstall lifecycle, the core/custom layout, and the new `apply`/
  `devcov_core_include` behaviors.
  The `devcov begin`/`end` documentation blocks ensure the CLI/fixer refactors
  can finish. (AI assistant)
  Files:
  SPEC.md
  PLAN.md

## Version 0.1.1
- 2026-01-11: Finalized the core/user layout, moved fixers into
  `devcovenant/core`, expanded core exclusion paths, and refreshed structure
  guard/tests/docs. (AI assistant)
  Files:
  .gitignore
  .pre-commit-config.yaml
  AGENTS.md
  CHANGELOG.md
  devcovenant/registry.json
  CONTRIBUTING.md
  PLAN.md
  README.md
  SPEC.md
  devcov_check.py
  devcovenant/README.md
  devcovenant/__init__.py
  devcovenant/__main__.py
  devcovenant/cli.py
  devcovenant/common_policy_patches/README.md
  devcovenant/common_policy_scripts/documentation_growth_tracking.py
  devcovenant/config.yaml
  devcovenant/core/__init__.py
  devcovenant/core/base.py
  devcovenant/core/policy_scripts/__init__.py
  devcovenant/core/policy_scripts/changelog_coverage.py
  devcovenant/core/policy_scripts/dependency_license_sync.py
  devcovenant/core/policy_scripts/devcov_self_enforcement.py
  devcovenant/core/policy_scripts/devcov_structure_guard.py
  devcovenant/core/policy_scripts/devflow_run_gates.py
  devcovenant/core/policy_scripts/docstring_and_comment_coverage.py
  devcovenant/core/policy_scripts/documentation_growth_tracking.py
  devcovenant/core/policy_scripts/gcv_script_naming.py
  devcovenant/core/policy_scripts/last_updated_placement.py
  devcovenant/core/policy_scripts/line_length_limit.py
  devcovenant/core/policy_scripts/managed_bench.py
  devcovenant/core/policy_scripts/name_clarity.py
  devcovenant/core/policy_scripts/new_modules_need_tests.py
  devcovenant/core/policy_scripts/no_future_dates.py
  devcovenant/core/policy_scripts/patches_txt_sync.py
  devcovenant/core/policy_scripts/policy_text_presence.py
  devcovenant/core/policy_scripts/raw_string_escapes.py
  devcovenant/core/policy_scripts/read_only_directories.py
  devcovenant/core/policy_scripts/security_compliance_notes.py
  devcovenant/core/policy_scripts/security_scanner.py
  devcovenant/core/policy_scripts/semantic_version_scope.py
  devcovenant/core/policy_scripts/stock_policy_text_sync.py
  devcovenant/core/policy_scripts/track_test_status.py
  devcovenant/core/policy_scripts/version_sync.py
  devcovenant/core/engine.py
  devcovenant/core/fixers/__init__.py
  devcovenant/core/fixers/dependency_license_sync.py
  devcovenant/core/fixers/last_updated_placement.py
  devcovenant/core/fixers/no_future_dates.py
  devcovenant/core/fixers/raw_string_escapes.py
  devcovenant/core/hooks/pre_commit.py
  devcovenant/core/parser.py
  devcovenant/core/policy_locations.py
  devcovenant/core/policy_scripts/__init__.py
  devcovenant/core/policy_scripts/changelog_coverage.py
  devcovenant/core/policy_scripts/dependency_license_sync.py
  devcovenant/core/policy_scripts/devcov_self_enforcement.py
  devcovenant/core/policy_scripts/devcov_structure_guard.py
  devcovenant/core/policy_scripts/devflow_run_gates.py
  devcovenant/core/policy_scripts/docstring_and_comment_coverage.py
  devcovenant/core/policy_scripts/documentation_growth_tracking.py
  devcovenant/core/policy_scripts/gcv_script_naming.py
  devcovenant/core/policy_scripts/last_updated_placement.py
  devcovenant/core/policy_scripts/line_length_limit.py
  devcovenant/core/policy_scripts/managed_bench.py
  devcovenant/core/policy_scripts/name_clarity.py
  devcovenant/core/policy_scripts/new_modules_need_tests.py
  devcovenant/core/policy_scripts/no_future_dates.py
  devcovenant/core/policy_scripts/patches_txt_sync.py
  devcovenant/core/policy_scripts/policy_text_presence.py
  devcovenant/core/policy_scripts/raw_string_escapes.py
  devcovenant/core/policy_scripts/read_only_directories.py
  devcovenant/core/policy_scripts/security_compliance_notes.py
  devcovenant/core/policy_scripts/security_scanner.py
  devcovenant/core/policy_scripts/semantic_version_scope.py
  devcovenant/core/policy_scripts/stock_policy_text_sync.py
  devcovenant/core/policy_scripts/track_test_status.py
  devcovenant/core/policy_scripts/version_sync.py
  devcovenant/core/policy_texts.py
  devcovenant/core/registry.py
  devcovenant/core/selectors.py
  devcovenant/core/stock_policy_texts.json
  devcovenant/core/tests/__init__.py
  devcovenant/core/tests/test_devcov_check.py
  devcovenant/core/tests/test_engine.py
  devcovenant/core/tests/test_main_entrypoint.py
  devcovenant/core/tests/test_parser.py
  devcovenant/core/tests/test_policies/test_changelog_coverage.py
  devcovenant/core/tests/test_policies/test_dependency_license_sync.py
  devcovenant/core/tests/test_policies/test_devcov_self_enforcement.py
  devcovenant/core/tests/test_policies/test_devcov_structure_guard.py
  devcovenant/core/tests/test_policies/test_devflow_run_gates.py
  devcovenant/core/tests/test_policies/test_docstring_and_comment_coverage.py
  devcovenant/core/tests/test_policies/test_documentation_growth_tracking.py
  devcovenant/core/tests/test_policies/test_gcv_script_naming.py
  devcovenant/core/tests/test_policies/test_last_updated_placement.py
  devcovenant/core/tests/test_policies/test_line_length_limit.py
  devcovenant/core/tests/test_policies/test_managed_bench.py
  devcovenant/core/tests/test_policies/test_name_clarity.py
  devcovenant/core/tests/test_policies/test_new_modules_need_tests.py
  devcovenant/core/tests/test_policies/test_no_future_dates.py
  devcovenant/core/tests/test_policies/test_patches_txt_sync.py
  devcovenant/core/tests/test_policies/test_policy_text_presence.py
  devcovenant/core/tests/test_policies/test_raw_string_escapes.py
  devcovenant/core/tests/test_policies/test_read_only_directories.py
  devcovenant/core/tests/test_policies/test_security_compliance_notes.py
  devcovenant/core/tests/test_policies/test_security_scanner.py
  devcovenant/core/tests/test_policies/test_semantic_version_scope.py
  devcovenant/core/tests/test_policies/test_stock_policy_text_sync.py
  devcovenant/core/tests/test_policies/test_track_test_status.py
  devcovenant/core/tests/test_policies/test_version_sync.py
  devcovenant/core/tests/test_policy_patches.py
  devcovenant/core/tests/test_selectors.py
  devcovenant/core/update_hashes.py
  devcovenant/custom/policy_scripts/README.md
  devcovenant/custom/policy_scripts/__init__.py
  devcovenant/custom/__init__.py
  devcovenant/custom_policy_scripts/README.md
  devcovenant/custom_policy_scripts/__init__.py
  devcovenant/fixers/__init__.py
  devcovenant/fixers/last_updated_placement.py
  devcovenant/policy_scripts/devcov_structure_guard.py
  devcovenant/policy_scripts/managed_bench.py
  devcovenant/policy_scripts/name_clarity.py
  devcovenant/policy_scripts/new_modules_need_tests.py
  devcovenant/policy_scripts/semantic_version_scope.py
  devcovenant/policy_scripts/version_sync.py
  devcovenant/registry.json
  devcovenant/tests/test_devcovenant_check.py
  devcovenant/tests/test_policies/test_documentation_growth_tracking.py
  devcovenant/waivers/README.md
  tools/install_devcovenant.py
  tools/templates/LICENSE_GPL-3.0.txt
  tools/uninstall_devcovenant.py
- 2026-01-11: Moved core engine/policy code under `devcovenant/core`, aligned
  core exclusion config/docs/install flow, refreshed shims/tests, and added
  untracked-module detection plus entrypoint coverage. (AI assistant)
  Files:
  .gitignore
  .pre-commit-config.yaml
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/__init__.py
  devcovenant/base.py
  devcovenant/cli.py
  devcovenant/common_policy_patches/README.md
  devcovenant/common_policy_scripts/__init__.py
  devcovenant/common_policy_scripts/changelog_coverage.py
  devcovenant/common_policy_scripts/dependency_license_sync.py
  devcovenant/common_policy_scripts/devcov_self_enforcement.py
  devcovenant/common_policy_scripts/devcov_structure_guard.py
  devcovenant/common_policy_scripts/devflow_run_gates.py
  devcovenant/common_policy_scripts/docstring_and_comment_coverage.py
  devcovenant/common_policy_scripts/documentation_growth_tracking.py
  devcovenant/common_policy_scripts/gcv_script_naming.py
  devcovenant/common_policy_scripts/last_updated_placement.py
  devcovenant/common_policy_scripts/line_length_limit.py
  devcovenant/common_policy_scripts/managed_bench.py
  devcovenant/common_policy_scripts/name_clarity.py
  devcovenant/common_policy_scripts/new_modules_need_tests.py
  devcovenant/common_policy_scripts/no_future_dates.py
  devcovenant/common_policy_scripts/patches_txt_sync.py
  devcovenant/common_policy_scripts/raw_string_escapes.py
  devcovenant/common_policy_scripts/read_only_directories.py
  devcovenant/common_policy_scripts/security_compliance_notes.py
  devcovenant/common_policy_scripts/security_scanner.py
  devcovenant/common_policy_scripts/semantic_version_scope.py
  devcovenant/common_policy_scripts/track_test_status.py
  devcovenant/common_policy_scripts/version_sync.py
  devcovenant/config.yaml
  devcovenant/core/__init__.py
  devcovenant/core/base.py
  devcovenant/core/policy_scripts/__init__.py
  devcovenant/core/policy_scripts/changelog_coverage.py
  devcovenant/core/policy_scripts/dependency_license_sync.py
  devcovenant/core/policy_scripts/devcov_self_enforcement.py
  devcovenant/core/policy_scripts/devcov_structure_guard.py
  devcovenant/core/policy_scripts/devflow_run_gates.py
  devcovenant/core/policy_scripts/docstring_and_comment_coverage.py
  devcovenant/core/policy_scripts/documentation_growth_tracking.py
  devcovenant/core/policy_scripts/gcv_script_naming.py
  devcovenant/core/policy_scripts/last_updated_placement.py
  devcovenant/core/policy_scripts/line_length_limit.py
  devcovenant/core/policy_scripts/managed_bench.py
  devcovenant/core/policy_scripts/name_clarity.py
  devcovenant/core/policy_scripts/new_modules_need_tests.py
  devcovenant/core/policy_scripts/no_future_dates.py
  devcovenant/core/policy_scripts/patches_txt_sync.py
  devcovenant/core/policy_scripts/policy_text_presence.py
  devcovenant/core/policy_scripts/raw_string_escapes.py
  devcovenant/core/policy_scripts/read_only_directories.py
  devcovenant/core/policy_scripts/security_compliance_notes.py
  devcovenant/core/policy_scripts/security_scanner.py
  devcovenant/core/policy_scripts/semantic_version_scope.py
  devcovenant/core/policy_scripts/stock_policy_text_sync.py
  devcovenant/core/policy_scripts/track_test_status.py
  devcovenant/core/policy_scripts/version_sync.py
  devcovenant/core/engine.py
  devcovenant/core/fixers/__init__.py
  devcovenant/core/fixers/dependency_license_sync.py
  devcovenant/core/fixers/last_updated_placement.py
  devcovenant/core/fixers/no_future_dates.py
  devcovenant/core/fixers/raw_string_escapes.py
  devcovenant/core/hooks/pre_commit.py
  devcovenant/core/parser.py
  devcovenant/core/policy_locations.py
  devcovenant/core/policy_scripts/__init__.py
  devcovenant/core/policy_scripts/changelog_coverage.py
  devcovenant/core/policy_scripts/dependency_license_sync.py
  devcovenant/core/policy_scripts/devcov_self_enforcement.py
  devcovenant/core/policy_scripts/devcov_structure_guard.py
  devcovenant/core/policy_scripts/devflow_run_gates.py
  devcovenant/core/policy_scripts/docstring_and_comment_coverage.py
  devcovenant/core/policy_scripts/documentation_growth_tracking.py
  devcovenant/core/policy_scripts/gcv_script_naming.py
  devcovenant/core/policy_scripts/last_updated_placement.py
  devcovenant/core/policy_scripts/line_length_limit.py
  devcovenant/core/policy_scripts/managed_bench.py
  devcovenant/core/policy_scripts/name_clarity.py
  devcovenant/core/policy_scripts/new_modules_need_tests.py
  devcovenant/core/policy_scripts/no_future_dates.py
  devcovenant/core/policy_scripts/patches_txt_sync.py
  devcovenant/core/policy_scripts/policy_text_presence.py
  devcovenant/core/policy_scripts/raw_string_escapes.py
  devcovenant/core/policy_scripts/read_only_directories.py
  devcovenant/core/policy_scripts/security_compliance_notes.py
  devcovenant/core/policy_scripts/security_scanner.py
  devcovenant/core/policy_scripts/semantic_version_scope.py
  devcovenant/core/policy_scripts/stock_policy_text_sync.py
  devcovenant/core/policy_scripts/track_test_status.py
  devcovenant/core/policy_scripts/version_sync.py
  devcovenant/core/policy_texts.py
  devcovenant/core/registry.py
  devcovenant/core/selectors.py
  devcovenant/core/stock_policy_texts.json
  devcovenant/core/tests/__init__.py
  devcovenant/core/tests/test_devcov_check.py
  devcovenant/core/tests/test_engine.py
  devcovenant/core/tests/test_main_entrypoint.py
  devcovenant/core/tests/test_parser.py
  devcovenant/core/tests/test_policies/test_changelog_coverage.py
  devcovenant/core/tests/test_policies/test_dependency_license_sync.py
  devcovenant/core/tests/test_policies/test_devcov_self_enforcement.py
  devcovenant/core/tests/test_policies/test_devcov_structure_guard.py
  devcovenant/core/tests/test_policies/test_devflow_run_gates.py
  devcovenant/core/tests/test_policies/test_docstring_and_comment_coverage.py
  devcovenant/core/tests/test_policies/test_documentation_growth_tracking.py
  devcovenant/core/tests/test_policies/test_gcv_script_naming.py
  devcovenant/core/tests/test_policies/test_last_updated_placement.py
  devcovenant/core/tests/test_policies/test_line_length_limit.py
  devcovenant/core/tests/test_policies/test_managed_bench.py
  devcovenant/core/tests/test_policies/test_name_clarity.py
  devcovenant/core/tests/test_policies/test_new_modules_need_tests.py
  devcovenant/core/tests/test_policies/test_no_future_dates.py
  devcovenant/core/tests/test_policies/test_patches_txt_sync.py
  devcovenant/core/tests/test_policies/test_policy_text_presence.py
  devcovenant/core/tests/test_policies/test_raw_string_escapes.py
  devcovenant/core/tests/test_policies/test_read_only_directories.py
  devcovenant/core/tests/test_policies/test_security_compliance_notes.py
  devcovenant/core/tests/test_policies/test_security_scanner.py
  devcovenant/core/tests/test_policies/test_semantic_version_scope.py
  devcovenant/core/tests/test_policies/test_stock_policy_text_sync.py
  devcovenant/core/tests/test_policies/test_track_test_status.py
  devcovenant/core/tests/test_policies/test_version_sync.py
  devcovenant/core/tests/test_policy_patches.py
  devcovenant/core/tests/test_selectors.py
  devcovenant/core/update_hashes.py
  devcovenant/custom/policy_scripts/README.md
  devcovenant/engine.py
  devcovenant/fixers/__init__.py
  devcovenant/fixers/dependency_license_sync.py
  devcovenant/fixers/last_updated_placement.py
  devcovenant/fixers/no_future_dates.py
  devcovenant/fixers/raw_string_escapes.py
  devcovenant/hooks/pre_commit.py
  devcovenant/parser.py
  devcovenant/policy_locations.py
  devcovenant/policy_scripts/__init__.py
  devcovenant/policy_scripts/changelog_coverage.py
  devcovenant/policy_scripts/dependency_license_sync.py
  devcovenant/policy_scripts/devcov_self_enforcement.py
  devcovenant/policy_scripts/devcov_structure_guard.py
  devcovenant/policy_scripts/devflow_run_gates.py
  devcovenant/policy_scripts/docstring_and_comment_coverage.py
  devcovenant/policy_scripts/documentation_growth_tracking.py
  devcovenant/policy_scripts/gcv_script_naming.py
  devcovenant/policy_scripts/last_updated_placement.py
  devcovenant/policy_scripts/line_length_limit.py
  devcovenant/policy_scripts/managed_bench.py
  devcovenant/policy_scripts/name_clarity.py
  devcovenant/policy_scripts/new_modules_need_tests.py
  devcovenant/policy_scripts/no_future_dates.py
  devcovenant/policy_scripts/patches_txt_sync.py
  devcovenant/policy_scripts/raw_string_escapes.py
  devcovenant/policy_scripts/read_only_directories.py
  devcovenant/policy_scripts/security_compliance_notes.py
  devcovenant/policy_scripts/security_scanner.py
  devcovenant/policy_scripts/semantic_version_scope.py
  devcovenant/policy_scripts/track_test_status.py
  devcovenant/policy_scripts/version_sync.py
  devcovenant/registry.json
  devcovenant/registry.py
  devcovenant/selectors.py
  devcovenant/tests/__init__.py
  devcovenant/tests/test_devcovenant_check.py
  devcovenant/tests/test_engine.py
  devcovenant/tests/test_parser.py
  devcovenant/tests/test_policies/test_changelog_coverage.py
  devcovenant/tests/test_policies/test_dependency_license_sync.py
  devcovenant/tests/test_policies/test_devcov_self_enforcement.py
  devcovenant/tests/test_policies/test_devcov_structure_guard.py
  devcovenant/tests/test_policies/test_devflow_run_gates.py
  devcovenant/tests/test_policies/test_docstring_and_comment_coverage.py
  devcovenant/tests/test_policies/test_documentation_growth_tracking.py
  devcovenant/tests/test_policies/test_gcv_script_naming.py
  devcovenant/tests/test_policies/test_last_updated_placement.py
  devcovenant/tests/test_policies/test_line_length_limit.py
  devcovenant/tests/test_policies/test_managed_bench.py
  devcovenant/tests/test_policies/test_name_clarity.py
  devcovenant/tests/test_policies/test_new_modules_need_tests.py
  devcovenant/tests/test_policies/test_no_future_dates.py
  devcovenant/tests/test_policies/test_patches_txt_sync.py
  devcovenant/tests/test_policies/test_raw_string_escapes.py
  devcovenant/tests/test_policies/test_read_only_directories.py
  devcovenant/tests/test_policies/test_security_compliance_notes.py
  devcovenant/tests/test_policies/test_security_scanner.py
  devcovenant/tests/test_policies/test_semantic_version_scope.py
  devcovenant/tests/test_policies/test_track_test_status.py
  devcovenant/tests/test_policies/test_version_sync.py
  devcovenant/tests/test_policy_patches.py
  devcovenant/tests/test_selectors.py
  devcovenant/update_hashes.py
  devcovenant/waivers/README.md
  devcovenant_check.py
  tools/install_devcovenant.py
  tools/uninstall_devcovenant.py

- 2026-01-11: Extended core exclusion handling, added compatibility fixers,
  and updated installer/config/docs for the core layout. (AI assistant)
  Files:
  README.md
  devcovenant/README.md
  devcovenant/config.yaml
  devcovenant/fixers/__init__.py
  devcovenant/fixers/dependency_license_sync.py
  devcovenant/fixers/last_updated_placement.py
  devcovenant/fixers/no_future_dates.py
  devcovenant/fixers/raw_string_escapes.py
  devcovenant/policy_scripts/__init__.py
  devcovenant/registry.json
  devcovenant/core/policy_scripts/devcov_structure_guard.py
  devcovenant/core/tests/test_devcov_check.py
  devcovenant/core/tests/test_policies/test_devflow_run_gates.py
  devcovenant/core/tests/test_policies/test_docstring_and_comment_coverage.py
  devcovenant/core/tests/test_policies/test_documentation_growth_tracking.py
  devcovenant/core/tests/test_policies/test_gcv_script_naming.py
  devcovenant/core/tests/test_policies/test_line_length_limit.py
  devcovenant/core/tests/test_policies/test_managed_bench.py
  devcovenant/core/tests/test_policies/test_name_clarity.py
  devcovenant/core/tests/test_policies/test_no_future_dates.py
  devcovenant/core/tests/test_policies/test_patches_txt_sync.py
  devcovenant/core/tests/test_policies/test_raw_string_escapes.py
  devcovenant/core/tests/test_policies/test_security_scanner.py
  devcovenant/core/tests/test_policies/test_version_sync.py
  devcovenant/core/hooks/pre_commit.py
  devcovenant/core/update_hashes.py
  devcovenant/core/tests/test_policies/test_devcov_structure_guard.py
  tools/install_devcovenant.py
- 2026-01-11: Reworded policy messaging and documentation to prefer
  `python3`, clarified patch-script behavior, and aligned documentation-growth
  rules with the user-facing file definition. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/__main__.py
  devcovenant/common_policy_patches/README.md
  devcovenant/common_policy_scripts/devflow_run_gates.py
  devcovenant/common_policy_scripts/documentation_growth_tracking.py
  devcovenant/common_policy_scripts/stock_policy_text_sync.py
  devcovenant/common_policy_scripts/track_test_status.py
  devcovenant/custom/policy_scripts/README.md
  devcovenant/engine.py
  devcovenant/parser.py
  devcovenant/registry.json
  devcovenant/stock_policy_texts.json
- 2026-01-11: Replaced waiver metadata with an `apply` flag, added fiducial
  reminders, and removed the waiver/override file system. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/common_policy_scripts/semantic_version_scope.py
  devcovenant/engine.py
  devcovenant/parser.py
  devcovenant/registry.json
  devcovenant/tests/test_parser.py
  devcovenant/tests/test_policy_patches.py
  devcovenant/tests/test_policies/test_read_only_directories.py
  devcovenant/tests/test_policies/test_semantic_version_scope.py
- 2026-01-11: Added CLI-only installer modes, preserved custom policy
  artifacts on updates, expanded install options, and ensured CI installs
  required tooling. (AI assistant)
  Files:
  .github/workflows/ci.yml
  CHANGELOG.md
  PLAN.md
  SPEC.md
  tools/install_devcovenant.py
- 2026-01-11: Treat separator-only policy descriptions as missing so policy
  text enforcement is meaningful. (AI assistant)
  Files:
  CHANGELOG.md
  devcovenant/common_policy_scripts/policy_text_presence.py
  devcovenant/registry.json
- 2026-01-11: Documented the policy text helpers, tightened naming, and
  excluded the stock policy text map from line-length checks. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  devcovenant/policy_texts.py
  devcovenant/registry.json
  devcovenant/tests/test_policies/test_policy_text_presence.py
  devcovenant/tests/test_policies/test_stock_policy_text_sync.py
- 2026-01-11: Filled in policy descriptions for all stock policies and
  refreshed stock policy text baselines and registry hashes. (AI assistant)
  Files:
  AGENTS.md
  devcovenant/registry.json
  devcovenant/stock_policy_texts.json
- 2026-01-11: Added stock policy text tooling, SPEC docs, devcov naming, and
  the devcov check wrapper rename. (AI assistant)
  Files:
  .gitignore
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  SPEC.md
  devcov_check.py
  devcovenant/__main__.py
  devcovenant/README.md
  devcovenant/cli.py
  devcovenant/common_policy_patches/README.md
  devcovenant/common_policy_scripts/devcov_structure_guard.py
  devcovenant/common_policy_scripts/documentation_growth_tracking.py
  devcovenant/common_policy_scripts/policy_text_presence.py
  devcovenant/common_policy_scripts/semantic_version_scope.py
  devcovenant/common_policy_scripts/stock_policy_text_sync.py
  devcovenant/custom/policy_scripts/README.md
  devcovenant/policy_scripts/devcov_structure_guard.py
  devcovenant/policy_scripts/policy_text_presence.py
  devcovenant/policy_scripts/stock_policy_text_sync.py
  devcovenant/policy_texts.py
  devcovenant/registry.json
  devcovenant/stock_policy_texts.json
  devcovenant/tests/test_devcov_check.py
  devcovenant/tests/test_policies/test_devcov_structure_guard.py
  devcovenant/tests/test_policies/test_documentation_growth_tracking.py
  devcovenant/tests/test_policies/test_policy_text_presence.py
  devcovenant/tests/test_policies/test_semantic_version_scope.py
  devcovenant/tests/test_policies/test_stock_policy_text_sync.py
  devcovenant/waivers/README.md
  devcovenant_check.py
  devcovenant/tests/test_devcovenant_check.py
  tools/install_devcovenant.py
  tools/uninstall_devcovenant.py
  tools/templates/LICENSE_GPL-3.0.txt
- 2026-01-11: Adopted DEVCOV markers, standardized .devcov metadata paths,
  and updated documentation and policy compatibility for the new naming.
  (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/common_policy_patches/README.md
  devcovenant/common_policy_scripts/devcov_structure_guard.py
  devcovenant/common_policy_scripts/documentation_growth_tracking.py
  devcovenant/common_policy_scripts/semantic_version_scope.py
  devcovenant/custom/policy_scripts/README.md
  devcovenant/policy_scripts/devcov_structure_guard.py
  devcovenant/registry.json
  devcovenant/tests/test_policies/test_documentation_growth_tracking.py
  devcovenant/tests/test_policies/test_semantic_version_scope.py
  devcovenant/waivers/README.md
  tools/install_devcovenant.py
  tools/uninstall_devcovenant.py
  tools/templates/LICENSE_GPL-3.0.txt
- 2026-01-11: Switched DevCovenant markers to the DEVCOV prefix and clarified
  first-run guidance in docs and AGENTS. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  README.md
  devcovenant/README.md
  tools/install_devcovenant.py
  tools/uninstall_devcovenant.py
- 2026-01-11: Raised documentation quality guidance and added install-time
  GPL-3.0 license template for user repos. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/common_policy_patches/README.md
  devcovenant/common_policy_scripts/devcov_structure_guard.py
  devcovenant/common_policy_scripts/documentation_growth_tracking.py
  devcovenant/custom/policy_scripts/README.md
  devcovenant/policy_scripts/devcov_structure_guard.py
  devcovenant/registry.json
  devcovenant/tests/test_policies/test_documentation_growth_tracking.py
  devcovenant/waivers/README.md
  tools/install_devcovenant.py
  tools/templates/LICENSE_GPL-3.0.txt
- 2026-01-11: Expanded DevCovenant documentation and added quality checks for
  documentation growth enforcement. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/common_policy_patches/README.md
  devcovenant/common_policy_scripts/devcov_structure_guard.py
  devcovenant/common_policy_scripts/documentation_growth_tracking.py
  devcovenant/custom/policy_scripts/README.md
  devcovenant/policy_scripts/devcov_structure_guard.py
  devcovenant/registry.json
  devcovenant/tests/test_policies/test_documentation_growth_tracking.py
  devcovenant/waivers/README.md
- 2026-01-11: Bootstrapped standalone DevCovenant repo structure, core docs,
  and versioned metadata. (AI assistant)
  Files:
  .github/workflows/ci.yml
  .gitignore
  .pre-commit-config.yaml
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  LICENSE
  PLAN.md
  README.md
  VERSION
  devcovenant/README.md
  devcovenant/__init__.py
  devcovenant/base.py
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/engine.py
  devcovenant/fixers/__init__.py
  devcovenant/fixers/dependency_license_sync.py
  devcovenant/fixers/last_updated_placement.py
  devcovenant/fixers/no_future_dates.py
  devcovenant/fixers/raw_string_escapes.py
  devcovenant/hooks/pre_commit.py
  devcovenant/parser.py
  devcovenant/policy_scripts/__init__.py
  devcovenant/policy_scripts/changelog_coverage.py
  devcovenant/policy_scripts/dependency_license_sync.py
  devcovenant/policy_scripts/devcov_self_enforcement.py
  devcovenant/policy_scripts/devflow_run_gates.py
  devcovenant/policy_scripts/docstring_and_comment_coverage.py
  devcovenant/policy_scripts/documentation_growth_tracking.py
  devcovenant/policy_scripts/gcv_script_naming.py
  devcovenant/policy_scripts/last_updated_placement.py
  devcovenant/policy_scripts/line_length_limit.py
  devcovenant/policy_scripts/managed_bench.py
  devcovenant/policy_scripts/name_clarity.py
  devcovenant/policy_scripts/new_modules_need_tests.py
  devcovenant/policy_scripts/no_future_dates.py
  devcovenant/policy_scripts/patches_txt_sync.py
  devcovenant/policy_scripts/raw_string_escapes.py
  devcovenant/policy_scripts/read_only_directories.py
  devcovenant/policy_scripts/security_compliance_notes.py
  devcovenant/policy_scripts/security_scanner.py
  devcovenant/policy_scripts/semantic_version_scope.py
  devcovenant/policy_scripts/track_test_status.py
  devcovenant/policy_scripts/version_sync.py
  devcovenant/registry.json
  devcovenant/registry.py
  devcovenant/selectors.py
  devcovenant/tests/__init__.py
  devcovenant/tests/test_devcovenant_check.py
  devcovenant/tests/test_engine.py
  devcovenant/tests/test_parser.py
  devcovenant/tests/test_policies/test_changelog_coverage.py
  devcovenant/tests/test_policies/test_dependency_license_sync.py
  devcovenant/tests/test_policies/test_devcov_self_enforcement.py
  devcovenant/tests/test_policies/test_devflow_run_gates.py
  devcovenant/tests/test_policies/test_docstring_and_comment_coverage.py
  devcovenant/tests/test_policies/test_documentation_growth_tracking.py
  devcovenant/tests/test_policies/test_gcv_script_naming.py
  devcovenant/tests/test_policies/test_last_updated_placement.py
  devcovenant/tests/test_policies/test_line_length_limit.py
  devcovenant/tests/test_policies/test_managed_bench.py
  devcovenant/tests/test_policies/test_name_clarity.py
  devcovenant/tests/test_policies/test_new_modules_need_tests.py
  devcovenant/tests/test_policies/test_no_future_dates.py
  devcovenant/tests/test_policies/test_patches_txt_sync.py
  devcovenant/tests/test_policies/test_raw_string_escapes.py
  devcovenant/tests/test_policies/test_read_only_directories.py
  devcovenant/tests/test_policies/test_security_compliance_notes.py
  devcovenant/tests/test_policies/test_security_scanner.py
  devcovenant/tests/test_policies/test_semantic_version_scope.py
  devcovenant/tests/test_policies/test_track_test_status.py
  devcovenant/tests/test_policies/test_version_sync.py
  devcovenant/tests/test_selectors.py
  devcovenant/update_hashes.py
  devcovenant/waivers/README.md
  devcovenant_check.py
  pyproject.toml
  tools/install_devcovenant.py
  tools/run_pre_commit.py
  tools/run_tests.py
  tools/uninstall_devcovenant.py
  tools/update_lock.py
  tools/update_test_status.py
  devcovenant/common_policy_patches/README.md
  devcovenant/common_policy_patches/__init__.py
  devcovenant/common_policy_scripts/__init__.py
  devcovenant/common_policy_scripts/changelog_coverage.py
  devcovenant/common_policy_scripts/dependency_license_sync.py
  devcovenant/common_policy_scripts/devcov_self_enforcement.py
  devcovenant/common_policy_scripts/devcov_structure_guard.py
  devcovenant/common_policy_scripts/devflow_run_gates.py
  devcovenant/common_policy_scripts/docstring_and_comment_coverage.py
  devcovenant/common_policy_scripts/documentation_growth_tracking.py
  devcovenant/common_policy_scripts/gcv_script_naming.py
  devcovenant/common_policy_scripts/last_updated_placement.py
  devcovenant/common_policy_scripts/line_length_limit.py
  devcovenant/common_policy_scripts/managed_bench.py
  devcovenant/common_policy_scripts/name_clarity.py
  devcovenant/common_policy_scripts/new_modules_need_tests.py
  devcovenant/common_policy_scripts/no_future_dates.py
  devcovenant/common_policy_scripts/patches_txt_sync.py
  devcovenant/common_policy_scripts/raw_string_escapes.py
  devcovenant/common_policy_scripts/read_only_directories.py
  devcovenant/common_policy_scripts/security_compliance_notes.py
  devcovenant/common_policy_scripts/security_scanner.py
  devcovenant/common_policy_scripts/semantic_version_scope.py
  devcovenant/common_policy_scripts/track_test_status.py
  devcovenant/common_policy_scripts/version_sync.py
  devcovenant/custom/policy_scripts/README.md
  devcovenant/custom/policy_scripts/__init__.py
  devcovenant/policy_locations.py
  devcovenant/policy_scripts/devcov_structure_guard.py
  devcovenant/tests/test_policy_patches.py
  devcovenant/tests/test_policies/test_devcov_structure_guard.py
