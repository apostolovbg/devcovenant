# DevCovenant Delivery Plan
**Last Updated:** 2026-01-11
**Version:** 0.1.1

DevCovenant is being spun out into a standalone, self-enforcing tool. This
plan tracks the migration and stabilization steps.

## 1) Foundation (current)
- Package core code under `devcovenant/`.
- Provide `AGENTS.md`, `DEVCOVENANT.md`, `README.md`, `CONTRIBUTING.md`.
- Add `VERSION`, `CHANGELOG.md`, `CITATION.cff`, `LICENSE`.
- Pre-commit + tests + CI wired and enforced.

## 2) Installer and uninstaller
- Implement `tools/install_devcovenant.py` and
  `tools/uninstall_devcovenant.py`.
- Maintain an install manifest to avoid overwriting repo docs.
- Support update-only behavior when already installed.

## 3) Policy schema standardization
- Enforce full standard fields in every policy block.
- Split policy-specific fields into a clearly labeled section.
- Introduce `apply` flag to replace waivers (with compatibility layer).

## 4) Policy packs and API
- Expose a formal Policy base class and helper utilities.
- Provide built-in "commons" policy pack.
- Add language presets for Python and JS/TS tooling.

## 5) Publishing and migration
- Publish to PyPI and document GitHub install path.
- Migrate copernican, custom, and infra repos to standalone DevCovenant.
- Keep compatibility adapters during transition.
