# Custom Profile Templates

## Table of Contents
1. Overview
2. Custom Manifests
3. Workflow

## Overview
Use this directory to override or extend profile assets without editing
core templates. When a template path exists under
`devcovenant/custom/templates/profiles/<profile>/`, it overrides the core
template with the same path. This keeps updates safe while allowing repo
specific behavior. Custom profile templates are ideal for teams that need
extra docs, alternative dependency manifests, or additional ignore rules
that are not a good fit for the shared core profiles.

## Custom Manifests
If you add a custom profile, include `profile.yaml` in the profile folder
and list any assets or policy overlays there. Custom profile manifests
override core manifests when the profile name matches. The manifest should
list every asset you expect the installer to create so updates stay
predictable and reproducible.

## Workflow
Add templates and ensure any required policy assets are registered. The
profile catalog is generated automatically during install/update, so there
are no manual catalog edits. Keep profile names stable so overrides apply
consistently across updates. If a repo uses multiple profiles, verify that
assets do not collide across profiles, or explicitly decide which profile
owns the asset so precedence remains clear.
