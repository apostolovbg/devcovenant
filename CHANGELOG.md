# Changelog
**Last Updated:** 2026-02-27
**Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
**Doc ID:** CHANGELOG
**Doc Type:** changelog
**Managed By:** DevCovenant

## How to Log Changes
Add one entry for each substantive change under the current version header.
Keep entries newest-first and record dates in ISO format (`YYYY-MM-DD`).
Each entry must include Change/Why/Impact summary lines with action verbs.
Example:
```
## Version 1.0.1

- 2026-01-23:
  Change: Fixed null-pointer crash in invoice import.
  Why: Production job failed when optional contact data was missing.
  Impact: Imports now complete for records with partial contact details.
  Files:
  billing/imports/parser.py
  billing/imports/test_parser.py
  docs/imports.md
  Long paths should be wrapped with a trailing \
  backslash and continued on the next indented line.
  Example:
  services/customer/contact/normalization/\
    fallback_rules.py

- 2026-01-22:
  Change: Fixed duplicate email notifications on retry.
  Why: Retry worker re-enqueued already-confirmed notification events.
  Impact: Users now receive one email per successful notification event.
  Files:
  notifications/worker.py
  notifications/retry.py
  notifications/test_retry.py

## Version 1.0.0

- 2026-01-21:
  Change: Added initial release for invoice import and notification flow.
  Why: Defined a first production-ready baseline for billing automation.
  Impact: Teams can import invoices and send notifications end-to-end.
  Files:
  billing/imports/parser.py
  notifications/worker.py
  CHANGELOG.md
```
<!-- DEVCOV:END -->

## Log changes here

## Version 1.0.0

- 2026-02-27:
  Change: Updated repository documentation through a full `.md` sweep,
    standardized required `gate --mid` guidance across stale docs/templates,
    and removed the `audit_digest` runtime feature, code paths, and related
    tests from the refresh/registry surface.
  Why: Removed non-canonical drift artifacts and aligned release docs with the
    current gate/runtime contracts before the 1.0.0 baseline publish flow.
  Impact: Improved operator clarity, reduced maintenance surface, and kept one
    canonical workflow authority in AGENTS while preserving gate/test evidence
    behavior.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/policies/README.md
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/core/README.md
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/audit_digest.py
  devcovenant/core/services/registry.py
  devcovenant/custom/README.md
  devcovenant/custom/policies/README.md
  devcovenant/custom/profiles/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/README.md
  tests/devcovenant/core/services/test_audit_digest.py
  tests/devcovenant/core/services/test_registry.py

- 2026-02-27:
  Change: Updated README banner tags to one-line absolute GitHub raw URLs,
    enabled defaults profile long-line escape toggles, and fixed policy-def
    metadata parsing so colon-containing continuation values stay intact for
    URL prefixes and long-line marker lists.
  Why: Fixed README/PyPI image rendering and removed parser drift that could
    truncate `allow_long_url_lines`, `long_lines_contain`, and
    `long_lines_between` metadata values.
  Impact: Improved release-readme reliability and strengthened line-length
    escape-hatch behavior so both long-line regimes and URL-based allowances
    apply consistently from managed policy metadata.
  Files:
  AGENTS.md
  CHANGELOG.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/config.yaml
  devcovenant/core/services/policy_parse.py
  devcovenant/docs/architecture.md
  devcovenant/docs/profiles.md
  tests/devcovenant/core/services/test_policy_parse.py

- 2026-02-27:
  Change: Standardized the public `1.0.0` changelog surface by removing
    pre-1.0 internal history and keeping release-baseline entries only.
  Why: Clarified external release documentation and removed internal
    stabilization details from the public narrative.
  Impact: Reduced historical exposure while preserving `1.0.0` baseline
    traceability for current operators.
  Files:
  AGENTS.md
  CHANGELOG.md

- 2026-02-27:
  Change: Updated repository and package version surfaces from `0.2.6` to
    `1.0.0` across runtime metadata, docs headers, and global template assets.
  Why: Aligned stabilization state with release intent before mainline
    orchestration and cleanup decisions.
  Impact: Strengthened a consistent 1.0.0 baseline without changing runtime
    semantics or API contracts.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  LICENSE
  PLAN.md
  POLICY_MAP.md
  PROFILE_MAP.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/VERSION
  devcovenant/__init__.py
  devcovenant/builtin/policies/README.md
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/CHANGELOG.yaml
  devcovenant/builtin/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/builtin/profiles/global/assets/LICENSE.yaml
  devcovenant/builtin/profiles/global/assets/PLAN.yaml
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/global/assets/SPEC.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/README.md
  devcovenant/custom/README.md
  devcovenant/custom/policies/README.md
  devcovenant/custom/profiles/README.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/translators.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/registry/README.md
  licenses/THIRD_PARTY_LICENSES.md
  pyproject.toml
