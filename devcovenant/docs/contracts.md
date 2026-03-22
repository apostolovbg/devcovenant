# Contracts
**Last Updated:** 2026-03-22
**Project Version:** 1.0.0

## Overview
This document is the contract index for the DevCovenant package docs.
Use it when you need to know which page is the normative home for a stable
public contract and where a future change should be documented first.

The detailed docs should stay operator-oriented and explanatory.
That does not remove the need for a stable contract map.
This page exists so the package docs can stay readable without turning every
page into a competing master index.

## Frozen Contract Homes
The current normative homes are:

- `devcovenant/docs/installation.md` for the lifecycle command contract

- `devcovenant/docs/refresh.md` for the managed-documents contract and
  managed doc descriptor schema

- `devcovenant/docs/workflow.md` for the gate sequence and run-artifact
  contract

- `devcovenant/docs/config.md` for the public `devcovenant/config.yaml`
  contract

- `devcovenant/docs/project_governance.md` for the `project-governance`
  contract

- `devcovenant/docs/registry.md` for the registry contract

- `devcovenant/docs/policies.md` for the policy descriptor contract and
  version-governance adapter contract

## Documentation Writing Contract
Documentation in this package should be operator-oriented and explanatory at
the same time.
Write for a technically serious reader who needs a clear next action and a
clear explanation, not for someone who enjoys decoding insider shorthand.

The stable writing rules are:

- expand an abbreviation on first use in each document

- avoid soft marketing phrasing when direct technical wording is clearer

- treat half-documented behavior, repeated boilerplate, and duplicate
  competing explanations as defects

- prefer direct technical prose over artistic or self-conscious wording

- keep templates substantial enough that new repos start from real documents,
  not placeholder stubs

## Practical Use
When you change one of the contract pages, update that page first.
Then update any operator-facing summaries, templates, or supporting docs that
point back to it.
