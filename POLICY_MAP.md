# Policy Map
**Version:** 0.2.6

## Purpose
Authoritative reference for how each policy MUST be activated and configured.
Use this to keep profiles, adapters, assets, and metadata aligned. Policies
are activated via config `policy_state`. Profiles provide metadata overlays
and assets; custom policies are opt-in via custom profiles or config overrides.

## Core Policies (global-activated)
- devcov-integrity-guard — Assets: AGENTS.md, policy descriptors,
  registry/local/policy_registry.yaml, devcovenant/registry/local/
  test_status.json; Metadata: policy_definitions, registry_file,
  test_status_file, watch_dirs, watch_files.
- devcov-structure-guard — Assets: registry/local/manifest.json; Metadata:
  enforcement, code_extensions.
- devflow-run-gates — Assets: run_pre_commit.py, run_tests.py,
  devcovenant/registry/local/test_status.json; Metadata: test_status_file,
  required_commands, require_
  pre_commit_start/end, pre_commit_command, epoch/command keys.
- changelog-coverage — Assets: CHANGELOG.md; Metadata: main_changelog,
  skipped_files, skipped_globs, summary_labels, summary_verbs.
- no-future-dates — Logic-only.
- read-only-directories — Metadata: include_globs.
- managed-environment — Metadata: expected_paths, expected_interpreters,
  required_commands, command_hints (enabled: false by default).
- semantic-version-scope — Assets: VERSION (profile override),
  CHANGELOG.md; Metadata: version_file, changelog_file
  (enabled: false).
- last-updated-placement — Assets: managed docs; Metadata: allowed_globs.
- documentation-growth-tracking — Metadata: selector roles,
  required_headings, min_word_count, mention rules; overlays expected per
  profile for user_facing suffixes/keywords and doc sets (global provides
  the baseline, devcovrepo adds devcovenant docs).
- line-length-limit — Metadata: max_length, selectors.
- version-sync — Assets: VERSION (profile override),
  README/AGENTS/CONTRIBUTING/SPEC/PLAN, LICENSE; language profiles add
  pyproject.toml or other manifests; devcovrepo overlays add
  devcovenant/README.md + devcovenant/VERSION. Metadata: version_file,
  readme_files, optional_files, pyproject_files, license_files,
  changelog_file, header_prefix.

`devcov-integrity-guard` is the active replacement for legacy integrity checks.

## Profile-Overlayed Core Policies
- dependency-license-sync — Profiles: python, javascript, typescript, java,
  csharp, php, ruby, go, rust, swift, dart, flutter, fastapi, frappe,
  objective-c. Overlays must reference each ecosystem’s manifest files; the
  policy defaults are intentionally general.
- docstring-and-comment-coverage — Adapters per language; Metadata: include/
  exclude selectors. Profiles: python, javascript, typescript, go, rust, java,
  csharp.
- name-clarity — Adapters per language; Metadata: selectors. Profiles:
  python, javascript, typescript, go, rust, java, csharp.
- new-modules-need-tests — Adapters per language; Metadata: tests_watch_dirs,
  include/exclude selectors. Profiles: python, javascript, typescript, go,
  rust, java, csharp, fastapi, frappe.
- security-scanner — Adapters per language; Metadata: include/exclude
  selectors. Profiles: python, javascript, typescript, go, rust, java, csharp,
  fastapi, frappe.
- raw-string-escapes — Metadata: apply default false; Profile: python.

## Custom Policies (repo-only, opt-in via `devcovrepo` or config)
- managed-doc-assets — Managed doc descriptors.
- readme-sync — Mirrors README into package README with repo-only blocks
  stripped.
- devcov-raw-string-escapes — Repo-only raw string guard.

## Adapters (by policy)
- docstring-and-comment-coverage: python, javascript, typescript, go, rust,
  java, csharp adapters under policy/adapters/.
- name-clarity: adapters for python, javascript, typescript, go, rust, java,
  csharp under policy/adapters/.
- new-modules-need-tests: adapters for python, javascript, typescript, go,
  rust, java, csharp; shared logic covers others via selectors.
- security-scanner: language-specific adapters for python/js/ts/go/rust/java/
  csharp.

## Required Metadata Keys (summary)
- Enforcement/activation: status, severity, enabled, enforcement.
- Selectors: include/exclude prefixes/globs/suffixes, selector_roles.
- Commands: required_commands, command_hints (devflow-run-gates, managed-
  environment).
- Dependency/license: dependency_files, third_party_file, licenses_dir.
- Versioning: version_file, readme_files, optional_files, pyproject_files,
  license_files, changelog_file.
- Docs quality: required_headings, min_word_count, mention rules.
