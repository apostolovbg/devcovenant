# Profile and Policy Draft
**Version:** 0.2.6

## Purpose
Always-on profiles: `global`, `data`, `docs`, `suffixes`.

This scratchpad maps profiles to suffixes, ignore dirs, assets, and policy
metadata overlays. It also lists the reverse mapping from policies to
profile_scopes. Use it to populate profile manifests and policy metadata
without drifting the asset hierarchy or the profile asset plan.

## Asset hierarchy
Policy and profile layout (target structure):
```text
devcovenant/core/policies/<policy>/
  <policy>.py
  adapters/
  tests/
  fixers/
  assets/
devcovenant/core/profiles/global/assets/
devcovenant/core/profiles/<profile>/assets/
devcovenant/custom/policies/<policy>/
devcovenant/custom/profiles/global/assets/
devcovenant/custom/profiles/<profile>/assets/
```

1) Global assets live under `devcovenant/core/profiles/global/assets/`.
2) Profile assets live under `devcovenant/core/profiles/<profile>/assets/`.
3) Policy assets live under `devcovenant/core/policies/<policy>/assets/`.
4) Custom overrides under `devcovenant/custom/` take precedence over core
   for matching policy/profile ids.
5) When a policy requires an asset that also exists in a profile, the profile
   asset wins for that profile.
6) Policy assets are only created when the policy is active and the profile
   is active.

Adapter model (per policy):
- Adapters live under each policy folder (`adapters/`).
- Adapter names follow language ids (python.py, js.py, go.py).
- Custom adapters override core for the same policy + language.


## Global policies (apply to every profile)
- devcov-self-enforcement
- devcov-structure-guard
- policy-text-presence
- stock-policy-text-sync
- changelog-coverage
- no-future-dates
- read-only-directories
- managed-environment (off by default)
- semantic-version-scope (off by default)

## Global + profile overlays
These policies always exist but need profile-specific metadata:
- version-sync
- dependency-license-sync
- devflow-run-gates
- documentation-growth-tracking
- line-length-limit
- last-updated-placement

## Language-bound policies (until adapters exist)
These policies need language-specific parsers or scanners:
- docstring-and-comment-coverage
- name-clarity
- new-modules-need-tests
- security-scanner

## Profile definitions
Each profile entry lists suffixes, ignore_dirs, assets, overlays, and the
policy list. "Policies" means: global policies + global overlays + any
language-bound policies listed for the profile.

### global (baseline, always on)
- Suffixes: none (baseline only).
- Ignore dirs: none (baseline only).
- Assets:
  - AGENTS.md, README.md, CHANGELOG.md, CONTRIBUTING.md
  - LICENSE, VERSION
  - .pre-commit-config.yaml
  - .github/workflows/ci.yml
  - .gitignore (global section)
- Policy overlays:
  - version-sync: readme_files, changelog_file, license_files, version_file.
  - last-updated-placement: required docs list.
- Policies: global policies + global overlays.

### docs (always on)
- Base profile: global.
- Suffixes: .md, .rst, .txt.
- Ignore dirs: _site, site, build.
- Assets: mkdocs.yml or docs/ configuration (policy assets).
- Policy overlays: line-length-limit include_suffixes (.md, .rst, .txt).
- Policies: global + overlays (no language-bound policies).

### data (always on)
- Base profile: global.
- Suffixes: .csv, .tsv, .json, .ndjson, .parquet, .avro.
- Ignore dirs: data/raw, data/tmp, data/cache.
- Assets: data/README.md, data/manifest.* (profile asset).
- Policy overlays: line-length-limit include_suffixes for data formats.
- Policies: global + overlays (no language-bound policies).

### suffixes (always on)
- Base profile: global.
- Suffixes: none (acts as an overlay bucket only).
- Ignore dirs: none.
- Assets: suffix overlay lists only (no files).
- Policy overlays: line-length-limit and documentation-growth suffixes.
- Policies: global + overlays.

### python
- Base profile: global.
- Suffixes: .py, .pyi, .pyw, .ipynb.
- Ignore dirs: .venv, __pycache__, .pytest_cache, .mypy_cache, build, dist.
- Assets:
  - pyproject.toml
  - requirements.in
  - requirements.lock
  - .python-version (optional)
