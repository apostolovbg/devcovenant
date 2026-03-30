# DevCovenant Docs

## Overview
This folder holds the detailed reference docs for DevCovenant.
`README.md` is the operator entrypoint.
These docs explain the deeper runtime, config, policy, profile, registry, and
refresh behavior that the top-level README only points to.

## Doc Set
The intended reference set is smaller and stricter:
- `installation.md` for lifecycle commands and first activation
- `workflow.md` for the exact gate sequence and recovery rules
- `config.md` for config ownership, project governance, and review
- `profiles.md` for profiles, assets, overlays, translators, and workflow runs
- `policies.md` for policy descriptors, runtime actions, and policy commands
- `refresh.md` for refresh ownership and managed-doc behavior
- `architecture.md` for runtime layers, evidence flow, and contract map
- `registry.md` for tracked and runtime registry state
- `troubleshooting.md` for common failures and recovery

## Working Rules
Keep these docs concrete.
Avoid turning them into meta-commentary about documentation itself.
Titles should match contents closely, and a short doc should not be forced to
carry extra sections only because some older template expected them.

## Formatting Rules
Prefer short paragraphs, explicit examples, and readable lists.
Avoid dense bullet walls and avoid treating every doc like it needs the same
shape regardless of topic.
