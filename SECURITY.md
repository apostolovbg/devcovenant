# Security Policy
**Doc ID:** SECURITY
**Doc Type:** security-policy
**Project Version:** 1.0.1b1
**Last Updated:** 2026-04-04
**DevCovenant Version:** 1.0.1b1

<!-- DEVCOV:BEGIN -->
This opening section is managed by DevCovenant.
Use this document for repository-specific security reporting,
disclosure, and assurance notes.
<!-- DEVCOV:END -->

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
DevCovenant is maintained as a local repository-governance tool, but we
still handle security defects as product defects.

Use this document for:
- vulnerability reporting
- disclosure expectations
- static-analysis interpretation
- support boundaries for security fixes

## Reporting A Vulnerability
For non-sensitive security defects, open a normal repository issue.

For potentially sensitive findings:
- do not publish exploit details, proof-of-concept payloads, or
  secret-bearing reproduction material in a public issue first
- use the repository host's private security-reporting path if it is
  enabled
- if no private reporting path is available, open a minimal public issue
  that requests a private contact channel without disclosing the exploit
  details

## What To Include
A useful report should include:
- the DevCovenant version or commit under test
- the operating system and Python version
- whether the issue affects source checkout, installed package use, or both
- exact commands, configuration, and files needed to reproduce
- expected behavior, actual behavior, and practical impact
- whether the issue is local-only, repository-content dependent, or package
  or release-surface dependent

Redact secrets before sharing logs or configs.
If the defect depends on a secret-bearing value, describe the shape of the
value rather than pasting the real secret.

## Disclosure Expectations
Our normal security posture is:
- reproduce and scope the issue first
- keep exploit details narrow until a fix or mitigation exists
- fix the latest maintained line first
- publish clear remediation guidance once the fix is ready

We do not promise a paid bug bounty or a formal service-level agreement
(SLA).
We do promise to treat credible security reports as high-priority
maintenance work.

## Static Analysis And Triage
DevCovenant uses static-analysis tools such as Bandit and dependency
auditing as review tools, not as unquestioned truth.

Interpret them this way:
- real runtime-hardening defects should be fixed in code
- boundary-reviewed process execution that uses explicit tokenized argument
  lists and avoids `shell=True` still requires review, but scanner warnings
  on those paths are not automatically vulnerabilities by themselves
- false positives, such as secret-literal warnings on ordinary control
  tokens, should be documented explicitly rather than silently ignored
- `bandit.yaml` skips Bandit `B105` because that heuristic repeatedly
  misclassifies ordinary control tokens such as `start`, `critical`,
  `stdout`, and `false` as secret material
- reviewed process boundaries now carry targeted `# nosec` markers so
  Bandit output stays focused on unexpected subprocess surfaces rather than
  on the deliberate core runtime boundaries we already review manually

The runtime deliberately keeps:
- no outbound telemetry in DevCovenant itself
- explicit process boundaries
- local evidence artifacts under `devcovenant/logs/` and
  `devcovenant/registry/runtime/`

## Continuous Assurance
DevCovenant keeps release assurance visible in normal automation:
1. the builtin `github` profile supplies the generic source-tree `CI`
   workflow for GitHub Actions, including the bootstrap gate/run automation
   on Python `3.14`
2. this repository activates `github`, then its custom same-name
   `userproject` profile extends the main `governance` job
   with `pip-audit -r requirements.lock` and
   `bandit -q -c bandit.yaml -r devcovenant`
3. the repo-specific `Build` job inside `CI` owns built-artifact proof for
   the wheel, sdist, and documented `pipx` install path, and each proof
   runs the full public workflow: `gate --start`, `gate --mid`, `run`,
   `gate --end`, then `check`
4. repo-specific CI jobs use DevCovenant's managed-environment contract
   instead of hardcoding one environment type's shell-activation command
5. `bandit.yaml` is the tracked Bandit configuration surface for this repo's
   low-signal skip list
6. the publish workflow uses PyPI trusted publishing instead of a long-lived
   upload token, and PyPI-side attestations are emitted through that publish
   path

These checks are review surfaces, not a claim that one scanner is
infallible.
When scanners disagree, DevCovenant's rule is to document the disagreement,
keep the reviewed boundary explicit, and avoid silently suppressing the
result.
The repo-specific `pip-audit` invocation carries one documented temporary
ignore for `CVE-2026-4539` in transitive `pygments`, because `pytest`
requires `pygments`, the advisory currently has no published fix release,
and the report describes local-only exploitation.
That exception belongs in repo-specific CI only and should be removed as
soon as upstream publishes a fixable release path.

## Workflow
Use this document in the normal reporting flow:
- start here when the issue is security-relevant or when you are unsure
  whether a defect crosses into security territory
- use `PRIVACY.md` alongside it when the report includes logs, snapshots, or
  local evidence artifacts
- use `SUPPORT.md` for ordinary non-security help requests after you rule
  out a security angle
- when the finding is sensitive, keep the first report minimal and private
  if the repository host provides a private security-reporting path

## Supported Security Baseline
Security fixes are handled against:
- the maintained public `1.0.1` release line
- the main source tree in this repository

If you report an issue against an older tree, reproduce it against the
latest maintained line or the main source tree first when possible.
