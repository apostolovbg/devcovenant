# DevCovenant
**Last Updated:** 2026-01-11
**Version:** 0.1.1

<!-- DEVCOVENANT:BEGIN -->
**Read first:** `AGENTS.md` is the canonical source of truth. See
`DEVCOVENANT.md` for architecture and lifecycle details.
<!-- DEVCOVENANT:END -->

DevCovenant is a self-enforcing policy system that keeps human-readable
standards and automated checks in lockstep. It was born inside the Copernican
Suite, matured through dogfooding in production repos, and is now a standalone
project focused on stability and portability.

If you installed DevCovenant into another repo, read the user-facing guide at
`devcovenant/README.md` inside that repo.

## Table of Contents
1. [Overview](#overview)
2. [Why DevCovenant](#why-devcovenant)
3. [How It Works](#how-it-works)
4. [Repo Layout](#repo-layout)
5. [Install, Update, Uninstall](#install-update-uninstall)
6. [Using DevCovenant in a Repo](#using-devcovenant-in-a-repo)
7. [History and Dogfooding](#history-and-dogfooding)
8. [License](#license)

## Overview
DevCovenant turns policy documents into executable checks. It reads the policy
blocks in `AGENTS.md`, synchronizes them into a registry, and runs checks that
use the same source text to enforce behavior.

Key capabilities:
- Single source of truth: policy text and enforcement stay aligned.
- Drift detection: hash registry flags when policy and code diverge.
- Flexible severity: warn, block, or auto-fix depending on policy.
- Policy evolution: new, updated, deprecated, and deleted states are tracked.

## Why DevCovenant
Teams often document rules in one place and enforce them somewhere else. That
creates drift, ambiguity, and hidden requirements. DevCovenant fixes this by
making the documentation itself the executable spec.

## How It Works
1. `AGENTS.md` stores policy definitions and metadata.
2. `devcovenant/parser.py` extracts policy blocks and hashes them.
3. `devcovenant/registry.json` records those hashes alongside script hashes.
4. `devcovenant/engine.py` runs checks from policy scripts.
5. Pre-commit and CI run the same engine and rules.

## Repo Layout
- `AGENTS.md`: canonical policy definitions for this repo.
- `DEVCOVENANT.md`: architecture, schema, and lifecycle reference.
- `devcovenant/`: engine, CLI, and policy script layout.
  - `common_policy_scripts/`: built-in policy scripts.
  - `custom_policy_scripts/`: repo-specific policy scripts.
  - `common_policy_patches/`: YAML overrides for built-in policies.
- `tools/`: install, uninstall, and workflow helpers.

## Install, Update, Uninstall
Install DevCovenant into a target repository:
```bash
python tools/install_devcovenant.py --target /path/to/repo
```

Update an existing installation without overwriting docs/config:
```bash
python tools/install_devcovenant.py --target /path/to/repo
```

Force overwrite docs or config when needed:
```bash
python tools/install_devcovenant.py --target /path/to/repo --force-docs
python tools/install_devcovenant.py --target /path/to/repo --force-config
```

Uninstall and remove DevCovenant-managed blocks from docs:
```bash
python tools/uninstall_devcovenant.py --target /path/to/repo
```

Remove installed docs as well:
```bash
python tools/uninstall_devcovenant.py --target /path/to/repo --remove-docs
```

The installer records an `.devcovenant/install_manifest.json` to make updates
and removals safe and predictable.

## Using DevCovenant in a Repo
Common commands:
```bash
python -m devcovenant.cli check
python -m devcovenant.cli check --mode pre-commit
python -m devcovenant.cli check --fix
python -m devcovenant.cli update-hashes
```

When DevCovenant is enforced, the expected workflow is:
1. `python tools/run_pre_commit.py --phase start`
2. `python tools/run_tests.py`
3. `python tools/run_pre_commit.py --phase end`

The user-facing guide in `devcovenant/README.md` covers policy authoring,
patching built-ins, and troubleshooting.

## History and Dogfooding
DevCovenant originated inside the Copernican Suite and was hardened by using
it in real repos (including the GCV-ERP custom/infra stack). This repo
continues that dogfooding: policies enforce the project that ships them.

## License
This project is released under the DevCovenant License v1.0. Redistribution
is prohibited without explicit written permission.
