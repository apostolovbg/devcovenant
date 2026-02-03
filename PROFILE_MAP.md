# Profile Map
**Version:** 0.2.6

## Purpose
Declarative expectations for every shipped profile. Lists required assets,
policies, overlays, and activation rules. Profiles are explicit; no implicit
inheritance. Custom policies stay opt-in via custom profiles/config.

## Core Profiles
- global — Assets: managed doc descriptors, tooling scripts (.pre-commit,
  CI workflow, VERSION, gitignore fragments). Policies: all core global
  policies. Mode: static, update keeps descriptors current.
- docs — Assets: mkdocs.yml, doc .gitignore. Policies: version-sync,
  documentation-growth-tracking, line-length-limit, last-updated-placement.
- data — Assets: data/README.md, data/manifest.json, .gitignore. Policies:
  documentation-growth-tracking, last-updated-placement, security-scanner
  (excluded data), name-clarity, new-modules-need-tests (excluded),
  line-length-limit, version-sync.
- suffixes — Assets: suffixes.txt (merge). Policies: version-sync.
- devcovuser (custom-use) — Assets: .gitignore (merge placeholder); ignores
  vendored trees (`vendor`, `third_party`, `node_modules`). Policies:
  new-modules-need-tests with excludes to keep devcovenant core out.
- devcovrepo (custom) — Assets: .gitignore placeholder. Policies: doc-growth,
  line-length, new-modules-need-tests, devcov-raw-string-escapes, managed-
  doc-assets, readme-sync.

## Language / Framework Profiles
- python — Assets: requirements.in/lock, pyproject.toml, .python-version,
  venv.md, .gitignore; Policies: dependency-license-sync, devflow-run-gates,
  doc/comment coverage, name-clarity, new-modules-need-tests, security-
  scanner, documentation-growth-tracking, line-length-limit, version-sync,
  raw-string-escapes.
- javascript — Assets: package.json, .gitignore; Policies: dependency-license-
  sync, devflow-run-gates, doc/comment coverage, name-clarity, new-modules-
  need-tests, security-scanner, doc-growth, line-length-limit, version-sync.
- typescript — Assets: package.json, tsconfig.json, .gitignore; Policies:
  same as javascript.
- java — Assets: build.gradle, .gitignore; Policies: dependency-license-sync,
  devflow-run-gates, doc/comment coverage, name-clarity, new-modules-need-
  tests, security-scanner, doc-growth, line-length-limit, version-sync.
- go — Assets: go.mod, go.sum, .gitignore; Policies: dependency-license-sync,
  devflow-run-gates, doc/comment coverage, name-clarity, new-modules-need-
  tests, security-scanner, doc-growth, line-length-limit, version-sync.
- rust — Assets: Cargo.toml, Cargo.lock, .gitignore; Policies: dependency-
  license-sync, devflow-run-gates, doc/comment coverage, name-clarity,
  new-modules-need-tests, security-scanner, doc-growth, line-length-limit,
  version-sync.
- php — Assets: composer.json, composer.lock, phpunit.xml, .gitignore;
  Policies: dependency-license-sync, devflow-run-gates, doc-growth, line-
  length-limit, version-sync.
- ruby — Assets: Gemfile, Gemfile.lock, .gitignore; Policies: dependency-
  license-sync, devflow-run-gates, doc-growth, line-length-limit, version-
  sync.
- csharp — Assets: Project.csproj, packages.lock.json, .gitignore; Policies:
  dependency-license-sync, devflow-run-gates, doc/comment coverage, name-
  clarity, new-modules-need-tests, security-scanner, doc-growth, line-length-
  limit, version-sync.
- sql — Assets: schema.sql, .gitignore; Policies: doc-growth, line-length-
  limit, version-sync.
- docker — Assets: Dockerfile, docker-compose.yml, .dockerignore, .gitignore;
  Policies: devflow-run-gates, doc-growth, line-length-limit, version-sync.
- terraform — Assets: main.tf, variables.tf, .gitignore; Policies: doc-
  growth, line-length-limit, version-sync, devflow-run-gates (terraform
  validate).
- kubernetes — Assets: Chart.yaml, values.yaml, .gitignore; Policies:
  devflow-run-gates (helm lint), doc-growth, line-length-limit, version-sync.
- fastapi — Assets: main.py, openapi.json, .gitignore; Policies: dependency-
  license-sync, devflow-run-gates (pytest/unittest), doc/comment coverage,
  name-clarity, new-modules-need-tests, security-scanner, doc-growth,
  line-length-limit, version-sync.
- frappe — Assets: hooks.py, modules.txt, .gitignore; Policies: dependency-
  license-sync, devflow-run-gates (pytest/unittest/npm test), doc/comment
  coverage (py), name-clarity (py), new-modules-need-tests (py/js),
  security-scanner (py/js), doc-growth, line-length-limit, version-sync.
- dart — Assets: pubspec.yaml, pubspec.lock, .gitignore; Policies:
  dependency-license-sync, devflow-run-gates (dart test), doc-growth, line-
  length-limit, version-sync.
- flutter — Assets: pubspec.yaml, pubspec.lock, .gitignore; Policies:
  dependency-license-sync, devflow-run-gates (flutter test), doc-growth,
  line-length-limit, version-sync.
- swift — Assets: Package.swift, .gitignore; Policies: dependency-license-
  sync, devflow-run-gates (swift test), doc-growth, line-length-limit,
  version-sync.
- objective-c — Assets: .gitignore, Podfile; Policies: dependency-license-
  sync (Podfile/lock), devflow-run-gates (xcodebuild test), doc-growth, line-
  length-limit, version-sync.

## Custom Profiles
- devcovrepo — see Core Profiles above; activates custom policies.

## Expectations
- All .gitignore assets use merge mode to preserve user entries.
- Assets listed above are required for profile completeness; updates must keep
  modes (replace/merge) consistent with policy needs.
- Profiles listed under a policy’s profile_scopes MUST list that policy unless
  explicitly excluded via config overrides.