- Policy overlays:
  - dependency-license-sync: requirements.in, requirements.lock,
    pyproject.toml.
  - devflow-run-gates: required_commands=pytest; python -m unittest discover.
  - documentation-growth-tracking: user_facing suffixes include .py.
  - line-length-limit: include_suffixes include .py.
  - version-sync: pyproject_files=pyproject.toml.
  - security-scanner: applies to .py.
  - new-modules-need-tests: include_suffixes=.py, watch_dirs=tests.
  - docstring-and-comment-coverage: include_suffixes=.py.
  - name-clarity: applies to .py.
- Policies: global + overlays + python-bound policies.

### django
- Base profile: python.
- Suffixes: python + .html (server-rendered views), .css, .js.
- Ignore dirs: same as python + .static_cache.
- Assets: manage.py, settings.py, urls.py, wsgi.py, asgi.py.
- Policy overlays: inherits python; add template suffixes to doc growth.
- Policies: global + overlays + python-bound policies.

### fastapi
- Base profile: python.
- Suffixes: python + .json, .yaml (OpenAPI).
- Ignore dirs: python defaults + .venv.
- Assets: main.py, openapi.json (optional template).
- Policy overlays: inherits python; add api schemas to doc tracking.
- Policies: global + overlays + python-bound policies.

### flask
- Base profile: python.
- Suffixes: python + .html, .css, .js.
- Ignore dirs: python defaults.
- Assets: app.py (or wsgi.py).
- Policy overlays: inherits python.
- Policies: global + overlays + python-bound policies.

### frappe
- Base profile: python + javascript + data.
- Suffixes: .py, .js, .json, .md.
- Ignore dirs: python + node + site caches.
- Assets: hooks.py, modules.txt, doctype JSON assets.
- Policy overlays:
  - version-sync: include app metadata files.
  - documentation-growth-tracking: include .json + .js.
- Policies: global + overlays + python-bound policies.

### javascript
- Base profile: global.
- Suffixes: .js, .jsx, .mjs, .cjs.
- Ignore dirs: node_modules, dist, build, coverage, .cache.
- Assets: package.json, package-lock.json (or yarn.lock, pnpm-lock.yaml).
- Policy overlays:
  - dependency-license-sync: package.json + lock file(s).
  - devflow-run-gates: required_commands=npm test (or yarn/pnpm).
  - documentation-growth-tracking: user_facing suffixes include .js.
  - line-length-limit: include_suffixes include .js.
- Policies: global + overlays (language-bound policies once JS adapters exist).

### typescript
- Base profile: javascript.
- Suffixes: .ts, .tsx.
- Ignore dirs: node_modules, dist, build.
- Assets: tsconfig.json, package.json, lock files.
- Policy overlays: inherits javascript; add .ts/.tsx to suffix lists.
- Policies: global + overlays (language-bound policies when TS adapters exist).

### angular
- Base profile: typescript.
- Suffixes: .ts, .html, .css, .scss.
- Ignore dirs: node_modules, dist, .angular.
- Assets: angular.json, tsconfig.json.
- Policy overlays: inherits typescript.
- Policies: global + overlays (language-bound policies when TS adapters exist).

### react
- Base profile: javascript or typescript.
- Suffixes: .jsx, .tsx.
- Ignore dirs: node_modules, dist, build.
- Assets: package.json, vite.config.* (optional).
- Policy overlays: inherits JS/TS.
- Policies: global + overlays.

### nextjs
- Base profile: react + typescript.
- Suffixes: .js, .jsx, .ts, .tsx.
- Ignore dirs: .next, node_modules.
- Assets: next.config.js, tsconfig.json.
- Policy overlays: inherits react.
- Policies: global + overlays.

### vue
- Base profile: javascript or typescript.
- Suffixes: .vue, .js, .ts.
- Ignore dirs: node_modules, dist.
- Assets: vue.config.js, package.json.
- Policy overlays: inherits JS/TS.
- Policies: global + overlays.

