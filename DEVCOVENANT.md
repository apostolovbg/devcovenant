# DevCovenant Reference
**Last Updated:** 2026-01-11
**Version:** 0.1.1

This document describes how DevCovenant works, how policies are structured,
and how to install, update, or remove it from other repositories. Keep
`AGENTS.md` as the canonical source of truth for policy definitions.

## 1. What DevCovenant Is
DevCovenant is a policy engine that reads human-readable rules, validates
repository state, and enforces consistency. Each policy has a plain-language
statement and a machine-readable metadata block.

## 2. Core Architecture
- `devcovenant/parser.py` reads policy blocks from `AGENTS.md`.
- `devcovenant/registry.json` stores policy hashes to detect drift.
- `devcovenant/policy_scripts/` implements checks and optional fixes.
- `devcovenant/cli.py` drives check/fix commands.

## 3. Policy Schema
Each policy block has two sections:

### 3.1 Standard fields
These apply to every policy and are always present:
- `id`, `status`, `severity`, `apply`, `auto_fix`, `updated`
- `applies_to`, `enforcement`, `waiver` (legacy until `apply` replaces it)
- `include_prefixes`, `exclude_prefixes`, `include_globs`, `exclude_globs`
- `include_suffixes`, `exclude_suffixes`, `force_include_globs`
- `force_exclude_globs`, `notes`

### 3.2 Policy-specific fields
Each policy can define its own extra keys (for example `version_file`,
`changelog_file`, or `required_commands`). Document them inside the policy
block so contributors learn how to extend the system.

## 4. Install, Update, Uninstall
- Install: `python tools/install_devcovenant.py --target <repo>`
- Update: re-run install; it updates core files and avoids overwriting
  existing project docs (AGENTS, README, VERSION, etc.).
- Uninstall: `python tools/uninstall_devcovenant.py --target <repo>`

The install script records an `.devcovenant/install_manifest.json` so updates
and removals are predictable and safe.

## 5. Self-Enforcement
This repo is enforced by DevCovenant itself. The required workflow is:
1. `python tools/run_pre_commit.py --phase start`
2. `python tools/run_tests.py`
3. `python tools/run_pre_commit.py --phase end`

## 6. Repository Standards
- `AGENTS.md` is the canonical source of truth.
- Keep versions and last-updated timestamps synchronized across docs.
- Enforce 79-character lines for code and docs unless explicitly overridden.

## 7. Roadmap
See `PLAN.md` for the staged roadmap to full standalone packaging and the
migration of downstream repos.
