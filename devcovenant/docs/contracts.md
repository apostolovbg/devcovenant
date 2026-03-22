# Product Contracts
**Last Updated:** 2026-03-21
**Project Version:** 1.0.0

## Table of Contents
- [Overview](#overview)
- [Contract Index](#contract-index)
- [Normative and Explanatory Documents](#normative-and-explanatory-documents)
- [Documentation Writing Contract](#documentation-writing-contract)
- [Workflow](#workflow)

## Overview
This document is the index for DevCovenant's frozen product contracts.

Each contract below has one normative home. That normative home defines what
DevCovenant promises, what inputs it accepts, what outputs it owns, and where
runtime enforcement already exists. Other documents may explain or summarize
those contracts, but they must point back to the normative home instead of
becoming alternate competing sources of truth.

Use this document when you need to answer questions like:
- which document is the contract for managed docs?
- where is the exact lifecycle command contract frozen?
- which docs are explanatory, and which docs define the stable rule?
- what writing rules apply to DevCovenant documentation itself?

## Contract Index
The frozen contract set is:
- managed-documents contract:
  `devcovenant/docs/refresh.md`
- managed-document descriptor schema:
  `devcovenant/docs/refresh.md`
- bootstrap, install, deploy, refresh, upgrade, undeploy, and uninstall
  contract:
  `devcovenant/docs/installation.md`
- gate sequence and run-artifact contract:
  `devcovenant/docs/workflow.md`
- public config contract:
  `devcovenant/docs/config.md`
- project-governance contract:
  `devcovenant/docs/project_governance.md`
- registry contract:
  `devcovenant/docs/registry.md`
- policy descriptor contract:
  `devcovenant/docs/policies.md`
- version-governance adapter contract:
  `devcovenant/docs/policies.md`
- documentation writing contract:
  this document

## Normative and Explanatory Documents
Normative documents:
- define the exact rule or interface
- are the first place to update when the contract changes
- should be cited by other docs instead of duplicated loosely

Explanatory documents:
- teach how to use the contract in practice
- give examples, scenarios, and operator guidance
- may summarize the contract only enough to support their own topic
- must point back to the normative home when exact truth matters

Primary-home rule:
- each major contract gets one normative home
- reference docs should stay aligned with that home
- when two docs start restating the same rule in full, one of them should be
  reduced to a summary plus pointer

## Documentation Writing Contract
Documentation in this repository must be operator-oriented and explanatory at
the same time.

Stable writing rules:
- explain what a thing is, why it exists, what it controls, and when to use
  it
- keep operational steps explicit and easy to follow
- avoid insider shorthand when a concrete phrase is clearer
- avoid soft marketing phrasing such as whether DevCovenant "fits" a repo;
  prefer concrete phrasing such as how it works, how to use it, or how to
  integrate it
- expand an abbreviation on first use in each document
- keep config comments practical, concrete, and useful at the point of
  reading
- treat undocumented behavior, half-documented behavior, and duplicate
  competing explanations as defects

Documentation should teach by being clear. It should not rely on rhetoric
about learning or teaching to do that work.

## Workflow
When behavior changes:
1. update the normative home first
2. update runtime enforcement or validation when needed
3. update tests that prove the contract
4. update explanatory docs so they point back to the normative home and stay
   aligned with it
5. run the normal gate workflow from `devcovenant/docs/workflow.md`
