# Configuration

## Overview
Use this doc to explain `devcovenant/config.yaml` as a practical control
surface.
Make it clear which sections are human-owned, which are regenerated, and which
settings matter most during first review.

A good config doc should help someone review a fresh install without already
knowing DevCovenant internals.
It should explain what a setting controls, when a human should change it, and
what kind of trouble appears when it is wrong.

## What This Doc Should Cover
Explain:

1. ownership boundaries in config

2. how to review a fresh install baseline

3. `developer_mode`

4. `profiles.active`

5. `doc_assets`

6. `project-governance`

7. `core_invariants`

8. `policy_state`

9. `ci_and_test`

10. `engine` behavior

## Writing Rules
Keep the prose practical.
Say what a setting controls, when a human should change it, and what happens if
it is wrong. Avoid abstract language when a direct explanation is possible.
Be explicit that reusable extra CI jobs belong in profile
`ci_and_test` fragments, while local config overlays are for
repository-specific adjustments.