### nuxt
- Base profile: vue + typescript.
- Suffixes: .vue, .ts.
- Ignore dirs: .nuxt, node_modules.
- Assets: nuxt.config.ts.
- Policy overlays: inherits vue.
- Policies: global + overlays.

### svelte
- Base profile: javascript or typescript.
- Suffixes: .svelte, .js, .ts.
- Ignore dirs: node_modules, dist.
- Assets: svelte.config.js.
- Policy overlays: inherits JS/TS.
- Policies: global + overlays.

### nestjs
- Base profile: typescript.
- Suffixes: .ts.
- Ignore dirs: node_modules, dist.
- Assets: nest-cli.json, tsconfig.json.
- Policy overlays: inherits TS.
- Policies: global + overlays.

### express
- Base profile: javascript.
- Suffixes: .js.
- Ignore dirs: node_modules, dist.
- Assets: app.js, server.js, package.json.
- Policy overlays: inherits JS.
- Policies: global + overlays.

### node (implicit via javascript)
- Use javascript or typescript profiles. No standalone node profile.

### go
- Base profile: global.
- Suffixes: .go.
- Ignore dirs: bin, pkg, vendor.
- Assets: go.mod, go.sum.
- Policy overlays:
  - dependency-license-sync: go.mod, go.sum.
  - devflow-run-gates: required_commands=go test ./...
  - documentation-growth-tracking: include .go.
  - line-length-limit: include .go.
- Policies: global + overlays (language-bound policies when Go adapters
  exist).

### rust
- Base profile: global.
- Suffixes: .rs.
- Ignore dirs: target.
- Assets: Cargo.toml, Cargo.lock.
- Policy overlays:
  - dependency-license-sync: Cargo.toml, Cargo.lock.
  - devflow-run-gates: required_commands=cargo test.
  - documentation-growth-tracking: include .rs.
  - line-length-limit: include .rs.
- Policies: global + overlays (language-bound policies when Rust adapters
  exist).

### java
- Base profile: global.
- Suffixes: .java.
- Ignore dirs: target, build.
- Assets: pom.xml or build.gradle.
- Policy overlays:
  - dependency-license-sync: pom.xml or build.gradle.
  - devflow-run-gates: required_commands=mvn test or gradle test.
  - documentation-growth-tracking: include .java.
  - line-length-limit: include .java.
- Policies: global + overlays (language-bound policies when Java adapters
  exist).

### kotlin
- Base profile: java.
- Suffixes: .kt, .kts.
- Ignore dirs: build.
- Assets: build.gradle.kts.
- Policy overlays: inherits java.
- Policies: global + overlays.

### scala
- Base profile: java.
- Suffixes: .scala.
- Ignore dirs: target, project/target.
- Assets: build.sbt.
- Policy overlays: inherits java.
- Policies: global + overlays.

### groovy
- Base profile: java.
- Suffixes: .groovy.
- Ignore dirs: build.
- Assets: build.gradle.
- Policy overlays: inherits java.
- Policies: global + overlays.

### spring
- Base profile: java.
- Suffixes: .java, .properties, .yml.
- Ignore dirs: target, build.
- Assets: application.yml.
- Policy overlays: inherits java.
- Policies: global + overlays.

### quarkus
- Base profile: java.
- Suffixes: .java, .properties, .yml.
- Ignore dirs: target, build.
- Assets: application.properties.
- Policy overlays: inherits java.
- Policies: global + overlays.

### micronaut
- Base profile: java or kotlin.
- Suffixes: .java, .kt, .yml.
- Ignore dirs: build.
- Assets: application.yml.
- Policy overlays: inherits java/kotlin.
- Policies: global + overlays.

### dotnet
- Base profile: global.
- Suffixes: .cs, .fs, .vb.
- Ignore dirs: bin, obj.
- Assets: *.csproj, *.fsproj, *.sln, packages.lock.json.
- Policy overlays:
  - dependency-license-sync: *.csproj, packages.lock.json.
  - devflow-run-gates: required_commands=dotnet test.
  - documentation-growth-tracking: include .cs/.fs.
  - line-length-limit: include .cs/.fs.
- Policies: global + overlays (language-bound policies when .NET adapters
  exist).

