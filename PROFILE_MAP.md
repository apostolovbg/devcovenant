# Profile Map
**Version:** 0.2.6

## Purpose
This document is the authoritative profile-map for DevCovenant 0.2.6. Every
profile listed here describes the asset files, policy metadata overlays,
scanner adapters, and gitignore fragments that installers and updates must
apply when the profile is active. Profiles always derive from the `global`
baseline (with `data`, `docs`, and `suffixes` staying perpetually active), but
custom repos may select only the language/framework/data combinations that
match their stack. The map also documents the per-profile gitignore template
(`gitignore_fragment.txt`) that merges into `.gitignore` after applying the
global base fragment.

## Asset and scanner hierarchy
1. Core profiles live under
   `devcovenant/core/profiles/<profile>/assets/` and supply templates
   (`AGENTS.md`, README fragments, gitignore fragments, tool configs,
   scanner scripts, etc.).
2. Global profile assets appear in
   `devcovenant/core/profiles/global/assets/` and include shared headers,
   OS/editor gitignore entries, and the basis for `AGENTS.md`/README/CHANGELOG.
3. Policy assets live under `devcovenant/core/policies/<policy>/assets/`. They
   are written only when the policy is enabled and a matching profile is active
   (i.e., listed in the policy’s `profile_scopes`).
4. Scanner adapters sit beside each policy
   (`docstring_and_comment_coverage`, `name_clarity`, `new_modules_need_tests`,
   `security_scanner`) under `scanners/<profile>.py`.
   An active profile points to its adapter. For example, the python docstring
   scanner resides in
   `devcovenant/core/policies/docstring_and_comment_coverage/scanners/`
   `python.py`.
5. Custom profiles/policies in `devcovenant/custom/` override core assets when
   their IDs collide.
6. Each profile provides a `gitignore_fragment.txt` in its assets folder; the
   installer merges these fragments in the order: global base → selected
   profile fragments → OS-specific fragments → preserved user section.

## Global gitignore entries (`global/assets/gitignore_fragment.txt`)
- OS cruft: `.DS_Store`, `Thumbs.db`, `desktop.ini`, `ehthumbs.db`,
  `.Spotlight-V100`, `.Trashes`, `Icon?`, `._*`, `.fseventsd`,
  `.TemporaryItems`
- Editors: `.vscode/`, `.idea/`, `*.suo`, `*.user`, `*.VC.db`, `*.swp`,
  `*.swo`, `__pycache__/`, `*.pyc`, `*.pyo` (guards any language profile)
- Tools: `*.log`, `.cache/`, `*.tmp`, `*.bak`, `*.orig`, `*.rej`,
  `.terraform/`, `.mypy_cache/`, `.pytest_cache/` (common cleanup)
- `.env`, `.env.*`, `.venv`, `.virtualenv`, `env/`, `venv/` (baseline)

## Profile gitignore fragments
Installers must concatenate the fragments found at
`devcovenant/core/profiles/<profile>/assets/gitignore_fragment.txt`. Each
fragment is minimal and only lists the additional paths the profile owns. For
example the `python` fragment adds `.venv/`, `__pycache__/`, `*.egg-info/`,
the `node` fragment adds `node_modules/` plus lock caches, and data fragments
add `data/tmp/`, `data/cache/`. Merge order: global fragment →
active-profile fragments (base first, derived second) → OS fragment
(`devcovenant/core/profiles/global/assets/gitignore_os.txt`).

## Default-on profiles
Only `global` stays truly always-on; `docs`, `data`, and `suffixes` install
as defaults. Remove them from `profiles.active` and rerun `devcovenant update`
to drop their assets/overlays.
### Profile: global (baseline)
- Base: applied to every install by default.
- Assets (from `global/global.yaml`): `AGENTS.md`, `README.md`, `CHANGELOG.md`,
  `CONTRIBUTING.md`, `SPEC.md`, `PLAN.md`, `LICENSE`, `VERSION`,
  `devcovenant/README.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.
  yml`,
  and the merged gitignore fragment.
- Policy overlays:
  - `version-sync`: `version_file=VERSION`, managed docs in `readme_files`,
    `changelog_file=CHANGELOG.md`, `license_files=LICENSE`.
  - `last-updated-placement`: allowed globs mirror the managed docs above.
  - `documentation-growth-tracking`: `user_visible_files` mirror the managed
    docs above.
- Gitignore fragment: OS/editor/tooling cleanup merged into `.gitignore`.

### Profile: docs (default)
- Base: global.
- Assets: `docs/assets/mkdocs.yml`.
- Policy overlays:
  - `line-length-limit`: `include_suffixes` expanded to `.md,.rst,.txt`.
  - `documentation-growth-tracking`: inherits global doc set; no extra dirs.
