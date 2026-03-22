# Registry Files
**Last Updated:** 2026-03-22
**Project Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Tracked Registry](#tracked-registry)
- [Runtime Registry](#runtime-registry)
- [Gate Status Contract](#gate-status-contract)
- [Lifecycle](#lifecycle)
- [Validation and Integrity](#validation-and-integrity)
- [Workflow](#workflow)

## Overview
DevCovenant uses one visible registry root under `devcovenant/registry/`.
Tracked governance metadata lives in `registry.yaml`, while disposable runtime
state lives under `devcovenant/registry/runtime/`.

Treat generated registry files as:
- diagnostics
- reproducibility artifacts
- synchronization evidence for integrity checks

For the meanings of the resolved `project-governance` fields stored here, see
`devcovenant/docs/project_governance.md`.

Manual edits are unsupported and typically interpreted as drift.

How to use the registry in practice:
- use `devcovenant/config.yaml` to decide what the repo should do
- use `AGENTS.md` to read the active workflow and policy contract
- use `devcovenant/registry/registry.yaml` to audit what DevCovenant
  actually resolved from that configuration

That makes the registry an explanation surface, not a normal editing surface.
This is the primary home for registry meaning. Use
`devcovenant/docs/refresh.md` for regeneration behavior and
`devcovenant/docs/workflow.md` for gate/session order.
It is also the normative home for the registry contract. Use
`devcovenant/docs/contracts.md` for the contract index.

## Tracked Registry
`devcovenant/registry/registry.yaml` is the only tracked registry artifact.
Changes to that file are routed here by documentation-growth-tracking because
this document is the user-facing explanation of the tracked registry contract.
It includes:
- resolved `project-governance` state as its own top-level registry section
- resolved `managed-docs` state as its own top-level registry section
- discovered policy IDs (identifiers)
- descriptor/script paths and hashes
- refresh-generated policy hashes and metadata snapshots that also move when
  shared runtime services change policy behavior
- tracked policy hashes therefore also move when a policy script changes only
  in its loading boundary or helper wiring, because the registry records the
  current shipped policy code, not only user-visible policy prose
- descriptor-driven managed-doc runtime changes that affect generated
  governance output, including authoritative-source coverage, after refresh
  regenerates the tracked registry
- resolved managed-doc selection from `doc_assets`, including optional
  builtin-doc disablement and any custom managed docs discovered from active
  profile asset roots
- managed-doc descriptor paths plus body-only fingerprints for current
  template bodies and any exact legacy generic bodies that refresh may
  replace
- resolved metadata snapshots
- per-key metadata resolution trace (`metadata_resolution`)
- structured override-replacement diagnostics (`metadata_warnings`)
- typed runtime metadata view (`runtime_metadata_options`)
- typed config-override view (`runtime_config_overrides`)
- merged runtime-effective option view (`runtime_effective_options`)
- discovered profile inventory and active-profile state
- tracked inventory data used by refresh and integrity checks
- current policy identities and resolved metadata for shipped frameworks such
  as `version-governance`, including the configured scheme and bump
  enforcement options that active profiles/config resolved
- resolved `project-governance` lifecycle metadata, including stage,
  development stance, versioning mode, public project identity
  (`project_name`, `project_description`), optional codename/build identity,
  displayed project version, and active release headings

Metadata trace intent:
- `metadata` remains the final effective string-map used for policy/runtime
  loading contracts
- `metadata_resolution` explains how each effective key was composed across
  descriptor, profile overlay, config overlay, config override, and
  policy-state layers
- `metadata_warnings` records destructive override cases where an override
  replaced inherited non-empty values; this is an audit aid, not a silent
  autofix
- typed runtime option views make the final policy surface inspectable without
  re-deriving values by hand
- scheme-driven policies such as `version-governance` also record the
  configured adapter identity and resolved options here so package-facing
  repos can prove whether repo version checks are running under a general
  scheme contract, a packaging-aware contract such as `pep440`, or a
  repo-defined custom contract using `custom_regex_pattern` or
  `custom_adapter_path`
- `version-sync` records scheme-neutral extractor mappings such as
  `project_version_line`, optional role-legality mappings such as
  `package_manifest=>pep440`, and leaves repo-level equality semantics to
  the active `version-governance` scheme
- the top-level `project-governance` registry section records whether the
  repo is versioned or intentionally unversioned, plus the configured
  displayed non-version label and unreleased changelog heading when those
  apply
- the top-level `managed-docs` registry section records descriptor roots,
  enabled managed docs, and per-doc body fingerprints; those fingerprints
  intentionally ignore generated headers so routine `Last Updated` changes do
  not look like template changes
- runtime readers now reuse one shared YAML cache when they consult the
  tracked registry during `check`, gate, refresh, install, deploy, and
  undeploy, but the tracked registry file itself remains the same
  deterministic refresh-owned source of truth
- fresh installs therefore record an explicit unversioned baseline
  instead of relying on a fabricated placeholder version token
- generic profile defaults now keep version-governance scheme selection
  explicit; tracked registry output therefore shows the scheme a repo chose
  intentionally instead of implying a hidden global baseline

## Runtime Registry
`devcovenant/registry/runtime/` stores runtime-local state such as:
- `gate_status.json`
- `session_snapshot.json`
- `latest.json`

Runtime registry files are:
- untracked
- disposable
- local to the current machine/session/branch context

Cleanup rule:
- `devcovenant clean --registry` removes runtime registry residue only
- `devcovenant clean --logs` removes disposable run-log directories only
- tracked files such as `devcovenant/registry/registry.yaml`,
  `devcovenant/registry/README.md`, and `devcovenant/logs/README.md`
  remain outside cleanup scope

## Gate Status Contract
`gate_status.json` is the concise workflow session ledger used by
gate-aware policies. It is also a core evidence artifact in the gate-session
evidence family.

Heavy session payloads live in the companion
`devcovenant/registry/runtime/session_snapshot.json` file. That companion
stores:
- `session_start_snapshot`
- optional `session_baseline_snapshot`
- `session_end_snapshot`
- `last_run_snapshot`
- `document_exemption_baseline`
- full normalized `test_events`

Key evidence families:
- concise lifecycle timestamps and command records
- open/closed session state
- pointer metadata for the companion session snapshot
- changelog snapshot anchors/fingerprints
- active release-heading behavior resolved from the top-level
  `project-governance` registry section
- heavy session baseline/snapshot evidence in `session_snapshot.json`
- test lifecycle event payloads in `session_snapshot.json`

Relationship to run-log evidence artifacts:
- `gate_status.json` stores concise lifecycle/session evidence
- `session_snapshot.json` stores heavy snapshot/baseline evidence
- `latest.json` stores the latest run-pointer metadata for status helpers
- `devcovenant/logs/<run-id>-<command>/` stores per-command run evidence
- use both together when reconstructing what happened in a work slice

Operational rule:
- do not delete or rewrite runtime registry files during an active session
  unless a recovery procedure explicitly requires it

## Lifecycle
Tracked registry regeneration occurs on full refresh paths:
- `devcovenant refresh`
- `devcovenant deploy`
- `devcovenant upgrade`
- gate pre-commit phases (`devcovenant gate --start` / `--end`) through the
  gate-owned `check` orchestration path
- policy descriptor text/hash changes propagate into
  `devcovenant/registry/registry.yaml` on the next full refresh path, so the
  tracked registry keeps the current policy contract text, hash state, and
  synchronized-equality contract changes

Gate status evolves on:
- `devcovenant gate --start`
- `devcovenant gate --mid` (non-lifecycle checks only; no status writes)
- `devcovenant test`
- `devcovenant gate --end`
- `devcovenant gate --status` (read-only inspection; no ledger writes)

Session snapshot companion data evolves on:
- `devcovenant gate --start`
- `devcovenant test`
- `devcovenant gate --end`

Registry behavior expectations:
- deterministic for unchanged tracked inputs
- aligned with current descriptors/profiles/config
- validated by integrity policies and gate workflow
- recreated explicitly by refresh-producing commands when missing
- kept out of package payloads even though install/refresh/upgrade recreate
  the tracked registry structure inside a repository

## Validation and Integrity
`devcov-integrity-guard` validates registry state against active policy source
and runtime expectations.

When drift is detected:
1. run `devcovenant refresh`
2. rerun `devcovenant test`
3. rerun `devcovenant gate --end`

If drift persists:
- verify descriptor/profile edits were completed
- verify managed blocks were not manually edited
- verify refresh ran from repository root

## Workflow
Use this document when the question is "what does this registry artifact
mean?" or "which state is tracked versus runtime-local?".
For the exact gate sequence, use `devcovenant/docs/workflow.md`.

Registry-change loop:
1. Change descriptor/profile/config inputs.
2. Run refresh to regenerate tracked registry artifacts.
3. Inspect `devcovenant/registry/runtime/` for live session state only.
4. Run the normal gate workflow from `devcovenant/docs/workflow.md`.