### csharp
- Base profile: dotnet.
- Suffixes: .cs.
- Ignore dirs: bin, obj.
- Assets: *.csproj.
- Policy overlays: inherits dotnet.
- Policies: global + overlays.

### fsharp
- Base profile: dotnet.
- Suffixes: .fs, .fsx.
- Ignore dirs: bin, obj.
- Assets: *.fsproj.
- Policy overlays: inherits dotnet.
- Policies: global + overlays.

### php
- Base profile: global.
- Suffixes: .php.
- Ignore dirs: vendor.
- Assets: composer.json, composer.lock.
- Policy overlays:
  - dependency-license-sync: composer.json, composer.lock.
  - devflow-run-gates: required_commands=phpunit.
  - documentation-growth-tracking: include .php.
  - line-length-limit: include .php.
- Policies: global + overlays (language-bound policies when PHP adapters
  exist).

### laravel
- Base profile: php.
- Suffixes: .php, .blade.php.
- Ignore dirs: vendor, storage.
- Assets: artisan, composer.json.
- Policy overlays: inherits php.
- Policies: global + overlays.

### symfony
- Base profile: php.
- Suffixes: .php, .twig.
- Ignore dirs: var, vendor.
- Assets: composer.json.
- Policy overlays: inherits php.
- Policies: global + overlays.

### ruby
- Base profile: global.
- Suffixes: .rb, .rake.
- Ignore dirs: .bundle, vendor/bundle.
- Assets: Gemfile, Gemfile.lock.
- Policy overlays:
  - dependency-license-sync: Gemfile, Gemfile.lock.
  - devflow-run-gates: required_commands=bundle exec rake test.
  - documentation-growth-tracking: include .rb.
  - line-length-limit: include .rb.
- Policies: global + overlays (language-bound policies when Ruby adapters
  exist).

### rails
- Base profile: ruby.
- Suffixes: .rb, .erb.
- Ignore dirs: log, tmp, vendor/bundle.
- Assets: Gemfile.
- Policy overlays: inherits ruby.
- Policies: global + overlays.

### elixir
- Base profile: global.
- Suffixes: .ex, .exs.
- Ignore dirs: _build, deps.
- Assets: mix.exs, mix.lock.
- Policy overlays:
  - dependency-license-sync: mix.exs, mix.lock.
  - devflow-run-gates: required_commands=mix test.
  - documentation-growth-tracking: include .ex.
  - line-length-limit: include .ex.
- Policies: global + overlays.

### erlang
- Base profile: global.
- Suffixes: .erl, .hrl.
- Ignore dirs: _build, deps.
- Assets: rebar.config, rebar.lock.
- Policy overlays:
  - dependency-license-sync: rebar.config, rebar.lock.
  - devflow-run-gates: required_commands=rebar3 ct.
  - documentation-growth-tracking: include .erl.
  - line-length-limit: include .erl.
- Policies: global + overlays.

### haskell
- Base profile: global.
- Suffixes: .hs, .lhs.
- Ignore dirs: dist-newstyle, .stack-work.
- Assets: stack.yaml, *.cabal.
- Policy overlays:
  - dependency-license-sync: stack.yaml, *.cabal.
  - devflow-run-gates: required_commands=stack test.
  - documentation-growth-tracking: include .hs.
  - line-length-limit: include .hs.
- Policies: global + overlays.

### clojure
- Base profile: global.
- Suffixes: .clj, .cljs, .cljc, .edn.
- Ignore dirs: target, .cpcache.
- Assets: deps.edn, project.clj.
- Policy overlays:
  - dependency-license-sync: deps.edn, project.clj.
  - devflow-run-gates: required_commands=clojure -M:test.
  - documentation-growth-tracking: include .clj.
  - line-length-limit: include .clj.
- Policies: global + overlays.

### lisp
- Base profile: global.
- Suffixes: .lisp, .lsp.
- Ignore dirs: build.
- Assets: none (language-dependent).
- Policy overlays: documentation-growth suffixes include lisp.
- Policies: global + overlays.

### scheme
- Base profile: global.
- Suffixes: .scm, .ss.
- Ignore dirs: build.
- Assets: none.
- Policy overlays: documentation-growth suffixes include scheme.
- Policies: global + overlays.

