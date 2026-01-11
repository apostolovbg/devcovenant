# Changelog

## How to Log Changes
Add one line for each substantive commit or pull request directly under the
latest version header so entries stay newest-first (descending dates). Always
confirm the actual current date before logging new changes and keep entries in
chronological order. Record timestamps as ISO dates (`YYYY-MM-DD`).

## Log changes here

## Version 0.1.1
- 2026-01-11: Bootstrapped standalone DevCovenant repo structure, core docs,
  and versioned metadata. (AI assistant)
  Files:
  .github/workflows/ci.yml
  .gitignore
  .pre-commit-config.yaml
  AGENTS.md
  CHANGELOG.md
  CITATION.cff
  CONTRIBUTING.md
  DEVCOVENANT.md
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
  devcovenant/custom_policy_scripts/README.md
  devcovenant/custom_policy_scripts/__init__.py
  devcovenant/policy_locations.py
  devcovenant/policy_scripts/devcov_structure_guard.py
  devcovenant/tests/test_policy_patches.py
  devcovenant/tests/test_policies/test_devcov_structure_guard.py