- Gitignore additions: `_site/`, `site/`, `build/`.

### Profile: data (default)
- Base: global.
- Assets: none (overlay-only profile).
- Policy overlays (from `data/data.yaml`):
  - `line-length-limit`: exclude `data/**`.
  - `documentation-growth-tracking`: exclude `data/**`.
  - `security-scanner`: exclude `data/**`.
  - `name-clarity`: exclude `data/**`.
  - `new-modules-need-tests`: exclude `data/**` and drop it from watch dirs.
- Gitignore fragment: `data/raw/`, `data/tmp/`, `data/cache/`.

### Profile: suffixes (default)
- Base: global (overlay helper only).
- Assets: suffix mapping JSON for installers.
- Policy overlays: none.
- Gitignore fragment: none beyond global.

## Language profiles
Each language profile includes:
- suffix list for tooling and selectors,
- `assets/` containing language-specific lockfiles/manifests,
- `gitignore_fragment.txt` with caches/build dirs,
- policy overlays for `dependency-license-sync`, `devflow-run-gates`,
  `documentation-growth-tracking`, `line-length-limit`, `version-sync` (where
  applicable), plus the scanner policies named above.
- Scanner adapters under
  `devcovenant/core/policies/<policy>/scanners/<lang>.py`.
- `tests_watch_dirs`: `tests` and language-specific nested suites (e.g.,
  `tests/devcovenant/core/profiles/python` mirrors the package layout).

### Profile: python
- Suffixes: `.py,.pyi,.pyw,.ipynb`.
- Assets: `pyproject.toml`, `requirements.in`, `requirements.lock`.
- Policy overlays (from `python/python.yaml`):
  - `dependency-license-sync`: watch `requirements.in`, `requirements.lock`,
    and `pyproject.toml`.
  - `devflow-run-gates`: `required_commands=["pytest","python3 -m unittest d
  iscover"]`.
  - `documentation-growth-tracking`, `line-length-limit`, `name-clarity`,
    `docstring-and-comment-coverage`, `new-modules-need-tests`,
    `security-scanner`: include `.py` suffix; tests watch `tests`.
  - `version-sync`: `pyproject_files=pyproject.toml`.
- Gitignore: `.venv/`, `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`,
  `build/`, `dist/`, `*.egg-info/`.

### Profile: django
- Base: python.
- Additional assets: `manage.py`, `settings.py`, `urls.py`, `wsgi.py`,
  `asgi.py`, plus a sample app.
- Overlays: extend the documentation tracker to `.html`, `.css`, and `.js`
  templates and add `.static_cache` to the gitignore fragment.

### Profile: fastapi
- Base: python.
- Assets: `main.py`, `app/__init__.py`, `openapi.json` template.
- Overlays:
  - include `.json`/`.yaml` in documentation tracking.
  - add `docs/` pipeline files and API schema watchers.
- Gitignore: inherits python plus `__pydantic_cache__/`.

### Profile: flask
- Base: python.
- Assets: `app.py`, `config.py`, optional `wsgi.py`.
- Gitignore: python plus `.uploads/` or `instance/` (app-specific).

### Profile: frappe
- Base: python + javascript + data.
- Assets: `hooks.py`, `modules.txt`, sample doctype JSON, `sites/` stub.
- Policy overlays:
  - treat `.json`/`.js` as user-facing for doc tracking.
  - point version-sync at `hooks.py`.
- Gitignore: python caches plus `sites/`, `public/files`, `private/backups`.

### JavaScript family
- Scopes: javascript, typescript, react, nextjs, vue, nuxt, svelte,
  angular, nestjs, express, node.
- Shared assets: `package.json`; lockfiles (`package-lock.json`, `yarn.lock`,
  `pnpm-lock.yaml`); tooling configs (`tsconfig.json`, `webpack.config.js`,
  `vite.config.ts`, `next.config.js`, `vue.config.js`, `nest-cli.json`).
- Shared gitignore: `node_modules/`, `dist/`, `build/`, `.cache/`, `.turbo/`,
  `.parcel-cache/`, `.next/`, `.nuxt/`, `coverage/`, `*.log`.
- Policy overlays (see per-profile YAML):
  - javascript: dependency/license sync on package + lock files; devflow gate
    `npm test`; doc-growth/line-length/name-clarity/new-tests for `.js`.
  - typescript: inherit JS overlays, add `.ts/.tsx` coverage and `tsconfig.j
  son` asset.
  - react: inherit TS overlays, add `.jsx/.tsx` coverage and framework configs
    (e.g., `vite.config.*`).
- Scanner policies (future): `name-clarity`, `security-scanner`,
  `new-modules-need-tests` get JS/TS adapters when shipped.
