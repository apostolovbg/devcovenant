# Profiles

## Table of Contents
1. Overview
2. Structure
3. Workflow

## Overview
Profiles describe repository shapes (languages, frameworks, and data layouts)
so DevCovenant can select the right policy scopes, suffixes, ignores, and
profile-specific assets. Core profiles live under
`devcovenant/core/profiles/<profile>/`. Custom overrides live under
`devcovenant/custom/profiles/<profile>/` and take precedence when the same
profile name exists in both locations. The `global` profile is always active
and supplies baseline assets such as standard docs and tooling helpers.

## Structure
Each profile folder contains:
- `profile.yaml` describing suffixes, ignores, and policy overlays.
- `assets/` containing files that should be installed when the profile is
  active (for example, framework configs or language-specific assets).

Profile assets override policy assets when they declare the same path, so
framework-specific files win over generic defaults.

## Workflow
When adding or updating a profile, adjust its `profile.yaml`, update any assets
in the `assets/` folder, and refresh the generated profile catalog. Ensure
install/update logic can resolve the profile assets and that the manifest lists
any new required paths.
