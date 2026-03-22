# Support and Maintenance
## Table of Contents
- [Overview](#overview)
- [How To Ask For Help](#how-to-ask-for-help)
- [What To Include](#what-to-include)
- [Support Scope](#support-scope)
- [Workflow](#workflow)
- [What Is Out Of Scope](#what-is-out-of-scope)

## Overview
DevCovenant is maintained as a serious open repository tool, but it does not
come with a commercial support desk or a formal service-level agreement (SLA).

This document explains how to ask for help and what kind of maintenance support
this repository currently aims to provide.

## How To Ask For Help
Use the public repository issue tracker for:
- bug reports
- usage questions
- unclear documentation
- governance or workflow regressions
- package and installation problems

For security-sensitive defects, use `SECURITY.md` instead of posting exploit
material publicly.

## What To Include
A good support report should include:
- the DevCovenant version or commit you are using
- operating system and Python version
- the exact command you ran
- the active profiles or relevant config overrides
- the smallest reproduction you can provide
- `summary.txt` and `tail.txt` when a run-log folder exists
- relevant parts of `stdout.log` or `stderr.log` after reviewing them for
  secrets

Start small.
In many cases, `summary.txt`, the failing command, and one relevant config
excerpt are enough to unblock triage.

## Support Scope
Reasonable support scope for this repository includes:
- the current maintained public release line
- the current mainline source state in this repository
- built-in policies, profiles, translators, commands, and managed docs
- the documented workflow, config, and runtime evidence model

Custom extensions are still supported at the interface level, but debugging
custom policy or profile code is naturally more repo-specific and may require
more self-service from the integrator.

## Workflow
Use this support flow when you need help:
- start with the public issue tracker for normal product and documentation
  questions
- use `SECURITY.md` instead when the issue is potentially security-sensitive
- use `PRIVACY.md` before attaching logs or snapshots so you know what each
  artifact may contain
- include the smallest useful reproduction and the most relevant run-log
  artifacts first, then expand only if follow-up triage needs more detail

## What Is Out Of Scope
The current support posture does not promise:
- a formal uptime or response-time commitment
- custom consulting for arbitrary downstream repositories
- private support channels for ordinary non-security questions
- maintenance of forks or heavily modified private derivatives as if they were
  the upstream product

When a report falls outside the built-in product surface, we should still try
to leave the reporter with a concrete next step rather than a dead end.