- Individual frameworks add assets (nextjs, vue, nuxt, svelte, angular,
  nestjs, express, node) using the shared patterns above.

### Profile: go
- Suffixes: `.go`.
- Assets: `go.mod`, `go.sum`, `Makefile` stub, `tools` for lint/test.
- Gitignore: `bin/`, `pkg/`, `vendor/`, `*.test`.
- Policies:
  - add dependency/license metadata.
  - `devflow-run-gates` uses `go test ./...`.
  - `documentation-growth-tracking` tracks `.go`.
  - `line-length-limit` includes `.go`.

### Profile: rust
- Assets: `Cargo.toml`, `Cargo.lock`.
- Gitignore: `target/`, `.cargo/`, `*.rs.bk`.
- Policies:
  - `devflow-run-gates` uses `cargo test`.
  - `dependency-license-sync` watches Cargo files.
  - `documentation-growth-tracking` tracks `.rs`.

### JVM languages (java, kotlin, scala, groovy, spring, quarkus, micronaut)
- Assets: `pom.xml`/`build.gradle*`, `settings.gradle`, `gradle.properties`,
  `application.yml`.
- Gitignore: `target/`, `build/`, `.gradle/`, `.idea/` plus IntelliJ configs.
- Policies:
  - `devflow-run-gates` commands: `mvn test` or `gradle test` (project selects
    extras via metadata).
  - Documentation tracks `.java,.kt,.kts,.scala,.groovy`.
  - `line-length-limit` includes the same suffixes.
  - Dependency sync monitors build files.

### .NET family (dotnet, csharp, fsharp)
- Assets: `.csproj`/`.fsproj`, `.sln`, `packages.lock.json`.
- Gitignore: `bin/`, `obj/`, `.vs/`, `TestResults/`, `*.user`, `*.suo`.
- Policies:
  - `devflow-run-gates` uses `dotnet test`.
  - `dependency-license-sync` reads project files.
  - Documentation tracks `.cs/.fs`.

### PHP/ecosystem (php, laravel, symfony)
- Assets: `composer.json`, `composer.lock`, `artisan`, `symfony.lock`.
- Gitignore: `vendor/`, `storage/`, `var/`, `node_modules/` (when JS interop
  exists).
- Policies:
  - `devflow-run-gates` uses `phpunit`.
  - `dependency-license-sync` watches composer data.

### Ruby/Rails
- Assets: `Gemfile`, `Gemfile.lock`, `Rakefile`, `config.ru`.
- Gitignore: `.bundle/`, `vendor/bundle/`, `log/`, `tmp/`.
- Policies:
  - `devflow-run-gates` uses `bundle exec rake test`.
  - Dependency sync via `Gemfile`.

### Profile: ruby
- See the Ruby/Rails section above for shared assets and gitignore guidance.
- Documentation tracking follows the Ruby/Rails description.

### Profile: rails
- Inherits Ruby’s assets, gitignore, and policy coverage above.

### Elixir/Erlang
- Assets: `mix.exs`, `mix.lock`, `rebar.config`, `rebar.lock`.
- Gitignore: `_build/`, `deps/`, `.elixir_ls/`.
- Policies:
  - `devflow-run-gates` uses `mix test`/`rebar3 ct`.
  - `dependency-license-sync` watches manifests.
  - Documentation tracks `.ex/.exs/.erl`.

### Profile: elixir
- Refer to the Elixir/Erlang section above for shared assets and policy spans.

### Profile: erlang
- Refer to the Elixir/Erlang section above for shared assets and policy spans.

### Functional languages (haskell, clojure, lisp, scheme, ocaml)
- Assets: language-specific project files (`stack.yaml`, `*.cabal`, `deps.edn`,
  `project.clj`, `opam` directories).
- Gitignore: `.stack-work/`, `.cpcache/`, `_build/`, `.opam/`.
- Policies:
  - Dependency sync monitors manifest files.
  - Documentation tracks `.hs/.clj/.cljs/.cljc/.edn/.lisp/.scm/.ml`.

### Systems languages (c, cpp, objective-c, swift, zig)
- Assets: `CMakeLists.txt`, `Makefile`, `Package.swift`, `build.zig`.
- Gitignore: `build/`, `out/`, `*.o`, `*.a`, `.build/`.
- Policies:
  - `documentation-growth-tracking` logs `.c,.cpp,.h,.hpp,.swift,.zig`.
  - Dependency sync hooks into cargo/zig crates when available.

### Scripted/utility languages
(perl, lua, r, julia, matlab, bash, powershell, sql)
- Assets: `cpanfile`, `rockspec`, `DESCRIPTION`, `Project.toml`,
  `pubspec.yaml`, `CITATION.md` (science), shell configs, `schema.sql`.
