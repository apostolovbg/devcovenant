# Policy Map
**Version:** 0.2.6 (slim catalog)

## Overview
Each policy below lists its key metadata knobs, managed assets, and the
profiles that activate it. Activation is explicit: a policy runs only if a
profile lists it under `policies:` (global counts as a profile).

## Global Policies (activated by `global`)
- devcov-self-enforcement — registry sync; assets:
  registry/local/policy_registry.yaml
- devcov-structure-guard — repo layout; assets: registry/local/manifest.json
- policy-text-presence — AGENTS.md prose guard
- devcov-parity-guard — policy text vs descriptors
- devflow-run-gates — gate recorder; assets: run_pre_commit.py,
  run_tests.py, .devcov-state/test_status.json; overlays per profile for
  required_commands
- track-test-status — records last test run; asset:
  .devcov-state/test_status.json
- changelog-coverage — ensures CHANGELOG entries
- no-future-dates — blocks future timestamps
- read-only-directories — protects declared paths
- managed-environment — warns on missing env hints
- semantic-version-scope (disabled) — semver tag enforcement; assets: VERSION,
  CHANGELOG.md
- last-updated-placement — enforces header placement
- documentation-growth-tracking — doc quality/mentions; overlays per profile
- line-length-limit — 79-char soft cap
- version-sync — version coherence across VERSION, README, etc.
- dependency-license-sync — licenses + manifests stay in sync

## Profile-Scoped Policies
- docstring-and-comment-coverage — Profiles: python, javascript, typescript,
  go, rust, java, csharp; knobs: include/exclude selectors.
- name-clarity — Profiles: python, javascript, typescript, go, rust, java,
  csharp; knobs: selector roles, suffixes.
- new-modules-need-tests — Profiles: python, javascript, typescript, go, rust,
  java, csharp, fastapi, frappe; knobs: tests_watch_dirs, include/exclude.
- security-scanner — Profiles: python, javascript, typescript, go, rust, java,
  csharp, fastapi, frappe; knobs: include/exclude selectors.
- raw-string-escapes — Profile: python (apply disabled by default); checks
  for unsafe escapes.

- Repo-only custom policies (activated by `devcovrepo` profile or config):
  managed-doc-assets, readme-sync, devcov-raw-string-escapes.
- devflow-run-gates — gate recorder; assets: run_pre_commit.py, run_tests.py,
  .devcov-state/test_status.json; overlays per profile for required_commands
