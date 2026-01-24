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
  Long paths should be wrapped with a trailing \
  backslash and continued on the next indented line.
  Example:
  devcovenant/core/templates/policies/dependency-license-sync/\
    licenses/README.md
<!-- DEVCOV:END -->

## Log changes here

## Version 0.2.6
- 2026-01-23: Added profile manifests, gitignore fragments, and
  profile overlays, plus managed-environment guidance and template
  refreshes. (AI assistant)
  Files:
  AGENTS.md
  CHANGELOG.md
  MANIFEST.in
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/core/install.py
  devcovenant/core/manifest.py
  devcovenant/core/policy_assets.yaml
  devcovenant/core/policy_scripts/managed_environment.py
  devcovenant/core/profiles.py
  devcovenant/core/templates/global/AGENTS.md
  devcovenant/core/templates/global/gitignore_base.txt
  devcovenant/core/templates/global/gitignore_os.txt
  devcovenant/core/templates/profiles/angular/README.md
  devcovenant/core/templates/profiles/angular/profile.yaml
  devcovenant/core/templates/profiles/ansible/README.md
  devcovenant/core/templates/profiles/ansible/profile.yaml
  devcovenant/core/templates/profiles/bash/README.md
  devcovenant/core/templates/profiles/bash/profile.yaml
  devcovenant/core/templates/profiles/c/README.md
  devcovenant/core/templates/profiles/c/profile.yaml
  devcovenant/core/templates/profiles/clojure/README.md
  devcovenant/core/templates/profiles/clojure/profile.yaml
  devcovenant/core/templates/profiles/cobol/README.md
  devcovenant/core/templates/profiles/cobol/profile.yaml
  devcovenant/core/templates/profiles/cpp/README.md
  devcovenant/core/templates/profiles/cpp/profile.yaml
  devcovenant/core/templates/profiles/crystal/README.md
  devcovenant/core/templates/profiles/crystal/profile.yaml
  devcovenant/core/templates/profiles/csharp/README.md
  devcovenant/core/templates/profiles/csharp/profile.yaml
  devcovenant/core/templates/profiles/dart/README.md
  devcovenant/core/templates/profiles/dart/profile.yaml
  devcovenant/core/templates/profiles/data/README.md
  devcovenant/core/templates/profiles/data/profile.yaml
  devcovenant/core/templates/profiles/django/README.md
  devcovenant/core/templates/profiles/django/profile.yaml
  devcovenant/core/templates/profiles/docker/README.md
  devcovenant/core/templates/profiles/docker/profile.yaml
  devcovenant/core/templates/profiles/docs/README.md
  devcovenant/core/templates/profiles/docs/profile.yaml
  devcovenant/core/templates/profiles/dotnet/.gitignore
  devcovenant/core/templates/profiles/dotnet/README.md
  devcovenant/core/templates/profiles/dotnet/profile.yaml
  devcovenant/core/templates/profiles/elixir/README.md
  devcovenant/core/templates/profiles/elixir/profile.yaml
  devcovenant/core/templates/profiles/erlang/README.md
  devcovenant/core/templates/profiles/erlang/profile.yaml
  devcovenant/core/templates/profiles/express/README.md
  devcovenant/core/templates/profiles/express/profile.yaml
  devcovenant/core/templates/profiles/fastapi/README.md
  devcovenant/core/templates/profiles/fastapi/profile.yaml
  devcovenant/core/templates/profiles/flask/README.md
  devcovenant/core/templates/profiles/flask/profile.yaml
  devcovenant/core/templates/profiles/flutter/README.md
  devcovenant/core/templates/profiles/flutter/profile.yaml
  devcovenant/core/templates/profiles/fortran/README.md
  devcovenant/core/templates/profiles/fortran/profile.yaml
  devcovenant/core/templates/profiles/frappe/README.md
  devcovenant/core/templates/profiles/frappe/profile.yaml
  devcovenant/core/templates/profiles/fsharp/README.md
  devcovenant/core/templates/profiles/fsharp/profile.yaml
  devcovenant/core/templates/profiles/go/.gitignore
  devcovenant/core/templates/profiles/go/README.md
  devcovenant/core/templates/profiles/go/profile.yaml
  devcovenant/core/templates/profiles/groovy/README.md
  devcovenant/core/templates/profiles/groovy/profile.yaml
  devcovenant/core/templates/profiles/haskell/README.md
  devcovenant/core/templates/profiles/haskell/profile.yaml
  devcovenant/core/templates/profiles/java/.gitignore
  devcovenant/core/templates/profiles/java/README.md
  devcovenant/core/templates/profiles/java/profile.yaml
  devcovenant/core/templates/profiles/javascript/.gitignore
  devcovenant/core/templates/profiles/javascript/README.md
  devcovenant/core/templates/profiles/javascript/profile.yaml
  devcovenant/core/templates/profiles/julia/README.md
  devcovenant/core/templates/profiles/julia/profile.yaml
  devcovenant/core/templates/profiles/kotlin/.gitignore
  devcovenant/core/templates/profiles/kotlin/README.md
  devcovenant/core/templates/profiles/kotlin/profile.yaml
  devcovenant/core/templates/profiles/kubernetes/README.md
  devcovenant/core/templates/profiles/kubernetes/profile.yaml
  devcovenant/core/templates/profiles/laravel/README.md
  devcovenant/core/templates/profiles/laravel/profile.yaml
  devcovenant/core/templates/profiles/lisp/README.md
  devcovenant/core/templates/profiles/lisp/profile.yaml
  devcovenant/core/templates/profiles/lua/README.md
  devcovenant/core/templates/profiles/lua/profile.yaml
  devcovenant/core/templates/profiles/matlab/README.md
  devcovenant/core/templates/profiles/matlab/profile.yaml
  devcovenant/core/templates/profiles/micronaut/README.md
  devcovenant/core/templates/profiles/micronaut/profile.yaml
  devcovenant/core/templates/profiles/nestjs/README.md
  devcovenant/core/templates/profiles/nestjs/profile.yaml
  devcovenant/core/templates/profiles/nextjs/README.md
  devcovenant/core/templates/profiles/nextjs/profile.yaml
  devcovenant/core/templates/profiles/nim/README.md
  devcovenant/core/templates/profiles/nim/profile.yaml
  devcovenant/core/templates/profiles/nuxt/README.md
  devcovenant/core/templates/profiles/nuxt/profile.yaml
  devcovenant/core/templates/profiles/objective-c/README.md
  devcovenant/core/templates/profiles/objective-c/profile.yaml
  devcovenant/core/templates/profiles/ocaml/README.md
  devcovenant/core/templates/profiles/ocaml/profile.yaml
  devcovenant/core/templates/profiles/pascal/README.md
  devcovenant/core/templates/profiles/pascal/profile.yaml
  devcovenant/core/templates/profiles/perl/README.md
  devcovenant/core/templates/profiles/perl/profile.yaml
  devcovenant/core/templates/profiles/php/.gitignore
  devcovenant/core/templates/profiles/php/README.md
  devcovenant/core/templates/profiles/php/profile.yaml
  devcovenant/core/templates/profiles/powershell/README.md
  devcovenant/core/templates/profiles/powershell/profile.yaml
  devcovenant/core/templates/profiles/prolog/README.md
  devcovenant/core/templates/profiles/prolog/profile.yaml
  devcovenant/core/templates/profiles/python/.gitignore
  devcovenant/core/templates/profiles/python/README.md
  devcovenant/core/templates/profiles/python/profile.yaml
  devcovenant/core/templates/profiles/quarkus/README.md
  devcovenant/core/templates/profiles/quarkus/profile.yaml
  devcovenant/core/templates/profiles/r/README.md
  devcovenant/core/templates/profiles/r/profile.yaml
  devcovenant/core/templates/profiles/rails/README.md
  devcovenant/core/templates/profiles/rails/profile.yaml
  devcovenant/core/templates/profiles/react/README.md
  devcovenant/core/templates/profiles/react/profile.yaml
  devcovenant/core/templates/profiles/ruby/.gitignore
  devcovenant/core/templates/profiles/ruby/README.md
  devcovenant/core/templates/profiles/ruby/profile.yaml
  devcovenant/core/templates/profiles/rust/.gitignore
  devcovenant/core/templates/profiles/rust/README.md
  devcovenant/core/templates/profiles/rust/profile.yaml
  devcovenant/core/templates/profiles/scala/README.md
  devcovenant/core/templates/profiles/scala/profile.yaml
  devcovenant/core/templates/profiles/scheme/README.md
  devcovenant/core/templates/profiles/scheme/profile.yaml
  devcovenant/core/templates/profiles/spring/README.md
  devcovenant/core/templates/profiles/spring/profile.yaml
  devcovenant/core/templates/profiles/sql/README.md
  devcovenant/core/templates/profiles/sql/profile.yaml
  devcovenant/core/templates/profiles/suffixes/README.md
  devcovenant/core/templates/profiles/suffixes/profile.yaml
  devcovenant/core/templates/profiles/svelte/README.md
  devcovenant/core/templates/profiles/svelte/profile.yaml
  devcovenant/core/templates/profiles/swift/README.md
  devcovenant/core/templates/profiles/swift/profile.yaml
  devcovenant/core/templates/profiles/symfony/README.md
  devcovenant/core/templates/profiles/symfony/profile.yaml
  devcovenant/core/templates/profiles/terraform/README.md
  devcovenant/core/templates/profiles/terraform/profile.yaml
  devcovenant/core/templates/profiles/typescript/.gitignore
  devcovenant/core/templates/profiles/typescript/README.md
  devcovenant/core/templates/profiles/typescript/profile.yaml
  devcovenant/core/templates/profiles/vue/README.md
  devcovenant/core/templates/profiles/vue/profile.yaml
  devcovenant/core/templates/profiles/zig/README.md
  devcovenant/core/templates/profiles/zig/profile.yaml
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_policies/test_managed_environment.py
  devcovenant/core/tests/test_profiles.py
  devcovenant/custom/policy_assets.yaml
  devcovenant/registry.json