### ocaml
- Base profile: global.
- Suffixes: .ml, .mli.
- Ignore dirs: _build.
- Assets: dune, opam.
- Policy overlays: dependency-license-sync uses opam files.
- Policies: global + overlays.

### nim
- Base profile: global.
- Suffixes: .nim.
- Ignore dirs: nimcache.
- Assets: *.nimble.
- Policy overlays: documentation-growth suffixes include .nim.
- Policies: global + overlays.

### crystal
- Base profile: global.
- Suffixes: .cr.
- Ignore dirs: lib, .crystal.
- Assets: shard.yml, shard.lock.
- Policy overlays: dependency-license-sync uses shard.*.
- Policies: global + overlays.

### lua
- Base profile: global.
- Suffixes: .lua.
- Ignore dirs: build.
- Assets: rockspec.
- Policy overlays: documentation-growth suffixes include .lua.
- Policies: global + overlays.

### perl
- Base profile: global.
- Suffixes: .pl, .pm.
- Ignore dirs: local, blib.
- Assets: cpanfile.
- Policy overlays: dependency-license-sync uses cpanfile.
- Policies: global + overlays.

### prolog
- Base profile: global.
- Suffixes: .pl, .pro, .prolog.
- Ignore dirs: build.
- Assets: none.
- Policy overlays: documentation-growth suffixes include .pro.
- Policies: global + overlays.

### r
- Base profile: global.
- Suffixes: .r, .R.
- Ignore dirs: .Rproj.user.
- Assets: DESCRIPTION, NAMESPACE.
- Policy overlays: dependency-license-sync uses DESCRIPTION.
- Policies: global + overlays.

### julia
- Base profile: global.
- Suffixes: .jl.
- Ignore dirs: .julia.
- Assets: Project.toml, Manifest.toml.
- Policy overlays: dependency-license-sync uses Project.toml.
- Policies: global + overlays.

### matlab
- Base profile: global.
- Suffixes: .m.
- Ignore dirs: build.
- Assets: none.
- Policy overlays: documentation-growth suffixes include .m.
- Policies: global + overlays.

### fortran
- Base profile: global.
- Suffixes: .f, .f90, .f95, .f03, .f08.
- Ignore dirs: build.
- Assets: none.
- Policy overlays: documentation-growth suffixes include Fortran.
- Policies: global + overlays.

### cobol
- Base profile: global.
- Suffixes: .cob, .cbl, .cpy.
- Ignore dirs: build.
- Assets: none.
- Policy overlays: documentation-growth suffixes include cobol.
- Policies: global + overlays.

### pascal
- Base profile: global.
- Suffixes: .pas, .pp, .dpr.
- Ignore dirs: build.
- Assets: none.
- Policy overlays: documentation-growth suffixes include pascal.
- Policies: global + overlays.

### c
- Base profile: global.
- Suffixes: .c, .h.
- Ignore dirs: build, out.
- Assets: Makefile, CMakeLists.txt.
- Policy overlays: documentation-growth suffixes include c.
- Policies: global + overlays.

### cpp
- Base profile: c.
- Suffixes: .cpp, .cc, .cxx, .hpp, .hxx, .hh.
- Ignore dirs: build, out.
- Assets: CMakeLists.txt.
- Policy overlays: documentation-growth suffixes include cpp.
- Policies: global + overlays.

### objective-c
- Base profile: c.
- Suffixes: .m, .mm, .h.
- Ignore dirs: build.
- Assets: Xcode project assets (optional).
- Policy overlays: documentation-growth suffixes include objective-c.
- Policies: global + overlays.

### swift
- Base profile: global.
- Suffixes: .swift.
- Ignore dirs: .build.
- Assets: Package.swift.
- Policy overlays: dependency-license-sync uses Package.swift.
- Policies: global + overlays.

### zig
- Base profile: global.
- Suffixes: .zig.
- Ignore dirs: zig-cache, zig-out.
- Assets: build.zig.
- Policy overlays: documentation-growth suffixes include .zig.
- Policies: global + overlays.

