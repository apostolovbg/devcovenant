# Troubleshooting

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Policy Registry Drift](#policy-registry-drift)
- [Doc Growth Warnings](#doc-growth-warnings)
- [Gate Failures](#gate-failures)
- [Repo Bytecode Drift](#repo-bytecode-drift)
- [Translator Issues](#translator-issues)

## Overview
This guide lists common DevCovenant errors and the fastest way to resolve
them. When in doubt, rerun refresh, confirm the active profiles, and check
the registry for mismatched hashes.

## Workflow
1. Identify the failing policy and message.
2. Inspect the relevant file or registry entry.
3. Re-run the appropriate command (`refresh`, `test`, or `check`).

## Policy Registry Drift
Symptom: policy hash mismatch or registry warnings.
Fix:
- Run `devcovenant refresh` after policy edits.

## Doc Growth Warnings
Symptom: documentation-growth-tracking reports missing doc updates.
Fix:
- Update the user-facing doc set listed in the policy metadata.
- Mention the changed file or component in the docs.

## Gate Failures
Symptom: `devflow-run-gates` reports missing start/test/end records.
Fix:
- Re-run `devcovenant gate --start`.
- Run `devcovenant gate --mid` until clean.
- Run `devcovenant test`.
- Finish with `devcovenant gate --end`.

## Repo Bytecode Drift
Symptom: `devcov-structure-guard` reports `devcovenant/__pycache__/` or
`*.py[cod]` under `devcovenant/`.
Fix:
- Delete repo-local bytecode artifacts under `devcovenant/`.
- Re-run the required gate step (and `devcovenant test` first if the gate
  sequence requires a fresh test run).
Prevention:
- Enable `engine.pycache_prefix_enabled: true` in `devcovenant/config.yaml`
  so DevCovenant-managed Python subprocesses use `PYTHONPYCACHEPREFIX`.
- For fallback launcher runs (`python3 -m devcovenant ...`), set
  `PYTHONPYCACHEPREFIX` in the shell/CI environment before Python starts.

## Translator Issues
Symptom: policy reports missing translator coverage for active language
profiles.
Fix:
- Add/update the language profile translator declaration and translator
  module.
- Update tests to cover translator routing and `LanguageUnit` output.
