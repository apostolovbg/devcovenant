# Troubleshooting

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Policy Registry Drift](#policy-registry-drift)
- [Doc Growth Warnings](#doc-growth-warnings)
- [Gate Failures](#gate-failures)
- [Adapter Issues](#adapter-issues)

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
- Re-run `python3 -m devcovenant gate --start`.
- Run `python3 -m devcovenant test`.
- Finish with `python3 -m devcovenant gate --end`.

## Adapter Issues
Symptom: policy reports missing adapter for active profile.
Fix:
- Add the adapter under `adapters/<profile>.py`.
- Update tests to cover the new adapter dispatch.
