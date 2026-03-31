# Configuration
**Project Version:** 1.0.1.dev1

## Overview
`devcovenant/config.yaml` is the main control file for a repository using
DevCovenant.
It is where you choose the profile stack, the managed docs, the workflow
settings, the policy toggles, and the general CLI behavior.

Refresh rewrites the generated parts of this file and keeps the human-owned
parts in place.
So the practical question is not "is this file generated?"
The practical question is "which parts do I review and own, and which parts are
there so DevCovenant can show resolved state?"

## How To Read This File
Most people should read it in this order:

1. `project-governance`
2. `developer_mode`
3. `profiles.active`
4. `doc_assets`
5. `workflow`
6. `policy_state`
7. `engine`
8. `paths`

If you only remember one rule, remember this one:
change the human-owned settings to tell DevCovenant how the repository should
behave, and treat the generated sections as status and reference output.

## Ownership Model
### Human-Owned Sections
These are the parts a human is expected to review and edit:
- `project-governance`
- `developer_mode`
- `profiles.active`
- `doc_assets`
- `paths.*`
- `workflow.*`
- `policy_state`
- `user_metadata_overlays`
- `user_metadata_overrides`
- `clean.overlays`
- `clean.overrides`
- `engine.*`
- `install.config_reviewed`
- generated-workflow override sections such as `pre_commit.*`, `gitignore.*`,
  and `ci_and_test.*`

### Refresh-Owned Sections
These sections are rebuilt by refresh and should not be treated as normal edit
targets:
- `profiles.generated`
- `autogen_metadata_overlays`
- `autogen_metadata_overrides`
- `install.import_managed_docs`

### Mixed Sections
These sections contain both human-owned and refresh-owned keys:
- `profiles`
- `doc_assets`
- `install`
- metadata layers split as `autogen_*` and `user_*`

## Key Sections
### profiles.active
This is the active profile stack.
Profiles describe the repository shape: language, framework, tooling, assets,
and workflow additions.

For most repositories, the normal pattern is:
- keep the shared base profiles
- keep `devcovuser` active
- add `github` when the repository wants a generated GitHub Actions workflow
- add language or framework profiles as needed
- add a repo-specific custom profile on top when the repository needs its own
  rules, assets, or workflow additions

Use direct overlays for small one-off tweaks.
Use a custom profile when the repository has real repeatable behavior of its
own.
Before the first gate cycle, make sure the environment declared by that stack
actually exists.
If you keep the seeded `defaults` + `python` stack, that means creating
`.venv` and installing `requirements.lock`.
If the repository uses a bench-managed or other custom environment, declare
that environment in the profile stack or metadata overlays instead of relying
on DevCovenant to guess an unknown layout.

### doc_assets
This is the managed-doc selection.
Use it to choose which managed doc target paths are enabled for the repository.
The simple model is:
- global and active profiles contribute available managed-doc descriptors
- `doc_assets.autogen` names the target paths this repository enables
- `doc_assets.user` subtracts target paths after `autogen`
- when multiple active descriptor roots provide the same target path, the later
  active profile wins

### project-governance
This section describes the project itself.
It answers questions like:
- what is the project called?
- what copyright notice should seeded license docs use?
- what stage is it in?
- how actively is it maintained?
- what compatibility promise does it make?
- is it versioned or intentionally unversioned?

Managed docs and generated headers read from this section.
If those public-facing descriptions look wrong, start here.
That includes the global `LICENSE` template, which seeds:
- `Copyright (c) {{ COPYRIGHT_NOTICE }}`
- `All rights reserved.`

### paths
This section chooses where DevCovenant keeps important local files such as:
- `policy_definitions`
- `registry_file`
- `gate_status_file`
- `workflow_session_file`

These are path settings, not policy toggles.
Every key in this section is human-owned.

### workflow
This section controls workflow behavior such as:
- `pre_commit_command`
- `skipped_globs`

These settings define how the gate and run flow works.
They do not belong in `policy_state`.
When a managed Python environment is active, DevCovenant runs pre-commit
through that selected interpreter instead of depending on a host-side
console-script shim.

### policy_state
This is the on/off map for configurable policies.
Use it to decide which non-core policies are enabled.
Critical policies can still remain enforced even if a config toggle tries to
turn them off.

### engine
This section controls general CLI behavior such as:
- failure threshold
- autofix enablement
- output mode
- test output mode
- run-log retention
- bytecode cache routing

These settings change how DevCovenant behaves.
They do not change what the repository claims about itself.
CLI flags such as `--quiet`, `--normal`, and `--verbose` override output mode
for one command only.

### ci_and_test
This section is for repository-local customization of the generated `CI`
workflow.
Activate the builtin `github` profile when the repository wants the standard
generated GitHub Actions workflow.
Use it for:
1. small repository-local overlays on the generated workflow
2. the rarer case where the repository deliberately takes full ownership of the
   generated workflow payload

Do not use it as the first place to add reusable behavior for a shared custom
profile.
If the added job should travel with a profile stack, put that behavior in a
profile `ci_and_test` fragment instead.
The builtin `github` base bootstraps DevCovenant from the shipped
`devcovenant/requirements.lock`. If a repository needs extra project
dependency setup, keep that in the relevant profile or explicit local
override instead of changing the builtin base.

### clean
Cleanup settings decide what DevCovenant may delete.
Use `clean.overlays` for extra cleanup targets.
Use `clean.overrides` only when the repository intentionally wants to replace
inherited cleanup lists.

### developer_mode
`developer_mode` answers a simple question:
is this repository using DevCovenant as a tool, or is it being used to develop
DevCovenant itself?

Use `false` for a normal repository using DevCovenant.
Use `true` only when the repository is developing DevCovenant itself.

## Practical Review Order
For a new repository, this is the shortest useful config review:
1. set `project-governance`
2. confirm `developer_mode`
3. review `profiles.active`
4. keep `devcovuser` active for a normal repository
5. add `github` if the repository wants a generated GitHub Actions workflow
6. add a repo-specific custom profile if the repository needs one
7. review `doc_assets`
8. review `workflow` and `policy_state`
9. review `engine.*`
10. set `install.config_reviewed: true`
11. run `devcovenant deploy`

If generated docs or generated files do not match what you expect, the first
places to check are `project-governance`, `profiles.active`, and `doc_assets`.