- 2026-01-23: Embedded the policy scope map and language scanner tasks
  into the Phase L planning checklist.
  (AI assistant)
  Files:
  PLAN.md
  CHANGELOG.md
- 2026-01-23: Expanded the policy scope map to a per-policy checklist
  with overlays and asset precedence rules.
  (AI assistant)
  Files:
  PLAN.md
  CHANGELOG.md
- 2026-01-23: Expanded the policy scope map and profile overlay
  guidance for stock templates.
  (AI assistant)
  Files:
  PLAN.md
  CHANGELOG.md
- 2026-01-23: Expanded Phase L planning and added a policy scope map.
  (AI assistant)
  Files:
  PLAN.md
  CHANGELOG.md
- 2026-01-23: Replaced managed-bench with managed-environment and
  refreshed policy docs and templates. (AI assistant)
  Files:
  AGENTS.md
  PLAN.md
  SPEC.md
  devcovenant/README.md
  devcovenant/config.yaml
  devcovenant/core/policy_scripts/managed_environment.py
  devcovenant/core/tests/test_policies/test_managed_environment.py
  devcovenant/core/templates/global/AGENTS.md
  devcovenant/core/stock_policy_texts.yaml
  devcovenant/core/policy_scripts/managed_bench.py
  devcovenant/core/tests/test_policies/test_managed_bench.py
  CHANGELOG.md