- Gitignore: `local/`, `.julia/`, `.Rproj.user`, `.matlab`, `*.ps1~`,
  `.terraform/` (for SQL pipelines using Terraform).
- Policies:
  - Doc growth tracks their suffixes.
  - Dependency sync watches whichever manifest exists (CPAN, rockspec,
    Project).
  - The `science` profile adds `CITATION.md`, `analysis/` asset, and metadata
    overlay for data+docs combination.

### Infrastructure profiles (terraform, docker, kubernetes, ansible)
- Assets: `main.tf`, `variables.tf`, `Dockerfile`, `docker-compose.yml`,
  `.dockerignore`, `Chart.yaml`, `values.yaml`, `ansible.cfg`, `inventory.ini`.
- Gitignore: `.terraform/`, `.docker/`, `.helm/`, `secrets/`, `.ansible/`.
- Policies:
  - `line-length-limit` includes `.tf,.yml,.yaml`.
  - `documentation-growth-tracking` tracks `.yaml` manifests.
  - `devflow-run-gates` uses `terraform plan && terraform apply` (when enabled)
    or `docker compose` combos.

### Profile: dart
- Assets: `pubspec.yaml`, `pubspec.lock`, `analysis_options.yaml`.
- Gitignore: `.dart_tool/`, `build/`, `.packages`.
- Policies:
  - `devflow-run-gates` runs `dart test`.
  - `line-length-limit` covers `.dart`.

### Profile: flutter
- Assets: Dart plus Flutter templates (`pubspec.*`, `.flutter-plugins`).
- Policies:
  - `devflow-run-gates` runs `flutter test`.
  - Documentation tracks `.dart`.
- Gitignore: `.flutter-plugins`, `.dart_tool/`, `build/`, `.packages`.

### Profile: cobol
- Assets: source files and copybooks (`*.cbl`, `*.cpy`) plus linker scripts.
- Policies:
  - `line-length-limit` covers `.cbl`.
  - Dependency tracking uses project manifests.

### Profile: crystal
- Assets: `shard.yml`, `shard.lock`, `spec/`.
- Policies: dependency sync watches shards, doc tracking covers `.cr`.

### Profile: fortran
- Assets: `*.f90`, `*.f95`, `Makefile` stubs.
- Policies:
  - `line-length-limit` tracks `.f90`.
  - `documentation-growth-tracking` logs `.f90`.

### Profile: nim
- Assets: `nimblefile`, `nim.cfg`.
- Policies: doc growth covers `.nim`, dependency sync uses Nimble metadata.

### Profile: pascal
- Assets: `*.pas`, `*.pp`.
- Policies:
  - `line-length-limit` tracks Pascal suffixes.
  - Doc growth covers `.pas`.

### Profile: prolog
- Assets: `*.pl`, `*.pro`.
- Policies:
  - `line-length-limit` covers `.pl`.
  - Doc growth tracks `.pl` and `.yap`.

### Profile: devcovrepo (repo-specific)
- Base: global + python + docs + data, tuned for DevCovenant’s own sources.
- Assets: metadata-only overlay in
  `devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml`.
- Policy overlays:
  - `new-modules-need-tests`: trims the exclusion list and points both
    `watch_dirs` and `tests_watch_dirs` at `tests/devcovenant/core` and
    `tests/devcovenant/custom` so the mirrored adapters remain covered.
- Gitignore: none beyond the aggregate fragments from the active base
  profile set.
- Activation: enabled only when `devcov_core_include: true` (dogfooding in the
  DevCovenant repo); not shipped/active in user installs.

### Profile: devcovuser (user-focused)
- Base: global + docs + data (keeps interpreter languages optional for users).
- Assets: metadata-only overlay in
  `devcovenant/core/profiles/devcovuser/devcovuser.yaml` (core, always
  shipped).
- Policy overlays:
  - `new-modules-need-tests`: excludes `devcovenant/**` while including
    `devcovenant/custom/**` so user-side policies do not enforce the tooling
    tree but still monitor custom additions.
- Gitignore: none beyond the aggregate fragments from the active base
  profile set.
- Activation: default-on in user installs; automatically disabled when
  `devcov_core_include: true` so `devcovrepo` can enforce the full
  `devcovenant/**` tree during self-dogfood.
- Shared assets: `package.json`; lockfiles (`package-lock.json`, `yarn.lock`,
  `pnpm-lock.yaml`); tooling configs (`tsconfig.json`, `webpack.config.js`,
  `vite.config.ts`, `next.config.js`, `vue.config.js`, `nest-cli.json`).
  - typescript: inherit JS overlays; add `.ts/.tsx` coverage and
    `tsconfig.json`.
