# Profile Map
**Version:** 0.2.6 (slim catalog)

## Overview
Profiles are static descriptors under `devcovenant/core/profiles/<name>/`.
Policies run only when listed in a profile’s `policies:` section.

## Core Profiles
- global — activates all global core policies (no custom policies); no assets.
- docs — doc helpers; policies: version-sync, documentation-growth-tracking,
  line-length-limit, last-updated-placement.
- data — data/analytics assets; policies: version-sync, documentation-growth-
  tracking, line-length-limit.
- suffixes — generated file-suffix index; policies: version-sync.
- devcovuser — shields DevCovenant artifacts in user repos; policies:
  new-modules-need-tests (limited include/exclude).
- devcovrepo (custom) — repo-only overlays; policies: documentation-growth-
  tracking, line-length-limit, new-modules-need-tests, devcov-raw-string-
  escapes, managed-doc-assets, readme-sync.

## Language / Framework Profiles
- python — dependency-license-sync, devflow-run-gates, docstring-and-comment-
  coverage, documentation-growth-tracking, line-length-limit, name-clarity,
  new-modules-need-tests, raw-string-escapes, security-scanner, version-sync.
- javascript — dependency-license-sync, devflow-run-gates, documentation-
  growth-tracking, line-length-limit, name-clarity, new-modules-need-tests,
  security-scanner, version-sync.
- typescript — same as javascript.
- java — dependency-license-sync, devflow-run-gates, documentation-growth-
  tracking, line-length-limit, name-clarity, new-modules-need-tests,
  security-scanner, version-sync.
- go — devflow-run-gates, docstring-and-comment-coverage, documentation-
  growth-tracking, line-length-limit, name-clarity, new-modules-need-tests,
  security-scanner, version-sync.
- rust — same policy set as go (matching rust overlays).
- php — dependency-license-sync, devflow-run-gates, documentation-growth-
  tracking, line-length-limit, version-sync, security-scanner/new-modules
  not yet scoped.
- ruby — dependency-license-sync, devflow-run-gates, documentation-growth-
  tracking, line-length-limit, version-sync.
- csharp — dependency-license-sync, devflow-run-gates, documentation-growth-
  tracking, line-length-limit, name-clarity, docstring-and-comment-coverage,
  new-modules-need-tests, security-scanner, version-sync.
- sql — line-length-limit, version-sync (doc growth where applicable).
- docker — line-length-limit, documentation-growth-tracking, version-sync.
- terraform — line-length-limit, documentation-growth-tracking, version-sync.
- kubernetes — line-length-limit, documentation-growth-tracking, version-sync.
- fastapi — inherits python gates where relevant: dependency-license-sync,
  devflow-run-gates, documentation-growth-tracking, line-length-limit,
  new-modules-need-tests, security-scanner, version-sync.
- frappe — python stack overlay: same as fastapi.
- dart — dependency-license-sync, devflow-run-gates, documentation-growth-
  tracking, line-length-limit, version-sync.
- flutter — same as dart plus flutter-specific assets.
- swift — dependency-license-sync, devflow-run-gates, documentation-growth-
  tracking, line-length-limit, version-sync.
- objective-c — dependency-license-sync, devflow-run-gates, documentation-
  growth-tracking, line-length-limit, version-sync.
