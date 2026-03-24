# Security Policy
## Table of Contents
- [Overview](#overview)
- [Reporting A Vulnerability](#reporting-a-vulnerability)
- [What To Include](#what-to-include)
- [Disclosure Expectations](#disclosure-expectations)
- [Static Analysis And Triage](#static-analysis-and-triage)
- [Continuous Assurance](#continuous-assurance)
- [Workflow](#workflow)
- [Supported Security Baseline](#supported-security-baseline)

## Overview
DevCovenant is maintained as a local repository-governance tool, but we still
handle security defects as product defects.

Use this document for:
- vulnerability reporting
- disclosure expectations
- static-analysis interpretation
- support boundaries for security fixes

## Reporting A Vulnerability
For non-sensitive security defects, open a normal repository issue.

For potentially sensitive findings:
- do not publish exploit details, proof-of-concept payloads, or secret-bearing
  reproduction material in a public issue first
- use the repository host's private security-reporting path if it is enabled
- if no private reporting path is available, open a minimal public issue that
  requests a private contact channel without disclosing the exploit details

## What To Include
A useful report should include:
- the DevCovenant version or commit under test
- the operating system and Python version
- whether the issue affects source checkout, installed package use, or both
- exact commands, configuration, and files needed to reproduce
- expected behavior, actual behavior, and practical impact
- whether the issue is local-only, repository-content dependent, or package /
  release-surface dependent

Redact secrets before sharing logs or configs.
If the defect depends on a secret-bearing value, describe the shape of the
value rather than pasting the real secret.

## Disclosure Expectations
Our normal security posture is:
- reproduce and scope the issue first
- keep exploit details narrow until a fix or mitigation exists
- fix the latest maintained line first
- publish clear remediation guidance once the fix is ready

We do not promise a paid bug bounty or a formal service-level agreement (SLA).
We do promise to treat credible security reports as high-priority maintenance
work.

## Static Analysis And Triage
DevCovenant uses static-analysis tools such as Bandit and dependency auditing
as review surfaces, not as unquestioned truth.

Current interpretation rules:
- real runtime-hardening defects should be fixed in code
- boundary-reviewed process execution that uses explicit tokenized argument
  lists and avoids `shell=True` still requires review, but scanner warnings on
  those paths are not automatically vulnerabilities by themselves
- false positives, such as secret-literal warnings on ordinary control tokens,
  should be documented explicitly rather than silently ignored
- `bandit.yaml` skips Bandit `B105` because that heuristic repeatedly
  misclassifies ordinary control tokens such as `start`, `critical`,
  `stdout`, and `false` as secret material
- reviewed process boundaries now carry targeted `# nosec` markers so Bandit
  output stays focused on unexpected subprocess surfaces rather than on the
  deliberate core runtime boundaries we already review manually

The current runtime contract intentionally keeps:
- no outbound telemetry in DevCovenant itself
- explicit process boundaries
- local evidence artifacts under `devcovenant/logs/` and
  `devcovenant/registry/runtime/`

## Continuous Assurance
DevCovenant keeps release assurance visible in normal automation:
1. the generated `CI and Test` workflow provides the generic base gate/test
   automation on bootstrap Python `3.14`

2. this repository's `devcovrepo` profile extends the main `CI and Test`
   job with `pip-audit -r requirements.lock` and
   `bandit -q -c bandit.yaml -r devcovenant`

3. the same repo-specific profile adds one dependent `Build and Install Test`
   job that builds artifacts, runs `twine check`, installs the built CLI with
   `pipx`, and verifies the installed command surface

4. repo-specific CI jobs use DevCovenant's managed-environment contract
   instead of hardcoding one environment type's shell-activation command

5. `bandit.yaml` is the tracked Bandit configuration surface for this repo's
   low-signal skip list

7. the publish workflow uses PyPI trusted publishing instead of a long-lived
   upload token, and PyPI-side attestations are emitted through that publish
   path

These checks are review surfaces, not a claim that one scanner is infallible.
When scanners disagree, DevCovenant's rule is to document the disagreement,
keep the reviewed boundary explicit, and avoid silently suppressing the
result.

## Workflow
Use this document in the normal reporting flow:
- start here when the issue is security-relevant or when you are unsure
  whether a defect crosses into security territory
- use `PRIVACY.md` alongside it when the report includes logs, snapshots, or
  local evidence artifacts
- use `SUPPORT.md` for ordinary non-security help requests after you rule out
  a security angle
- when the finding is sensitive, keep the first report minimal and private if
  the repository host provides a private security-reporting path

## Supported Security Baseline
Security fixes are handled against:
- the current maintained public `1.x` release line
- the current mainline source state in this repository

If you report an issue against an older tree, reproduce it against the latest
maintained line or current mainline first when possible.
