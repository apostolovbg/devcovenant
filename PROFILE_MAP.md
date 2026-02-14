# Profile Map
**Version:** 0.2.6

## Purpose
This map documents shipped profile contracts for 0.2.6.
Profiles provide overlays, assets, hooks, selectors, and translators.
Profiles do not activate policies. Policy activation lives in `policy_state`.

## Contract Rules
- `global` is always active at runtime.
- Other profiles are selected in `devcovenant/config.yaml` under
  `profiles.active`.
- Core/custom origin is inferred by profile location.
- Only language profiles may declare translators.
- Translators are declared in profile YAML and routed by shared runtime.
- Assets are materialized by deploy/upgrade/refresh when missing.
- Existing non-one-liner assets are preserved on refresh paths.

## Core Profiles
- `global` (`core`): shared overlays and hook baseline. Owns managed docs,
  changelog coverage defaults, version-sync defaults, and gate baseline.
- `docs` (`ops`): documentation overlays for doc-growth and line-length.
  No standalone assets.
- `devcovuser` (`core`): user-repo safety overlays. Keeps
  `devcovenant/custom/**` mirrored under `tests/devcovenant/custom/**`.
- `python` (`language`): Python assets and overlays for dependency/license,
  tests, doc/comment coverage, name clarity, modules-need-tests,
  security-scanner, doc-growth, line-length, and version-sync.
- `javascript` (`language`): JS overlays for dependency/license, tests,
  doc/comment coverage, name clarity, modules-need-tests,
  security-scanner, doc-growth, and line-length.
- `typescript` (`language`): TS overlays similar to javascript.
- `java` (`language`): Java overlays for dependency/license, tests,
  doc/comment coverage, name clarity, modules-need-tests,
  security-scanner, doc-growth, and line-length.
- `go` (`language`): Go overlays for dependency/license, tests,
  doc/comment coverage, name clarity, modules-need-tests,
  security-scanner, doc-growth, and line-length.
- `rust` (`language`): Rust overlays for dependency/license, tests,
  doc/comment coverage, name clarity, modules-need-tests,
  security-scanner, doc-growth, and line-length.
- `csharp` (`language`): C# overlays for dependency/license, tests,
  doc/comment coverage, name clarity, modules-need-tests,
  security-scanner, doc-growth, and line-length.
- `php` (`language`): dependency/license, tests, doc-growth, and line-length.
- `ruby` (`language`): dependency/license, tests, doc-growth, and line-length.
- `swift` (`language`): dependency/license, tests, doc-growth, and line-length.
- `objective-c` (`language`): dependency/license, tests, doc-growth,
  and line-length.
- `dart` (`language`): dependency/license, tests, doc-growth, and line-length.
- `flutter` (`framework`): dependency/license, tests, doc-growth,
  and line-length.
- `fastapi` (`framework`): Python-centric framework overlays for tests,
  dependency/license, doc/comment coverage, name clarity,
  modules-need-tests, security-scanner, doc-growth, and line-length.
- `frappe` (`framework`): mixed stack overlays for tests,
  dependency/license, doc/comment coverage, name clarity,
  modules-need-tests, security-scanner, doc-growth, and line-length.
- `docker` (`ops`): Docker assets plus test/doc-growth/line-length overlays.
- `terraform` (`ops`): Terraform assets plus test/doc-growth/line-length.
- `kubernetes` (`ops`): Kubernetes assets plus test/doc-growth/line-length.
- `sql` (`ops`): SQL schema asset plus doc-growth/line-length overlays.

## Custom Profiles
- `devcovrepo` (`repo`): DevCovenant-repo overlays and docs assets.
  Adds custom-policy overlays (`no-spaghetti`) and extends
  modules-need-tests to full `devcovenant=>tests/devcovenant` mirroring.

## Translator Ownership
Language profiles with active translator declarations:
- `python`
- `javascript`
- `typescript`
- `java`
- `go`
- `rust`
- `csharp`

Language profiles without translator declarations yet:
- `dart`, `php`, `ruby`, `swift`, `objective-c`

## Notes
- Retired profiles (`data`, `suffixes`) are removed.
- Profile YAML overlays are metadata inputs only.
- Runtime policy list and final activation are compiled through refresh
  into AGENTS and `policy_state`.
