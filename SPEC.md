# DevCovenant Specification
**Last Updated:** 2026-01-11
**Version:** 0.1.1

This specification defines what DevCovenant must do for both the standalone
project and for any repository that installs it.

## Table of Contents
1. [Overview](#overview)
2. [Workflow](#workflow)
3. [Functional Requirements](#functional-requirements)
4. [Policy Requirements](#policy-requirements)
5. [Installation Requirements](#installation-requirements)
6. [Non-Functional Requirements](#non-functional-requirements)

## Overview
DevCovenant is a self-enforcing policy engine. It reads policy definitions from
`AGENTS.md`, enforces them through policy scripts, and prevents drift between
human documentation and automated checks. The system must be portable, safe to
install, and reversible without losing user documentation.

## Workflow
- Policies are defined in `AGENTS.md` and treated as the source of truth.
- Policy changes require updates to scripts and tests.
- Hash synchronization prevents policy/script drift.
- The standard gate sequence is pre-commit start → tests → pre-commit end.
- Use `python3` for helper scripts when available (`python` only if it points
  to Python 3 on the host system).

## Functional Requirements
- Parse policy definitions from `AGENTS.md`.
- Run policy scripts and report violations by severity.
- Support auto-fix where policies allow it.
- Maintain a registry of policy and script hashes.
- Provide a CLI for `check`, `sync`, `test`, and `update-hashes` commands.
- Provide wrapper scripts for pre-commit and test gating.
- Provide a CLI-only installer with explicit modes for empty vs. existing
  repositories and options to preserve or overwrite docs/config/metadata.
- Support multi-language repos via configurable language profiles that extend
  the engine’s file suffix inventory.

## Policy Requirements
- Every policy definition must include descriptive text.
- Built-in policies ship with canonical text stored in DevCovenant.
- If canonical text is modified in a repo, DevCovenant must warn and guide
  the agent to either restore stock text or patch the policy logic.
- Provide a command to restore stock policy text by policy id.
- Policies must support an `apply` flag that enables or disables enforcement
  without removing the definition.
- Policies with status `fiducial` must be enforced and emit a reminder that
  includes the policy text on every run.

## Installation Requirements
- Install the full DevCovenant toolchain into the target repo.
- Preserve existing user documentation unless explicitly overridden.
- Inject DevCovenant-managed doc blocks using DEVCOV markers.
- Track installations with `.devcov/install_manifest.json`.
- If no license exists, install a GPL-3.0 license by default.
- Default user installs to `devcov_core_include: false` so core files remain
  excluded from enforcement and update-safe.
- Treat `SPEC.md` and `PLAN.md` as required documentation files during
  installation and enforcement.
- Preserve custom policy scripts, patches, and configuration during updates
  unless explicitly overridden.
- Install or update CI workflows to ensure pre-commit, pytest, PyYAML, and
  semver dependencies are available for checks.

## Non-Functional Requirements
- The engine must run quickly enough for pre-commit usage.
- Policies must produce actionable, readable violation messages.
- Documentation must meet minimum quality standards.
- Installation and removal must be deterministic and reversible.
