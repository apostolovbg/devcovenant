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
- 2026-01-23: Implemented Phase F install/update convergence with
  auto-uninstall prompts, disable-policy support, version discovery
  order, and backup logging, plus docs/tests updates. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/cli_options.py
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_policy_replacements.py
  devcovenant/manifest.json
- 2026-01-23: Added manifest support for profiles and policy assets,
  updated schema docs, and aligned tests/spec. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/cli_options.py
  devcovenant/core/manifest.py
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_policy_replacements.py
  devcovenant/manifest.json
- 2026-01-23: Reordered the plan phases to separate completed and
  remaining work without revisit markers. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/README.md
  devcovenant/core/cli_options.py
  devcovenant/core/tests/test_policy_replacements.py
- 2026-01-23: Revised profile scope semantics and template layout to
  use core/custom templates with explicit global scopes. (AI assistant)
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/README.md
  devcovenant/core/cli_options.py
  devcovenant/core/tests/test_policy_replacements.py
