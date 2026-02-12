# Custom Profiles

## Table of Contents
1. Overview
2. Declaring Assets
3. Workflow

## Overview
Custom profiles override core profiles when names match. Use this folder to
ship profile-specific assets, suffixes, and overlays without changing core
DevCovenant. Custom profiles take precedence over core profiles during install
and update. Keep overrides lean and document the intent.

## Declaring Assets
Define a profile in `devcovenant/custom/profiles/<profile>/<profile>.yaml` and
place any assets under `devcovenant/custom/profiles/<profile>/assets/`.

Example:
```yaml
version: 1
profile: frappe
category: framework
suffixes:
  - .py
assets:
  - path: requirements.in
    template: requirements.in
```

## Workflow
Add or adjust the profile manifest, update assets, and ensure the profile
catalog is refreshed. Custom profile assets are created when missing for active
profiles; existing files stay user-owned unless managed blocks handle them.
