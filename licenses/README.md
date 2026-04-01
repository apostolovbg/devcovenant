# License Assets

## Table of Contents
- [Overview](#overview)
- [Contents](#contents)
- [Update Checklist](#update-checklist)

## Overview
This directory stores generated dependency license artifacts for the
surface tracked here.
Keep these files synchronized whenever the owning dependency
manifests or resolved lockfiles change so the local license set
stays readable and auditable.

## Contents
- `THIRD_PARTY_LICENSES.md` records the dependency inputs and
  generated license inventory for this surface.
- `*.txt` files store the generated upstream license texts
  that match the current direct dependency set.

## Update Checklist
- Keep `licenses/THIRD_PARTY_LICENSES.md` synchronized with dependency
  manifest and lock updates for this surface.
- Add, remove, or refresh generated license files when dependency
  versions change.
- Re-run DevCovenant checks and commit report and license artifact
  updates together.
