# License Assets

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Update Checklist](#update-checklist)

## Overview
This directory stores third-party license texts and generated
compliance notes for repository dependency manifests. Keep these
files synchronized whenever dependency declarations or lock files
change. The goal is to preserve a clear audit trail that maps
dependency inputs to local license artifacts without requiring
manual reconstruction during release reviews or legal checks.

## Workflow
- Keep `licenses/THIRD_PARTY_LICENSES.md` synchronized with dependency
  manifest updates.
- Add, remove, or refresh license files in this directory when
  dependency versions change.
- Record each changed dependency manifest in the report section so
  coverage checks can verify synchronization.

## Update Checklist
- Verify each dependency entry points to a current license file.
- Replace placeholders with upstream license texts before release.
- Re-run DevCovenant checks and commit both report and license
  artifact updates together.
