# Global Registry Namespace

## Table of Contents
- [Overview](#overview)
- [Workflow](#workflow)
- [Future Use](#future-use)

## Overview
The `devcovenant/registry/global/` path is a reserved namespace for shared
registry assets that may be introduced in later DevCovenant releases. The
current runtime contract does not require payload files in this directory, and
all active execution paths rely on `devcovenant/registry/local/` for generated
state. Keeping this global directory present is intentional because it avoids
future layout churn and keeps package consumers stable when global registry
capabilities are introduced.

## Workflow
At the moment, refresh commands regenerate only local registry artifacts.
Contributors should treat this directory as reserved and avoid storing
session-specific, machine-specific, or user-edited state here. If a future
feature needs global registry data, it should define a schema and documentation
contract before adding files so readers can understand lifecycle and ownership.

## Future Use
This directory remains pluggable by design. New global assets should be added
only when they provide a documented runtime or packaging contract that cannot
be represented in local registry state.