### dart
- Base profile: global.
- Suffixes: .dart.
- Ignore dirs: .dart_tool, build.
- Assets: pubspec.yaml, pubspec.lock.
- Policy overlays: dependency-license-sync uses pubspec.*.
- Policies: global + overlays.

### flutter
- Base profile: dart.
- Suffixes: .dart.
- Ignore dirs: .dart_tool, build.
- Assets: pubspec.yaml.
- Policy overlays: inherits dart.
- Policies: global + overlays.

### terraform
- Base profile: global.
- Suffixes: .tf, .tfvars, .hcl.
- Ignore dirs: .terraform.
- Assets: main.tf, variables.tf (assets).
- Policy overlays: documentation-growth suffixes include .tf.
- Policies: global + overlays.

### docker
- Base profile: global.
- Suffixes: Dockerfile, .dockerignore, .yml, .yaml.
- Ignore dirs: none.
- Assets: Dockerfile, docker-compose.yml, .dockerignore.
- Policy overlays: line-length-limit include_suffixes .yml, .yaml.
- Policies: global + overlays.

### kubernetes
- Base profile: docker.
- Suffixes: .yml, .yaml.
- Ignore dirs: charts/.
- Assets: Chart.yaml, values.yaml (helm).
- Policy overlays: documentation-growth suffixes include .yaml.
- Policies: global + overlays.

### ansible
- Base profile: global.
- Suffixes: .yml, .yaml, .j2, .ini.
- Ignore dirs: .ansible.
- Assets: ansible.cfg, inventory.ini.
- Policy overlays: documentation-growth suffixes include .yml.
- Policies: global + overlays.

### bash
- Base profile: global.
- Suffixes: .sh, .bash, .zsh.
- Ignore dirs: none.
- Assets: none.
- Policy overlays: documentation-growth suffixes include shell.
- Policies: global + overlays.

### powershell
- Base profile: global.
- Suffixes: .ps1, .psm1, .psd1.
- Ignore dirs: none.
- Assets: none.
- Policy overlays: documentation-growth suffixes include powershell.
- Policies: global + overlays.

### sql
- Base profile: data.
- Suffixes: .sql.
- Ignore dirs: none.
- Assets: schema.sql (template).
- Policy overlays: documentation-growth suffixes include sql.
- Policies: global + overlays.

## Policy scope map (policy -> profile_scopes)
Use this for the `profile_scopes:` metadata key in stock AGENTS policies.

- devcov-self-enforcement: global
- devcov-structure-guard: global
- policy-text-presence: global
- stock-policy-text-sync: global
- changelog-coverage: global
- no-future-dates: global
- read-only-directories: global
- managed-environment: global
- semantic-version-scope: global

- version-sync: global, docs, data, python, javascript, typescript, java,
  kotlin, scala, groovy, dotnet, csharp, fsharp, php, ruby, go, rust,
  swift, dart, flutter, terraform, docker, kubernetes.

- dependency-license-sync: python, javascript, typescript, java, kotlin,
  scala, groovy, dotnet, csharp, fsharp, php, ruby, go, rust, swift, dart,
  flutter, elixir, erlang, haskell, clojure, julia, ocaml, crystal.

- devflow-run-gates: global, python, javascript, typescript, java, kotlin,
  scala, groovy, dotnet, csharp, fsharp, php, ruby, go, rust, swift, dart,
  flutter, elixir, erlang, haskell, clojure, julia, ocaml, crystal.

- documentation-growth-tracking: global, docs, data, python, javascript,
  typescript, go, rust, java, kotlin, scala, groovy, dotnet, csharp, fsharp,
  php, ruby, swift, dart, terraform, docker, kubernetes, ansible.

- line-length-limit: global, docs, data, python, javascript, typescript, go,
  rust, java, kotlin, scala, groovy, dotnet, csharp, fsharp, php, ruby, swift,
  dart, terraform, docker, kubernetes, ansible.

- last-updated-placement: global, docs, data.

- docstring-and-comment-coverage: python (future: go, rust, java, csharp).
- name-clarity: python (future: go, rust, java, csharp, js, ts).
- new-modules-need-tests: python (future: js, ts, go, rust, java, csharp).
- security-scanner: python (future: js, ts, go, rust, java, csharp, php,
  ruby).
