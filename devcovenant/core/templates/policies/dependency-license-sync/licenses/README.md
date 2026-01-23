# Dependency License Sync Template

## Table of Contents
1. Overview
2. Template Contents
3. Workflow
4. Notes

## Overview
This template documents the license directory shipped with the
dependency-license-sync policy. It provides a consistent place to keep
third-party license texts when the policy is enabled in a target repo.

## Template Contents
When DevCovenant installs this policy, it creates a licenses folder and
expects future automation to drop refreshed license texts here. The
templates are placeholders that remind maintainers to keep the directory
aligned with dependency manifests and the license report.

## Workflow
After installation, update this directory whenever dependency versions
change. Use the dependency-license-sync auto-fix to refresh the report
and then replace any placeholder files with real license text.

## Notes
Add repo-specific guidance here if the project needs a custom license
collection workflow.