- 2026-01-23: Made config profile-generated and expanded
  config schema documentation. (AI assistant)
  Files:
  devcovenant/core/install.py
  devcovenant/config.yaml
  devcovenant/README.md
  SPEC.md
  CHANGELOG.md
- 2026-01-23: Planned profile-driven config, custom catalogs, and
  gitignore assets. (AI assistant)
  Files:
  PLAN.md
  CHANGELOG.md
- 2026-01-23: Documented custom profiles, policies, and asset
  overrides. (AI assistant)
  Files:
  devcovenant/README.md
  SPEC.md
  CHANGELOG.md
- 2026-01-23: Fixed install template resolution for profile assets.
  (AI assistant)
  Files:
  devcovenant/core/install.py
  CHANGELOG.md
- 2026-01-23: Added Phase G tests for profile assets and manifests.
  (AI assistant)
  Files:
  devcovenant/core/tests/test_install.py
  devcovenant/core/tests/test_manifest.py
  CHANGELOG.md
- 2026-01-23: Removed real-repo validation from Phase G.
  (AI assistant)
  Files:
  PLAN.md
  CHANGELOG.md
- 2026-01-23: Completed Phase K asset gating and tests. (AI assistant)
- 2026-01-23: Added profile-aware templates,
  install/update logic, and profile catalog tests. (AI assistant)
  Files:
