# License Assets

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Update Checklist](#update-checklist)

## Overview
This directory stores generated third-party license texts and
generated compliance notes for direct repository dependencies.
Keep these files synchronized whenever dependency declarations or
resolved lock versions change. The goal is to preserve a clear audit
trail that maps declared direct dependencies to local license
artifacts without requiring manual reconstruction during release
reviews or legal checks.

## Workflow
- Keep `licenses/THIRD_PARTY_LICENSES.md` synchronized with dependency
  manifest updates.
- Add, remove, or refresh generated license files in this directory
  when dependency versions change.
- Record each changed dependency manifest in the report section so
  coverage checks can verify synchronization.
- Keep the dependency inventory aligned with the actual generated
  license files.

## Update Checklist
- Verify each direct dependency entry points to a current license
  file.
- Verify generated license files reflect the currently installed
  upstream distribution notices.
- Re-run DevCovenant checks and commit both report and license
  artifact updates together.