AGENTS.md
CHANGELOG.md
MANIFEST.in
PLAN.md
README.md
SPEC.md
devcovenant/README.md
devcovenant/__init__.py
devcovenant/cli.py
devcovenant/config.yaml
devcovenant/core/engine.py
devcovenant/core/install.py
devcovenant/core/manifest.py
devcovenant/core/metadata_normalizer.py
devcovenant/core/policy_assets.yaml
devcovenant/core/policy_scripts/changelog_coverage.py
devcovenant/core/profile_catalog.yaml
devcovenant/core/profiles.py
devcovenant/core/templates/global/.github/workflows/ci.yml
devcovenant/core/templates/global/.pre-commit-config.yaml
devcovenant/core/templates/global/AGENTS.md
devcovenant/core/templates/global/CONTRIBUTING.md
devcovenant/core/templates/global/LICENSE_GPL-3.0.txt
devcovenant/core/templates/global/VERSION
devcovenant/core/templates/global/tools/run_pre_commit.py
devcovenant/core/templates/global/tools/run_tests.py
devcovenant/core/templates/global/tools/update_test_status.py
devcovenant/core/templates/policies/dependency-license-sync/\
  THIRD_PARTY_LICENSES.md
devcovenant/core/templates/policies/dependency-license-sync/licenses/README.md
devcovenant/core/templates/profiles/angular/README.md
devcovenant/core/templates/profiles/ansible/README.md
devcovenant/core/templates/profiles/bash/README.md
devcovenant/core/templates/profiles/c/README.md
devcovenant/core/templates/profiles/clojure/README.md
devcovenant/core/templates/profiles/cobol/README.md
devcovenant/core/templates/profiles/cpp/README.md
devcovenant/core/templates/profiles/crystal/README.md
devcovenant/core/templates/profiles/csharp/README.md
devcovenant/core/templates/profiles/dart/README.md
devcovenant/core/templates/profiles/data/README.md
devcovenant/core/templates/profiles/django/README.md
devcovenant/core/templates/profiles/docker/README.md
devcovenant/core/templates/profiles/docs/README.md
devcovenant/core/templates/profiles/dotnet/README.md
devcovenant/core/templates/profiles/dotnet/global.json
devcovenant/core/templates/profiles/elixir/README.md
devcovenant/core/templates/profiles/erlang/README.md
devcovenant/core/templates/profiles/express/README.md
devcovenant/core/templates/profiles/fastapi/README.md
devcovenant/core/templates/profiles/flask/README.md
devcovenant/core/templates/profiles/flutter/README.md
devcovenant/core/templates/profiles/fortran/README.md
devcovenant/core/templates/profiles/frappe/README.md
devcovenant/core/templates/profiles/fsharp/README.md
devcovenant/core/templates/profiles/go/README.md
devcovenant/core/templates/profiles/go/go.mod
devcovenant/core/templates/profiles/groovy/README.md
devcovenant/core/templates/profiles/haskell/README.md
devcovenant/core/templates/profiles/java/README.md
devcovenant/core/templates/profiles/java/build.gradle
devcovenant/core/templates/profiles/javascript/README.md
devcovenant/core/templates/profiles/javascript/package.json
devcovenant/core/templates/profiles/julia/README.md
devcovenant/core/templates/profiles/kotlin/README.md
devcovenant/core/templates/profiles/kotlin/build.gradle.kts
devcovenant/core/templates/profiles/kubernetes/README.md
devcovenant/core/templates/profiles/laravel/README.md
devcovenant/core/templates/profiles/lisp/README.md
devcovenant/core/templates/profiles/lua/README.md
devcovenant/core/templates/profiles/matlab/README.md
devcovenant/core/templates/profiles/micronaut/README.md
devcovenant/core/templates/profiles/nestjs/README.md
devcovenant/core/templates/profiles/nextjs/README.md
devcovenant/core/templates/profiles/nim/README.md
devcovenant/core/templates/profiles/nuxt/README.md
devcovenant/core/templates/profiles/objective-c/README.md
devcovenant/core/templates/profiles/ocaml/README.md
devcovenant/core/templates/profiles/pascal/README.md
devcovenant/core/templates/profiles/perl/README.md
devcovenant/core/templates/profiles/php/README.md
devcovenant/core/templates/profiles/php/composer.json
devcovenant/core/templates/profiles/powershell/README.md
devcovenant/core/templates/profiles/prolog/README.md
devcovenant/core/templates/profiles/python/README.md
devcovenant/core/templates/profiles/python/requirements.in
devcovenant/core/templates/profiles/python/requirements.lock
devcovenant/core/templates/profiles/quarkus/README.md
devcovenant/core/templates/profiles/r/README.md
devcovenant/core/templates/profiles/rails/README.md
devcovenant/core/templates/profiles/react/README.md
devcovenant/core/templates/profiles/ruby/Gemfile
devcovenant/core/templates/profiles/ruby/README.md
devcovenant/core/templates/profiles/rust/Cargo.toml
devcovenant/core/templates/profiles/rust/README.md
devcovenant/core/templates/profiles/scala/README.md
devcovenant/core/templates/profiles/scheme/README.md
devcovenant/core/templates/profiles/spring/README.md
devcovenant/core/templates/profiles/sql/README.md
devcovenant/core/templates/profiles/suffixes/README.md
devcovenant/core/templates/profiles/svelte/README.md
devcovenant/core/templates/profiles/swift/README.md
devcovenant/core/templates/profiles/symfony/README.md
devcovenant/core/templates/profiles/terraform/README.md
devcovenant/core/templates/profiles/typescript/README.md
devcovenant/core/templates/profiles/typescript/package.json
devcovenant/core/templates/profiles/typescript/tsconfig.json
devcovenant/core/templates/profiles/vue/README.md
devcovenant/core/templates/profiles/zig/README.md
devcovenant/core/tests/test_policies/test_changelog_coverage.py
devcovenant/core/tests/test_profiles.py
devcovenant/core/update.py
devcovenant/manifest.json
devcovenant/registry.json
devcovenant/templates/.github/workflows/ci.yml
devcovenant/templates/.pre-commit-config.yaml
devcovenant/templates/AGENTS.md
devcovenant/templates/CONTRIBUTING.md
devcovenant/templates/LICENSE_GPL-3.0.txt
devcovenant/templates/VERSION
devcovenant/templates/tools/run_pre_commit.py
devcovenant/templates/tools/run_tests.py
devcovenant/templates/tools/update_test_status.py
devcovenant/core/tests/test_install.py
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
