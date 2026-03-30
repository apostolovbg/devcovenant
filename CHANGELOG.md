# Changelog
**Doc ID:** CHANGELOG
**Doc Type:** changelog
**Project Version:** 1.0.0
**Project Stage:** stable
**Maintenance Stance:** active
**Compatibility Policy:** forward-only
**Versioning Mode:** versioned
**Last Updated:** 2026-03-30
**DevCovenant Version:** 1.0.0

<!-- DEVCOV:BEGIN -->
## DevCovenant Change Logging Rules
This opening section is managed by DevCovenant for repositories that
use DevCovenant.
Add one entry for each substantive change under the current version header.
Keep entries newest-first and record dates in ISO format (`YYYY-MM-DD`).
Each entry must include Change/Why/Impact summary lines with action verbs.
Example:
```
## Version 1.0.1

- 2026-01-23:
  Change: Fixed null-pointer crash in invoice import.
  Why: Production job failed when optional contact data was missing.
  Impact: Imports now complete for records with partial contact details.
  Files:
  billing/imports/parser.py
  billing/imports/test_parser.py
  docs/imports.md
  Long paths should be wrapped with a trailing \
  backslash and continued on the next indented line.
  Example:
  services/customer/contact/normalization/\
    fallback_rules.py

- 2026-01-22:
  Change: Fixed duplicate email notifications on retry.
  Why: Retry worker re-enqueued already-confirmed notification events.
  Impact: Users now receive one email per successful notification event.
  Files:
  notifications/worker.py
  notifications/retry.py
  notifications/test_retry.py

## Version 1.0.0

- 2026-01-21:
  Change: Added initial release for invoice import and notification flow.
  Why: Defined a first production-ready baseline for billing automation.
  Impact: Teams can import invoices and send notifications end-to-end.
  Files:
  billing/imports/parser.py
  notifications/worker.py
  CHANGELOG.md
```
<!-- DEVCOV:END -->

## Log changes here

## Version 1.0.0

- 2026-03-30:
  Change: hardened managed gate pre-commit launching around the selected
    interpreter and updated the owned CI action pins to Node-24-ready
    majors.
  Why: fixed the remaining pipx-proof `gate --start` failure caused by
    console-script shim dependence and cleared the GitHub Actions Node 20
    deprecation warning at the workflow-template source.
  Impact: Build proof repos now launch pre-commit through the managed Python
    path deterministically, and Governance/Build use refreshed `checkout`
    and `setup-python` action majors.
  Files:
  .github/workflows/ci.yml
  CHANGELOG.md
  devcovenant/builtin/profiles/global/assets/ci.yml
  devcovenant/core/flow/gate.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-30:
  Change: corrected managed-environment interpreter matching so DevCovenant
    only reuses the current Python when it actually matches the declared
    managed environment, and added a regression for the GitHub-hosted
    `.../bin/python` case.
  Why: fixed the governance-job start-gate failure where a host runner Python
    under a generic `bin/` path was incorrectly treated as the repo's managed
    interpreter, which skipped `.venv` bootstrap and caused the pre-commit
    DevCovenant hook to fail its own managed-environment policy.
  Impact: host Python no longer masquerades as `.venv`, start-stage bootstrap
    runs when the declared managed env is missing, and CI can re-enter the
    real managed interpreter before policy enforcement.
  Files:
  CHANGELOG.md
  devcovenant/builtin/policies/managed_environment/\
    managed_environment_runtime.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/docs/policies.md
  tests/devcovenant/builtin/policies/managed_environment/\
    test_managed_environment_runtime.py

- 2026-03-30:
  Change: aligned managed-doc inventory and refresh/docs ownership around
    available-versus-enabled doc selection, documented descriptor precedence
    by active profile order, and added trust-doc rendering tests for both the
    global baseline and repo/profile overrides.
  Why: removed the stale default/optional-doc mental model that no longer
    matched runtime behavior and proved that `SECURITY.md`, `PRIVACY.md`, and
    `SUPPORT.md` now follow the same descriptor-precedence contract as the
    rest of the managed-doc system.
  Impact: tracked inventory now reports available and enabled docs honestly,
    structure validation only requires enabled docs, refresh/config docs
    explain the real `doc_assets` contract, and the trust-doc template
    precedence path is covered by focused regressions.
  Files:
  CHANGELOG.md
  devcovenant/builtin/profiles/global/assets/PRIVACY.yaml
  devcovenant/builtin/profiles/global/assets/SECURITY.yaml
  devcovenant/builtin/profiles/global/assets/SUPPORT.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/managed_docs.py
  devcovenant/core/services/manifest_inventory.py
  devcovenant/core/services/structure_validation.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_managed_docs.py
  tests/devcovenant/core/services/test_manifest_inventory.py
  tests/devcovenant/core/services/test_structure_validation.py
  tests/devcovenant/test_refresh.py

- 2026-03-30:
  Change: removed the invariant framework from the runtime, split repo-only
    trust and release surfaces out of package docs, tightened dependency-lock
    refresh to use direct lock inputs, and aligned the generated repo surfaces
    with the forward-only contract.
  Why: addressed the stale invariant-era generated output, package-doc
    leakage of repo-only details, and a dependency autofix path that tried to
    recompile `requirements.lock` for unrelated package-metadata edits.
  Impact: folded integrity, structure, and workflow checks fully under the
    engine runtime, added repo-owned `SECURITY.md` / `PRIVACY.md` /
    `SUPPORT.md`, kept package docs package-scoped, and made gate-time
    dependency refresh converge without user-cache or needless network
    dependence.
  Files:
  AGENTS.md
  CHANGELOG.md
  MANIFEST.in
  PRIVACY.md
  README.md
  SECURITY.md
  SPEC.md
  SUPPORT.md
  devcovenant/README.md
  devcovenant/builtin/policies/dependency_management/\
    dependency_lock_runtime.py
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/global/assets/PLAN.yaml
  devcovenant/builtin/profiles/global/assets/SPEC.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/global.yaml
  devcovenant/config.yaml
  devcovenant/core/README.md
  devcovenant/core/contracts/invariant.py
  devcovenant/core/contracts/invariants/devcov_integrity_guard.yaml
  devcovenant/core/contracts/invariants/devcov_structure_guard.yaml
  devcovenant/core/contracts/invariants/devflow_run_gates.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/core/flow/workflow_validation.py
  devcovenant/core/lib/agents_blocks.py
  devcovenant/core/lib/document_exemptions.py
  devcovenant/core/runtime/registry.py
  devcovenant/core/runtime/workflow_session.py
  devcovenant/core/services/core_invariants.py
  devcovenant/core/services/integrity_validation.py
  devcovenant/core/services/managed_docs.py
  devcovenant/core/services/manifest_inventory.py
  devcovenant/core/services/metadata.py
  devcovenant/core/services/policy_engine.py
  devcovenant/core/services/policy_registry.py
  devcovenant/core/services/structure_validation.py
  devcovenant/core/services/tracked_registry.py
  devcovenant/custom/profiles/devcovrepo/assets/POLICY_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/PROFILE_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/PRIVACY.yaml
  devcovenant/custom/profiles/devcovrepo/assets/SECURITY.yaml
  devcovenant/custom/profiles/devcovrepo/assets/SUPPORT.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/contracts.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/project_governance.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  licenses/THIRD_PARTY_LICENSES.md
  pyproject.toml
  tests/devcovenant/builtin/policies/dependency_management/\
    test_dependency_lock_runtime.py
  tests/devcovenant/core/contracts/test_invariant.py
  tests/devcovenant/core/flow/test_workflow_validation.py
  tests/devcovenant/core/lib/test_agents_blocks.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/runtime/test_workflow_session.py
  tests/devcovenant/core/services/test_core_invariants.py
  tests/devcovenant/core/services/test_integrity_validation.py
  tests/devcovenant/core/services/test_managed_docs.py
  tests/devcovenant/core/services/test_metadata.py
  tests/devcovenant/core/services/test_structure_validation.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py

- 2026-03-30:
  Change: removed the managed-doc generic-scaffold legacy bridge, split core
    invariant descriptor loading away from policy descriptors, and corrected
    the live `SPEC.md` compatibility story to match the repo's
    `forward-only` governance state.
  Why: the read-only QA audit found one stale contract doc, one still-active
    legacy managed-doc migration path, and one remaining invariant/runtime
    coupling seam that kept invariants looking more policy-shaped than they
    really are.
  Impact: eliminated the legacy `SPEC`/`PLAN` replacement fallback from the
    managed-doc runtime and tracked registry, made invariants load and test as
    invariant-owned descriptors, and aligned the spec with the current public
    compatibility posture.
  Files:
  CHANGELOG.md
  SPEC.md
  devcovenant/builtin/profiles/global/assets/PLAN.yaml
  devcovenant/builtin/profiles/global/assets/SPEC.yaml
  devcovenant/core/contracts/invariant.py
  devcovenant/core/flow/workflow_validation.py
  devcovenant/core/services/core_invariants.py
  devcovenant/core/services/integrity_validation.py
  devcovenant/core/services/managed_docs.py
  devcovenant/core/services/structure_validation.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/docs/architecture.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/contracts/test_invariant.py
  tests/devcovenant/core/flow/test_workflow_validation.py
  tests/devcovenant/core/services/test_core_invariants.py
  tests/devcovenant/core/services/test_managed_docs.py
  tests/devcovenant/test_refresh.py

- 2026-03-30:
  Change: added the `forward-only` compatibility policy, generated
    policy-specific AGENTS governance guidance, removed touched legacy
    compatibility shims, and tightened `gate --start` to report managed drift
    explicitly instead of as a generic pre-commit failure.
  Why: aligned the repo around an explicit no-legacy-fallback stance,
    required project-governance review up front in the workflow, and removed
    the remaining start-gate/reporting and workflow-validation bridges that
    were still hiding the real contract from operators.
  Impact: made `Compatibility Policy` an active workflow decision in
    `AGENTS.md`, switched this repo to `forward-only`, rejected old recorded
    `python -m pre_commit` evidence shapes, aligned config/profile/workflow
    docs with that stance, and made start-gate drift failures identify the
    changed paths and managed-file refresh cause directly.
  Files:
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/builtin/policies/managed_environment/\
    managed_environment_runtime.py
  devcovenant/builtin/policies/modules_need_tests/modules_need_tests.yaml
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/config.yaml
  devcovenant/core/flow/gate.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/flow/workflow_validation.py
  devcovenant/core/services/managed_docs.py
  devcovenant/core/services/project_governance.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/project_governance.md
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/flow/test_workflow_validation.py
  tests/devcovenant/core/services/test_project_governance.py

- 2026-03-30:
  Change: clarified config ownership across the template and live config,
    removed the remaining invariant-policy-shaped config narration, and
    synchronized the package docs around the dedicated `paths.*` and
    `workflow.*` runtime contract sections.
  Why: the invariant refactor and contracts documentation were structurally
    right, but a few operator-facing config comments and docs still mixed
    ownership boundaries or described the removed `core_invariants` shape.
  Impact: aligned the config, template, README surfaces, contracts docs,
    registry docs, and refresh tests around one consistent ownership story
    for human-owned, refresh-owned, and mixed sections.
  Files:
  AGENTS.md
  CHANGELOG.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/config.yaml
  devcovenant/core/contracts/invariant.py
  devcovenant/core/contracts/invariants/devcov_integrity_guard.yaml
  devcovenant/core/contracts/invariants/devcov_structure_guard.yaml
  devcovenant/core/contracts/invariants/devflow_run_gates.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/core/lib/agents_blocks.py
  devcovenant/core/services/core_invariants.py
  devcovenant/custom/profiles/devcovrepo/assets/POLICY_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/contracts.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/lib/test_agents_blocks.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/runtime/test_registry.py
  tests/devcovenant/core/services/test_core_invariants.py
  tests/devcovenant/core/services/test_metadata.py
  tests/devcovenant/test_refresh.py

- 2026-03-30:
  Change: simplified the managed-environment runtime to reuse a valid target
    interpreter, bootstrap only when the configured environment is still
    missing or invalid, and fall back to `python -m pre_commit` when a Python
    console-script shim is absent.
  Why: build and proof-repo gates were still failing because the runtime kept
    treating environment preparation and environment selection as the same
    thing, which made `gate --start` too destructive and too dependent on a
    direct `pre-commit` executable on PATH.
  Impact: stabilized DevCovenant behavior across repo `.venv`s, pre-seeded
    proof environments, and other configured interpreters, while the repo
    profile, tracked registry, and public docs now describe the same single
    execution-environment contract.
  Files:
  AGENTS.md
  CHANGELOG.md
  devcovenant/builtin/policies/managed_environment/managed_environment.yaml
  devcovenant/builtin/policies/managed_environment/\
    managed_environment_runtime.py
  devcovenant/config.yaml
  devcovenant/core/flow/gate.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/managed_environment/\
    test_managed_environment_runtime.py
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-30:
  Change: fixed managed-doc sync so `Last Updated` date rollover alone no
    longer rewrites clean descriptor-backed docs during refresh or start gate.
  Why: `gate --start` and CI were failing after UTC midnight because managed
    docs rewrote only their header date, which mutated the baseline even when
    the repository content had not changed.
  Impact: clean repositories now stay clean across day boundaries, start gate
    no longer fails on date-only managed-doc churn, and real doc-content
    updates still sync normally.
  Files:
  CHANGELOG.md
  devcovenant/core/services/managed_docs.py
  devcovenant/docs/architecture.md
  tests/devcovenant/core/services/test_managed_docs.py

- 2026-03-30:
  Change: fixed the gate pre-commit contract to use the canonical
    `pre-commit run --all-files` launcher, normalized equivalent
    `python -m pre_commit` evidence in validation, and updated the matching
    config, docs, registry, and tests.
  Why: GitHub Build proof repos were still failing `gate --start` when the
    hosted `python3` interpreter lacked `pre_commit`, even though the managed
    `.venv` and its `PATH` were the real execution contract.
  Impact: start, mid, and end gates now execute pre-commit through the managed
    environment across local work and artifact proofs, while older recorded
    gate evidence still validates as the same logical command.
  Files:
  CHANGELOG.md
  AGENTS.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/global.yaml
  devcovenant/config.yaml
  devcovenant/core/flow/gate.py
  devcovenant/core/flow/workflow_validation.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/flow/test_workflow_validation.py

- 2026-03-29:
  Change: corrected the Python-family `tests` workflow runs to keep
    `python3 -m unittest discover -v`, remove the redundant `pytest`
    launcher, and preserve the separate `pipx` proof wheel-seeding fix.
  Why: the previous slice fixed the `pipx` dependency gap correctly but
    changed the wrong Python runner, even though this repo's intended single
    structural Python test pass is the `unittest` command.
  Impact: the repo and Python-family profiles now use one
    `python3 -m unittest discover -v`-based Python test pass, while the
    `pipx` proof still seeds its proof `.venv` with the proven wheel so
    source-tree `python -m devcovenant` commands have the shipped runtime
    dependencies.
  Files:
  CHANGELOG.md
  devcovenant/builtin/profiles/fastapi/fastapi.yaml
  devcovenant/builtin/profiles/frappe/frappe.yaml
  devcovenant/builtin/profiles/python/python.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-29:
  Change: removed the duplicate Python `unittest` launcher from the
    Python-family `tests` workflow runs and seeded the `pipx` proof `.venv`
    with the proven wheel before the governed lifecycle begins.
  Why: prevented Build from running Python suites twice and fixed the `pipx`
    proof path where source-tree `python -m devcovenant` re-exec could import
    DevCovenant before `PyYAML` and the other shipped runtime dependencies
    were present in the proof environment.
  Impact: keeps the repo and Python-family profiles on one `pytest`-based
    Python test pass, and lets the `pipx` proof complete
    `gate --start -> gate --mid -> run -> gate --end -> check` with the same
    runtime dependencies declared by the shipped artifact.
  Files:
  .github/workflows/ci.yml
  CHANGELOG.md
  devcovenant/builtin/profiles/fastapi/fastapi.yaml
  devcovenant/builtin/profiles/frappe/frappe.yaml
  devcovenant/builtin/profiles/python/python.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-29:
  Change: extracted a detailed durable product specification into `SPEC.md`
    from the live code, CLI surface, generated workflow contract, and
    repository docs.
  Why: the repository needed to define a real specification that states what
    DevCovenant is, what contracts it enforces, and how workflow, policy,
    registry, packaging, and publish behavior fit together.
  Impact: `SPEC.md` now describes the stable product contract in one place,
    making future audits, governance decisions, and release work easier to
    reason about without reverse-engineering the implementation every time.
  Files:
  CHANGELOG.md
  SPEC.md

- 2026-03-29:
  Change: hardened the shared PTY child-output runner to treat Linux EOF
    `EIO` races as normal command completion once the child exits, and added
    regression coverage plus workflow-doc wording for the CI proof path.
  Why: the Build wheel proof hit a successful `gate --mid` path that still
    raised `[Errno 5] Input/output error` at PTY EOF before the child exit had
    been reaped.
  Impact: successful proof-gate commands now finish cleanly in Linux CI
    instead of failing after all hook output has already passed, and the docs
    now explain that runtime output behavior honestly.
  Files:
  CHANGELOG.md
  devcovenant/core/runtime/execution.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/runtime/test_execution.py

- 2026-03-29:
  Change: updated workflow-validation guidance to teach the four-stage
    `gate --start -> gate --mid -> run -> gate --end` contract, extended
    manual publish to verify `ci_run_attempt`, and reset `PLAN.md` to the
    generic managed template body.
  Why: the residual review found one stale operator-guidance surface, one
    small provenance-verification gap, and the repo plan still carried
    completed audit-remediation history instead of the generic active-work
    template.
  Impact: validation errors now teach the right workflow, manual publish
    checks CI provenance more exactly, and `PLAN.md` is back to a neutral
    template for future work instead of a frozen release-remediation record.
  Files:
  .github/workflows/publish.yml
  CHANGELOG.md
  PLAN.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/core/flow/workflow_validation.py
  devcovenant/docs/workflow.md
  tests/devcovenant/core/flow/test_workflow_validation.py
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-29:
  Change: clarified the profile and registry docs so they no longer say the
    repo profile owns the `.gha-pycache/` ignore rule or that tracked
    registry state itself records the generated ignore surface.
  Why: the previous wording fixed behavior but still blurred ownership between
    the repo-specific CI layer, the shared generated gitignore asset, and the
    tracked registry document.
  Impact: docs now describe the real split accurately: the repo profile owns
    the CI behavior, the global generated asset owns `.gha-pycache/`, and the
    registry docs distinguish tracked state from broader refresh outputs.
  Files:
  CHANGELOG.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md

- 2026-03-29:
  Change: aligned the CI managed-environment docs with the real
    `Governance` and `Build` behavior, renamed provenance fields from
    build-run ids to CI-run ids, and added `.gha-pycache/` to the generated
    ignore surface.
  Why: the workflow docs still described a removed gate-status priming step,
    the provenance payload still carried stale separate-build naming, and
    proof repos could sweep runner bytecode caches into bootstrap commits.
  Impact: reviewers now see the real CI contract, manual publish verifies CI
    provenance with accurate field names, and wheel, sdist, and `pipx` proof
    repos ignore `.gha-pycache` noise by default.
  Files:
  .github/workflows/ci.yml
  .github/workflows/publish.yml
  .gitignore
  CHANGELOG.md
  devcovenant/builtin/profiles/global/assets/gitignore.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/test_refresh.py

- 2026-03-29:
  Change: moved built-artifact proof back into the `Build` job inside
    `CI`, renamed the main `CI` job to `governance`, deleted the separate
    `build.yml` workflow, switched manual publish to select a validated `CI`
    run, and fixed the `pipx` proof to hand the governed gate/run path to
    the repo-managed `.venv`.
  Why: simplified the Actions surface back to `CI` plus manual `Publish`,
    removed the duplicate workflow split, and resolved the `pipx` proof
    failure where `gate --start` launched `pre_commit` from the wrong
    interpreter path.
  Impact: GitHub Actions now shows `Governance` and dependent `Build` in one
    `CI` workflow, publish consumes the exact validated `CI` artifact, and
    the `pipx` proof still verifies bootstrap before the governed workflow
    runs in the managed environment.
  Files:
  .github/workflows/build.yml
  .github/workflows/ci.yml
  .github/workflows/publish.yml
  CHANGELOG.md
  SECURITY.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/builtin/profiles/global/assets/ci.yml
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-29:
  Change: fixed the workflow-validation missing-runs message construction to
    avoid the multiline f-string parse failure in Python 3.11 and added a
    regression assertion for the rerun guidance.
  Why: the wheel proof exposed a Python 3.11 syntax error in that message
    path and broke `gate --start`.
  Impact: keeps the missing-runs contract unchanged while restoring Build
    compatibility for installed-artifact proof on Python 3.11.
  Files:
  CHANGELOG.md
  devcovenant/core/flow/workflow_validation.py
  tests/devcovenant/core/flow/test_workflow_validation.py

- 2026-03-29:
  Change: renamed the generated CI workflow from `ci-and-test.yml` to
    `ci.yml`, updated refresh and policy ownership around the new path, and
    clarified that `build.yml` follows the `CI` workflow defined there.
  Why: kept the separate `CI`, `Build`, and `Publish` workflows while making
    the generated workflow filename simpler and aligning the trigger/docs/test
    surfaces with that exact GitHub Actions layout.
  Impact: preserves separate workflow domains, keeps `Build` chained after
    `CI` success, regenerates the governance workflow at
    `.github/workflows/ci.yml`, and removes the old `ci-and-test.yml` path
    from live repo contracts.
  Files:
  .github/workflows/build.yml
  .github/workflows/ci-and-test.yml
  .github/workflows/ci.yml
  CHANGELOG.md
  POLICY_MAP.md
  PROFILE_MAP.md
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/global/assets/ci-and-test.yml
  devcovenant/builtin/profiles/global/assets/ci.yml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/global.yaml
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/manifest_inventory.py
  devcovenant/custom/profiles/devcovrepo/assets/POLICY_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/PROFILE_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/changelog_coverage/\
    test_changelog_coverage.py
  tests/devcovenant/builtin/policies/documentation_growth_tracking/\
    test_documentation_growth_tracking.py
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/test_refresh.py

- 2026-03-29:
  Change: simplified CI ownership by removing generated built-artifact proof
    from `ci_and_test`, moved the `pipx` lifecycle proof into `build.yml`,
    and aligned the package and security docs with the new
    `CI = source tree` and `Build = shipped artifacts` contract.
  Why: reduced overlap between generated and repo-maintained workflows so the
    automation story stays easier to reason about and external audits see one
    truthful proof boundary instead of two fuzzy ones.
  Impact: keeps the generated `CI` workflow focused on source-tree checks,
    makes `Build` the single owner of wheel/sdist/`pipx` artifact proof,
    and updates the docs and tests to match the simplified workflow model.
  Files:
  .github/workflows/build.yml
  .github/workflows/ci-and-test.yml
  CHANGELOG.md
  SECURITY.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-29:
  Change: aligned the last stale `test` workflow residue with the public
    `run` contract, strengthened the `pipx` lifecycle proof to execute the
    full installed workflow, and normalized the final managed-environment
    stage token to `run`.
  Why: closed the remaining doc/proof/internal seams that an external
    release-candidate audit could still flag after the larger workflow
    contract fixes had already landed.
  Impact: preserves a fully truthful `run` contract across package and custom
    docs, records gate-to-run evidence honestly in the policy maps, proves
    the full documented workflow in `pipx` CI, and removes the old internal
    `test` token from managed-environment stage persistence.
  Files:
  .github/workflows/ci-and-test.yml
  CHANGELOG.md
  POLICY_MAP.md
  devcovenant/builtin/policies/README.md
  devcovenant/builtin/policies/managed_environment/\
    managed_environment_runtime.py
  devcovenant/custom/README.md
  devcovenant/custom/policies/README.md
  devcovenant/custom/profiles/README.md
  devcovenant/custom/profiles/devcovrepo/assets/POLICY_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/managed_environment/\
    test_managed_environment_runtime.py

- 2026-03-29:
  Change: tightened `devcovenant asset` to a Desktop-only copy contract with
    an optional Desktop output filename instead of accepting general
    destination paths.
  Why: fixed the over-broad initial destination surface so asset
    materialization no longer risks arbitrary writes or path-escape behavior,
    and aligned the docs with the safer command semantics.
  Impact: preserves Desktop-only asset materialization, rejects path-like
    output arguments, keeps `--overwrite`, and preserves the shared
    rendering machinery for plain assets and managed docs.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/README.md
  devcovenant/asset.py
  devcovenant/core/services/asset_materialization.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/refresh.md
  tests/devcovenant/core/services/test_asset_materialization.py
  tests/devcovenant/test_asset.py

- 2026-03-29:
  Change: added `devcovenant asset FILE.ext [path]`, shared asset
    materialization helpers, and the matching docs/tests so reusable profile
    assets and managed docs can be rendered on demand.
  Why: exposed seeded docs and manifest templates through one operator-facing
    command without duplicating refresh or managed-doc rendering logic, while
    making destination and same-name resolution rules explicit.
  Impact: operators can now materialize assets to the Desktop or exact output
    paths with `--overwrite`, deterministic profile precedence, and the same
    content machinery that normal refresh/deploy already use.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/README.md
  devcovenant/asset.py
  devcovenant/cli.py
  devcovenant/core/README.md
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/asset_materialization.py
  devcovenant/core/services/manifest_inventory.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_asset_materialization.py
  tests/devcovenant/test_asset.py
  tests/devcovenant/test_cli.py

- 2026-03-29:
  Change: fixed `changelog-coverage` to preserve the gate-start top entry by
    fingerprint anywhere below the fresh session entry instead of requiring
    a hard-coded second-slot position.
  Why: corrected the old second-position rule that caused persistent false
    failures across valid closed-session boundaries and made the policy care
    about entry slot layout instead of the active gate session.
  Impact: changelog coverage now stays session-local, stops tripping over
    valid follow-up sessions, and still requires a fresh top entry while
    keeping the pre-session entry intact somewhere below it.
  Files:
  CHANGELOG.md
  devcovenant/builtin/policies/changelog_coverage/changelog_coverage.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/docs/policies.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/changelog_coverage/\
    test_changelog_coverage.py

- 2026-03-29:
  Change: fixed long-description sync in generated `pyproject.toml` by
    replacing the whole TOML field block and reusing the wrapped TOML
    renderer during refresh.
  Why: the previous wrapping attempt kept the full description text but left
    stray TOML lines behind when refresh rewrote `description`, which broke
    installed-artifact proof repos instead of actually satisfying the style
    rule.
  Impact: refresh now preserves the full project description, keeps generated
    `pyproject.toml` valid TOML, and lets long repo-owned description text
    stay wrapped without carving manifest files out of the line-length policy.
  Files:
  CHANGELOG.md
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/project_governance.py
  tests/devcovenant/test_refresh.py

- 2026-03-29:
  Change: updated the generic seeded project-description rendering across
    generated
    README and Python package metadata surfaces, and refreshed the routed
    docs and dependency artifacts that track that manifest template.
  Why: fixed the proof-repo line-length warnings without truncating the
    default identity sentence and kept the current gate session honest after
    dependency-management refreshed its lock and license evidence.
  Impact: generic installs now preserve the full project-description prompt
    while rendering wrapped README and TOML source lines, and the tracked
    docs, registry, lockfile, and license report stay aligned with that
    behavior.
  Files:
  CHANGELOG.md
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/python/assets/pyproject.toml
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/project_governance.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/project_governance.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  licenses/THIRD_PARTY_LICENSES.md
  requirements.lock
  tests/devcovenant/test_refresh.py
  tests/devcovenant/core/services/test_project_governance.py

- 2026-03-29:
  Change: implemented real workflow-run ordering semantics with validated
    `after` and `before` references, truthful `mid` status reporting, and
    full packaged-workflow proof in the Build lifecycle.
  Why: fixed release-candidate contract drift where run positioning was
    decorative, `gate --status` hid the public `mid` stage, and installed
    artifact proof was narrower than the documented workflow.
  Impact: workflow contracts now reject unknown references and cycles, status
    reports the real four-stage lifecycle, Build proves the installed
    `gate --start -> gate --mid -> run -> gate --end` workflow for wheel and
    sdist artifacts, and the last internal `phase` residue was removed.
  Files:
  .github/workflows/build.yml
  CHANGELOG.md
  devcovenant/core/flow/gate_status_helpers.py
  devcovenant/core/flow/workflow_contract.py
  devcovenant/core/runtime/execution.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/flow/test_gate_status_helpers.py
  tests/devcovenant/core/flow/test_workflow_contract.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-29:
  Change: marked the release-candidate preparation roadmap item done after
    proving the exact candidate tree through governed, packaging, and
    isolated artifact-lifecycle checks.
  Why: closed the final pre-release remediation step once the current tree
    was externally and locally proven as the real release candidate.
  Impact: the plan now treats the remediation roadmap as complete and leaves
    only human-controlled release mechanics beyond the proven candidate tree.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-28:
  Change: marked the `run` migration and core de-spaghettization roadmap
    items done and revised the plan summary to reflect release-candidate
    proof as the remaining work.
  Why: aligned the plan with the now-proven code, docs, CI, and architecture
    state so the roadmap stops describing closed workflow and ownership work
    as still open.
  Impact: clarified that Items 8 and 9 are complete, updated the audit
    baseline framing, and left release-candidate preparation as the next
    active roadmap item.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-28:
  Change: documented that `clean --all` cleans the runtime registry only for
    its `registry` scope and preserves the tracked `registry.yaml` contract.
  Why: clarified the cleanup boundary so operators do not mistake routine
    cleanup for destructive tracked-registry removal.
  Impact: explained in the README, installation, and registry docs that
    cleanup removes `devcovenant/registry/runtime/` artifacts while keeping
    the tracked registry document intact.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/docs/installation.md
  devcovenant/docs/registry.md

- 2026-03-28:
  Change: fixed stale `run` guidance in workflow runtime/docs, documented the
    public manual-attestation and artifact-check operator contract, and
    excluded transient bytecode from profile asset discovery.
  Why: aligned the live and source-managed docs with the one-command `run`
    workflow surface, removed misleading rerun guidance that still said
    `run run` or `test`, and prevented refresh from recording repo-local
    `__pycache__` artifacts in tracked profile assets.
  Impact: aligned troubleshooting and workflow recovery text on the real
    `devcovenant run` contract, published the attestation/env-var and
    artifact-path semantics for non-command runs, hardened tracked registry
    refresh against bytecode drift, and added regressions for the new
    guidance and asset-filtering behavior.
  Files:
  CHANGELOG.md
  devcovenant/core/contracts/policy.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/services/profile_registry.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/test_run.py

- 2026-03-28:
  Change: removed the lingering `required_run_ids` carry-forward seam from
    workflow-session persistence and renamed the flow-layer clean module to
    `clean_command.py` so it no longer doubles the top-level `clean.py`.
  Why: closed the last live migration shim now that the new `run_ids`
    contract is proven, and reduced naming drift in the clean-command
    implementation layout.
  Impact: removed the legacy runtime-session carry-forward path so
    workflow-session writes now persist only `run_ids`, aligned
    clean-command imports/tests around a distinct flow module name, and
    dropped the obsolete workflow-run `required` field from test fixtures.
  Files:
  CHANGELOG.md
  devcovenant/clean.py
  devcovenant/core/flow/clean.py
  devcovenant/core/flow/clean_command.py
  devcovenant/core/flow/workflow_contract.py
  devcovenant/core/runtime/workflow_session.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/docs/installation.md
  tests/devcovenant/core/flow/test_clean.py
  tests/devcovenant/core/flow/test_clean_command.py
  tests/devcovenant/core/flow/test_workflow_contract.py
  tests/devcovenant/core/flow/test_workflow_validation.py
  tests/devcovenant/core/runtime/test_workflow_session.py
  tests/devcovenant/test_clean.py

- 2026-03-28:
  Change: aligned the live workflow-run contract in code, docs, profiles,
    and tests so `devcovenant run` now means “run all configured runs”
    without a required-versus-optional split.
  Why: removed the remaining drift between the corrected plan and the
    implementation so public wording, tracked contract keys, and generated
    workflow assets all teach the same model.
  Impact: simplified workflow-run ownership around configured runs,
    preserved temporary legacy fallbacks only for stale generated state,
    and refreshed the governed docs, profile manifests, registry contract,
    runtime messages, and regression coverage around the new wording.
  Files:
  AGENTS.md
  CHANGELOG.md
  POLICY_MAP.md
  PROFILE_MAP.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/csharp/csharp.yaml
  devcovenant/builtin/profiles/dart/dart.yaml
  devcovenant/builtin/profiles/docker/docker.yaml
  devcovenant/builtin/profiles/fastapi/fastapi.yaml
  devcovenant/builtin/profiles/flutter/flutter.yaml
  devcovenant/builtin/profiles/frappe/frappe.yaml
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/go/go.yaml
  devcovenant/builtin/profiles/java/java.yaml
  devcovenant/builtin/profiles/javascript/javascript.yaml
  devcovenant/builtin/profiles/kubernetes/kubernetes.yaml
  devcovenant/builtin/profiles/objective_c/objective_c.yaml
  devcovenant/builtin/profiles/php/php.yaml
  devcovenant/builtin/profiles/python/python.yaml
  devcovenant/builtin/profiles/ruby/ruby.yaml
  devcovenant/builtin/profiles/rust/rust.yaml
  devcovenant/builtin/profiles/swift/swift.yaml
  devcovenant/builtin/profiles/terraform/terraform.yaml
  devcovenant/builtin/profiles/typescript/typescript.yaml
  devcovenant/core/README.md
  devcovenant/core/contracts/invariants/devflow_run_gates.yaml
  devcovenant/core/flow/gate.py
  devcovenant/core/flow/workflow_contract.py
  devcovenant/core/flow/workflow_validation.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/runtime/workflow_session.py
  devcovenant/core/services/integrity_validation.py
  devcovenant/custom/profiles/devcovrepo/assets/POLICY_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/PROFILE_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  devcovenant/run.py
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/flow/test_workflow_contract.py
  tests/devcovenant/core/flow/test_workflow_validation.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/runtime/test_workflow_session.py
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_run.py

- 2026-03-28:
  Change: clarified the workflow-run roadmap in `PLAN.md` so `devcovenant
    run` now plainly means “run all configured runs” without an
    optional-versus-required split.
  Why: corrected the plan after the fresh contract clarification so the
    roadmap no longer teaches drifted one-run or optional-run behavior.
  Impact: aligned the plan with the intended workflow, documented
    per-command recording for `command_group` runs, and tightened the
    file-check and end-gate language around all configured runs.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-28:
  Change: removed the last live `test_events` compatibility shims, fixed the
    managed workflow doc source, and added direct coverage for the public
    advanced workflow-run kinds.
  Why: closed the remaining closure-audit seams so managed docs cannot
    reintroduce the wrong `run` contract and the public advanced run kinds are
    proven instead of only documented.
  Impact: clarified that `run_events` is now the only accepted run-event
    contract, aligned the managed workflow asset with the public `run`
    behavior, documented the runtime event ownership more clearly in registry
    docs, and exercised runtime-action, policy-command, manual-attestation,
    and external-artifact workflow runs directly in runtime tests.
  Files:
  CHANGELOG.md
  devcovenant/core/flow/gate.py
  devcovenant/core/flow/workflow_contract.py
  devcovenant/core/runtime/event.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/runtime/session_snapshot.py
  devcovenant/core/services/profile_registry.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/registry.md
  tests/devcovenant/core/flow/test_workflow_contract.py
  tests/devcovenant/core/runtime/test_event.py
  tests/devcovenant/core/runtime/test_execution.py

- 2026-03-28:
  Change: Removed the drifted duplicate workflow-run surface across the CLI,
    runtime, registry, docs, generated outputs, and tests.
  Why: Removed drift between the intended `devcovenant gate --start ->
    devcovenant gate --mid -> devcovenant run -> devcovenant gate --end`
    contract and the half-duplicated extra command/model implementation.
  Impact: Aligned the public command surface, tracked runtime schema,
    generated AGENTS/registry outputs, and tests on one `run` contract while
    deleting the duplicate legacy surface.
  Files:
  .github/workflows/ci-and-test.yml
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  POLICY_MAP.md
  PROFILE_MAP.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/policies/README.md
  devcovenant/builtin/policies/changelog_coverage/changelog_coverage.py
  devcovenant/builtin/policies/documentation_growth_tracking/\
    documentation_growth_tracking.py
  devcovenant/builtin/policies/tests_coverage/tests_coverage.py
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/csharp/csharp.yaml
  devcovenant/builtin/profiles/dart/dart.yaml
  devcovenant/builtin/profiles/docker/docker.yaml
  devcovenant/builtin/profiles/fastapi/fastapi.yaml
  devcovenant/builtin/profiles/flutter/flutter.yaml
  devcovenant/builtin/profiles/frappe/frappe.yaml
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/global/assets/ci-and-test.yml
  devcovenant/builtin/profiles/go/go.yaml
  devcovenant/builtin/profiles/java/java.yaml
  devcovenant/builtin/profiles/javascript/javascript.yaml
  devcovenant/builtin/profiles/kubernetes/kubernetes.yaml
  devcovenant/builtin/profiles/objective_c/objective_c.yaml
  devcovenant/builtin/profiles/php/php.yaml
  devcovenant/builtin/profiles/python/python.yaml
  devcovenant/builtin/profiles/ruby/ruby.yaml
  devcovenant/builtin/profiles/rust/rust.yaml
  devcovenant/builtin/profiles/swift/swift.yaml
  devcovenant/builtin/profiles/terraform/terraform.yaml
  devcovenant/builtin/profiles/typescript/typescript.yaml
  devcovenant/cli.py
  devcovenant/core/README.md
  devcovenant/core/contracts/invariant.py
  devcovenant/core/contracts/invariants/devflow_run_gates.yaml
  devcovenant/core/contracts/policy.py
  devcovenant/core/flow/gate.py
  devcovenant/core/flow/gate_status_helpers.py
  devcovenant/core/flow/policy_check_context.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/flow/workflow_contract.py
  devcovenant/core/flow/workflow_validation.py
  devcovenant/core/runtime/event.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/runtime/session_snapshot.py
  devcovenant/core/runtime/workflow_session.py
  devcovenant/core/services/integrity_validation.py
  devcovenant/core/services/manifest_inventory.py
  devcovenant/core/services/profile_registry.py
  devcovenant/core/services/runtime_profile.py
  devcovenant/custom/profiles/devcovrepo/assets/POLICY_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/PROFILE_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/gate.py
  devcovenant/phase.py
  devcovenant/run.py
  devcovenant/registry/README.md
  devcovenant/registry/registry.yaml
  devcovenant/run.py
  tests/devcovenant/builtin/policies/changelog_coverage/\
    test_changelog_coverage.py
  tests/devcovenant/builtin/policies/tests_coverage/test_tests_coverage.py
  tests/devcovenant/core/contracts/test_policy.py
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/flow/test_gate_status_helpers.py
  tests/devcovenant/core/flow/test_policy_check_context.py
  tests/devcovenant/core/flow/test_workflow_contract.py
  tests/devcovenant/core/flow/test_workflow_validation.py
  tests/devcovenant/core/runtime/test_event.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/runtime/test_workflow_session.py
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/core/services/test_runtime_profile.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_gate.py
  tests/devcovenant/test_phase.py
  tests/devcovenant/test_run.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_run.py

- 2026-03-28:
  Change: generalized workflow phase-event reporting and formalized
    configurable runtime evidence paths across the runtime, profiles, docs,
    and tests.
  Why: removed the last test-shaped reporting seam and made both gate status
    and workflow-session evidence follow one explicit invariant contract
    instead of a half-fixed, half-configurable path model.
  Impact: phases now record canonical `phase_events`, profiles declare
    `phase_events` adapters generically, and `gate_status_file` plus
    `workflow_session_file` are configurable only within the runtime registry
    root.
  Files:
  AGENTS.md
  CHANGELOG.md
  POLICY_MAP.md
  PROFILE_MAP.md
  devcovenant/builtin/profiles/csharp/csharp.yaml
  devcovenant/builtin/profiles/dart/dart.yaml
  devcovenant/builtin/profiles/docker/docker.yaml
  devcovenant/builtin/profiles/fastapi/fastapi.yaml
  devcovenant/builtin/profiles/flutter/flutter.yaml
  devcovenant/builtin/profiles/frappe/frappe.yaml
  devcovenant/builtin/profiles/go/go.yaml
  devcovenant/builtin/profiles/java/java.yaml
  devcovenant/builtin/profiles/javascript/javascript.yaml
  devcovenant/builtin/profiles/kubernetes/kubernetes.yaml
  devcovenant/builtin/profiles/objective_c/objective_c.yaml
  devcovenant/builtin/profiles/php/php.yaml
  devcovenant/builtin/profiles/python/python.yaml
  devcovenant/builtin/profiles/ruby/ruby.yaml
  devcovenant/builtin/profiles/rust/rust.yaml
  devcovenant/builtin/profiles/swift/swift.yaml
  devcovenant/builtin/profiles/terraform/terraform.yaml
  devcovenant/builtin/profiles/typescript/typescript.yaml
  devcovenant/core/README.md
  devcovenant/core/contracts/invariants/devflow_run_gates.yaml
  devcovenant/core/flow/gate.py
  devcovenant/core/flow/workflow_contract.py
  devcovenant/core/flow/workflow_validation.py
  devcovenant/core/runtime/event.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/runtime/registry.py
  devcovenant/core/runtime/session_snapshot.py
  devcovenant/core/services/profile_registry.py
  devcovenant/custom/profiles/devcovrepo/assets/POLICY_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/PROFILE_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/README.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/flow/test_workflow_contract.py
  tests/devcovenant/core/flow/test_workflow_validation.py
  tests/devcovenant/core/runtime/test_event.py
  tests/devcovenant/core/runtime/test_registry.py

- 2026-03-27:
  Change: defined explicit workflow-run freshness and universal
    per-invocation output-mode overrides across the CLI, runtime, docs, and
    tests.
  Why: removed the hidden `tests`-only changelog invalidation rule and
    converted `--quiet`, `--normal`, and `--verbose` into a stable command
    contract instead of a config-only runtime behavior.
  Impact: clarified that required runs now declare freshness behavior
    explicitly, every public command accepts shared output-mode overrides,
    and the public docs now describe the workflow-run contract more
    directly.
  Files:
  CHANGELOG.md
  devcovenant/cli.py
  devcovenant/core/flow/workflow_contract.py
  devcovenant/core/runtime/execution.py
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/flow/test_workflow_contract.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/test_cli.py

- 2026-03-27:
  Change: amended the roadmap to formalize the remaining workflow-contract
    hardening gaps after the core `run` migration.
  Why: converted the latest architecture audit findings into explicit plan
    work so run freshness, advanced workflow kinds, generic run events,
    output overrides, and evidence-path ownership do not remain implicit.
  Impact: sharpens the boundary between Item 8 and Item 9, adds the missing
    closure work to the plan, and keeps the remaining workflow formalization
    visible instead of tribal.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-27:
  Change: simplified the repeated full-check sequencing inside
    `policy_engine.py` into private helper paths.
  Why: reduced duplicated invariant/context rerun logic so the public
    `check()` flow stays narrower while preserving the same autofix-and-rerun
    behavior.
  Impact: keeps `policy_engine.py` service-owned but thinner, adds a focused
    autofix-rerun regression, and updates the architecture doc to describe the
    slimmer orchestration role more precisely.
  Files:
  CHANGELOG.md
  devcovenant/core/services/policy_engine.py
  devcovenant/docs/architecture.md
  tests/devcovenant/core/services/test_policy_engine.py

- 2026-03-27:
  Change: migrated gate/session-derived policy-check context out of
    `core/services` into the workflow-owned `core/flow` layer.
  Why: clarified that snapshot and gate-state interpretation belongs with the
    flow runtime, while `policy_engine.py` should stay focused on policy
    orchestration rather than owning session-truth helpers.
  Impact: rewires the policy-engine context builder to the new flow module,
    moves the mirrored tests under `tests/devcovenant/core/flow/`, and updates
    the workflow/core architecture docs to the tighter ownership split.
  Files:
  CHANGELOG.md
  devcovenant/core/README.md
  devcovenant/core/flow/policy_check_context.py
  devcovenant/core/services/policy_check_context.py
  devcovenant/core/services/policy_engine.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/flow/test_policy_check_context.py
  tests/devcovenant/core/services/test_policy_check_context.py

- 2026-03-27:
  Change: moved workflow-contract resolution out of `core/services` into the
    workflow-owned `core/flow` layer.
  Why: aligned the tracked workflow contract with the rest of the gate/run
    code so run-contract normalization no longer lives in the
    services grab-bag.
  Impact: rewires gate, runtime, and profile-registry imports to the new
    flow-owned module, moves the mirrored tests under
    `tests/devcovenant/core/flow/`, and updates the inventory/workflow docs
    to the cleaner ownership map.
  Files:
  CHANGELOG.md
  devcovenant/core/README.md
  devcovenant/core/flow/gate.py
  devcovenant/core/flow/workflow_contract.py
  devcovenant/core/flow/workflow_validation.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/services/manifest_inventory.py
  devcovenant/core/services/profile_registry.py
  devcovenant/core/services/workflow_contract.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/flow/test_workflow_contract.py
  tests/devcovenant/core/services/test_workflow_contract.py

- 2026-03-27:
  Change: migrated namespaced policy-command parsing and runtime-action
    dispatch out of `core/services` into `core/runtime`.
  Why: clarified that explicit `devcovenant policy ...` execution belongs on
    the same runtime boundary as `run` and `run run`, while the policy
    engine remains responsible for policy meaning and orchestration.
  Impact: rewires policy command/action imports, moves the mirrored tests into
    `tests/devcovenant/core/runtime/`, and updates the workflow,
    architecture, policies, and installation docs to the tighter ownership
    map.
  Files:
  CHANGELOG.md
  devcovenant/builtin/policies/dependency_management/dependency_management.py
  devcovenant/core/README.md
  devcovenant/core/flow/refresh.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/runtime/policy_commands.py
  devcovenant/core/runtime/policy_runtime_actions.py
  devcovenant/core/services/core_invariants.py
  devcovenant/core/services/manifest_inventory.py
  devcovenant/core/services/policy_commands.py
  devcovenant/core/services/policy_engine.py
  devcovenant/core/services/policy_runtime_actions.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/policy.py
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/runtime/test_policy_commands.py
  tests/devcovenant/core/runtime/test_policy_runtime_actions.py
  tests/devcovenant/core/services/test_policy_commands.py
  tests/devcovenant/core/services/test_policy_runtime_actions.py

- 2026-03-27:
  Change: migrated runtime-facing event-adapter loading and policy-report
    output
    formatting out of `core/services` into `core/runtime`.
  Why: clarified that `metadata.py` is the real service-layer cross-cutting
    resolver while event recording and policy-check output belong to runtime
    execution.
  Impact: rewires the Python test-event adapter entrypoint and engine imports
    to the new runtime modules, moves the mirrored tests under
    `tests/devcovenant/core/runtime/`, and updates the workflow/core docs to
    the narrower ownership map.
  Files:
  CHANGELOG.md
  devcovenant/builtin/profiles/python/python.yaml
  devcovenant/core/README.md
  devcovenant/core/runtime/event.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/runtime/policy_reporting.py
  devcovenant/core/services/event.py
  devcovenant/core/services/policy_engine.py
  devcovenant/core/services/policy_reporting.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/workflow.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/runtime/test_event.py
  tests/devcovenant/core/runtime/test_policy_reporting.py
  tests/devcovenant/core/services/test_event.py
  tests/devcovenant/core/services/test_policy_reporting.py

- 2026-03-27:
  Change: restructured AGENTS policy/core-invariant block refresh out of
    `core/services` into the shared `core/lib/agents_blocks.py` helper and
    trimmed `core_invariants.py` back to invariant loading and registry data.
  Why: reduced managed-block rendering overlap so the
    service layer describes invariant and policy business logic instead of
    also owning AGENTS block scaffolding.
  Impact: updated `refresh.py` to use one shared AGENTS block helper surface,
    reduced service-layer overlap, and rewrote managed-doc/runtime imports to
    the new
    ownership map, and rewrites the mirrored tests/docs around the new lib
    helper.
  Files:
  CHANGELOG.md
  devcovenant/core/README.md
  devcovenant/core/flow/refresh.py
  devcovenant/core/lib/agents_blocks.py
  devcovenant/core/services/core_invariant_block_refresh.py
  devcovenant/core/services/core_invariants.py
  devcovenant/core/services/managed_docs.py
  devcovenant/core/services/manifest_inventory.py
  devcovenant/core/services/policy_block_refresh.py
  devcovenant/docs/architecture.md
  devcovenant/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/lib/test_agents_blocks.py
  tests/devcovenant/core/services/test_core_invariant_block_refresh.py
  tests/devcovenant/core/services/test_policy_block_refresh.py

- 2026-03-26:
  Change: split the mixed services-layer `registry.py` into tracked-registry,
    policy-registry, and manifest-inventory helpers and removed the old
    catch-all module.
  Why: reduce `core/services` overlap so tracked document I/O, policy
    descriptor loading, and manifest inventory ownership stop sharing one
    mixed service surface.
  Impact: clarifies registry ownership for the ongoing workflow
    de-spaghettization, rewires the affected runtime and policy services to
    the new helpers, and adds mirrored tests/docs for the new split.
  Files:
  CHANGELOG.md
  devcovenant/builtin/policies/dependency_management/\
    dependency_lock_runtime.py
  devcovenant/builtin/policies/managed_environment/\
    managed_environment_runtime.py
  devcovenant/builtin/policies/version_governance/version_governance.py
  devcovenant/core/README.md
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/core_invariant_block_refresh.py
  devcovenant/core/services/core_invariants.py
  devcovenant/core/services/integrity_validation.py
  devcovenant/core/services/manifest_inventory.py
  devcovenant/core/services/metadata.py
  devcovenant/core/services/policy_block_refresh.py
  devcovenant/core/services/policy_commands.py
  devcovenant/core/services/policy_engine.py
  devcovenant/core/services/policy_reporting.py
  devcovenant/core/services/policy_registry.py
  devcovenant/core/services/policy_runtime_actions.py
  devcovenant/core/services/profile_registry.py
  devcovenant/core/services/registry.py
  devcovenant/core/services/structure_validation.py
  devcovenant/core/services/tracked_registry.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/registry.md
  devcovenant/install.py
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/last_updated/test_last_updated.py
  tests/devcovenant/core/services/test_integrity_validation.py
  tests/devcovenant/core/services/test_manifest_inventory.py
  tests/devcovenant/core/services/test_metadata.py
  tests/devcovenant/core/services/test_policy_registry.py
  tests/devcovenant/core/services/test_policy_reporting.py
  tests/devcovenant/core/services/test_registry.py
  tests/devcovenant/core/services/test_structure_validation.py
  tests/devcovenant/core/services/test_tracked_registry.py
  tests/devcovenant/test_install.py

- 2026-03-26:
  Change: moved gate-status payload validation into flow-owned helpers and
    renamed the remaining core-invariant service modules to
    `integrity_validation` and `structure_validation`.
  Why: clarified that workflow-state schema enforcement belongs under
    `core/flow` while the service layer should describe descriptor, registry,
    and repo-structure validation without legacy guard-module naming.
  Impact: keeps invariant ids stable while making the module ownership map
    more truthful, gives flow one canonical gate-status validation helper,
    updates manifest/core-invariant path resolution to the renamed modules,
    and adds mirrored tests/docs for the new architecture split.
  Files:
  CHANGELOG.md
  devcovenant/core/README.md
  devcovenant/core/flow/gate_status_helpers.py
  devcovenant/core/flow/gate_status_validation.py
  devcovenant/core/services/core_invariants.py
  devcovenant/core/services/devcov_integrity_guard.py
  devcovenant/core/services/devcov_structure_guard.py
  devcovenant/core/services/integrity_validation.py
  devcovenant/core/services/registry.py
  devcovenant/core/services/structure_validation.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/flow/test_gate_status_validation.py
  tests/devcovenant/core/services/test_core_invariants.py
  tests/devcovenant/core/services/test_devcov_integrity_guard.py
  tests/devcovenant/core/services/test_devcov_structure_guard.py
  tests/devcovenant/core/services/test_integrity_validation.py
  tests/devcovenant/core/services/test_structure_validation.py

- 2026-03-26:
  Change: normalized workflow-state recording to `last_run_utc` plus
    `commands`, moved workflow child output onto a generic channel, and
    declared run-reporting hooks in workflow metadata instead of
    hardcoding `tests`.
  Why: removed transitional duplicate fields and the remaining
    run-id-specific execution branches so richer workflow reporting can
    be run-owned and reusable.
  Impact: records workflow sessions with canonical UTC-plus-commands
    payloads, collapses legacy duplicate keys on write,
    integrity checks validate the canonical schema, command-group runs can
    opt into output-mode overrides, event adapters, and runtime profiling
    declaratively, and built-in test runs use that generic contract.
  Files:
  CHANGELOG.md
  devcovenant/builtin/profiles/csharp/csharp.yaml
  devcovenant/builtin/profiles/dart/dart.yaml
  devcovenant/builtin/profiles/docker/docker.yaml
  devcovenant/builtin/profiles/fastapi/fastapi.yaml
  devcovenant/builtin/profiles/flutter/flutter.yaml
  devcovenant/builtin/profiles/frappe/frappe.yaml
  devcovenant/builtin/profiles/go/go.yaml
  devcovenant/builtin/profiles/java/java.yaml
  devcovenant/builtin/profiles/javascript/javascript.yaml
  devcovenant/builtin/profiles/kubernetes/kubernetes.yaml
  devcovenant/builtin/profiles/objective_c/objective_c.yaml
  devcovenant/builtin/profiles/php/php.yaml
  devcovenant/builtin/profiles/python/python.yaml
  devcovenant/builtin/profiles/ruby/ruby.yaml
  devcovenant/builtin/profiles/rust/rust.yaml
  devcovenant/builtin/profiles/swift/swift.yaml
  devcovenant/builtin/profiles/terraform/terraform.yaml
  devcovenant/builtin/profiles/typescript/typescript.yaml
  devcovenant/core/flow/gate.py
  devcovenant/core/flow/gate_status_helpers.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/runtime/output.py
  devcovenant/core/runtime/workflow_session.py
  devcovenant/core/services/devcov_integrity_guard.py
  devcovenant/core/services/event.py
  devcovenant/core/services/workflow_contract.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/flow/test_workflow_validation.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/runtime/test_output.py
  tests/devcovenant/core/runtime/test_workflow_session.py
  tests/devcovenant/core/services/test_devcov_integrity_guard.py
  tests/devcovenant/core/services/test_workflow_contract.py

- 2026-03-26:
  Change: moved workflow-validation ownership into `core/flow`, split
    tracked and runtime registry path helpers, and rewired the invariant
    loader and mirrored docs/tests to the new module boundaries.
  Why: split the first de-spaghettization seam so workflow truth no longer
    has to live behind a service-layer invariant module and one catch-all
    registry path API.
  Impact: clarified that flow now owns `workflow_validation.py`, runtime
    owns runtime registry paths, services own tracked registry paths, and
    the repo has mirrored tests and docs for the new architecture split.
  Files:
  CHANGELOG.md
  devcovenant/builtin/policies/managed_environment/\
    managed_environment_runtime.py
  devcovenant/core/README.md
  devcovenant/core/flow/clean.py
  devcovenant/core/flow/gate.py
  devcovenant/core/flow/gate_changelog_helpers.py
  devcovenant/core/flow/gate_status_helpers.py
  devcovenant/core/flow/workflow_validation.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/runtime/registry.py
  devcovenant/core/runtime/session_snapshot.py
  devcovenant/core/runtime/workflow_session.py
  devcovenant/core/services/core_invariants.py
  devcovenant/core/services/devflow_run_gates.py
  devcovenant/core/services/policy_block_refresh.py
  devcovenant/core/services/registry.py
  devcovenant/core/services/tracked_registry.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/policies.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/flow/test_workflow_validation.py
  tests/devcovenant/core/runtime/test_registry.py
  tests/devcovenant/core/services/test_core_invariants.py
  tests/devcovenant/core/services/test_devflow_run_gates.py
  tests/devcovenant/core/services/test_registry.py
  tests/devcovenant/core/services/test_tracked_registry.py

- 2026-03-26:
  Change: revised the roadmap to dissolve `devflow_run_gates`, split
    registry code by both ephemerity and ownership, and replace leftover
    tests-only runtime privilege with generic run-reporting hooks and
    generic file-dependent success checks.
  Why: locked the architecture direction after the read-only `run` audit so
    the next de-spaghettization slice has a precise target instead of vague
    cleanup language.
  Impact: the active plan now treats workflow truth consolidation,
    UTC-only `last_run_utc`, `commands`-only command groups, registry
    ownership separation, reusable run hooks, and explicit absolute or
    relative file-check contracts as one coherent architecture rewrite.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-26:
  Change: renamed the visible generated workflow contract from `Workflows`
    to `CI`, renamed the generated main job to `DevCovenant`, and
    synchronized the source, generated, test, and roadmap surfaces around
    the new Actions naming.
  Why: resolved the GitHub Actions sidebar ambiguity caused by `Workflows`,
    aligned the generated workflow and `build.yml` trigger with the intended
    `CI` contract, and preserved the earlier roadmap entry intact under a
    fresh session changelog entry.
  Impact: GitHub Actions now presents a cleaner `CI` workflow with
    `DevCovenant` and `Build and Install` job labels, while the generated
    workflow, registry, docs, tests, and roadmap all point at the same
    contract for the next build-proof verification pass.
  Files:
  CHANGELOG.md
  PLAN.md
  .github/workflows/build.yml
  .github/workflows/ci-and-test.yml
  devcovenant/builtin/profiles/global/assets/ci-and-test.yml
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-26:
  Change: amended the roadmap to add the immediate CI naming/blocker work and
    a full post-`run` core de-spaghettization item.
  Why: clarified that the active redesign still needs both the GitHub Actions
    cleanup (`CI` naming and build-proof stability) and a deliberate
    core-module ownership reshaping after the workflow system lands.
  Impact: expanded the plan so release prep now depends on resolving the
    current CI workflow contract and on re-hashing core module ownership,
    especially around `devflow_run_gates`, the guard modules, and the crowded
    `core/services` layer.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-26:
  Change: corrected the artifact-lifecycle GitHub Actions scripts to use
    direct temp-repo directory switches, renamed the visible CI workflow
    from `Checks` to `Workflows`, and tightened the roadmap around the
    workflow-runtime schema.
  Why: fixed a real shell-parse failure where GitHub could not terminate the
    inline Python config-review helper in the build-proof steps, removed the
    last redundant workflow label in the GitHub Actions UI, and captured the
    schema-tightening decisions needed to keep the `run` redesign from
    feeling flimsy.
  Impact: repaired the `Build` lifecycle proof, aligned the generated
    `Workflows` pipeline name, and clarified that the active migration keeps
    `last_run_utc` canonical, uses `commands`-only command groups, and does
    not let structural policies such as `modules-need-tests` masquerade as
    the engine that powers workflow execution.
  Files:
  CHANGELOG.md
  .github/workflows/build.yml
  devcovenant/builtin/profiles/global/assets/ci-and-test.yml
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/config.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  devcovenant/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  PLAN.md
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-26:
  Change: amended the roadmap to require universal `--quiet`, `--normal`, \
    and `--verbose` CLI overrides as part of the core `run` migration.
  Why: clarified that output modes should default from config, allow
    per-invocation overrides, and stay owned by the shared output/runtime
    layer instead of bespoke command logic.
  Impact: standardized the active plan to treat command-wide mode overrides and
    mode-agnostic command execution as release-blocking parts of the
    workflow-command redesign.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-26:
  Change: implemented the core `run` migration by adding the new root command,
  moving built-in profiles onto declared `workflow_runs`, and rewriting the
  gate/runtime/docs contract away from the old public `test` surface.
  Why: closed the stitched workflow boundary where core still hardcoded
  `devcovenant test` while the tracked workflow contract claimed a generic
  run model.
  Impact: standardized DevCovenant on `gate --start -> gate --mid -> run ->
  gate --end`, with explicit `run` reruns, profile-owned run
  declarations, and aligned docs/registry evidence instead of legacy
  `required_commands` test wiring.
  Files:
  AGENTS.md
  CHANGELOG.md
  POLICY_MAP.md
  PROFILE_MAP.md
  README.md
  CONTRIBUTING.md
  devcovenant/README.md
  devcovenant/builtin/policies/README.md
  devcovenant/builtin/policies/managed_environment/managed_environment.yaml
  devcovenant/builtin/policies/managed_environment/\
    managed_environment_runtime.py
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/csharp/csharp.yaml
  devcovenant/builtin/profiles/dart/dart.yaml
  devcovenant/builtin/profiles/docker/docker.yaml
  devcovenant/builtin/profiles/fastapi/fastapi.yaml
  devcovenant/builtin/profiles/flutter/flutter.yaml
  devcovenant/builtin/profiles/frappe/frappe.yaml
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/global/assets/ci-and-test.yml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/builtin/profiles/go/go.yaml
  devcovenant/builtin/profiles/java/java.yaml
  devcovenant/builtin/profiles/javascript/javascript.yaml
  devcovenant/builtin/profiles/kubernetes/kubernetes.yaml
  devcovenant/builtin/profiles/objective_c/objective_c.yaml
  devcovenant/builtin/profiles/php/php.yaml
  devcovenant/builtin/profiles/python/python.yaml
  devcovenant/builtin/profiles/ruby/ruby.yaml
  devcovenant/builtin/profiles/rust/rust.yaml
  devcovenant/builtin/profiles/swift/swift.yaml
  devcovenant/builtin/profiles/terraform/terraform.yaml
  devcovenant/builtin/profiles/typescript/typescript.yaml
  devcovenant/cli.py
  devcovenant/core/contracts/invariants/devflow_run_gates.yaml
  devcovenant/core/flow/gate.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/flow/gate_status_helpers.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/services/devcov_integrity_guard.py
  devcovenant/core/services/devflow_run_gates.py
  devcovenant/core/services/registry.py
  devcovenant/core/services/runtime_profile.py
  devcovenant/core/services/workflow_contract.py
  devcovenant/core/README.md
  devcovenant/custom/profiles/devcovrepo/assets/PROFILE_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/assets/POLICY_MAP.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/run.py
  devcovenant/registry/README.md
  devcovenant/registry/registry.yaml
  devcovenant/run.py
  devcovenant/test.py
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/flow/test_gate_status_helpers.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/runtime/test_run_logging.py
  tests/devcovenant/core/services/test_devflow_run_gates.py
  tests/devcovenant/core/services/test_metadata.py
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/core/services/test_runtime_profile.py
  tests/devcovenant/core/services/test_workflow_contract.py
  tests/devcovenant/builtin/policies/managed_environment/\
    test_managed_environment_runtime.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_run.py
  tests/devcovenant/test_test.py

- 2026-03-26:
  Change: rewrote the active plan to treat the half-migrated workflow-run
  redesign as a release blocker and to sequence the full `devcovenant run`
  migration in ordered work packages.
  Why: documented the resolved paper design so the next implementation slice
  replaces the stitched-in `devcovenant test` model with one coherent
  command/runtime/docs/CI contract instead of drifting through partial fixes.
  Impact: the repo now has a concrete migration blueprint for root-command
  ownership, generic run execution, gate/invariant messaging, CI, docs, test
  coverage, and the follow-up naming decision around `modules-need-tests`.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-26:
  Change: reran the external-grade release audit against the current staged
  release-candidate tree and recorded the closure outcome in the plan.
  Why: verified that the remaining blocker and high-severity audit findings
  are now closed by shipped artifacts, real lifecycle proof, workflow
  truthfulness, publish provenance, lock semantics, and workflow-run
  recording rather than by local reasoning alone.
  Impact: the repo now has a fresh outside-in audit pass showing no
  substantive blocker or high-severity release-truthfulness mismatches, so
  the next work is release-candidate preparation rather than more remediation.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-26:
  Change: clarified the baseline-first lifecycle for repo-specific custom
  policies and profiles in the operator docs and locked that guidance with a
  regression test.
  Why: closed the external-audit docs gap where normal repositories could
  read custom-extension support without seeing plainly that the first reviewed
  baseline should come before seeding repo-specific custom surfaces.
  Impact: normal-repo activation guidance now states `install`, config review,
  and `deploy` first, then repo-specific custom extensions, and deploy cleanup
  reads as an intentional lifecycle boundary instead of arbitrary deletion.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PLAN.md
  POLICY_MAP.md
  PROFILE_MAP.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  tests/devcovenant/core/runtime/test_execution.py

- 2026-03-25:
  Change: formalized workflow runs as a tracked/runtime contract by adding
  `workflow_contract`, `workflow_session.json`, the generic
  `devcovenant run` command, and run-aware gate and invariant
  behavior.
  Why: closed the workflow-boundary defect where gate mechanics still depended
  on test-centric or policy-adjacent assumptions instead of one explicit
  profile-declared workflow interface.
  Impact: the Python profile now declares `tests` as the first real workflow
  run, start and end gates enforce required runs generically, tracked
  registry state records the workflow contract, and the runtime records run
  evidence separately from the short gate lifecycle ledger.
  Files:
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  devcovenant/builtin/profiles/python/python.yaml
  devcovenant/cli.py
  devcovenant/core/contracts/invariants/devflow_run_gates.yaml
  devcovenant/core/flow/gate.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/runtime/workflow_session.py
  devcovenant/core/services/devflow_run_gates.py
  devcovenant/core/services/profile_registry.py
  devcovenant/core/services/registry.py
  devcovenant/core/services/workflow_contract.py
  devcovenant/run.py
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/runtime/test_workflow_session.py
  tests/devcovenant/core/services/test_devflow_run_gates.py
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/core/services/test_workflow_contract.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_run.py
  tests/devcovenant/test_refresh.py

- 2026-03-25:
  Change: rewrote the active release plan to formalize the intended
  workflow-run extension redesign, including run ownership, tracked and
  runtime schemas, start-gate carry-forward rules, end-gate closure rules,
  and the initial success-contract set.
  Why: captured the new workflow-boundary decision before implementation so
  gate mechanics no longer drift around customizable policy state and the
  upcoming redesign has one explicit contract to build against.
  Impact: the plan now records workflow-run formalization as a first-class
  release-blocking remediation item, records `external_artifact_check` in the
  initial success-contract vocabulary, and makes the future registry and
  migration work concrete enough to execute without reconstructing this thread.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-25:
  Change: tightened dependency-management lock refresh so
  `requirements.lock` ignores and scrubs environment-specific pip option
  lines instead of treating them as semantic dependency drift.
  Why: closed the external-audit finding that emitted index or trusted-host
  directives could make refresh behave differently across environments and
  could leak non-semantic pip source control lines into the stable lock body.
  Impact: Python lock refresh now preserves a normalized dependency-resolution
  contract, the new regressions cover both no-drift and cleanup cases, and
  the policy docs now state plainly that package-source behavior belongs in
  dependency-management metadata/config rather than the lock file body.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/builtin/policies/dependency_management/\
    dependency_lock_runtime.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/docs/policies.md
  tests/devcovenant/builtin/policies/dependency_management/\
    test_dependency_lock_runtime.py

- 2026-03-25:
  Change: removed rebuild-in-publish behavior and wired publish to download,
  verify, and release the exact previously validated Build artifact.
  Why: closed the external-audit provenance gap where `publish.yml` could
  upload a fresh dist that the normal build/test path had never actually
  validated for the reviewed SHA.
  Impact: release publishing now depends on one specific successful Build run,
  verified provenance, and the exact dist artifact already proven earlier in
  CI.
  Files:
  .github/workflows/build.yml
  .github/workflows/publish.yml
  CHANGELOG.md
  PLAN.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/installation.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-25:
  Change: replaced the shallow CI artifact startup checks with real
  built-artifact lifecycle proof for wheel, sdist, and the `pipx`
  machine-install path.
  Why: closed the external-audit blocker that CI was only proving CLI startup
  instead of the documented `install -> config review -> deploy` contract.
  Impact: `Checks` and the dependent build workflow now verify that built
  artifacts can activate a repository and pass a read-only post-deploy audit
  before release automation relies on them.
  Files:
  .github/workflows/ci-and-test.yml
  .github/workflows/build.yml
  CHANGELOG.md
  PLAN.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-25:
  Change: added the core invariant descriptor YAMLs to wheel and sdist
  packaging, then corrected the dependency-management no-touch false positive
  that the packaging edit surfaced.
  Why: closed the external-audit blocker where built artifacts omitted
  `devcovenant/core/contracts/invariants/*.yaml` and could fail during
  install -> review -> deploy, while the gate was still demanding fake
  license churn even when dependency artifacts were already synchronized.
  Impact: ensured built artifacts now carry the invariant descriptors the
  runtime resolves at deploy time, packaging tests now reject that omission,
  and dependency-management now accepts already-synced compliance artifacts
  for package-manifest-only edits.
  Files:
  CHANGELOG.md
  MANIFEST.in
  PLAN.md
  devcovenant/builtin/policies/dependency_management/dependency_management.py
  pyproject.toml
  requirements.lock
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/dependency_management/\
    test_dependency_management.py
  tests/devcovenant/test_install.py

- 2026-03-25:
  Change: rewrote the active remediation roadmap around the external
  release-grade audit findings.
  Why: replaced the older mostly-complete polish plan with a focused
  blocker-first plan for artifact completeness, CI proof, publish
  provenance, lockfile semantics, and first-activation docs clarity.
  Impact: the repo now has a concrete pre-release closure plan that matches
  the current external audit verdict instead of the older internal polish
  milestones.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-25:
  Change: documented and configured a reviewed repo-specific `pip-audit`
  exception for `CVE-2026-4539`.
  Why: clarified that `pytest` currently pulls vulnerable `pygments` without
  an upstream fix release, so CI needed an explicit temporary decision.
  Impact: kept GitHub Actions green without pretending a dependency bump
  resolves an unfixable advisory.
  Files:
  CHANGELOG.md
  SECURITY.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-25:
  Change: Renamed the generated workflow's visible common-denominator label to
  `Checks`, then made the build-and-install job resolve pipx's bin directory
  before verifying the installed CLI on GitHub runners.
  Why: Removed the redundant `CI and Test / CI and Test ...` GitHub Actions
  naming and fixed the build-job failure caused by hardcoding
  `~/.local/bin/devcovenant` instead of using pipx's configured bin path.
  Impact: GitHub Actions now shows a cleaner `Checks / ...` workflow label,
  the build workflow listens to the renamed workflow correctly, and the
  installed-CLI verification step no longer depends on one runner-specific
  pipx shim location.
  Files:
  CHANGELOG.md
  .github/workflows/build.yml
  .github/workflows/ci-and-test.yml
  devcovenant/builtin/profiles/global/assets/ci-and-test.yml
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  SECURITY.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-24:
  Change: Sorted profile and policy-source discovery before refresh writes its
  tracked outputs, then added regression coverage and doc notes for that
  filesystem-order stability contract.
  Why: Fixed the Linux-only CI start-gate churn where refresh could rewrite
  generated files even though policy checks passed, because raw filesystem
  iteration order was leaking into tracked output order.
  Impact: Stabilized `gate --start` across macOS, Linux, and Windows
  filesystems, and the test suite now rejects a return to platform-dependent
  generated ordering.
  Files:
  CHANGELOG.md
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/profile_registry.py
  devcovenant/docs/architecture.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/test_refresh.py

- 2026-03-24:
  Change: Replaced the generated repo-specific CI sprawl with one
  `ci-and-test` job that carries the scanner steps and one dependent
  `build-and-install-test` job, then rewrote the owning docs and workflow
  contract checks to match that profile-driven shape.
  Why: Removed the previous compatibility-matrix, assurance, and
  `installed-cli-smoke` split because it drifted away from the intended
  two-job CI model and made the generated workflow noisier than the
  repository contract allowed.
  Impact: The generated `CI and Test` workflow now matches the requested
  structure, the public/security docs describe the same contract, and the
  profile-registry tests now reject a return to the old multi-job sprawl.
  Files:
  .github/workflows/ci-and-test.yml
  CHANGELOG.md
  PLAN.md
  SECURITY.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-24:
  Change: Closed the final store-bought QA audit by rerunning the outside-in
  checks across docs, config, registry, workflows, packaged README behavior,
  and built artifacts, then rewrote Item 6 in `PLAN.md` to record that clean
  audit result as completed roadmap state.
  Why: Completed the remaining verification work after the remediation slices
  were already done, so the repo no longer had to leave the plan parked on an
  already-resolved audit step.
  Impact: Recorded a clean final audit result, confirmed that the built sdist
  and wheel are warning-free and pass `twine check`, and moved the roadmap
  forward to release-candidate preparation as the next remaining item.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-24:
  Change: Rewrote the openings of the main package reference docs so they keep
  the explicit contract markers the test suite expects while shifting the
  reading experience back toward direct operator questions, concrete decisions,
  and lighter contract-index language.
  Why: The docs had already been structurally reduced, but several key pages
  still sounded more like administration notes than like technical references,
  and that was the last stated documentation-polish gap before the final
  audit.
  Impact: Reduced the remaining meta tone in the package docs, kept
  `contracts.md` as the stable map instead of the voice every page speaks in,
  and recorded the polish slice as completed roadmap state without weakening
  the existing documentation-contract tests.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/docs/config.md
  devcovenant/docs/contracts.md
  devcovenant/docs/policies.md
  devcovenant/docs/project_governance.md
  devcovenant/docs/registry.md

- 2026-03-24:
  Change: Rewrote Item 4 in `PLAN.md` to record the completed `pipx` install
  contract, the repo-specific installed-CLI smoke proof, and the current
  release-validation expectations that now follow from that work.
  Why: Closed the final documentation gap between the implemented install-story
  slice and the active remediation roadmap after the governed proof and
  installed-CLI validation had already landed.
  Impact: Recorded the `pipx`-first install story as completed roadmap state,
  preserved the prior install-story changelog entry directly below this one as
  required by the gate snapshot rule, and kept the plan truthful about what
  now remains before the final audit.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-24:
  Change: Standardized the public install story around `pipx`, updated the
  operator and support docs to distinguish installed-CLI use from source
  checkout development, added a repo-specific installed-CLI smoke job through
  the `devcovrepo` CI extension layer, and extended the profile-registry
  regression suite to lock that repo-specific proof into the generated CI
  contract.
  Why: Clarified the public machine-install path now that `pipx` is the
  preferred way to install DevCovenant as a CLI, kept contributor guidance
  honest about source checkout and managed-environment use, and proved the
  documented installed-CLI path without pushing Python-package assumptions back
  into the language-agnostic global workflow template.
  Impact: Added a consistent `pipx`-first install story across the README,
  installation, troubleshooting, workflow, and support surfaces, proved the
  installed CLI path in this repository's CI the same way the docs describe
  it, and strengthened the profile boundary for repo-specific CI jobs with
  registry-backed and test-backed evidence.
  Files:
  CHANGELOG.md
  README.md
  SUPPORT.md
  devcovenant/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-24:
  Change: Simplified `MANIFEST.in`, replaced implicit setuptools package-data
  scanning with explicit package-data declarations in `pyproject.toml`, fixed
  the dependency-management autofix/runtime handoff so changed package
  manifests stay reflected in the license report, refreshed those
  dependency-management artifacts after the package-manifest change, refreshed
  the tracked registry hash that records the updated policy/runtime contract,
  and completed the packaging-remediation slice across the UTC rollover on the
  final manifest, registry, docs, and test surfaces.
  Why: Removed the stale manifest rules and ambiguous package discovery that
  were still producing build warnings, while keeping the runtime docs,
  built-in profile assets, tracked package README surfaces, and synchronized
  dependency-compliance artifacts in the package contract and keeping live
  runtime state out of it, corrected the runtime handoff bug that made the
  dependency-management checker and autofixer disagree about which manifests
  the license report had to name, and recorded the active post-midnight
  continuation of the same packaging work under the current UTC day.
  Impact: `python -m build` now completes quietly, the wheel content contract
  stays test-backed, the lock/license surfaces stay synchronized with the
  package manifest set, and the packaging slice stays traceable under the
  current gate day without displacing the pre-session top changelog entry.
  Files:
  CHANGELOG.md
  MANIFEST.in
  PLAN.md
  devcovenant/builtin/policies/dependency_management/autofix/global.py
  devcovenant/builtin/policies/dependency_management/dependency_lock_runtime.py
  devcovenant/builtin/policies/dependency_management/dependency_management.py
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  licenses/THIRD_PARTY_LICENSES.md
  pyproject.toml
  requirements.lock
  tests/devcovenant/builtin/policies/dependency_management/autofix/\
  test_global.py
  tests/devcovenant/builtin/policies/dependency_management/\
  test_dependency_lock_runtime.py
  tests/devcovenant/test_install.py

- 2026-03-23:
  Change: Reconciled the generated config commentary with the current cleanup
  and CI contract, removed the stale hardcoded `.venv` wording, restored the
  packaged README template to an intentionally empty managed block, and added
  refresh regressions for both behaviors.
  Why: Fixed the real generator drift instead of patching the live config by
  hand, and restored the explicit design that both README surfaces keep empty
  `<!-- DEVCOV -->` blocks so DevCovenant does not inject top-of-file runtime
  prose into user-facing READMEs.
  Impact: Strengthened the generated config truth surface, documented and
  enforced the README descriptor contract, and reduced the chance that refresh
  drifts back into stale commentary or non-empty README managed blocks.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/refresh.md
  tests/devcovenant/test_refresh.py

- 2026-03-23:
  Change: Amended `PLAN.md` to insert a detailed remediation item for making
  `pipx` the explicit, validated public install path, and adjusted the
  remaining item order and validation notes around that new installation
  contract.
  Why: Clarified that the cleaner machine-level install story now needs to be
  reflected consistently in public docs, release proof, and repo-specific CI
  rather than living only as an ad hoc operational success.
  Impact: Standardized the remediation roadmap around installed-CLI
  distribution as an explicit release-quality task, so the final audit will
  not sign off before the documented `pipx` path is aligned and proven.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-23:
  Change: Updated the repo-specific `readme-sync` policy so the packaged
  README can rewrite repo-relative public links from package metadata instead
  of from a hardcoded upstream URL, and updated the owning docs for that
  package-facing contract.
  Why: Avoided hardcoded repository URLs in both runtime logic and tests so
  forks can keep their packaged README links correct by updating
  `pyproject.toml` rather than patching repo-specific policy code.
  Impact: Packaged README sync is now safer for forks, the PyPI-facing link
  strategy is clearer, and the profile/registry/policy docs now explain the
  metadata-driven contract behind that behavior.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/README.md
  devcovenant/custom/policies/readme_sync/readme_sync.py
  devcovenant/custom/policies/readme_sync/readme_sync.yaml
  devcovenant/custom/profiles/devcovrepo/assets/POLICY_MAP.yaml
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/custom/policies/readme_sync/test_readme_sync.py

- 2026-03-23:
  Change: Rewrote `PLAN.md` into a detailed pre-release remediation roadmap
  organized around the final audit findings, with explicit items for the PyPI
  README link contract, generated config comment drift, packaging warnings,
  final docs polish, renewed QA closure, and release-candidate preparation.
  Why: Clarified that the previous plan still read like a status ledger for
  already-landed stabilization work, while the repo now needs a sharp working
  document that sequences the remaining finish work before the next audit and
  release cut.
  Impact: Clarifies the remaining product-finish defects instead of restating
  earlier completed work, so the next slices can close the last gaps
  methodically and with clearer done criteria.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-23:
  Change: Replaced the old project-governance `development_stance` model with
  `maintenance_stance` plus `compatibility_policy`, updated the default stage
  and maintenance vocabularies, and rewired managed headers, registry output,
  config comments, and governance-heavy tests to the new schema.
  Why: The previous stance field was too vague to express release reality, so
  the repo needed a clearer split between lifecycle stage, current maintenance
  posture, and compatibility promise before the pre-release audit work.
  Impact: DevCovenant now renders and validates `stage`,
  `maintenance_stance`, `compatibility_policy`, and `versioning_mode`
  together, the current repo advertises `breaking-allowed` compatibility
  explicitly, and refresh migrates the managed docs and registry to that new
  governance contract.
  Files:
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  SPEC.md
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/managed_docs.py
  devcovenant/core/services/project_governance.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/project_governance.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/changelog_coverage/\
  test_changelog_coverage.py
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/flow/test_gate_changelog_helpers.py
  tests/devcovenant/core/services/test_managed_docs.py
  tests/devcovenant/core/services/test_project_governance.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_refresh.py

- 2026-03-23:
  Change: Removed hardcoded `.venv` cleanup protection, made managed
  environment cleanup protection metadata-driven, and summarized protected
  cleanup skips by root instead of dumping nested cache paths.
  Why: Fixed the cleanup contract because protection should follow the active
  managed-environment metadata rather than a Python-specific hardcode, and the
  old skip reporting was noisy enough to hide the real protected root.
  Impact: Cleanup now keeps the active managed environment safe through
  `cleanup_protected_paths` or `expected_paths`, reports protected skips as
  readable root summaries, and documents that generic cleanup boundary across
  the config, workflow, policy, profile, and architecture docs.
  Files:
  CHANGELOG.md
  devcovenant/builtin/policies/managed_environment/managed_environment.yaml
  devcovenant/builtin/policies/managed_environment/\
  managed_environment_runtime.py
  devcovenant/builtin/profiles/global/global.yaml
  devcovenant/core/flow/clean.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/services/cleanup.py
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/managed_environment/\
  test_managed_environment_runtime.py
  tests/devcovenant/core/flow/test_clean.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/services/test_cleanup.py

- 2026-03-23:
  Change: Protected the active clean run directory from log cleanup so
  `clean --logs` and `clean --all` keep their own reported run-artifact path
  alive after the command finishes.
  Why: Prevented the clean command from deleting its own summary folder,
  because the previous behavior printed a run-log path and then removed that
  same directory while cleaning log targets.
  Impact: Clean now still prunes older log runs, but it keeps the active clean
  run folder as a runtime-provided protected path and documents that artifact
  guarantee in the lifecycle and workflow docs.
  Files:
  CHANGELOG.md
  devcovenant/core/services/cleanup.py
  devcovenant/core/flow/clean.py
  tests/devcovenant/core/services/test_cleanup.py
  tests/devcovenant/core/flow/test_clean.py
  devcovenant/docs/installation.md
  devcovenant/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md

- 2026-03-23:
  Change: Fixed refresh so legacy all-empty `clean.overrides` blocks collapse
  back to `{}`, restoring profile-driven cleanup targets and making
  `clean --all` honor the active profile metadata again.
  Why: Restored the inherited cleanup lists because the generated config had
  carried a stale empty-override shape that
  silently replaced the inherited cleanup lists, so build artifacts such as
  `dist/` and `*.egg-info/` stopped matching even though the profiles already
  declared them.
  Impact: Refresh now restores the intended cleanup contract, the config/docs
  explain that cleanup targets come from active profile `clean_overlays`, and
  the regression coverage locks the normalization path in place.
  Files:
  CHANGELOG.md
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  tests/devcovenant/test_refresh.py
  devcovenant/docs/config.md
  devcovenant/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md

- 2026-03-23:
  Change: Removed the one-off `update_lock` command, dropped its
  dependency-management alias/helper surfaces, and expanded the
  `project-governance` config contract so the live config/docs spell out the
  full key and value rules directly.
  Why: Standardized dependency operations were already namespaced under
  `devcovenant policy`, but the retired wrapper still shipped, and the
  project-governance contract still required too much code/doc chasing to
  discover all allowed keys and values.
  Impact: Removed the retired wrapper path and alias from generated
  config/registry state and clarified project-governance keys and allowed
  values directly in `config.yaml` and the detailed docs, so dependency
  management now uses only
  `devcovenant policy dependency-management refresh-all`.
  Files:
  CHANGELOG.md
  devcovenant/builtin/policies/dependency_management/\
    dependency_lock_runtime.py
  devcovenant/builtin/policies/dependency_management/\
    dependency_management.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/contracts/policy.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/policy_file_scope.py
  devcovenant/core/services/registry.py
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/project_governance.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  devcovenant/update_lock.py
  tests/devcovenant/builtin/policies/dependency_management/\
    test_dependency_lock_runtime.py
  tests/devcovenant/core/services/test_policy_commands.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_update_lock.py

- 2026-03-23:
  Change: Removed `.github/dependabot.yml`, renamed the generated CI workflow
  contract from `governance-and-test` to `ci-and-test`, and updated the
  workflow/config/profile/runtime/test surfaces to use the new file, key, job,
  and display names consistently.
  Why: Corrected the remaining half-renamed CI surface and removed unsolicited
  bot-update automation so the repo keeps one explicit `ci-and-test` contract
  without leftover Dependabot or old workflow naming drift.
  Impact: Removed the remaining mixed CI naming so the repository now keeps
  one consistent `ci-and-test` workflow
  surface, no Dependabot file or doc-route residue, refreshed generated
  metadata, and tests/docs that now enforce the renamed contract end-to-end.
  Files:
  .github/dependabot.yml
  .github/workflows/build.yml
  .github/workflows/ci-and-test.yml
  .github/workflows/governance-and-test.yml
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  POLICY_MAP.md
  PROFILE_MAP.md
  SECURITY.md
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/global/assets/ci-and-test.yml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/assets/governance-and-test.yml
  devcovenant/builtin/profiles/global/global.yaml
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/profile_registry.py
  devcovenant/core/services/registry.py
  devcovenant/custom/profiles/devcovrepo/assets/POLICY_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/PROFILE_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/changelog_coverage/\
    test_changelog_coverage.py
  tests/devcovenant/builtin/policies/documentation_growth_tracking/\
    test_documentation_growth_tracking.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/test_refresh.py

- 2026-03-23:
  Change: Moved the supported-Python compatibility and assurance jobs out of
  the global generated workflow, restored the generic `CI and Tests` base, and
  documented the profile-fragment CI contract together with managed-
  environment-generic CI bootstrapping.
  Why: Corrected the boundary drift that had pushed repo-specific Python CI
  proof into the language-agnostic global workflow instead of keeping those
  extra jobs in the `devcovrepo` profile.
  Impact: Aligned ordinary repositories to a generic generated CI baseline
  while letting this repository add its compatibility matrix and assurance
  scanners through `devcovrepo`, with tests and docs now enforcing that split.
  Files:
  .github/workflows/governance-and-test.yml
  CHANGELOG.md
  .github/workflows/build.yml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/assets/governance-and-test.yml
  devcovenant/config.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  SECURITY.md
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-03-22:
  Change: Removed empty former policy directories from the working tree
  after the policy-to-core invariant migration and recorded the cleanup.
  Why: Prevented dead directory residue from confusing package audits,
  filesystem inspection, and future maintenance work.
  Impact: Left the repository layout cleaner and closer to the current
  runtime architecture without changing tracked product behavior.
  Files:
  CHANGELOG.md

- 2026-03-22:
  Change: Rewrote DevCovenant's documentation set around an operator-first
  `README.md`, merged overlapping detailed docs into a smaller reference set,
  restored the lean contract-index surfaces the package still needs, and
  expanded the live and template docs so refresh produces fuller,
  easier-to-scan pages instead of terse or fragmented ones.
  Why: Reduced documentation sprawl, title-content mismatch, dense list-driven
  formatting, and template-driven repetition while preserving the explicit
  package contract surfaces and wording the current runtime and tests still
  rely on.
  Impact: Aligned the live docs, managed doc templates, profile doc routes,
  documentation quality policy, and doc-contract tests around a smaller,
  clearer, more readable documentation architecture that future refresh and
  upgrade runs can preserve.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/policies/documentation_growth_tracking/\
    documentation_growth_tracking.yaml
  devcovenant/builtin/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/builtin/profiles/global/assets/PLAN.yaml
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/global/assets/SPEC.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/config.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/translators.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/custom/profiles/restapi/assets/docs/api.yaml
  devcovenant/custom/profiles/restapi/assets/docs/auth.yaml
  devcovenant/custom/profiles/restapi/assets/docs/errors.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/contracts.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/project_governance.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/translators.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/test_refresh.py

- 2026-03-22:
  Change: Strengthened the roadmap so managed document templates across builtin
  and relevant custom profiles must become detailed, reader-useful blueprints
  rather than terse one-pagers, and so Item 2 now retires `update_lock`
  entirely in favor of the formal namespaced policy-command surface.
  Why: Clarified that template depth is part of the
  documentation problem and that DevCovenant is not keeping backward-
  compatibility command aliases where the new standardized command contract
  already exists.
  Impact: Standardized the plan so template depth and formatting are part of
  the documentation-rebuild acceptance criteria, and removed ambiguity about
  `update_lock` by making the namespaced dependency-management commands the
  only supported direction.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-22:
  Change: Added a detailed documentation-restructure roadmap ahead of the
  final store-bought QA closure and rewrote the plan's writing-direction and
  validation expectations around operator-first entrypoints, fewer stronger
  docs, clearer topic ownership, and better readability.
  Why: The latest documentation audit showed that DevCovenant still reads as
  too fragmented, too meta, too dense, and too hard to scan even after the
  earlier external-readiness work landed.
  Impact: The roadmap now treats documentation architecture as a real
  release-blocking product concern instead of a vague polish item, and the
  final QA audit is now explicitly gated on fixing that documentation shape.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-22:
  Change: Hardened release assurance by adding CI compatibility/scanner jobs,
  CycloneDX SBOM generation, and PyPI trusted publishing while tightening
  reviewed process-boundary scanner annotations.
  Why: Raised DevCovenant's release and supply-chain posture from basic
  build/test hygiene to a more professional assurance baseline with explicit
  scanner, inventory, automation, and publish-trust contracts.
  Impact: CI now proves the supported Python range more credibly, release
  workflows emit stronger software-inventory evidence, Bandit stays useful
  instead of noisy, and publish no longer depends on a long-lived PyPI token.
  Files:
  .github/workflows/build.yml
  .github/workflows/ci-and-test.yml
  .github/workflows/publish.yml
  CHANGELOG.md
  PLAN.md
  PRIVACY.md
  SECURITY.md
  SUPPORT.md
  bandit.yaml
  devcovenant/builtin/policies/dependency_management/\
    dependency_lock_runtime.py
  devcovenant/builtin/profiles/global/assets/ci-and-test.yml
  devcovenant/cli.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/runtime/execution.py
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  devcovenant/update_lock.py
  tests/devcovenant/test_refresh.py

- 2026-03-22:
  Change: Added public `SECURITY.md`, `PRIVACY.md`, and `SUPPORT.md`
  surfaces, hardened run-log metadata redaction, and replaced runtime
  `assert`-based policy validation with explicit configuration errors.
  Why: Clarified DevCovenant's external trust posture and prevented obvious
  secret-like values from being written blindly into structured run metadata.
  Impact: Documented security, privacy, and support expectations clearly for
  operators while making structured runtime evidence safer and more explicit.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  PRIVACY.md
  SECURITY.md
  SUPPORT.md
  devcovenant/README.md
  devcovenant/builtin/policies/documentation_growth_tracking/\
    documentation_growth_tracking.py
  devcovenant/core/runtime/run_logging.py
  devcovenant/docs/policies.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/documentation_growth_tracking/\
    test_documentation_growth_tracking.py
  tests/devcovenant/core/runtime/test_run_logging.py

- 2026-03-22:
  Change: Standardized dependency-management operations by promoting core
  invariants out of policy land, converging dependency-license-sync into the
  dependency-management policy, and adding formal policy runtime-action and
  namespaced policy-command contracts.
  Why: Removed the last architectural split where DevCovenant-owned
  invariants still behaved like ordinary policies and dependency maintenance
  still depended on one-off wrapper behavior instead of one explicit
  check/autofix/command contract.
  Impact: Standardized DevCovenant's operator surface by keeping `gate` as a
  core command, surfacing core invariant metadata separately from
  `policy_state`, routing dependency mutation through autofix or explicit
  policy commands only, and providing a reusable command/runtime contract for
  future customizable policies.
  Files:
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  POLICY_MAP.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/policies/dependency_license_sync/__init__.py
  devcovenant/builtin/policies/dependency_license_sync/autofix/__init__.py
  devcovenant/builtin/policies/dependency_license_sync/autofix/global.py
  devcovenant/builtin/policies/dependency_license_sync/\
    dependency_license_sync.py
  devcovenant/builtin/policies/dependency_license_sync/\
    dependency_license_sync.yaml
  devcovenant/builtin/policies/dependency_license_sync/\
    dependency_lock_runtime.py
  devcovenant/builtin/policies/dependency_management/__init__.py
  devcovenant/builtin/policies/dependency_management/autofix/__init__.py
  devcovenant/builtin/policies/dependency_management/autofix/global.py
  devcovenant/builtin/policies/dependency_management/dependency_lock_runtime.py
  devcovenant/builtin/policies/dependency_management/dependency_management.py
  devcovenant/builtin/policies/dependency_management/dependency_management.yaml
  devcovenant/builtin/policies/devcov_integrity_guard/__init__.py
  devcovenant/builtin/policies/devcov_integrity_guard/devcov_integrity_guard.py
  devcovenant/builtin/policies/devcov_integrity_guard/\
    devcov_integrity_guard.yaml
  devcovenant/builtin/policies/devcov_structure_guard/__init__.py
  devcovenant/builtin/policies/devcov_structure_guard/devcov_structure_guard.py
  devcovenant/builtin/policies/devcov_structure_guard/\
    devcov_structure_guard.yaml
  devcovenant/builtin/policies/devflow_run_gates/__init__.py
  devcovenant/builtin/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/builtin/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/builtin/policies/managed_environment/managed_environment.yaml
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/csharp/csharp.yaml
  devcovenant/builtin/profiles/dart/dart.yaml
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/docker/docker.yaml
  devcovenant/builtin/profiles/fastapi/fastapi.yaml
  devcovenant/builtin/profiles/flutter/flutter.yaml
  devcovenant/builtin/profiles/frappe/frappe.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/global.yaml
  devcovenant/builtin/profiles/go/go.yaml
  devcovenant/builtin/profiles/java/java.yaml
  devcovenant/builtin/profiles/javascript/javascript.yaml
  devcovenant/builtin/profiles/kubernetes/kubernetes.yaml
  devcovenant/builtin/profiles/objective_c/objective_c.yaml
  devcovenant/builtin/profiles/php/php.yaml
  devcovenant/builtin/profiles/python/python.yaml
  devcovenant/builtin/profiles/ruby/ruby.yaml
  devcovenant/builtin/profiles/rust/rust.yaml
  devcovenant/builtin/profiles/swift/swift.yaml
  devcovenant/builtin/profiles/typescript/typescript.yaml
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/contracts/invariant.py
  devcovenant/core/contracts/invariants/devcov_integrity_guard.yaml
  devcovenant/core/contracts/invariants/devcov_structure_guard.yaml
  devcovenant/core/contracts/invariants/devflow_run_gates.yaml
  devcovenant/core/contracts/policy.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/services/core_invariant_block_refresh.py
  devcovenant/core/services/core_invariants.py
  devcovenant/core/services/devcov_integrity_guard.py
  devcovenant/core/services/devcov_structure_guard.py
  devcovenant/core/services/devflow_run_gates.py
  devcovenant/core/services/managed_docs.py
  devcovenant/core/services/metadata.py
  devcovenant/core/services/policy_check_context.py
  devcovenant/core/services/policy_commands.py
  devcovenant/core/services/policy_engine.py
  devcovenant/core/services/policy_file_scope.py
  devcovenant/core/services/policy_runtime_actions.py
  devcovenant/core/services/registry.py
  devcovenant/custom/profiles/devcovrepo/assets/POLICY_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/PROFILE_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/policy.py
  devcovenant/registry/registry.yaml
  devcovenant/update_lock.py
  tests/devcovenant/builtin/policies/dependency_license_sync/__init__.py
  tests/devcovenant/builtin/policies/dependency_license_sync/autofix/\
    __init__.py
  tests/devcovenant/builtin/policies/dependency_license_sync/autofix/\
    test_global.py
  tests/devcovenant/builtin/policies/dependency_license_sync/\
    test_dependency_license_sync.py
  tests/devcovenant/builtin/policies/dependency_license_sync/\
    test_dependency_lock_runtime.py
  tests/devcovenant/builtin/policies/dependency_management/__init__.py
  tests/devcovenant/builtin/policies/dependency_management/autofix/__init__.py
  tests/devcovenant/builtin/policies/dependency_management/autofix/\
    test_global.py
  tests/devcovenant/builtin/policies/dependency_management/\
    test_dependency_lock_runtime.py
  tests/devcovenant/builtin/policies/dependency_management/\
    test_dependency_management.py
  tests/devcovenant/builtin/policies/devcov_integrity_guard/__init__.py
  tests/devcovenant/builtin/policies/devcov_integrity_guard/\
    test_devcov_integrity_guard.py
  tests/devcovenant/builtin/policies/devcov_structure_guard/__init__.py
  tests/devcovenant/builtin/policies/devcov_structure_guard/\
    test_devcov_structure_guard.py
  tests/devcovenant/builtin/policies/devflow_run_gates/__init__.py
  tests/devcovenant/builtin/policies/devflow_run_gates/\
    test_devflow_run_gates.py
  tests/devcovenant/core/contracts/test_invariant.py
  tests/devcovenant/core/services/test_core_invariant_block_refresh.py
  tests/devcovenant/core/services/test_core_invariants.py
  tests/devcovenant/core/services/test_devcov_integrity_guard.py
  tests/devcovenant/core/services/test_policy_check_context.py
  tests/devcovenant/core/services/test_devcov_structure_guard.py
  tests/devcovenant/core/services/test_devflow_run_gates.py
  tests/devcovenant/core/services/test_metadata.py
  tests/devcovenant/core/services/test_policy_commands.py
  tests/devcovenant/core/services/test_policy_engine.py
  tests/devcovenant/core/services/test_policy_runtime_actions.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_policy.py

- 2026-03-22:
  Change: Completed the public package and compliance baseline slice by
  tightening buyer-facing package metadata, documenting the public package
  surface more explicitly, and marking PLAN Item 1 complete.
  Why: Clarified the last remaining Item 1 package-contract work so the built
  package metadata reads more intentionally and the completed baseline is
  recorded clearly.
  Impact: Improved the distributed package metadata and packaging contract
  clarity while closing the first external-readiness roadmap item.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/docs/installation.md
  licenses/THIRD_PARTY_LICENSES.md
  pyproject.toml

- 2026-03-22:
  Change: Amended the active roadmap so core DevCovenant invariants are
  promoted out of policy land before the dependency-management and
  policy-command standardization work continues.
  Why: Clarified that `devflow-run-gates`, `devcov-structure-guard`, and
  `devcov-integrity-guard` define the engine's own trust boundary and should
  stay first-class core behavior rather than reading like optional policies
  or making `gate` look like a policy-born command.
  Impact: Makes the roadmap dependency-aware by treating the core invariant
  split as a prerequisite for the later dependency-management runtime and
  policy-command contract work.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-22:
  Change: Amended the active roadmap to add a formal
  dependency-management and policy-command standardization item and reorder
  the later hardening work around that dependency.
  Why: Clarified that dependency operations, autofix delegation, and
  policy-born CLI commands need one coherent contract before broader
  release-assurance work is layered on top.
  Impact: Makes the plan dependency-aware by treating
  dependency-management standardization as an explicit prerequisite for the
  later supply-chain and QA closure slices.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-22:
  Change: Aligned public project identity, package metadata synchronization,
  managed-doc rendering, dependency-license inventory generation, and the
  active external-readiness roadmap around the current store-bought baseline
  push.
  Why: Replaced the abandoned repo-specific README override path with one
  repo-owned `project-governance` identity source so public README surfaces,
  package metadata, and this repo's derived packaged README stop duplicating
  or drifting.
  Impact: Makes DevCovenant present itself from shared governance metadata,
  keeps `devcovenant/README.md` derived from the root `README.md` in this
  repository, improves public package/compliance groundwork, and records the
  remaining hardening work in a tighter release plan.
  Files:
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  CONTRIBUTING.md
  POLICY_MAP.md
  PROFILE_MAP.md
  README.md
  SPEC.md
  devcovenant/README.md
  devcovenant/builtin/policies/dependency_license_sync/\
    dependency_license_sync.py
  devcovenant/builtin/policies/dependency_license_sync/\
    dependency_lock_runtime.py
  devcovenant/builtin/policies/line_length_limit/\
    line_length_limit.yaml
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/python/assets/pyproject.toml
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/managed_docs.py
  devcovenant/core/services/project_governance.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/project_governance.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  licenses/PyYAML-6.0.2.txt
  licenses/PyYAML-6.0.3.txt
  licenses/README.md
  licenses/THIRD_PARTY_LICENSES.md
  licenses/packaging-26.0.txt
  licenses/pip-tools-7.5.3.txt
  licenses/pre-commit-4.5.1.txt
  licenses/pytest-9.0.2.txt
  licenses/semver-3.0.2.txt
  licenses/semver-3.0.4.txt
  pyproject.toml
  tests/devcovenant/builtin/policies/dependency_license_sync/\
    autofix/test_global.py
  tests/devcovenant/builtin/policies/dependency_license_sync/\
    test_dependency_license_sync.py
  tests/devcovenant/builtin/policies/dependency_license_sync/\
    test_dependency_lock_runtime.py
  tests/devcovenant/core/services/test_managed_docs.py
  tests/devcovenant/core/services/test_project_governance.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py

- 2026-03-21:
  Change: Rewrote the active roadmap into a tight external-readiness plan
  focused on package polish, compliance accuracy, security and privacy trust
  surfaces, and stronger release assurance.
  Why: A fresh third-party-style QA audit showed that DevCovenant is
  technically serious but still not polished enough to feel fully
  store-bought.
  Impact: Reorients the next work slices around the real release blockers:
  public package presentation, legal and license correctness, trust-surface
  docs, supply-chain hardening, and a final outside-in QA closure pass.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-21:
  Change: Froze the simplified product contracts through a new contract
  index, tightened the primary docs into explicit normative homes, added
  direct contract tests, and marked PLAN Item 4 complete.
  Why: The runtime and docs were simpler after the earlier cleanup work, so
  the right next step was to centralize contract truth without creating a
  second fragmented documentation tree.
  Impact: Made the managed-doc, lifecycle, workflow, config,
  project-governance, registry, policy-descriptor, version-governance
  adapter, and documentation-writing contracts explicit, linked, and
  test-backed.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/contracts.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/project_governance.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/services/test_managed_docs.py
  tests/devcovenant/core/services/test_policy_block_refresh.py

- 2026-03-21:
  Change: Simplified the docs information architecture around clearer
  primary homes, slimmed the README entrypoint, simplified documentation
  route fan-out, and marked PLAN Item 3 complete.
  Why: Clarified doc ownership because the README was carrying too much deep
  reference material, several reference docs were repeating workflow/setup
  framing, and some documentation routes were forcing the same change into
  multiple docs by default.
  Impact: Reduced duplicate doc churn by making the README and packaged
  README clearer entrypoints, making the detailed docs state their ownership
  boundaries more explicitly, and simplifying the default route map.
  Files:
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/config.yaml
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/project_governance.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml

- 2026-03-21:
  Change: Reduced repeated cold setup in the slow refresh, deploy, upgrade,
  and managed-doc test families, kept the two standard test runs intact, and
  marked PLAN Item 2 complete.
  Why: Several heavy integration-style tests copied and refreshed the same
  install-and-refresh baseline repeatedly instead of reusing safe cached repo
  seeds, which had made the standard workflow slow.
  Impact: Cut the measured hotspot pytest subset from about `238.55s` to
  about `198.86s`, dropped the managed-doc-assets policy tests to sub-second
  checks, and preserved one explicit colder upgrade path so lifecycle proof
  remains visible.
  Files:
  CHANGELOG.md
  PLAN.md
  tests/devcovenant/custom/policies/managed_doc_assets/\
    test_managed_doc_assets.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_upgrade.py

- 2026-03-21:
  Change: Added a shared run-scoped YAML cache, rewired the hot command
  paths through it, documented the new runtime-loading ownership, and marked
  PLAN Item 1 complete.
  Why: Repeated tracked config, registry, profile, and descriptor parsing had
  become the main structural cause of slow `check`, gate, and refresh-related
  startup work.
  Impact: Reduced counted `yaml.safe_load` calls during `check` from `77` to
  `38`, cut local `check` runtime from about `14.35s` to `9.02s`, cut local
  `pre-commit run --all-files --verbose` runtime from about `28.01s` to
  `20.81s`, and left one explicit cache boundary for future runtime work.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/builtin/policies/devcov_structure_guard/\
    devcov_structure_guard.py
  devcovenant/builtin/policies/managed_environment/\
    managed_environment_runtime.py
  devcovenant/core/flow/gate_changelog_helpers.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/runtime/session_snapshot.py
  devcovenant/core/services/cleanup.py
  devcovenant/core/services/event.py
  devcovenant/core/services/managed_docs.py
  devcovenant/core/services/metadata.py
  devcovenant/core/services/policy_block_refresh.py
  devcovenant/core/services/policy_engine.py
  devcovenant/core/services/policy_runtime_actions.py
  devcovenant/core/services/profile_registry.py
  devcovenant/core/services/project_governance.py
  devcovenant/core/services/registry.py
  devcovenant/core/services/yaml_cache.py
  devcovenant/deploy.py
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/install.py
  devcovenant/registry/registry.yaml
  devcovenant/undeploy.py
  tests/devcovenant/core/services/test_yaml_cache.py

- 2026-03-21:
  Change: Rewrote `PLAN.md` into a dependency-ordered anti-fragmentation and
  performance-remediation roadmap that focuses first on command speed, test
  runtime, and documentation structure before freezing contracts.
  Why: Needed the active plan to reflect the real current bottlenecks so the
  next work removes structural slowness and documentation sprawl before
  formalizing the resulting contracts.
  Impact: Clarified the roadmap now starts with runtime loading reduction,
  test-runtime reduction, and documentation architecture cleanup, then
  freezes the simplified product contracts on top of that cleaner baseline.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-21:
  Change: Rewrote `PLAN.md` into a detailed contract-formalization roadmap
  that defines the next contract-freezing program across managed docs,
  config, registry, policies, version adapters, and gates.
  Why: Needed one dependency-ordered plan that turns implemented behavior
  into explicit normative contracts instead of leaving product surfaces
  scattered across code, comments, and habit.
  Impact: Clarified the next roadmap now gives each contract area a concrete
  goal, rationale, task list, and completion check so future work can
  freeze behavior deliberately instead of by drift.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-21:
  Change: Rewrote the live `PLAN.md` into the current detailed roadmap
  standard and rewrote the completed items so they read like completed work
  instead of half-finished planning notes.
  Why: Kept the real plan aligned with the stronger template and made the
  roadmap readable as a finished program record rather than a mixed planning
  artifact.
  Impact: Clarified `PLAN.md` now presents one consistent completed-roadmap
  contract that is easier to review, extend, and use as the manual
  harmonization baseline for future plans.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-21:
  Change: Updated the `PLAN.md` and `SPEC.md` templates into durable detailed
  scaffolds, tracked body-only managed-doc fingerprints in the registry, and
  enabled exact replacement of known old generic document bodies.
  Why: Let managed docs upgrade from older generic scaffolds without risking
  authored content, while making template behavior auditable and keeping
  generated header changes out of template matching.
  Impact: Enabled repositories to refresh old generic `PLAN.md` /
  `SPEC.md` scaffolds into stronger templates, preserve real authored docs,
  and inspect the managed-doc fingerprint contract in the tracked registry.
  Files:
  CHANGELOG.md
  SPEC.md
  devcovenant/builtin/profiles/global/assets/PLAN.yaml
  devcovenant/builtin/profiles/global/assets/SPEC.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/managed_docs.py
  devcovenant/core/services/registry.py
  devcovenant/docs/architecture.md
  devcovenant/docs/profiles.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_managed_docs.py
  tests/devcovenant/test_refresh.py

- 2026-03-21:
  Change: Expanded the main docs with clearer reader guidance, rewrote key
  sections in more practical language, and aligned the top-level README with
  the product name.
  Why: Made the docs work as both quick operator references and teaching
  material so readers can understand what to do, when to do it, and why the
  workflow exists.
  Impact: Clarified users can now choose the right doc faster, understand the
  install/config/workflow/governance relationships more easily, and operate
  DevCovenant with less insider knowledge.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/project_governance.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md

- 2026-03-21:
  Change: Expanded the initial integration and bootstrap docs, clarified
  `install.config_reviewed`, and rewrote install/config/workflow guidance in
  more practical language.
  Why: Explained empty-repo, seeded-doc, and existing-repo startup paths
  concretely so first-time users can understand what DevCovenant is doing
  and why deploy is blocked until config review is complete.
  Impact: Clarified repositories now have clearer install, config, and
  workflow docs that teach the activation model, the first gate cycle, and
  the bootstrap
  preservation rules without insider shorthand.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/config.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md

- 2026-03-20:
  Change: Added active-profile managed-doc descriptor resolution, enabled
  optional builtin docs and custom managed docs through `doc_assets`, and
  added `PROFILE_MAP.md` / `POLICY_MAP.md` as custom managed docs from the
  `devcovrepo` profile.
  Why: Supported repository-specific managed docs without forcing new
  hardcoded document paths or keeping builtin docs permanently mandatory.
  Impact: Repositories can now turn builtin managed docs off intentionally,
  add profile-owned managed docs through descriptors, and keep the same
  preservation rules across builtin and custom documents.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  POLICY_MAP.md
  PROFILE_MAP.md
  devcovenant/README.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/managed_docs.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.yaml
  devcovenant/custom/profiles/devcovrepo/assets/POLICY_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/PROFILE_MAP.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_managed_docs.py
  tests/devcovenant/custom/policies/managed_doc_assets/\
    test_managed_doc_assets.py
  tests/devcovenant/test_refresh.py

- 2026-03-20:
  Change: Refactored shared managed-doc behavior into descriptors, rewired the
  common doc engine and managed-doc-assets checks to read those descriptor
  flags, and kept AGENTS as the one explicit multi-block special case.
  Why: Stopped document behavior from depending on scattered hardcoded
  assumptions while avoiding the wrong abstraction of pretending every doc
  can or should behave like AGENTS.
  Impact: Aligned ordinary managed docs around one descriptor-driven
  contract for headers, seed import, and authoritative asset sync, while
  AGENTS keeps its
  dedicated workflow, policy, and governance layout without polluting the
  common engine.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/core/services/managed_docs.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.yaml
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/global/assets/PLAN.yaml
  devcovenant/builtin/profiles/global/assets/SPEC.yaml
  devcovenant/builtin/profiles/global/assets/CHANGELOG.yaml
  devcovenant/builtin/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/builtin/profiles/global/assets/LICENSE.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_managed_docs.py
  tests/devcovenant/test_refresh.py

- 2026-03-20:
  Change: Refactored managed-doc descriptor loading, seed adoption,
  preservation, and managed header/block rendering in one shared runtime
  service and rewired refresh/install/doc-asset checks to use it.
  Why: Removed the spread-out document-engine ownership that made managed
  docs harder to reason about and easier to drift across refresh, install,
  and integrity-check paths.
  Impact: Made managed-doc behavior easier to maintain by giving it one core
  owner, added direct service coverage, and recorded the completed service
  extraction in the active plan and architecture docs.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/core/services/managed_docs.py
  devcovenant/core/flow/refresh.py
  devcovenant/install.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/services/test_managed_docs.py
  tests/devcovenant/custom/policies/managed_doc_assets/\
    test_managed_doc_assets.py

- 2026-03-20:
  Change: Clarified Item 1 wording so `developer_mode`,
  `config_reviewed`, and normal-repo cleanup behavior now describe real repo
  usage in plain language.
  Why: Removed insider shorthand and corrected unclear config comments so a
  reader can tell when DevCovenant is being used as a tool versus when a
  repository is being used to develop DevCovenant itself.
  Impact: Made the config comments, install/workflow docs, and deploy test
  coverage more concrete by explaining repo-only development paths and by
  proving that normal repos prune only the intended DevCovenant-only files.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/config.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/deploy.py
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  tests/devcovenant/test_deploy.py

- 2026-03-20:
  Change: Rewrote `PLAN.md` into a fuller roadmap that keeps the same active
  tasks while making the direction more concrete, practical, and
  de-insider-ized.
  Why: Clarified that the next work is not just about shipping features, but
  also about rewriting config comments and docs so learning users can
  understand what DevCovenant is doing and when to use each concept.
  Impact: Expanded the active plan into a more detailed guide for the
  managed-docs service, descriptor-driven docs, optional docs, clearer
  bootstrap docs, and a broader teaching-quality documentation rewrite.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-20:
  Change: Finalized `developer_mode` and `install.config_reviewed`,
  documented the reviewed-true bootstrap contract, and marked Item 1 done in
  `PLAN.md`.
  Why: Preserved the pre-session rename entry while landing the final
  reviewed-true semantics and the route-doc updates required by the gate.
  Impact: Clarified that install now seeds `config_reviewed: false`, deploy
  now requires `config_reviewed: true`, and the workflow/profile docs explain
  the initial integration contract more clearly.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/deploy.py
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  devcovenant/install.py
  devcovenant/upgrade.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_install.py

- 2026-03-20:
  Change: Renamed `devcov_core_include` to `developer_mode` and
  `install.generic_config` to `install.config_review_pending` across runtime,
  config templates, docs, and tests.
  Why: Made the initial integration and self-hosting scope contract explicit
  instead of relying on vague or implementation-shaped names.
  Impact: Clarified bootstrap review flow, made developer-vs-user repo scope
  more understandable, and removed the old key names from the live runtime
  surface.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/policy_file_scope.py
  devcovenant/deploy.py
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/project_governance.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/install.py
  devcovenant/upgrade.py
  tests/devcovenant/core/services/test_policy_engine.py
  tests/devcovenant/core/services/test_policy_file_scope.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_install.py

- 2026-03-20:
  Change: Rewrote the active roadmap in `PLAN.md` around developer-mode
  naming, the managed-docs service, descriptor-driven docs, optional/custom
  managed docs, bootstrap clarity, and fuller teaching-oriented docs.
  Why: Clarified the next implementation program so the repo can move from
  recent governance fixes into the larger documentation and doc-engine
  architecture work without carrying stale cleanup-era planning.
  Impact: Defined a concrete six-item forward plan that now governs the next
  development slices for config naming, managed docs, doc descriptors,
  optional docs, bootstrap guidance, and documentation depth.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-20:
  Change: Expanded first-use abbreviations across repo docs, managed doc
  assets, and synced README surfaces.
  Why: Enforced the documentation rule that each document must decipher an
  abbreviation on first use instead of assuming reader familiarity.
  Impact: Improved readability and consistency across the README, AGENTS,
  CONTRIBUTING, reference docs, and self-hosting doc assets.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PROFILE_MAP.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md

- 2026-03-20:
  Change: Documented `project-governance` as a first-class service in the
  README surfaces, dedicated docs, and supporting reference docs.
  Why: Clarified where operators configure lifecycle metadata, how it
  relates to `version-governance`, and where its resolved state surfaces.
  Impact: Clarifies the full project-governance contract so readers can
  follow its config, registry, AGENTS, and changelog behavior without
  reconstructing it from scattered notes.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/project_governance.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md

- 2026-03-20:
  Change: Refactored `project-governance` into a core service, exposed it
  directly in config and registry state, and rendered its resolved state in
  managed doc surfaces instead of the policy block.
  Why: Defined one repo-owned runtime source for lifecycle metadata so
  AGENTS, SPEC, PLAN, and CHANGELOG can read one resolved source without
  treating project state as a normal policy toggle.
  Impact: Keeps project governance out of the policy registry, makes config
  ownership explicit, adds the AGENTS governance section, and preserves the
  same lifecycle rendering across managed docs.
  Files:
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  devcovenant/builtin/policies/changelog_coverage/changelog_coverage.py
  devcovenant/builtin/policies/project_governance/__init__.py
  devcovenant/builtin/policies/project_governance/project_governance.py
  devcovenant/builtin/policies/project_governance/project_governance.yaml
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/CHANGELOG.yaml
  devcovenant/builtin/profiles/global/assets/PLAN.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/config.yaml
  devcovenant/core/flow/gate_changelog_helpers.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/project_governance.py
  devcovenant/core/services/registry.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/project_governance/__init__.py
  tests/devcovenant/builtin/policies/changelog_coverage/\
    test_changelog_coverage.py
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/flow/test_gate_changelog_helpers.py
  tests/devcovenant/builtin/policies/project_governance/\
    test_project_governance.py
  tests/devcovenant/core/services/test_project_governance.py
  tests/devcovenant/test_refresh.py

- 2026-03-20:
  Change: Closed Item 3 in `PLAN.md`, fixed the final `version-sync`
  equality seam for format-only schemes, and aligned the routed docs for the
  closeout pass.
  Why: Defined a strict equality path for `version-sync` because
  `custom_regex` should stay format-only and should not pretend ordered
  progression exists.
  Impact: Keeps the final cleanup closure traceable, keeps format-only
  schemes synchronized without fake ordering, and records the routed-doc
  updates for this gate session.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/builtin/policies/version_sync/version_sync.py
  devcovenant/docs/architecture.md
  devcovenant/docs/policies.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml

- 2026-03-20:
  Change: Tightened Item 3 strictness by removing misleading fallback-style
  naming, replacing the fake `custom_regex` ordering path with an explicit
  error, and cleaning stale removed/unsupported wording.
  Why: Reduced the last naming noise that still made strict default
  resolution or rejected old shapes read like compatibility behavior.
  Impact: Clarified strict runtime behavior, kept docs aligned with the real
  default-resolution model, and prepared the final anti-bullshit closure
  audit.
  Files:
  CHANGELOG.md
  devcovenant/builtin/policies/README.md
  devcovenant/builtin/policies/modules_need_tests/modules_need_tests.py
  devcovenant/builtin/policies/no_print_outside_output_runtime/\
    no_print_outside_output_runtime.py
  devcovenant/builtin/policies/raw_string_escapes/raw_string_escapes.py
  devcovenant/builtin/policies/tests_coverage/tests_coverage.py
  devcovenant/builtin/policies/version_governance/custom_regex.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/lib/selectors.py
  devcovenant/docs/architecture.md
  devcovenant/docs/policies.md
  devcovenant/docs/workflow.md
  tests/devcovenant/builtin/policies/changelog_coverage/\
    test_changelog_coverage.py
  tests/devcovenant/builtin/policies/version_governance/test_custom_regex.py
  tests/devcovenant/core/services/test_metadata.py
  tests/devcovenant/core/services/test_policy_check_runner.py

- 2026-03-20:
  Change: Aligned the remaining Item 2 docs and policy wording around
  version-governance defaults, README ownership, and managed-doc asset sync.
  Why: Removed repo-specific product wording, made the root README versus
  packaged README contract explicit, and aligned managed-doc-assets text with
  its real synchronization role.
  Impact: Clarified the documentation contract, aligned policy prose with
  runtime behavior, and closed Item 2 in `PLAN.md`.
  Files:
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.yaml
  devcovenant/custom/policies/readme_sync/readme_sync.yaml
  devcovenant/README.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml

- 2026-03-20:
  Change: Restored explicit managed blocks for `PLAN.md` and `SPEC.md`
  through their global doc assets and refresh coverage.
  Why: Corrected the drift where only `README.md` was supposed to keep an
  intentionally empty managed block, while `PLAN.md` and `SPEC.md` should
  still render managed identity content.
  Impact: Restored non-empty managed blocks to `PLAN.md` and `SPEC.md`,
  proved the behavior in tests, and kept the root `README.md` as the only
  intentionally empty managed block.
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
  devcovenant/builtin/profiles/global/assets/PLAN.yaml
  devcovenant/builtin/profiles/global/assets/SPEC.yaml
  devcovenant/docs/profiles.md
  tests/devcovenant/test_refresh.py

- 2026-03-19:
  Change: Refined the remaining plan items so the closure path now focuses
  on docs-and-contract harmonization first, then strictness, naming, and
  final anti-bullshit closure.
  Why: Narrowed the roadmap to the exact cleanup still left after the latest
  audit and the README-model clarification for this repo.
  Impact: `PLAN.md` now states the real remaining release-readiness work
  without extra scope or implied redesign.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-19:
  Change: Corrected managed-doc rendering so empty managed blocks keep
  their `<!-- DEVCOV:BEGIN -->` / `<!-- DEVCOV:END -->` markers and
  restored the strict replacement path for older DevCovenant-shaped docs.
  Why: Corrected an intentionally blank root `README.md` managed block that
  had been collapsed into no block at all, and fixed the first pass that
  briefly let older SPEC seeds preserve body text that should be replaced.
  Impact: Preserved explicit empty managed blocks in `README.md` and
  `PLAN.md`, restored strict replacement for older seeded docs, and
  covered the exact behavior in refresh tests.
  Files:
  CHANGELOG.md
  devcovenant/core/flow/refresh.py

- 2026-03-19:
  Change: Restored `PLAN.md` as a real repo roadmap and fixed refresh so
  existing non-empty, non-one-line docs keep their authored body while only
  managed headers and explicit managed blocks are synchronized, including
  empty managed blocks that must keep their markers.
  Why: Prevented `PLAN.md` from staying on a bad full-replacement path, which
  violated the agreed document rules for refresh/install/deploy/upgrade
  behavior and had also collapsed an intentionally empty root `README.md`
  managed block into no block at all.
  Impact: Existing authored docs now survive refresh correctly, the exact
  document rules are recorded in the plan and docs, `PLAN.md` no longer
  collapses back to placeholder content on sync, and root `README.md`
  keeps an empty managed block with its markers intact.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  tests/devcovenant/test_refresh.py

- 2026-03-19:
  Change: Hardened source-checkout startup so Python cache files no longer
  linger in the repo and restored the audit remediation plan to the real
  three-slice Item 1/2/3 closure path.
  Why: The anti-bullshit audit still found live repo drift from
  `devcovenant/__pycache__`, and the routed docs needed to say clearly that
  source imports now clean their own package cache as part of that fix.
  Impact: Source imports now clean their own package cache on exit, the live
  cache drift repro is closed, and the plan again tracks the remaining strict
  follow-up work truthfully.
  Files:
  CHANGELOG.md
  devcovenant/__init__.py
  devcovenant/cli.py
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/runtime/execution.py
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/test_cli.py

- 2026-03-19:
  Change: Rewrote the active plan into a condensed remediation roadmap for
  the anti-bullshit audit findings.
  Why: Focus follow-up work on the live cache/runtime defect first, then
  clean the remaining naming and strictness noise without adding fallback
  pathways.
  Impact: The current roadmap now closes the audit in three explicit slices
  instead of leaving placeholder plan items.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-19:
  Change: Added install-time adoption for compatible pre-authored
  DevCovenant-managed docs and documented seeded `SPEC.md`, `README.md`,
  and `PLAN.md` startup flows.
  Why: Preserve DevCovenant-shaped starter docs created before install so
  fresh repositories can begin from authored planning/spec content instead
  of losing it during first bootstrap.
  Impact: `install` now records importable managed docs for first-refresh
  adoption, while docs and tests cover the seeded-doc workflow clearly.
  Files:
  CHANGELOG.md
  CONTRIBUTING.md
  README.md
  devcovenant/README.md
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  devcovenant/install.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_refresh.py

- 2026-03-19:
  Change: Removed the fake `0.0.0` project-version fallback, made fresh
  installs explicitly unversioned, and rendered project-governance headers
  in `SPEC.md` when the descriptor opts in.
  Why: Prevented refresh from inventing numbered versions for repos with no
  declared version and aligned the generic install baseline with the new
  project-governance contract.
  Impact: Aligned fresh installs to refresh truthfully as unversioned repos,
  start `CHANGELOG.md` with `## Unreleased` in that baseline, and surface
  lifecycle headers consistently in opted-in managed docs.
  Files:
  CHANGELOG.md
  PLAN.md
  SPEC.md
  devcovenant/builtin/policies/project_governance/project_governance.py
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/CHANGELOG.yaml
  devcovenant/builtin/profiles/global/assets/PLAN.yaml
  devcovenant/builtin/profiles/global/assets/SPEC.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/project_governance/\
    test_project_governance.py
  tests/devcovenant/test_refresh.py

- 2026-03-19:
  Change: Disabled Python cache-file writes for source-checkout
  `python3 -m devcovenant ...` launches and updated the source-run docs.
  Why: Prevented repo-local `__pycache__/` drift from the launcher process
  instead of asking operators to wrap source runs with shell env workarounds.
  Impact: Source runs now stay cache-clean by default while managed child
  Python commands keep their explicit routing controls.
  Files:
  CHANGELOG.md
  devcovenant/__init__.py
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  tests/devcovenant/test_cli.py

- 2026-03-19:
  Change: Closed the version-stack roadmap with a local-only Item 5 audit
  and proof pass.
  Why: Confirmed the remaining repo surfaces were already aligned and only
  the roadmap still carried an unnecessary downstream-proof requirement.
  Impact: Keeps the active plan consistent with the actual local closure
  scope for this completed version-stack program.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  devcovenant/README.md

- 2026-03-18:
  Change: Split `version-governance` into generic forward-ordering checks
  plus scheme-owned canonicalization and release-marker governance.
  Why: Needed Item 4 to keep SemVer-specific bump language contained while
  giving PEP 440 and future adapters explicit extension points for their
  own marker semantics.
  Impact: Enabled canonical version enforcement where schemes define it,
  added PEP 440 prerelease/dev/post-release controls, and kept non-SemVer
  schemes free from inherited major/minor/patch rules.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/builtin/policies/version_governance/calver.py
  devcovenant/builtin/policies/version_governance/custom_adapter.py
  devcovenant/builtin/policies/version_governance/custom_regex.py
  devcovenant/builtin/policies/version_governance/integer.py
  devcovenant/builtin/policies/version_governance/pep440.py
  devcovenant/builtin/policies/version_governance/semver.py
  devcovenant/builtin/policies/version_governance/version_governance.py
  devcovenant/builtin/policies/version_governance/version_governance.yaml
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  tests/devcovenant/builtin/policies/version_governance/\
    test_calver.py
  tests/devcovenant/builtin/policies/version_governance/\
    test_custom_adapter.py
  tests/devcovenant/builtin/policies/version_governance/\
    test_custom_regex.py
  tests/devcovenant/builtin/policies/version_governance/\
    test_integer.py
  tests/devcovenant/builtin/policies/version_governance/\
    test_pep440.py
  tests/devcovenant/builtin/policies/version_governance/\
    test_version_governance.py

- 2026-03-18:
  Change: Introduced orthogonal `project-governance` lifecycle
  governance and wired managed headers plus changelog heading resolution
  through it.
  Why: Needed a first-class way to govern project stage and intentionally
  unversioned lifecycle state without overloading `version-governance`
  or forcing fake numbered versions.
  Impact: Enabled repositories to keep `project-governance` alongside
  `version-governance`, render richer AGENTS-only governance headers,
  and use explicit non-version labels with `## Unreleased` when they are
  intentionally unversioned.
  Files:
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  devcovenant/builtin/policies/project_governance/__init__.py
  devcovenant/builtin/policies/project_governance/project_governance.py
  devcovenant/builtin/policies/project_governance/project_governance.yaml
  devcovenant/builtin/policies/changelog_coverage/changelog_coverage.py
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/config.yaml
  devcovenant/core/flow/gate_changelog_helpers.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/lib/document_exemptions.py
  devcovenant/custom/policies/managed_doc_assets/\
    managed_doc_assets.py
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/project_governance/__init__.py
  tests/devcovenant/builtin/policies/project_governance/\
    test_project_governance.py

- 2026-03-18:
  Change: Rewrote Item 3 in `PLAN.md` around an orthogonal
  `project-governance` policy instead of a mutually exclusive pre-version
  identity mode.
  Why: Clarified how project run, development stance, and intentionally
  unversioned repos should be governed without overloading
  `version-governance`.
  Impact: Planned a cleaner lifecycle model where `project-governance` can
  coexist with `version-governance`, `AGENTS.md` carries richer governance
  headers, and unversioned repos use explicit non-version labels plus
  `## Unreleased`.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PLAN.md
  README.md
  devcovenant/README.md

- 2026-03-17:
  Change: Added role-scoped package legality enforcement to
  `version-sync` and wired Python package manifests to PEP 440 legality.
  Why: Prevented ecosystem legality from inheriting repo-level scheme
  flexibility so custom governed schemes cannot allow illegal packaging
  metadata.
  Impact: Enforced PEP 440 validation for Python manifests under
  `version-sync` and defined an explicit `role_legality_schemes`
  extension path for future ecosystems.
  Files:
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  devcovenant/builtin/policies/version_governance/version_governance.py
  devcovenant/builtin/policies/version_sync/version_sync.py
  devcovenant/builtin/policies/version_sync/version_sync.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/python/python.yaml
  devcovenant/config.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/version_governance/\
    test_version_governance.py
  tests/devcovenant/builtin/policies/version_sync/test_version_sync.py

- 2026-03-17:
  Change: Standardized explicit version-governance scheme selection and
  clarified version-stack wording across defaults, docs, and upgrade
  runtime.
  Why: Removed hidden SemVer baseline assumptions from shared defaults so
  version readers inherit scheme semantics only from explicit repo
  metadata.
  Impact: Made generic profiles scheme-neutral, kept this repo's SemVer
  choice explicit in `devcovrepo`, and clarified that upgrade's SemVer
  comparison concerns DevCovenant package versions rather than governed
  repo versions.
  Files:
  AGENTS.md
  CHANGELOG.md
  PLAN.md
  POLICY_MAP.md
  devcovenant/builtin/policies/version_governance/version_governance.py
  devcovenant/builtin/policies/version_governance/version_governance.yaml
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  devcovenant/upgrade.py
  tests/devcovenant/builtin/policies/version_governance/\
    test_version_governance.py
  tests/devcovenant/test_upgrade.py

- 2026-03-17:
  Change: Replaced the completed registry-layout roadmap with a new
  version-stack roadmap in `PLAN.md`.
  Why: Defined the remaining future-facing work after the
  `version-governance` framework and `version-sync` integration exposed
  package-legality, pre-version-identity, and final SemVer-sweep needs.
  Impact: Sequenced DevCovenant's next version-stack program so future
  slices can finish scheme-neutral version governance without
  reintroducing SemVer assumptions or overloading versions with
  codename-only repo identity.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-16:
  Change: Refactored `version-sync` to delegate version parsing and
  equality to `version-governance` and replaced the old SemVer-only
  doc/legal extractor model with `project_version_line`.
  Why: Unified version semantics under one policy framework so synced
  docs, changelog, manifests, and legal text can follow non-SemVer
  schemes without parallel parsing rules.
  Impact: Enabled scheme-aware version-sync behavior across SemVer,
  CalVer, PEP 440, and custom schemes, and synchronized the generated
  policy/config/registry surfaces to the new extractor contract.
  Files:
  AGENTS.md
  CHANGELOG.md
  devcovenant/builtin/policies/version_governance/version_governance.py
  devcovenant/builtin/policies/version_sync/version_sync.py
  devcovenant/builtin/policies/version_sync/version_sync.yaml
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/config.yaml
  devcovenant/core/services/metadata.py
  devcovenant/docs/architecture.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/version_governance/\
    test_version_governance.py
  tests/devcovenant/builtin/policies/version_sync/test_version_sync.py

- 2026-03-16:
  Change: Added `custom_regex` and `custom_adapter` scheme support to
  `version-governance` and extended the shared adapter contract for
  repo-local version logic.
  Why: Enabled governed repositories to validate exotic version formats
  and define repo-local ordering rules without weakening the core
  version-governance framework.
  Impact: Enabled format-only custom regex validation, repo-relative
  custom adapter modules exporting `SCHEME`, and Roman-numeral-style
  coverage in the version-governance test suite.
  Files:
  AGENTS.md
  CHANGELOG.md
  devcovenant/builtin/policies/version_governance/calver.py
  devcovenant/builtin/policies/version_governance/custom_adapter.py
  devcovenant/builtin/policies/version_governance/custom_regex.py
  devcovenant/builtin/policies/version_governance/integer.py
  devcovenant/builtin/policies/version_governance/pep440.py
  devcovenant/builtin/policies/version_governance/semver.py
  devcovenant/builtin/policies/version_governance/version_governance.py
  devcovenant/builtin/policies/version_governance/version_governance.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/version_governance/\
    test_calver.py
  tests/devcovenant/builtin/policies/version_governance/\
    test_custom_adapter.py
  tests/devcovenant/builtin/policies/version_governance/\
    test_custom_regex.py
  tests/devcovenant/builtin/policies/version_governance/\
    test_integer.py
  tests/devcovenant/builtin/policies/version_governance/test_pep440.py
  tests/devcovenant/builtin/policies/version_governance/test_semver.py
  tests/devcovenant/builtin/policies/version_governance/\
    test_version_governance.py

- 2026-03-16:
  Change: Added first-class `pep440` scheme support to
  `version-governance` and wired Python-package version parsing into the
  scheme registry.
  Why: Enabled governed Python repos to validate PEP 440 versions
  directly instead of approximating Python packaging rules through other
  schemes.
  Impact: Enabled repositories to set
  `version-governance.scheme: pep440`, validate prerelease/package
  versions such as `1.2.0rc1`, and keep dependency manifests, lockfiles,
  and license reporting aligned with the new runtime dependency.
  Files:
  AGENTS.md
  CHANGELOG.md
  devcovenant/builtin/policies/version_governance/pep440.py
  devcovenant/builtin/policies/version_governance/version_governance.py
  devcovenant/builtin/policies/version_governance/version_governance.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  licenses/THIRD_PARTY_LICENSES.md
  pyproject.toml
  requirements.in
  requirements.lock
  tests/devcovenant/builtin/policies/version_governance/test_pep440.py
  tests/devcovenant/builtin/policies/version_governance/\
    test_version_governance.py

- 2026-03-16:
  Change: Refactored `version-governance` into a shared policy shell with
  separate SemVer, CalVer, and integer scheme adapters.
  Why: Standardized the internal framework so new versioning schemes can be
  added without growing one monolithic policy script.
  Impact: Documented the adapter architecture, added direct scheme-module
  tests, and synchronized registry evidence for the modular policy layout.
  Files:
  AGENTS.md
  CHANGELOG.md
  POLICY_MAP.md
  devcovenant/builtin/policies/version_governance/__init__.py
  devcovenant/builtin/policies/version_governance/calver.py
  devcovenant/builtin/policies/version_governance/integer.py
  devcovenant/builtin/policies/version_governance/semver.py
  devcovenant/builtin/policies/version_governance/version_governance.py
  devcovenant/builtin/policies/version_governance/version_governance.yaml
  devcovenant/builtin/policies/version_sync/version_sync.yaml
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/version_governance/test_calver.py
  tests/devcovenant/builtin/policies/version_governance/test_integer.py
  tests/devcovenant/builtin/policies/version_governance/test_semver.py
  tests/devcovenant/builtin/policies/version_governance/\
    test_version_governance.py
  tests/devcovenant/builtin/policies/version_sync/test_version_sync.py

- 2026-03-16:
  Change: Added build cleanup support for unpacked release trees named like
  `<project>-<version>/` in the repo root.
  Why: Prevented source-tree package extracts from lingering beside `build/`,
  `dist/`, and `*.egg-info` after packaging validation runs.
  Impact: Expanded `clean --build` and `clean --all` so they now remove
  repo-root release trees for the repo or manifest project name while
  leaving unrelated versioned directories alone.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/core/services/cleanup.py
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/services/test_cleanup.py
  tests/devcovenant/test_clean.py

- 2026-03-16:
  Change: Replaced the SemVer-only `semantic-version-scope` policy with
  the new `version-governance` framework and added CalVer/integer support.
  Why: Expanded version enforcement so DevCovenant can govern repos with
  different versioning schemes while keeping optional bump discipline
  explicit.
  Impact: Standardized version metadata, defaults, docs, tests, and
  registry output around one future-facing multi-scheme policy contract.
  Files:
  AGENTS.md
  CHANGELOG.md
  POLICY_MAP.md
  devcovenant/builtin/policies/semantic_version_scope/__init__.py
  devcovenant/builtin/policies/semantic_version_scope/\
    semantic_version_scope.py
  devcovenant/builtin/policies/semantic_version_scope/\
    semantic_version_scope.yaml
  devcovenant/builtin/policies/version_governance/__init__.py
  devcovenant/builtin/policies/version_governance/version_governance.py
  devcovenant/builtin/policies/version_governance/version_governance.yaml
  devcovenant/builtin/policies/version_sync/version_sync.yaml
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/config.yaml
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/semantic_version_scope/__init__.py
  tests/devcovenant/builtin/policies/semantic_version_scope/\
    test_semantic_version_scope.py
  tests/devcovenant/builtin/policies/version_governance/__init__.py
  tests/devcovenant/builtin/policies/version_governance/\
    test_version_governance.py
  tests/devcovenant/builtin/policies/version_sync/test_version_sync.py

- 2026-03-16:
  Change: Added an open-session guard so `devcovenant clean` now fails until
  the active gate is closed.
  Why: Prevented cleanup commands from deleting the runtime registry or logs
  that an open gate session still owns as live workflow evidence.
  Impact: Clarified that `clean` is a post-session maintenance command and
  verified the guard across clean runtime tests and lifecycle docs.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/core/flow/clean.py
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/flow/test_clean.py
  tests/devcovenant/test_clean.py

- 2026-03-16:
  Change: Added the question-mark prompt rule to the Dev Covenant and
  workflow template so question-only prompts stop command execution by
  default.
  Why: Prevented future conversational questions from accidentally starting
  work slices just because the broader workflow biases toward execution.
  Impact: Clarified that AGENTS-managed repos now state the question-only
  stop rule both as
  a top-level commandment and as an explicit execution-order branch.
  Files:
  AGENTS.md
  CHANGELOG.md
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/docs/profiles.md

- 2026-03-16:
  Change: Closed the registry/runtime/log migration plan with local rebuild
  proof and a clean downstream `dlmc` validation run.
  Why: Verified the installed package, this repo, and the cleaned downstream
  user repo all behaved correctly under the final tracked-vs-runtime
  contract.
  Impact: Completed the plan with direct evidence that rebuild, reinstall,
  upgrade, refresh, status, and cleanup flows now work end-to-end.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-16:
  Change: Removed the last stale mixed-registry wording from docs, tests, and
  generated config commentary.
  Why: Completed the registry-truth sweep so refresh, architecture, deploy, and
  refresh tests all describe one tracked registry plus separate runtime state.
  Impact: The written/tested contract now matches the forward-only
  registry/runtime/log model without leftover `local registries` narration.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/docs/architecture.md
  devcovenant/docs/refresh.md
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_refresh.py

- 2026-03-15:
  Change: Tightened install, refresh, upgrade, and packaging behavior around
  the tracked registry and runtime outputs.
  Why: Prevented source-checkout runtime logs from leaking into target repos
  and proved that missing tracked registry state is recreated without
  inventing runtime session payloads.
  Impact: Repository installs/upgrades now honor the tracked-vs-runtime split
  more strictly, and package tests/docs explicitly cover the registry/log
  exclusion contract.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/docs/installation.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/install.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_upgrade.py

- 2026-03-15:
  Change: Added first-class cleanup scopes for runtime registry and logs and
  widened `clean --all` to cover them.
  Why: Made disposable runtime artifacts explicitly cleanable while keeping
  tracked registry and README files outside cleanup scope.
  Impact: `devcovenant clean` can now prune build, cache, runtime-registry,
  and log residue without treating tracked governance artifacts as junk.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/global.yaml
  devcovenant/clean.py
  devcovenant/config.yaml
  devcovenant/core/flow/clean.py
  devcovenant/core/services/cleanup.py
  devcovenant/core/services/profile_registry.py
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/registry.yaml
  tests/devcovenant/core/flow/test_clean.py
  tests/devcovenant/core/services/test_cleanup.py
  tests/devcovenant/test_clean.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py

- 2026-03-15:
  Change: Documented and recorded the split gate runtime state contract
  across the roadmap and runtime docs.
  Why: Clarified that `gate_status.json` stays slim while
  `session_snapshot.json` carries heavy session payloads for the active
  session.
  Impact: Contributors now see the correct registry/runtime model in the
  README, workflow, registry, and architecture guidance.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/docs/architecture.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/README.md

- 2026-03-15:
  Change: Marked Item 1 complete in the plan after the clean gated close.
  Why: Recorded the registry-architecture slice closure in the roadmap after
  implementation, tests, and gates all passed.
  Impact: Updated the plan to reflect the real project state and keep the
  next slice starting point explicit.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-15:
  Change: Standardized the one-root registry architecture and repaired the
  migrated test and documentation contract around it.
  Why: Completed the Item 1 registry move by routing tracked governance data
  through `devcovenant/registry/registry.yaml`, keeping runtime state under
  `devcovenant/registry/runtime/`, and clearing the fallout that the full test
  suite and mid gate exposed.
  Impact: Refresh, install, upgrade, gate, clean, and documentation routing
  now align with the forward-only tracked-vs-runtime registry model, and the
  repo closes this slice without registry-layout drift.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/builtin/policies/changelog_coverage/changelog_coverage.py
  devcovenant/builtin/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/config.yaml
  devcovenant/core/services/profile_registry.py
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/registry/registry.yaml
  devcovenant/registry/registry.yaml
  tests/devcovenant/builtin/policies/devcov_structure_guard/\
    test_devcov_structure_guard.py
  tests/devcovenant/core/runtime/test_run_logging.py
  tests/devcovenant/core/services/test_cleanup.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_refresh.py

- 2026-03-15:
  Change: Replaced the roadmap with the forward-only registry architecture
  plan.
  Why: Defined the next 1.x program around tracked deterministic registry
  metadata, split runtime state, and explicit cleanup scopes without
  compatibility drift.
  Impact: Aligned the next execution cycle around one registry root, slim
  gate runtime state, and first-class registry/log cleanup.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-15:
  Change: Completed final validation and downstream operational proof.
  Why: Verified the strict no-fallback baseline with a local rebuild and a
  real upgraded user repo.
  Impact: Closed the remediation plan with evidence that the package works
  without removed fallback paths, while downstream repo-state issues remain
  explicit and separate from package behavior.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-15:
  Change: Rewrote docs and test narration to remove stale delegacy wording.
  Why: Clarified the 1.0.0 contract so docs and assertions describe current
  behavior instead of the old transition story.
  Impact: Tightened workflow, architecture, installation, profile, and
  troubleshooting guidance, and kept only intentional strict-behavior test
  assertions.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/contracts/test_policy.py
  tests/devcovenant/builtin/policies/dependency_license_sync/\
    test_dependency_lock_runtime.py
  tests/devcovenant/builtin/policies/managed_environment/\
    test_managed_environment_runtime.py
  tests/devcovenant/builtin/policies/tests_coverage/\
    test_assertion_signal.py
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/flow/test_gate_changelog_helpers.py
  tests/devcovenant/core/flow/test_gate_status_helpers.py
  tests/devcovenant/core/flow/test_refresh.py
  tests/devcovenant/core/flow/test_session.py
  tests/devcovenant/core/lib/test_document_exemptions.py
  tests/devcovenant/core/lib/test_selectors.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/runtime/test_run_logging.py
  tests/devcovenant/core/runtime/test_session_snapshot.py
  tests/devcovenant/core/services/test_event.py
  tests/devcovenant/core/services/test_metadata.py
  tests/devcovenant/core/services/test_policy_autofix.py
  tests/devcovenant/core/services/test_policy_block_refresh.py
  tests/devcovenant/core/services/test_policy_check_context.py
  tests/devcovenant/core/services/test_policy_check_runner.py
  tests/devcovenant/core/services/test_policy_engine.py
  tests/devcovenant/core/services/test_policy_parse.py
  tests/devcovenant/core/services/test_policy_reporting.py
  tests/devcovenant/core/services/test_policy_runtime_actions.py
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/core/services/test_runtime_profile.py
  tests/devcovenant/core/services/test_translator_engine.py

- 2026-03-15:
  Change: Removed lazy package-export shims and made test-event handling
  explicit.
  Why: Reduced transitional compatibility behavior so package surfaces and
  event recording follow the same no-fallback contract.
  Impact: Made core packages import concrete submodules directly, kept
  launcher wording explicit, and recorded test events only through
  declared adapters.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/builtin/policies/changelog_coverage/changelog_coverage.py
  devcovenant/builtin/policies/devcov_structure_guard/\
    devcov_structure_guard.py
  devcovenant/builtin/policies/managed_environment/\
    managed_environment_runtime.py
  devcovenant/core/contracts/__init__.py
  devcovenant/core/flow/__init__.py
  devcovenant/core/flow/clean.py
  devcovenant/core/flow/gate.py
  devcovenant/core/flow/gate_changelog_helpers.py
  devcovenant/core/flow/gate_status_helpers.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/flow/session.py
  devcovenant/core/lib/__init__.py
  devcovenant/core/runtime/__init__.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/services/__init__.py
  devcovenant/core/services/cleanup.py
  devcovenant/core/services/event.py
  devcovenant/core/services/metadata.py
  devcovenant/core/services/policy_block_refresh.py
  devcovenant/core/services/policy_check_runner.py
  devcovenant/core/services/policy_runtime_actions.py
  devcovenant/core/services/registry.py
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  devcovenant/install.py
  tests/devcovenant/core/services/test_event.py
  tests/devcovenant/core/services/test_registry.py

- 2026-03-15:
  Change: Removed hidden check flags, clean placeholder compatibility,
  and gate-status pointer scanning.
  Why: Reduced compatibility shims and recovery logic so command/config
  ownership stays explicit.
  Impact: Clarified audit-only check behavior, made clean overrides fully
  explicit, and made gate status rely only on owned pointers.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/check.py
  devcovenant/core/flow/gate_status_helpers.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/services/cleanup.py
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/flow/test_gate_status_helpers.py
  tests/devcovenant/core/services/test_cleanup.py
  tests/devcovenant/test_check.py
  tests/devcovenant/test_cli.py

- 2026-03-15:
  Change: Removed managed-environment rerun fallbacks and enforced
  local-registry-only runtime resolution.
  Why: Preferred explicit managed-environment failures over wrapper reruns
  and AGENTS parsing so command execution stays deterministic.
  Impact: Clarified that DevCovenant now stops on missing or
  non-executable managed interpreters across runtime surfaces.
  Files:
  CHANGELOG.md
  AGENTS.md
  CONTRIBUTING.md
  README.md
  devcovenant/builtin/policies/managed_environment/\
    managed_environment.py
  devcovenant/builtin/policies/managed_environment/\
    managed_environment.yaml
  devcovenant/builtin/policies/managed_environment/\
    managed_environment_runtime.py
  devcovenant/builtin/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/cli.py
  devcovenant/core/runtime/execution.py
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  PLAN.md
  tests/devcovenant/builtin/policies/managed_environment/\
    test_managed_environment.py
  tests/devcovenant/builtin/policies/managed_environment/\
    test_managed_environment_runtime.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/test_cli.py

- 2026-03-15:
  Change: Removed legacy gate-snapshot migration logic and rejected old
    snapshot row formats explicitly.
  Why: Replaced the old `legacy_numstat` bridge with strict current-format
    validation so stale gate payloads now fail clearly and require a fresh
    `devcovenant gate --start`.
  Impact: Kept session scoping deterministic, removed hidden migration
    behavior, and aligned snapshot tests and docs to the current gate format.
  Files:
  CHANGELOG.md
  PLAN.md
  devcovenant/core/runtime/execution.py
  devcovenant/core/runtime/session_snapshot.py
  devcovenant/core/services/policy_check_context.py
  devcovenant/docs/architecture.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/runtime/test_session_snapshot.py
  tests/devcovenant/core/services/test_policy_check_context.py

- 2026-03-15:
  Change: Removed the in-package launcher bootstrap and locked Item 2's
    honest launcher and pycache contract.
  Why: Clarified that source-checkout launcher-process bytecode control must
    belong to shell or CI `PYTHONPYCACHEPREFIX`, not to repo-root startup
    hooks or fake in-package pre-import fixes.
  Impact: Made pycache routing explicit, deleted the misleading bootstrap
    helper, and aligned tests and docs to the real zero-drift boundary.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/__main__.py
  devcovenant/cli.py
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/core/runtime/execution.py
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/test_cli.py

- 2026-03-15:
  Change: Amended the no-fallback roadmap to insert a launcher and pycache
    strictness item ahead of the deeper delegacy removals.
  Why: Clarified that source-checkout bytecode drift must be solved without
    repo-root bootstrap files and before the remaining fallback-removal work.
  Impact: Sequenced the plan around the real launcher contract, so later items
    no longer rely on ambiguous bootstrap assumptions.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-15:
  Change: Reverted the aborted repo-root bootstrap experiment and
    resynchronized the managed documentation headers.
  Why: Removed the rejected startup-hook approach so the repository returns to
    the prior staged state without introducing repo-root bootstrap files.
  Impact: Preserved the earlier staged work while keeping the bootstrap
    experiment out of the tree and aligning the managed docs to the current
    session date.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  README.md

- 2026-03-15:
  Change: Completed Item 1 of the strict no-fallback plan and recorded the
    validated baseline finding.
  Why: Confirmed that read-only source-checkout `devcovenant check` still
    recreates repo-local bytecode, so the next slices can target a real
    delegacy defect instead of incidental hygiene noise.
  Impact: Recorded the validated baseline in `PLAN.md`, so the next work can
    remove fallback behavior from a known-clean starting point.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-15:
  Change: Replaced the completed hardening roadmap with a new strict
    no-fallback remediation plan.
  Why: Captured the delegacy audit findings in dependency order so future
    slices can remove live compatibility behavior systematically.
  Impact: Defined `PLAN.md` as the governing roadmap for the next cycle around
    snapshot, runtime, command, package, docs, tests, and downstream
    no-fallback proof work.
  Files:
  CHANGELOG.md
  PLAN.md

- 2026-03-14:
  Change: Documented the builtin-only shipped profile authority after the
    legacy `devcovenant/core/profiles/**` mirror removal.
  Why: Clarified the doc route triggered by the repo profile metadata change
    in this gate session and made the forward `builtin` boundary explicit.
  Impact: `devcovenant/docs/profiles.md` now states that shipped manifests,
    assets, and translators live only under `builtin` plus repo-owned
    `custom`, reducing profile-layout confusion.
  Files:
  CHANGELOG.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/profiles.md

- 2026-03-14:
  Change: Removed the obsolete legacy `devcovenant/core`
    compatibility tree, regenerated managed metadata, and
    synchronized supporting package, docs, and license surfaces.
  Why: Eliminated duplicate pre-1.0 authorities that kept old policy,
    profile, and runtime mirrors alive after the builtin/core split.
  Impact: Simplified DevCovenant to one shipped policy/profile tree,
    reduced drift risk, and aligned generated repo surfaces with the
    forward 1.0 architecture.
  Files:
  AGENTS.md
  CHANGELOG.md
  devcovenant/config.yaml
  devcovenant/core/event_runtime.py
  devcovenant/core/execution_runtime.py
  devcovenant/core/gate_runtime.py
  devcovenant/core/lock_runtime.py
  devcovenant/core/metadata_runtime.py
  devcovenant/core/policies/README.md
  devcovenant/core/policies/__init__.py
  devcovenant/core/policies/changelog_coverage/__init__.py
  devcovenant/core/policies/changelog_coverage/assets/.gitkeep
  devcovenant/core/policies/changelog_coverage/changelog_coverage.py
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/policies/dependency_license_sync/__init__.py
  devcovenant/core/policies/dependency_license_sync/dependency_license_sync.py
  devcovenant/core/policies/dependency_license_sync/\
    dependency_license_sync.yaml
  devcovenant/core/policies/dependency_license_sync/fixers/__init__.py
  devcovenant/core/policies/dependency_license_sync/fixers/global.py
  devcovenant/core/policies/devcov_integrity_guard/__init__.py
  devcovenant/core/policies/devcov_integrity_guard/assets/.gitkeep
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.py
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.yaml
  devcovenant/core/policies/devcov_integrity_guard/fixers/__init__.py
  devcovenant/core/policies/devcov_structure_guard/__init__.py
  devcovenant/core/policies/devcov_structure_guard/assets/.gitkeep
  devcovenant/core/policies/devcov_structure_guard/devcov_structure_guard.py
  devcovenant/core/policies/devcov_structure_guard/devcov_structure_guard.yaml
  devcovenant/core/policies/devcov_structure_guard/fixers/__init__.py
  devcovenant/core/policies/devflow_run_gates/__init__.py
  devcovenant/core/policies/devflow_run_gates/assets/.gitkeep
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/policies/devflow_run_gates/fixers/__init__.py
  devcovenant/core/policies/docstring_and_comment_coverage/__init__.py
  devcovenant/core/policies/docstring_and_comment_coverage/assets/.gitkeep
  devcovenant/core/policies/docstring_and_comment_coverage/\
    docstring_and_comment_coverage.py
  devcovenant/core/policies/docstring_and_comment_coverage/\
    docstring_and_comment_coverage.yaml
  devcovenant/core/policies/docstring_and_comment_coverage/fixers/__init__.py
  devcovenant/core/policies/documentation_growth_tracking/__init__.py
  devcovenant/core/policies/documentation_growth_tracking/assets/.gitkeep
  devcovenant/core/policies/documentation_growth_tracking/\
    documentation_growth_tracking.py
  devcovenant/core/policies/documentation_growth_tracking/\
    documentation_growth_tracking.yaml
  devcovenant/core/policies/documentation_growth_tracking/fixers/__init__.py
  devcovenant/core/policies/last_updated_placement/__init__.py
  devcovenant/core/policies/last_updated_placement/assets/.gitkeep
  devcovenant/core/policies/last_updated_placement/fixers/__init__.py
  devcovenant/core/policies/last_updated_placement/fixers/global.py
  devcovenant/core/policies/last_updated_placement/last_updated_placement.py
  devcovenant/core/policies/last_updated_placement/last_updated_placement.yaml
  devcovenant/core/policies/line_length_limit/__init__.py
  devcovenant/core/policies/line_length_limit/assets/.gitkeep
  devcovenant/core/policies/line_length_limit/fixers/__init__.py
  devcovenant/core/policies/line_length_limit/line_length_limit.py
  devcovenant/core/policies/line_length_limit/line_length_limit.yaml
  devcovenant/core/policies/managed_environment/__init__.py
  devcovenant/core/policies/managed_environment/assets/.gitkeep
  devcovenant/core/policies/managed_environment/fixers/__init__.py
  devcovenant/core/policies/managed_environment/managed_environment.py
  devcovenant/core/policies/managed_environment/managed_environment.yaml
  devcovenant/core/policies/modules_need_tests/__init__.py
  devcovenant/core/policies/modules_need_tests/assets/.gitkeep
  devcovenant/core/policies/modules_need_tests/fixers/__init__.py
  devcovenant/core/policies/modules_need_tests/modules_need_tests.py
  devcovenant/core/policies/modules_need_tests/modules_need_tests.yaml
  devcovenant/core/policies/name_clarity/__init__.py
  devcovenant/core/policies/name_clarity/assets/.gitkeep
  devcovenant/core/policies/name_clarity/fixers/__init__.py
  devcovenant/core/policies/name_clarity/name_clarity.py
  devcovenant/core/policies/name_clarity/name_clarity.yaml
  devcovenant/core/policies/no_future_dates/__init__.py
  devcovenant/core/policies/no_future_dates/assets/.gitkeep
  devcovenant/core/policies/no_future_dates/fixers/__init__.py
  devcovenant/core/policies/no_future_dates/fixers/global.py
  devcovenant/core/policies/no_future_dates/no_future_dates.py
  devcovenant/core/policies/no_future_dates/no_future_dates.yaml
  devcovenant/core/policies/no_print_outside_output_runtime/__init__.py
  devcovenant/core/policies/no_print_outside_output_runtime/\
    no_print_outside_output_runtime.py
  devcovenant/core/policies/no_print_outside_output_runtime/\
    no_print_outside_output_runtime.yaml
  devcovenant/core/policies/raw_string_escapes/__init__.py
  devcovenant/core/policies/raw_string_escapes/assets/.gitkeep
  devcovenant/core/policies/raw_string_escapes/fixers/__init__.py
  devcovenant/core/policies/raw_string_escapes/fixers/global.py
  devcovenant/core/policies/raw_string_escapes/raw_string_escapes.py
  devcovenant/core/policies/raw_string_escapes/raw_string_escapes.yaml
  devcovenant/core/policies/read_only_directories/__init__.py
  devcovenant/core/policies/read_only_directories/assets/.gitkeep
  devcovenant/core/policies/read_only_directories/fixers/__init__.py
  devcovenant/core/policies/read_only_directories/read_only_directories.py
  devcovenant/core/policies/read_only_directories/read_only_directories.yaml
  devcovenant/core/policies/security_scanner/__init__.py
  devcovenant/core/policies/security_scanner/assets/.gitkeep
  devcovenant/core/policies/security_scanner/fixers/__init__.py
  devcovenant/core/policies/security_scanner/security_scanner.py
  devcovenant/core/policies/security_scanner/security_scanner.yaml
  devcovenant/core/policies/semantic_version_scope/__init__.py
  devcovenant/core/policies/semantic_version_scope/assets/.gitkeep
  devcovenant/core/policies/semantic_version_scope/fixers/__init__.py
  devcovenant/core/policies/semantic_version_scope/semantic_version_scope.py
  devcovenant/core/policies/semantic_version_scope/semantic_version_scope.yaml
  devcovenant/core/policies/tests_coverage/__init__.py
  devcovenant/core/policies/tests_coverage/fixers/__init__.py
  devcovenant/core/policies/tests_coverage/tests_coverage.py
  devcovenant/core/policies/tests_coverage/tests_coverage.yaml
  devcovenant/core/policies/version_sync/__init__.py
  devcovenant/core/policies/version_sync/assets/.gitkeep
  devcovenant/core/policies/version_sync/fixers/__init__.py
  devcovenant/core/policies/version_sync/version_sync.py
  devcovenant/core/policies/version_sync/version_sync.yaml
  devcovenant/core/policy_contracts.py
  devcovenant/core/policy_runtime.py
  devcovenant/core/profile_runtime.py
  devcovenant/core/profiles/README.md
  devcovenant/core/profiles/csharp/assets/Project.csproj
  devcovenant/core/profiles/csharp/assets/packages.lock.json
  devcovenant/core/profiles/csharp/csharp.yaml
  devcovenant/core/profiles/csharp/translator.py
  devcovenant/core/profiles/dart/assets/pubspec.lock
  devcovenant/core/profiles/dart/assets/pubspec.yaml
  devcovenant/core/profiles/dart/dart.yaml
  devcovenant/core/profiles/dart/translator.py
  devcovenant/core/profiles/defaults/defaults.yaml
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/docker/assets/.dockerignore
  devcovenant/core/profiles/docker/assets/Dockerfile
  devcovenant/core/profiles/docker/assets/docker-compose.yml
  devcovenant/core/profiles/docker/docker.yaml
  devcovenant/core/profiles/docs/docs.yaml
  devcovenant/core/profiles/fastapi/assets/main.py
  devcovenant/core/profiles/fastapi/assets/openapi.json
  devcovenant/core/profiles/fastapi/fastapi.yaml
  devcovenant/core/profiles/flutter/assets/pubspec.yaml
  devcovenant/core/profiles/flutter/flutter.yaml
  devcovenant/core/profiles/frappe/assets/hooks.py
  devcovenant/core/profiles/frappe/assets/modules.txt
  devcovenant/core/profiles/frappe/frappe.yaml
  devcovenant/core/profiles/global/assets/.github/workflows/ci.yml
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/LICENSE.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles/global/assets/config.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/profiles/global/assets/gitignore.yaml
  devcovenant/core/profiles/global/assets/ci-and-test.yml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/go/assets/go.mod
  devcovenant/core/profiles/go/assets/go.sum
  devcovenant/core/profiles/go/go.yaml
  devcovenant/core/profiles/go/translator.py
  devcovenant/core/profiles/java/assets/build.gradle
  devcovenant/core/profiles/java/java.yaml
  devcovenant/core/profiles/java/translator.py
  devcovenant/core/profiles/javascript/assets/package.json
  devcovenant/core/profiles/javascript/javascript.yaml
  devcovenant/core/profiles/javascript/translator.py
  devcovenant/core/profiles/kubernetes/assets/Chart.yaml
  devcovenant/core/profiles/kubernetes/assets/values.yaml
  devcovenant/core/profiles/kubernetes/kubernetes.yaml
  devcovenant/core/profiles/objective-c/assets/Podfile
  devcovenant/core/profiles/objective-c/objective-c.yaml
  devcovenant/core/profiles/objective-c/translator.py
  devcovenant/core/profiles/php/assets/composer.json
  devcovenant/core/profiles/php/assets/composer.lock
  devcovenant/core/profiles/php/assets/phpunit.xml
  devcovenant/core/profiles/php/php.yaml
  devcovenant/core/profiles/php/translator.py
  devcovenant/core/profiles/python/assets/.python-version
  devcovenant/core/profiles/python/assets/pyproject.toml
  devcovenant/core/profiles/python/assets/requirements.in
  devcovenant/core/profiles/python/assets/requirements.lock
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/profiles/python/translator.py
  devcovenant/core/profiles/ruby/assets/Gemfile
  devcovenant/core/profiles/ruby/assets/Gemfile.lock
  devcovenant/core/profiles/ruby/ruby.yaml
  devcovenant/core/profiles/ruby/translator.py
  devcovenant/core/profiles/rust/assets/Cargo.lock
  devcovenant/core/profiles/rust/assets/Cargo.toml
  devcovenant/core/profiles/rust/rust.yaml
  devcovenant/core/profiles/rust/translator.py
  devcovenant/core/profiles/sql/assets/schema.sql
  devcovenant/core/profiles/sql/sql.yaml
  devcovenant/core/profiles/sql/translator.py
  devcovenant/core/profiles/swift/assets/Package.swift
  devcovenant/core/profiles/swift/swift.yaml
  devcovenant/core/profiles/swift/translator.py
  devcovenant/core/profiles/terraform/assets/main.tf
  devcovenant/core/profiles/terraform/assets/variables.tf
  devcovenant/core/profiles/terraform/terraform.yaml
  devcovenant/core/profiles/typescript/assets/package.json
  devcovenant/core/profiles/typescript/assets/tsconfig.json
  devcovenant/core/profiles/typescript/translator.py
  devcovenant/core/profiles/typescript/typescript.yaml
  devcovenant/core/refresh_runtime.py
  devcovenant/core/registry_runtime.py
  devcovenant/core/selector_runtime.py
  devcovenant/core/tests_coverage_runtime.py
  devcovenant/core/translator_runtime.py
  devcovenant/custom/policies/readme_sync/fixers/global.py
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/installation.md
  licenses/THIRD_PARTY_LICENSES.md
  tests/devcovenant/core/policies/__init__.py
  tests/devcovenant/core/policies/changelog_coverage/__init__.py
  tests/devcovenant/core/policies/changelog_coverage/test_changelog_coverage.py
  tests/devcovenant/core/policies/dependency_license_sync/__init__.py
  tests/devcovenant/core/policies/dependency_license_sync/fixers/__init__.py
  tests/devcovenant/core/policies/dependency_license_sync/fixers/test_global.py
  tests/devcovenant/core/policies/dependency_license_sync/\
    test_dependency_license_sync.py
  tests/devcovenant/core/policies/devcov_integrity_guard/__init__.py
  tests/devcovenant/core/policies/devcov_integrity_guard/\
    test_devcov_integrity_guard.py
  tests/devcovenant/core/policies/devcov_structure_guard/__init__.py
  tests/devcovenant/core/policies/devcov_structure_guard/\
    test_devcov_structure_guard.py
  tests/devcovenant/core/policies/devflow_run_gates/__init__.py
  tests/devcovenant/core/policies/devflow_run_gates/test_devflow_run_gates.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/__init__.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/\
    test_docstring_and_comment_coverage.py
  tests/devcovenant/core/policies/documentation_growth_tracking/__init__.py
  tests/devcovenant/core/policies/documentation_growth_tracking/\
    test_documentation_growth_tracking.py
  tests/devcovenant/core/policies/last_updated_placement/__init__.py
  tests/devcovenant/core/policies/last_updated_placement/fixers/__init__.py
  tests/devcovenant/core/policies/last_updated_placement/fixers/test_global.py
  tests/devcovenant/core/policies/last_updated_placement/\
    test_last_updated_placement.py
  tests/devcovenant/core/policies/line_length_limit/__init__.py
  tests/devcovenant/core/policies/line_length_limit/test_line_length_limit.py
  tests/devcovenant/core/policies/managed_environment/__init__.py
  tests/devcovenant/core/policies/managed_environment/\
    test_managed_environment.py
  tests/devcovenant/core/policies/modules_need_tests/__init__.py
  tests/devcovenant/core/policies/modules_need_tests/test_modules_need_tests.py
  tests/devcovenant/core/policies/name_clarity/__init__.py
  tests/devcovenant/core/policies/name_clarity/test_name_clarity.py
  tests/devcovenant/core/policies/no_future_dates/__init__.py
  tests/devcovenant/core/policies/no_future_dates/fixers/__init__.py
  tests/devcovenant/core/policies/no_future_dates/fixers/test_global.py
  tests/devcovenant/core/policies/no_future_dates/test_no_future_dates.py
  tests/devcovenant/core/policies/no_print_outside_output_runtime/__init__.py
  tests/devcovenant/core/policies/no_print_outside_output_runtime/\
    test_no_print_outside_output_runtime.py
  tests/devcovenant/core/policies/raw_string_escapes/__init__.py
  tests/devcovenant/core/policies/raw_string_escapes/fixers/__init__.py
  tests/devcovenant/core/policies/raw_string_escapes/fixers/test_global.py
  tests/devcovenant/core/policies/raw_string_escapes/test_raw_string_escapes.py
  tests/devcovenant/core/policies/read_only_directories/__init__.py
  tests/devcovenant/core/policies/read_only_directories/\
    test_read_only_directories.py
  tests/devcovenant/core/policies/security_scanner/__init__.py
  tests/devcovenant/core/policies/security_scanner/test_security_scanner.py
  tests/devcovenant/core/policies/semantic_version_scope/__init__.py
  tests/devcovenant/core/policies/semantic_version_scope/\
    test_semantic_version_scope.py
  tests/devcovenant/core/policies/tests_coverage/__init__.py
  tests/devcovenant/core/policies/tests_coverage/test_tests_coverage.py
  tests/devcovenant/core/policies/version_sync/__init__.py
  tests/devcovenant/core/policies/version_sync/test_version_sync.py
  tests/devcovenant/core/profiles/__init__.py
  tests/devcovenant/core/profiles/csharp/__init__.py
  tests/devcovenant/core/profiles/csharp/test_translator.py
  tests/devcovenant/core/profiles/dart/__init__.py
  tests/devcovenant/core/profiles/dart/test_translator.py
  tests/devcovenant/core/profiles/fastapi/__init__.py
  tests/devcovenant/core/profiles/fastapi/assets/__init__.py
  tests/devcovenant/core/profiles/fastapi/assets/test_main.py
  tests/devcovenant/core/profiles/frappe/__init__.py
  tests/devcovenant/core/profiles/frappe/assets/__init__.py
  tests/devcovenant/core/profiles/frappe/assets/test_hooks.py
  tests/devcovenant/core/profiles/go/__init__.py
  tests/devcovenant/core/profiles/go/test_translator.py
  tests/devcovenant/core/profiles/java/__init__.py
  tests/devcovenant/core/profiles/java/test_translator.py
  tests/devcovenant/core/profiles/javascript/__init__.py
  tests/devcovenant/core/profiles/javascript/test_translator.py
  tests/devcovenant/core/profiles/objective-c/__init__.py
  tests/devcovenant/core/profiles/objective-c/test_translator.py
  tests/devcovenant/core/profiles/php/__init__.py
  tests/devcovenant/core/profiles/php/test_translator.py
  tests/devcovenant/core/profiles/python/__init__.py
  tests/devcovenant/core/profiles/python/test_translator.py
  tests/devcovenant/core/profiles/ruby/__init__.py
  tests/devcovenant/core/profiles/ruby/test_translator.py
  tests/devcovenant/core/profiles/rust/__init__.py
  tests/devcovenant/core/profiles/rust/test_translator.py
  tests/devcovenant/core/profiles/sql/__init__.py
  tests/devcovenant/core/profiles/sql/test_translator.py
  tests/devcovenant/core/profiles/swift/__init__.py
  tests/devcovenant/core/profiles/swift/test_translator.py
  tests/devcovenant/core/profiles/typescript/__init__.py
  tests/devcovenant/core/profiles/typescript/test_translator.py
  tests/devcovenant/core/test_event_runtime.py
  tests/devcovenant/core/test_execution_runtime.py
  tests/devcovenant/core/test_gate_runtime.py
  tests/devcovenant/core/test_lock_runtime.py
  tests/devcovenant/core/test_metadata_runtime.py
  tests/devcovenant/core/test_policy_contracts.py
  tests/devcovenant/core/test_policy_runtime.py
  tests/devcovenant/core/test_profile_runtime.py
  tests/devcovenant/core/test_refresh_runtime.py
  tests/devcovenant/core/test_registry_runtime.py
  tests/devcovenant/core/test_selector_runtime.py
  tests/devcovenant/core/test_tests_coverage_runtime.py
  tests/devcovenant/core/test_translator_runtime.py
  tests/devcovenant/custom/policies/readme_sync/fixers/__init__.py
  tests/devcovenant/custom/policies/readme_sync/fixers/test_global.py
- 2026-03-14:
  Change: Removed `tqdm`, redesigned managed doc intros, and restructured
    `CONTRIBUTING.md` so the standard DevCovenant contributor contract lives
    inside the managed block with preserved repo-specific notes below it.
  Why: Clarified DevCovenant-governed docs in user repositories, removed the
    stale progress-bar dependency from the legacy runtime surface, and kept
    the authoritative asset sets synchronized across builtin and core paths.
  Impact: Rendered docs now explain DevCovenant usage more naturally on
    GitHub, `CONTRIBUTING.md` upgrades safely without losing repo notes, and
    the runtime no longer carries `tqdm` or its license artifact.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  README.md
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/CHANGELOG.yaml
  devcovenant/builtin/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/\
    README.yaml
  devcovenant/core/execution_runtime.py
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  licenses/THIRD_PARTY_LICENSES.md
  licenses/tqdm-4.66.1.txt
  pyproject.toml
  requirements.in
  requirements.lock
  tests/devcovenant/test_refresh.py

- 2026-03-14:
  Change: Standardized command-scoped help usage across DevCovenant CLI
    entrypoints and removed the uninstall run-log pointer that could not
    survive package teardown.
  Why: Fixed the release-surface audit findings around misleading help text
    and dead `Run logs:` pointers for `devcovenant uninstall`.
  Impact: Clarified subcommand help across the full CLI surface and kept
    uninstall output honest about evidence artifacts that remain durable.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/check.py
  devcovenant/clean.py
  devcovenant/cli.py
  devcovenant/core/runtime/execution.py
  devcovenant/deploy.py
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/workflow.md
  devcovenant/gate.py
  devcovenant/install.py
  devcovenant/refresh.py
  devcovenant/test.py
  devcovenant/undeploy.py
  devcovenant/uninstall.py
  devcovenant/update_lock.py
  devcovenant/upgrade.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_undeploy.py
  tests/devcovenant/test_uninstall.py

- 2026-03-14:
  Change: Revised the `clean` command contract to require explicit scope
    selection, record cleanup details in run summaries, and honor explicit
    empty-list overrides without breaking legacy placeholder configs.
  Why: Fixed the remaining audit findings around clean CLI behavior, override
    semantics, artifact-first debugging, and registry side effects on fresh
    repos.
  Impact: Enabled explicit cleanup intent, preserved backward compatibility
    for older configs, and kept maintenance commands from materializing local
    policy registry state just to resolve managed-environment rules.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/clean.py
  devcovenant/builtin/policies/managed_environment/\
    managed_environment_runtime.py
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/core/flow/clean.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/services/cleanup.py
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  tests/devcovenant/builtin/policies/managed_environment/\
    test_managed_environment_runtime.py
  tests/devcovenant/core/flow/test_clean.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/services/test_cleanup.py
  tests/devcovenant/test_clean.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py

- 2026-03-14:
  Change: Added mirrored tests for internal runtime, policy, and profile
    surfaces while aligning package boundaries and repo policy scope for those
    internal modules.
  Why: Cleared gate violations exposed by the recent architecture resweep
    without weakening `modules-need-tests` or shipping internal core trees in
    package artifacts.
  Impact: Enabled gates to converge on the intended repo boundaries, the
    install package excludes internal-only trees, and internal module
    coverage stays explicit and enforced.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  MANIFEST.in
  README.md
  devcovenant/config.yaml
  devcovenant/core/event_runtime.py
  devcovenant/core/execution_runtime.py
  devcovenant/core/policies/README.md
  devcovenant/core/policies/last_updated_placement/fixers/global.py
  devcovenant/core/policies/modules_need_tests/modules_need_tests.py
  devcovenant/core/policies/raw_string_escapes/raw_string_escapes.py
  devcovenant/core/policy_runtime.py
  devcovenant/core/profiles/README.md
  devcovenant/core/profiles/global/assets/AGENTS.yaml
  devcovenant/core/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/core/profiles/global/assets/README.yaml
  devcovenant/core/profiles/global/assets/devcovenant/README.yaml
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  licenses/THIRD_PARTY_LICENSES.md
  pyproject.toml
  tests/devcovenant/builtin/policies/dependency_license_sync/\
    test_dependency_lock_runtime.py
  tests/devcovenant/builtin/policies/tests_coverage/test_assertion_signal.py
  tests/devcovenant/core/contracts/test_policy.py
  tests/devcovenant/core/flow/test_gate.py
  tests/devcovenant/core/flow/test_refresh.py
  tests/devcovenant/core/flow/test_session.py
  tests/devcovenant/core/lib/test_selectors.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/runtime/test_session_snapshot.py
  tests/devcovenant/core/services/test_event.py
  tests/devcovenant/core/services/test_metadata.py
  tests/devcovenant/core/services/test_policy_autofix.py
  tests/devcovenant/core/services/test_policy_block_refresh.py
  tests/devcovenant/core/services/test_policy_check_context.py
  tests/devcovenant/core/services/test_policy_check_runner.py
  tests/devcovenant/core/services/test_policy_engine.py
  tests/devcovenant/core/services/test_policy_file_scope.py
  tests/devcovenant/core/services/test_policy_parse.py
  tests/devcovenant/core/services/test_policy_reporting.py
  tests/devcovenant/core/services/test_policy_runtime_actions.py
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/core/services/test_runtime_profile.py
  tests/devcovenant/core/services/test_translator_engine.py
  tests/devcovenant/core/policies/__init__.py
  tests/devcovenant/core/policies/changelog_coverage/__init__.py
  tests/devcovenant/core/policies/changelog_coverage/test_changelog_coverage.py
  tests/devcovenant/core/policies/dependency_license_sync/__init__.py
  tests/devcovenant/core/policies/dependency_license_sync/fixers/__init__.py
  tests/devcovenant/core/policies/dependency_license_sync/fixers/test_global.py
  tests/devcovenant/core/policies/dependency_license_sync/\
    test_dependency_license_sync.py
  tests/devcovenant/core/policies/devcov_integrity_guard/__init__.py
  tests/devcovenant/core/policies/devcov_integrity_guard/\
    test_devcov_integrity_guard.py
  tests/devcovenant/core/policies/devcov_structure_guard/__init__.py
  tests/devcovenant/core/policies/devcov_structure_guard/\
    test_devcov_structure_guard.py
  tests/devcovenant/core/policies/devflow_run_gates/__init__.py
  tests/devcovenant/core/policies/devflow_run_gates/test_devflow_run_gates.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/__init__.py
  tests/devcovenant/core/policies/docstring_and_comment_coverage/\
    test_docstring_and_comment_coverage.py
  tests/devcovenant/core/policies/documentation_growth_tracking/__init__.py
  tests/devcovenant/core/policies/documentation_growth_tracking/\
    test_documentation_growth_tracking.py
  tests/devcovenant/core/policies/last_updated_placement/__init__.py
  tests/devcovenant/core/policies/last_updated_placement/fixers/__init__.py
  tests/devcovenant/core/policies/last_updated_placement/fixers/test_global.py
  tests/devcovenant/core/policies/last_updated_placement/\
    test_last_updated_placement.py
  tests/devcovenant/core/policies/line_length_limit/__init__.py
  tests/devcovenant/core/policies/line_length_limit/test_line_length_limit.py
  tests/devcovenant/core/policies/managed_environment/__init__.py
  tests/devcovenant/core/policies/managed_environment/\
    test_managed_environment.py
  tests/devcovenant/core/policies/modules_need_tests/__init__.py
  tests/devcovenant/core/policies/modules_need_tests/test_modules_need_tests.py
  tests/devcovenant/core/policies/name_clarity/__init__.py
  tests/devcovenant/core/policies/name_clarity/test_name_clarity.py
  tests/devcovenant/core/policies/no_future_dates/__init__.py
  tests/devcovenant/core/policies/no_future_dates/fixers/__init__.py
  tests/devcovenant/core/policies/no_future_dates/fixers/test_global.py
  tests/devcovenant/core/policies/no_future_dates/test_no_future_dates.py
  tests/devcovenant/core/policies/no_print_outside_output_runtime/__init__.py
  tests/devcovenant/core/policies/no_print_outside_output_runtime/\
    test_no_print_outside_output_runtime.py
  tests/devcovenant/core/policies/raw_string_escapes/__init__.py
  tests/devcovenant/core/policies/raw_string_escapes/fixers/__init__.py
  tests/devcovenant/core/policies/raw_string_escapes/fixers/test_global.py
  tests/devcovenant/core/policies/raw_string_escapes/test_raw_string_escapes.py
  tests/devcovenant/core/policies/read_only_directories/__init__.py
  tests/devcovenant/core/policies/read_only_directories/\
    test_read_only_directories.py
  tests/devcovenant/core/policies/security_scanner/__init__.py
  tests/devcovenant/core/policies/security_scanner/test_security_scanner.py
  tests/devcovenant/core/policies/semantic_version_scope/__init__.py
  tests/devcovenant/core/policies/semantic_version_scope/\
    test_semantic_version_scope.py
  tests/devcovenant/core/policies/tests_coverage/__init__.py
  tests/devcovenant/core/policies/tests_coverage/test_tests_coverage.py
  tests/devcovenant/core/policies/version_sync/__init__.py
  tests/devcovenant/core/policies/version_sync/test_version_sync.py
  tests/devcovenant/core/profiles/__init__.py
  tests/devcovenant/core/profiles/csharp/__init__.py
  tests/devcovenant/core/profiles/csharp/test_translator.py
  tests/devcovenant/core/profiles/dart/__init__.py
  tests/devcovenant/core/profiles/dart/test_translator.py
  tests/devcovenant/core/profiles/fastapi/__init__.py
  tests/devcovenant/core/profiles/fastapi/assets/__init__.py
  tests/devcovenant/core/profiles/fastapi/assets/test_main.py
  tests/devcovenant/core/profiles/frappe/__init__.py
  tests/devcovenant/core/profiles/frappe/assets/__init__.py
  tests/devcovenant/core/profiles/frappe/assets/test_hooks.py
  tests/devcovenant/core/profiles/go/__init__.py
  tests/devcovenant/core/profiles/go/test_translator.py
  tests/devcovenant/core/profiles/java/__init__.py
  tests/devcovenant/core/profiles/java/test_translator.py
  tests/devcovenant/core/profiles/javascript/__init__.py
  tests/devcovenant/core/profiles/javascript/test_translator.py
  tests/devcovenant/core/profiles/objective-c/__init__.py
  tests/devcovenant/core/profiles/objective-c/test_translator.py
  tests/devcovenant/core/profiles/php/__init__.py
  tests/devcovenant/core/profiles/php/test_translator.py
  tests/devcovenant/core/profiles/python/__init__.py
  tests/devcovenant/core/profiles/python/test_translator.py
  tests/devcovenant/core/profiles/ruby/__init__.py
  tests/devcovenant/core/profiles/ruby/test_translator.py
  tests/devcovenant/core/profiles/rust/__init__.py
  tests/devcovenant/core/profiles/rust/test_translator.py
  tests/devcovenant/core/profiles/sql/__init__.py
  tests/devcovenant/core/profiles/sql/test_translator.py
  tests/devcovenant/core/profiles/swift/__init__.py
  tests/devcovenant/core/profiles/swift/test_translator.py
  tests/devcovenant/core/profiles/typescript/__init__.py
  tests/devcovenant/core/profiles/typescript/test_translator.py
  tests/devcovenant/core/test_event_runtime.py
  tests/devcovenant/core/test_execution_runtime.py
  tests/devcovenant/core/test_gate_runtime.py
  tests/devcovenant/core/test_lock_runtime.py
  tests/devcovenant/core/test_metadata_runtime.py
  tests/devcovenant/core/test_policy_contracts.py
  tests/devcovenant/core/test_policy_runtime.py
  tests/devcovenant/core/test_profile_runtime.py
  tests/devcovenant/core/test_refresh_runtime.py
  tests/devcovenant/core/test_registry_runtime.py
  tests/devcovenant/core/test_selector_runtime.py
  tests/devcovenant/core/test_tests_coverage_runtime.py
  tests/devcovenant/core/test_translator_runtime.py
  tests/devcovenant/custom/policies/readme_sync/fixers/__init__.py
  tests/devcovenant/custom/policies/readme_sync/fixers/test_global.py
  tests/devcovenant/module_surface_helpers.py
  devcovenant/core/lock_runtime.py
  devcovenant/core/metadata_runtime.py
  devcovenant/core/policies/__init__.py
  devcovenant/core/policies/changelog_coverage/__init__.py
  devcovenant/core/policies/changelog_coverage/assets/.gitkeep
  devcovenant/core/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/core/policies/dependency_license_sync/__init__.py
  devcovenant/core/policies/dependency_license_sync/dependency_license_sync.py
  devcovenant/core/policies/dependency_license_sync/\
    dependency_license_sync.yaml
  devcovenant/core/policies/dependency_license_sync/fixers/__init__.py
  devcovenant/core/policies/dependency_license_sync/fixers/global.py
  devcovenant/core/policies/devcov_integrity_guard/__init__.py
  devcovenant/core/policies/devcov_integrity_guard/assets/.gitkeep
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.py
  devcovenant/core/policies/devcov_integrity_guard/devcov_integrity_guard.yaml
  devcovenant/core/policies/devcov_integrity_guard/fixers/__init__.py
  devcovenant/core/policies/devcov_structure_guard/__init__.py
  devcovenant/core/policies/devcov_structure_guard/assets/.gitkeep
  devcovenant/core/policies/devcov_structure_guard/devcov_structure_guard.py
  devcovenant/core/policies/devcov_structure_guard/devcov_structure_guard.yaml
  devcovenant/core/policies/devcov_structure_guard/fixers/__init__.py
  devcovenant/core/policies/devflow_run_gates/__init__.py
  devcovenant/core/policies/devflow_run_gates/assets/.gitkeep
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/core/policies/devflow_run_gates/devflow_run_gates.yaml
  devcovenant/core/policies/devflow_run_gates/fixers/__init__.py
  devcovenant/core/policies/docstring_and_comment_coverage/__init__.py
  devcovenant/core/policies/docstring_and_comment_coverage/assets/.gitkeep
  devcovenant/core/policies/docstring_and_comment_coverage/\
    docstring_and_comment_coverage.py
  devcovenant/core/policies/docstring_and_comment_coverage/\
    docstring_and_comment_coverage.yaml
  devcovenant/core/policies/docstring_and_comment_coverage/fixers/__init__.py
  devcovenant/core/policies/documentation_growth_tracking/__init__.py
  devcovenant/core/policies/documentation_growth_tracking/assets/.gitkeep
  devcovenant/core/policies/documentation_growth_tracking/\
    documentation_growth_tracking.py
  devcovenant/core/policies/documentation_growth_tracking/\
    documentation_growth_tracking.yaml
  devcovenant/core/policies/documentation_growth_tracking/fixers/__init__.py
  devcovenant/core/policies/last_updated_placement/__init__.py
  devcovenant/core/policies/last_updated_placement/assets/.gitkeep
  devcovenant/core/policies/last_updated_placement/fixers/__init__.py
  devcovenant/core/policies/last_updated_placement/last_updated_placement.py
  devcovenant/core/policies/last_updated_placement/last_updated_placement.yaml
  devcovenant/core/policies/line_length_limit/__init__.py
  devcovenant/core/policies/line_length_limit/assets/.gitkeep
  devcovenant/core/policies/line_length_limit/fixers/__init__.py
  devcovenant/core/policies/line_length_limit/line_length_limit.py
  devcovenant/core/policies/line_length_limit/line_length_limit.yaml
  devcovenant/core/policies/managed_environment/__init__.py
  devcovenant/core/policies/managed_environment/assets/.gitkeep
  devcovenant/core/policies/managed_environment/fixers/__init__.py
  devcovenant/core/policies/managed_environment/managed_environment.py
  devcovenant/core/policies/managed_environment/managed_environment.yaml
  devcovenant/core/policies/modules_need_tests/__init__.py
  devcovenant/core/policies/modules_need_tests/assets/.gitkeep
  devcovenant/core/policies/modules_need_tests/fixers/__init__.py
  devcovenant/core/policies/modules_need_tests/modules_need_tests.yaml
  devcovenant/core/policies/name_clarity/__init__.py
  devcovenant/core/policies/name_clarity/assets/.gitkeep
  devcovenant/core/policies/name_clarity/fixers/__init__.py
  devcovenant/core/policies/name_clarity/name_clarity.py
  devcovenant/core/policies/name_clarity/name_clarity.yaml
  devcovenant/core/policies/no_future_dates/__init__.py
  devcovenant/core/policies/no_future_dates/assets/.gitkeep
  devcovenant/core/policies/no_future_dates/fixers/__init__.py
  devcovenant/core/policies/no_future_dates/fixers/global.py
  devcovenant/core/policies/no_future_dates/no_future_dates.py
  devcovenant/core/policies/no_future_dates/no_future_dates.yaml
  devcovenant/core/policies/no_print_outside_output_runtime/__init__.py
  devcovenant/core/policies/no_print_outside_output_runtime/\
    no_print_outside_output_runtime.py
  devcovenant/core/policies/no_print_outside_output_runtime/\
    no_print_outside_output_runtime.yaml
  devcovenant/core/policies/raw_string_escapes/__init__.py
  devcovenant/core/policies/raw_string_escapes/assets/.gitkeep
  devcovenant/core/policies/raw_string_escapes/fixers/__init__.py
  devcovenant/core/policies/raw_string_escapes/fixers/global.py
  devcovenant/core/policies/raw_string_escapes/raw_string_escapes.yaml
  devcovenant/core/policies/read_only_directories/__init__.py
  devcovenant/core/policies/read_only_directories/assets/.gitkeep
  devcovenant/core/policies/read_only_directories/fixers/__init__.py
  devcovenant/core/policies/read_only_directories/read_only_directories.py
  devcovenant/core/policies/read_only_directories/read_only_directories.yaml
  devcovenant/core/policies/security_scanner/__init__.py
  devcovenant/core/policies/security_scanner/assets/.gitkeep
  devcovenant/core/policies/security_scanner/fixers/__init__.py
  devcovenant/core/policies/security_scanner/security_scanner.py
  devcovenant/core/policies/security_scanner/security_scanner.yaml
  devcovenant/core/policies/semantic_version_scope/__init__.py
  devcovenant/core/policies/semantic_version_scope/assets/.gitkeep
  devcovenant/core/policies/semantic_version_scope/fixers/__init__.py
  devcovenant/core/policies/semantic_version_scope/semantic_version_scope.yaml
  devcovenant/core/policies/tests_coverage/__init__.py
  devcovenant/core/policies/tests_coverage/fixers/__init__.py
  devcovenant/core/policies/tests_coverage/tests_coverage.py
  devcovenant/core/policies/tests_coverage/tests_coverage.yaml
  devcovenant/core/policies/version_sync/__init__.py
  devcovenant/core/policies/version_sync/assets/.gitkeep
  devcovenant/core/policies/version_sync/fixers/__init__.py
  devcovenant/core/policies/version_sync/version_sync.py
  devcovenant/core/policies/version_sync/version_sync.yaml
  devcovenant/core/policy_contracts.py
  devcovenant/core/profile_runtime.py
  devcovenant/core/profiles/csharp/assets/Project.csproj
  devcovenant/core/profiles/csharp/assets/packages.lock.json
  devcovenant/core/profiles/csharp/csharp.yaml
  devcovenant/core/profiles/csharp/translator.py
  devcovenant/core/profiles/dart/assets/pubspec.lock
  devcovenant/core/profiles/dart/assets/pubspec.yaml
  devcovenant/core/profiles/dart/dart.yaml
  devcovenant/core/profiles/dart/translator.py
  devcovenant/core/profiles/defaults/defaults.yaml
  devcovenant/core/profiles/devcovuser/devcovuser.yaml
  devcovenant/core/profiles/docker/assets/.dockerignore
  devcovenant/core/profiles/docker/assets/Dockerfile
  devcovenant/core/profiles/docker/assets/docker-compose.yml
  devcovenant/core/profiles/docker/docker.yaml
  devcovenant/core/profiles/docs/docs.yaml
  devcovenant/core/profiles/fastapi/assets/main.py
  devcovenant/core/profiles/fastapi/assets/openapi.json
  devcovenant/core/profiles/fastapi/fastapi.yaml
  devcovenant/core/profiles/flutter/assets/pubspec.yaml
  devcovenant/core/profiles/flutter/flutter.yaml
  devcovenant/core/profiles/frappe/assets/hooks.py
  devcovenant/core/profiles/frappe/frappe.yaml
  devcovenant/core/profiles/global/assets/.github/workflows/ci.yml
  devcovenant/core/profiles/global/assets/CHANGELOG.yaml
  devcovenant/core/profiles/global/assets/LICENSE.yaml
  devcovenant/core/profiles/global/assets/PLAN.yaml
  devcovenant/core/profiles/global/assets/SPEC.yaml
  devcovenant/core/profiles/global/assets/config.yaml
  devcovenant/core/profiles/global/assets/gitignore.yaml
  devcovenant/core/profiles/global/assets/ci-and-test.yml
  devcovenant/core/profiles/global/global.yaml
  devcovenant/core/profiles/go/assets/go.mod
  devcovenant/core/profiles/go/assets/go.sum
  devcovenant/core/profiles/go/go.yaml
  devcovenant/core/profiles/go/translator.py
  devcovenant/core/profiles/java/assets/build.gradle
  devcovenant/core/profiles/java/java.yaml
  devcovenant/core/profiles/java/translator.py
  devcovenant/core/profiles/javascript/assets/package.json
  devcovenant/core/profiles/javascript/javascript.yaml
  devcovenant/core/profiles/javascript/translator.py
  devcovenant/core/profiles/kubernetes/assets/Chart.yaml
  devcovenant/core/profiles/kubernetes/assets/values.yaml
  devcovenant/core/profiles/kubernetes/kubernetes.yaml
  devcovenant/core/profiles/objective-c/assets/Podfile
  devcovenant/core/profiles/objective-c/objective-c.yaml
  devcovenant/core/profiles/objective-c/translator.py
  devcovenant/core/profiles/php/assets/composer.json
  devcovenant/core/profiles/php/assets/composer.lock
  devcovenant/core/profiles/php/assets/phpunit.xml
  devcovenant/core/profiles/php/php.yaml
  devcovenant/core/profiles/php/translator.py
  devcovenant/core/profiles/python/assets/.python-version
  devcovenant/core/profiles/python/assets/pyproject.toml
  devcovenant/core/profiles/python/assets/requirements.in
  devcovenant/core/profiles/python/assets/requirements.lock
  devcovenant/core/profiles/python/python.yaml
  devcovenant/core/profiles/python/translator.py
  devcovenant/core/profiles/ruby/assets/Gemfile
  devcovenant/core/profiles/ruby/assets/Gemfile.lock
  devcovenant/core/profiles/ruby/ruby.yaml
  devcovenant/core/profiles/ruby/translator.py
  devcovenant/core/profiles/rust/assets/Cargo.lock
  devcovenant/core/profiles/rust/assets/Cargo.toml
  devcovenant/core/profiles/rust/rust.yaml
  devcovenant/core/profiles/rust/translator.py
  devcovenant/core/profiles/sql/assets/schema.sql
  devcovenant/core/profiles/sql/sql.yaml
  devcovenant/core/profiles/sql/translator.py
  devcovenant/core/profiles/swift/assets/Package.swift
  devcovenant/core/profiles/swift/swift.yaml
  devcovenant/core/profiles/swift/translator.py
  devcovenant/core/profiles/terraform/assets/main.tf
  devcovenant/core/profiles/terraform/assets/variables.tf
  devcovenant/core/profiles/terraform/terraform.yaml
  devcovenant/core/profiles/typescript/assets/package.json
  devcovenant/core/profiles/typescript/assets/tsconfig.json
  devcovenant/core/profiles/typescript/translator.py
  devcovenant/core/profiles/typescript/typescript.yaml
  devcovenant/core/registry_runtime.py
  devcovenant/core/selector_runtime.py
  devcovenant/core/tests_coverage_runtime.py
  devcovenant/core/translator_runtime.py
  devcovenant/custom/policies/readme_sync/fixers/global.py

- 2026-03-14:
  Change: Added a first-class `clean` command with profile-seeded cleanup
    targets, config-driven layering, and protected runtime fences.
  Why: Prevented build and cache residue from polluting gated work while
    standardizing disposable artifact cleanup across profiles and repos.
  Impact: Repositories can safely remove build-only, cache-only, or combined
    cleanup targets through one documented command with regression coverage.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/builtin/profiles/csharp/csharp.yaml
  devcovenant/builtin/profiles/dart/dart.yaml
  devcovenant/builtin/profiles/flutter/flutter.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/global.yaml
  devcovenant/builtin/profiles/go/go.yaml
  devcovenant/builtin/profiles/java/java.yaml
  devcovenant/builtin/profiles/javascript/javascript.yaml
  devcovenant/builtin/profiles/objective_c/objective_c.yaml
  devcovenant/builtin/profiles/php/php.yaml
  devcovenant/builtin/profiles/python/python.yaml
  devcovenant/builtin/profiles/ruby/ruby.yaml
  devcovenant/builtin/profiles/rust/rust.yaml
  devcovenant/builtin/profiles/swift/swift.yaml
  devcovenant/builtin/profiles/terraform/terraform.yaml
  devcovenant/builtin/profiles/typescript/typescript.yaml
  devcovenant/clean.py
  devcovenant/cli.py
  devcovenant/core/flow/__init__.py
  devcovenant/core/flow/clean.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/__init__.py
  devcovenant/core/services/cleanup.py
  devcovenant/core/services/profile_registry.py
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/services/test_cleanup.py
  tests/devcovenant/core/flow/test_clean.py
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/core/services/test_registry.py
  tests/devcovenant/test_clean.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py

- 2026-03-14:
  Change: Removed the retired `devcovenant/docs/README.md` vampire file and
    cleared the remaining stale references to it from current docs.
  Why: Prevented old untracked docset residue from re-triggering governance
    failures and kept the canonical docs entrypoint contract unambiguous.
  Impact: The packaged docs map now points only at live entrypoints, and
    future gates will not trip over the resurrected retired file.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/docs/profiles.md
  devcovenant/docs/README.md

- 2026-03-13:
  Change: Exposed typed runtime policy option views in the local policy
    registry alongside raw metadata trace and override warnings.
  Why: Clarified the exact option surface that policy runtime sees so audits
    do not have to reconstruct `PolicyCheck.get_option(...)` behavior by hand.
  Impact: Refresh now records runtime metadata, config-override, and
    effective-option views for each policy, and regression tests lock that
    debug contract in place.
  Files:
  CHANGELOG.md
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/policy_runtime_actions.py
  devcovenant/core/services/registry.py
  devcovenant/docs/architecture.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/services/test_policy_runtime_actions.py
  tests/devcovenant/test_refresh.py

- 2026-03-13:
  Change: Instrumented policy metadata resolution with per-key trace and
    override-replacement warnings recorded in the local policy registry.
  Why: Clarified descriptor/profile/config precedence so destructive
    replacements are auditable without guessing from final effective
    metadata alone.
  Impact: Refresh now records metadata provenance and warning diagnostics,
    and the resolution contract is documented and regression-tested.
  Files:
  CHANGELOG.md
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/metadata.py
  devcovenant/core/services/registry.py
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  tests/devcovenant/core/services/test_metadata.py
  tests/devcovenant/test_refresh.py

- 2026-03-13:
  Change: Promoted universal editor, packaging, coverage, and runtime artifact
    exclusions into the global baseline and builtin policy metadata while
    removing temporary repo-local tuning.
  Why: Standardized what belongs in shared defaults versus policy descriptors
    so repos inherit common noise suppression without rediscovering `.vscode`,
    `*.egg-info`, coverage, and runtime-state exclusions locally.
  Impact: New installs, refreshes, and policy checks now share a cleaner
    exclusion model, and this repo no longer relies on ad-hoc local overlays
    for universal artifact noise.
  Files:
  CHANGELOG.md
  devcovenant/builtin/policies/changelog_coverage/changelog_coverage.yaml
  devcovenant/builtin/policies/documentation_growth_tracking/\
    documentation_growth_tracking.yaml
  devcovenant/builtin/policies/line_length_limit/line_length_limit.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/builtin/profiles/global/assets/gitignore.yaml
  devcovenant/config.yaml
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py

- 2026-03-13:
  Change: Adjusted repo-local scope metadata to exclude transient
    `*.egg-info` build artifacts during rebuild-and-reinstall validation.
  Why: Prevented machine-level package validation slices from dragging local
    build metadata into changelog-governed session scope.
  Impact: Rebuild and reinstall checks now stay focused on real repository
    files while preserving governance on tracked project changes.
  Files:
  devcovenant/config.yaml

- 2026-03-13:
  Change: Adjusted `last-updated` builtin package-doc allowlists and
    diagnostics while adding regressions for installed-doc and lifecycle-state
    preservation behavior.
  Why: Prevented upgraded user repositories from warning on shipped
    DevCovenant docs and exposed effective allowlisted globs instead of
    misleading `only allowed in: none` suggestions.
  Impact: Installed repos now inherit safe `Last Updated` defaults for
    packaged docs, violation guidance is clearer, and refresh/upgrade
    preservation coverage is stronger.
  Files:
  devcovenant/builtin/policies/last_updated/last_updated.py
  devcovenant/builtin/policies/last_updated/last_updated.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/policies.md
  tests/devcovenant/builtin/policies/last_updated/test_last_updated.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_upgrade.py

- 2026-03-13:
  Change: Hardened upgrade custom-payload handling by pruning known
    repository-only custom paths leaked by older installs while preserving
    user custom policy/profile payload trees.
  Why: Prevented refresh/upgrade failures in user repositories caused by
    leaked repo-only custom scripts without descriptors and aligned upgrade
    behavior with the no-repo-custom-shipping contract.
  Impact: Upgrade now removes known leaked repo-only custom payload
    directories before refresh, preserves user custom trees, and is covered by
    new install/upgrade regressions plus updated workflow/installation/
    architecture docs.
  Files:
  CHANGELOG.md
  devcovenant/upgrade.py
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/workflow.md
  tests/devcovenant/test_install.py
  tests/devcovenant/test_upgrade.py

- 2026-03-09:
  Change: Documented gate changelog-helper default header-key alignment in
    workflow and architecture references.
  Why: Clarified that changelog exemption defaults now track generated header
    labels (`Last Updated`, `Project Version`, `DevCovenant Version`).
  Impact: Reduced doc/runtime drift risk for session-exemption behavior and
    made troubleshooting clearer for gate-start changelog checks.
  Files:
  devcovenant/docs/architecture.md
  devcovenant/docs/workflow.md

- 2026-03-09:
  Change: Renamed `last-updated-placement` to `last-updated`, migrated
    managed-doc header contracts to generated key fields, and hardened refresh
    preserve-block semantics.
  Why: Standardized policy/runtime naming and removed legacy header parsing so
    descriptor-governed docs and policy metadata remain deterministic.
  Impact: Strengthened forward-only release behavior by enforcing
    `Project Version` headers, preserving user blocks anywhere in managed docs,
    and documenting the migration across config/profile/runtime/test surfaces.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  PLAN.md
  POLICY_MAP.md
  PROFILE_MAP.md
  README.md
  SPEC.md
  devcovenant/builtin/policies/README.md
  devcovenant/builtin/policies/last_updated_placement/__init__.py
  devcovenant/builtin/policies/last_updated_placement/autofix/__init__.py
  devcovenant/builtin/policies/last_updated_placement/autofix/global.py
  devcovenant/builtin/policies/last_updated_placement/\
    last_updated_placement.py
  devcovenant/builtin/policies/last_updated_placement/\
    last_updated_placement.yaml
  devcovenant/builtin/policies/last_updated/__init__.py
  devcovenant/builtin/policies/last_updated/autofix/__init__.py
  devcovenant/builtin/policies/last_updated/autofix/global.py
  devcovenant/builtin/policies/last_updated/last_updated.py
  devcovenant/builtin/policies/last_updated/last_updated.yaml
  devcovenant/builtin/policies/version_sync/version_sync.py
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/CHANGELOG.yaml
  devcovenant/builtin/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/builtin/profiles/global/assets/LICENSE.yaml
  devcovenant/builtin/profiles/global/assets/PLAN.yaml
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/global/assets/SPEC.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/config.yaml
  devcovenant/core/README.md
  devcovenant/core/flow/gate_changelog_helpers.py
  devcovenant/core/flow/refresh.py
  devcovenant/core/lib/document_exemptions.py
  devcovenant/custom/README.md
  devcovenant/custom/policies/README.md
  devcovenant/custom/policies/managed_doc_assets/managed_doc_assets.py
  devcovenant/custom/profiles/README.md
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/translators.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/logs/README.md
  devcovenant/registry/README.md
  tests/devcovenant/builtin/policies/changelog_coverage/\
    test_changelog_coverage.py
  tests/devcovenant/builtin/policies/documentation_growth_tracking/\
    test_documentation_growth_tracking.py
  tests/devcovenant/builtin/policies/last_updated_placement/__init__.py
  tests/devcovenant/builtin/policies/last_updated_placement/autofix/\
    __init__.py
  tests/devcovenant/builtin/policies/last_updated_placement/autofix/\
    test_global.py
  tests/devcovenant/builtin/policies/last_updated_placement/\
    test_last_updated_placement.py
  tests/devcovenant/builtin/policies/last_updated/__init__.py
  tests/devcovenant/builtin/policies/last_updated/autofix/__init__.py
  tests/devcovenant/builtin/policies/last_updated/autofix/test_global.py
  tests/devcovenant/builtin/policies/last_updated/test_last_updated.py
  tests/devcovenant/builtin/policies/version_sync/test_version_sync.py
  tests/devcovenant/core/lib/test_document_exemptions.py
  tests/devcovenant/core/runtime/test_session_snapshot.py
  tests/devcovenant/custom/policies/managed_doc_assets/\
    test_managed_doc_assets.py
  tests/devcovenant/test_refresh.py

- 2026-03-09:
  Change: Replaced `CONTRIBUTING.md` and `SPEC.md` with current managed
    template outputs for a one-time baseline alignment.
  Why: Removed stale generic drift so both docs match current descriptor
    contract text and workflow guidance.
  Impact: Restored deterministic managed-doc baseline behavior for
    contributor/spec guidance in this repository.
  Files:
  CHANGELOG.md
  CONTRIBUTING.md
  SPEC.md

- 2026-03-09:
  Change: Hardened managed-doc descriptor validation in refresh and converted
    shipped doc asset templates to YAML literal block scalars.
  Why: Aligned descriptor schema enforcement with deterministic markdown
    generation to prevent template-serialization drift.
  Impact: Strengthened install/refresh reliability and local test coverage for
    descriptor contract failures outside CI-only execution.
  Files:
  CHANGELOG.md
  AGENTS.md
  devcovenant/config.yaml
  devcovenant/core/flow/refresh.py
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/builtin/profiles/global/assets/PLAN.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/docs/architecture.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  tests/devcovenant/test_refresh.py

- 2026-03-09:
  Change: Removed shipped-profile inventory lists from folder profile docs and
    clarified package docs to treat custom profiles as repository-owned.
  Why: Prevented documentation drift between folder contract docs and packaging
    behavior for builtin/custom profile payloads.
  Impact: Strengthened release-facing documentation clarity by keeping folder
    READMEs contract-focused and making custom-profile shipping boundaries
    explicit.
  Files:
  CHANGELOG.md
  devcovenant/builtin/profiles/README.md
  devcovenant/custom/profiles/README.md
  devcovenant/docs/profiles.md

- 2026-03-09:
  Change: Converted REST API doc assets to YAML template descriptors and
    wired them into the `restapi` custom profile asset list.
  Why: Enabled zero-setup seeding of core API contract docs when the profile
    is active, while aligning asset contracts to descriptor-based templates.
  Impact: Improved `restapi` profile usability and consistency for new repos
    by materializing `docs/api.md`, `docs/auth.md`, and `docs/errors.md`
    from YAML descriptors.
  Files:
  CHANGELOG.md
  PROFILE_MAP.md
  devcovenant/custom/profiles/README.md
  devcovenant/custom/profiles/restapi/restapi.yaml
  devcovenant/custom/profiles/restapi/assets/docs/api.yaml
  devcovenant/custom/profiles/restapi/assets/docs/auth.yaml
  devcovenant/custom/profiles/restapi/assets/docs/errors.yaml
  devcovenant/docs/profiles.md

- 2026-03-08:
  Change: Added a reusable `restapi` custom profile with strict API-focused
    policy overlays for docs routing, security scope, and test expectations.
  Why: Standardized endpoint-governance defaults so REST-heavy repositories
    can enable stronger API discipline without ad-hoc local policy wiring.
  Impact: Improved profile-level API hardening and documentation clarity for
    custom profile inventory, activation guidance, and REST policy intent.
  Files:
  CHANGELOG.md
  AGENTS.md
  PROFILE_MAP.md
  devcovenant/custom/profiles/README.md
  devcovenant/custom/profiles/restapi/restapi.yaml
  devcovenant/docs/profiles.md

- 2026-02-28:
  Change: Strengthened `no-raw-errors` to flag broad `except Exception`
    handlers and support explicit waiver markers/regions.
  Why: Prevented hidden broad-catch drift while preserving explicit boundary
    ownership through auditable waiver metadata.
  Impact: Improved explicit-failure enforcement consistency across runtime
    boundaries, policy/plugin isolation layers, and policy documentation.
  Files:
  CHANGELOG.md
  devcovenant/builtin/policies/no_raw_errors/no_raw_errors.py
  devcovenant/builtin/policies/no_raw_errors/no_raw_errors.yaml
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/policies/modules_need_tests/modules_need_tests.py
  devcovenant/builtin/policies/raw_string_escapes/raw_string_escapes.py
  devcovenant/builtin/policies/last_updated_placement/autofix/global.py
  devcovenant/cli.py
  devcovenant/core/services/event.py
  devcovenant/core/services/policy_autofix.py
  devcovenant/core/services/policy_check_runner.py
  devcovenant/core/services/policy_engine.py
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  tests/devcovenant/builtin/policies/no_raw_errors/\
    test_no_raw_errors.py
  tests/devcovenant/builtin/policies/last_updated_placement/autofix/\
    test_global.py

- 2026-02-28:
  Change: Implemented explicit runtime error contracts and CLI normalization,
    introduced builtin `no-raw-errors` policy with profile-owned metadata
    defaults, and swept docs/doc-assets to align contracts.
  Why: Standardized explicit failure surfaces at command boundaries and
    prevented raw Python error anti-pattern drift across repositories.
  Impact: Strengthened operator-facing error determinism, policy-governed
    explicit-error enforcement, and documentation fidelity for policy/profile
    ownership and runtime behavior.
  Files:
  CHANGELOG.md
  POLICY_MAP.md
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/devcovuser/devcovuser.yaml
  devcovenant/cli.py
  devcovenant/core/README.md
  devcovenant/core/contracts/__init__.py
  devcovenant/core/contracts/errors.py
  devcovenant/core/runtime/errors.py
  devcovenant/core/runtime/execution.py
  devcovenant/launcher_bootstrap.py
  devcovenant/builtin/policies/no_raw_errors/__init__.py
  devcovenant/builtin/policies/no_raw_errors/no_raw_errors.py
  devcovenant/builtin/policies/no_raw_errors/no_raw_errors.yaml
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/policies.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/profiles.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_launcher_bootstrap.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/contracts/test_errors.py
  tests/devcovenant/core/runtime/test_errors.py
  tests/devcovenant/builtin/policies/no_raw_errors/\
    test_no_raw_errors.py

- 2026-02-28:
  Change: Audited every repository Markdown doc and policy/profile doc-asset
    template, and aligned managed-environment re-exec wording across repo,
    packaged, and profile-template documentation.
  Why: Prevented documentation drift after managed-interpreter hardening so
    non-executable-path behavior and rerun fallback contracts stay explicit.
  Impact: Strengthened documentation/API clarity for operators and seeded repos
    while preserving existing command and policy behavior.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/config.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/builtin/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml

- 2026-02-28:
  Change: Hardened managed-interpreter auto-rerun by validating executable
    paths before `execve` and falling back to rerun adapters or explicit
    managed-environment errors.
  Why: Prevented raw `PermissionError` crashes when a configured managed
    interpreter path exists but is not executable.
  Impact: Improved CLI determinism for `check`/`gate`/`test` workflows with
    clear operator-facing failures and verified fallback behavior.
  Files:
  CHANGELOG.md
  devcovenant/cli.py
  devcovenant/docs/installation.md
  devcovenant/docs/workflow.md
  tests/devcovenant/test_cli.py

- 2026-02-28:
  Change: Stabilized read-only check bootstrap scope, quiet-mode error routing,
    and managed-environment defaults across policy/runtime layers.
  Why: Fixed false blocking in no-session audits and clarified output behavior
    so gate/test feedback remains deterministic and operator-visible.
  Impact: Strengthened API contracts and documentation fidelity while keeping
    strict gate enforcement for lifecycle commands and non-check paths.
  Files:
  CHANGELOG.md
  devcovenant/builtin/policies/changelog_coverage/changelog_coverage.py
  devcovenant/builtin/policies/devflow_run_gates/devflow_run_gates.py
  devcovenant/builtin/policies/managed_environment/managed_environment.py
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/builtin/profiles/devcovuser/devcovuser.yaml
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/core/contracts/policy.py
  devcovenant/core/runtime/execution.py
  devcovenant/core/services/policy_engine.py
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  tests/devcovenant/builtin/policies/changelog_coverage/\
    test_changelog_coverage.py
  tests/devcovenant/builtin/policies/devflow_run_gates/\
    test_devflow_run_gates.py
  tests/devcovenant/builtin/policies/managed_environment/\
    test_managed_environment.py
  tests/devcovenant/core/contracts/test_policy.py
  tests/devcovenant/core/runtime/test_execution.py
  tests/devcovenant/core/services/test_policy_engine.py

- 2026-02-28:
  Change: Fixed GitHub Actions workflow validity by replacing unsupported
    job-env `runner.temp` expressions with `.gha-pycache`.
  Why: Prevented immediate workflow parse failures that produced failed runs
    with no jobs for governance, build, and publish.
  Impact: Restored valid push-trigger governance execution while keeping build
    governance-dependent and publish manual-only.
  Files:
  CHANGELOG.md
  .github/workflows/build.yml
  .github/workflows/ci-and-test.yml
  .github/workflows/publish.yml
  devcovenant/builtin/profiles/global/assets/ci-and-test.yml
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md

- 2026-02-28:
  Change: Fixed GitHub Actions workflow env parsing by replacing job-level
    `${{ runner.temp }}` pycache expressions with a stable `.gha-pycache` path.
  Why: Prevented workflow-file validation failures that blocked governance,
    build, and publish runs before any jobs were created.
  Impact: Restored push-triggered governance execution, kept build dependent on
    governance success, and kept publish manual-only with valid workflow files.
  Files:
  CHANGELOG.md
  .github/workflows/build.yml
  .github/workflows/ci-and-test.yml
  .github/workflows/publish.yml
  devcovenant/builtin/profiles/global/assets/ci-and-test.yml
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md

- 2026-02-28:
  Change: Fixed governance workflow trigger rendering to emit canonical
    GitHub syntax (`on:`, `push:`, `pull_request:`) and validated it in
    refresh tests.
  Why: Prevented ambiguous serialized trigger forms (`'on':`, `*: null`) that
    can obscure push-trigger behavior after refresh regeneration.
  Impact: Kept governance/test activation on push explicit, preserved build as
    governance-dependent via `workflow_run`, and improved trigger reliability.
  Files:
  CHANGELOG.md
  .github/workflows/ci-and-test.yml
  devcovenant/core/flow/refresh.py
  devcovenant/docs/architecture.md
  devcovenant/docs/workflow.md
  tests/devcovenant/test_refresh.py

- 2026-02-28:
  Change: Fixed baseline recovery regressions in deploy/refresh test fixtures
    after accidental undo drift changed seeded-install expectations.
  Why: Restored contract alignment so seeded installs exclude shipped custom
    payload policy scripts while custom profile fixtures remain
    descriptor-valid.
  Impact: Stabilized `devcovenant test` and gate recovery in this repository
    by removing false failures from seeded refresh/deploy expectations.
  Files:
  CHANGELOG.md
  tests/devcovenant/core/services/test_profile_registry.py
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_install.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_upgrade.py

- 2026-02-28:
  Change: Fixed upgrade/install preservation contract to keep all user custom
    payload directories without name-based pruning, and tightened package
    build rules so repository-owned custom payloads do not ship.
  Why: Preservation semantics must be explicit and name-agnostic, while
    package payload leakage is prevented at build/install boundaries.
  Impact: Upgrade now preserves `devcovenant/custom/policies/*` and
    `devcovenant/custom/profiles/*` payloads as-is, and install/upgrade no
    longer depend on one-time cleanup behavior for leaked custom payloads.
  Files:
  CHANGELOG.md
  MANIFEST.in
  devcovenant/custom/profiles/__init__.py
  devcovenant/custom/profiles/devcovrepo/devcovrepo.yaml
  devcovenant/docs/installation.md
  devcovenant/docs/profiles.md
  devcovenant/docs/workflow.md
  devcovenant/install.py
  licenses/THIRD_PARTY_LICENSES.md
  pyproject.toml
  tests/devcovenant/test_install.py
  tests/devcovenant/test_deploy.py
  tests/devcovenant/test_refresh.py
  tests/devcovenant/test_upgrade.py

- 2026-02-28:
  Change: Fixed upgrade/refresh resilience by preserving custom policy trees
    while enforcing custom descriptor parity with core policies, and
    reconciled full shipped core files on every upgrade run.
  Why: Upgrade in user repositories could fail hard on stale custom policy
    scripts, and version-gated replacement could miss shipped
    `devcovenant/*.py` or builtin/core file updates.
  Impact: Preserved custom policy content, improved upgrade reliability, and
    ensured full shipped package files materialize on every upgrade run,
    with descriptor issues now blocking until fixed for both core and custom,
    without dropping repository `devcovenant/config.yaml`.
  Files:
  CHANGELOG.md
  devcovenant/docs/architecture.md
  devcovenant/docs/installation.md
  devcovenant/docs/workflow.md
  devcovenant/install.py
  devcovenant/upgrade.py
  tests/devcovenant/test_upgrade.py

- 2026-02-28:
  Change: Added a new builtin `opencl` language profile with translator/test
    coverage and aligned profile inventory docs so shipped language coverage is
    explicit for `opencl` and `rust`.
  Why: Expanded general-purpose language support for mixed Rust/OpenCL
    repositories while keeping profile contracts and translator ownership
    discoverable in packaged docs.
  Impact: Enabled baseline OpenCL suffix/policy/translator behavior without
    forcing toolchain-specific hooks, and improved release clarity for shipped
    language-profile coverage.
  Files:
  CHANGELOG.md
  PROFILE_MAP.md
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/opencl/opencl.yaml
  devcovenant/builtin/profiles/opencl/opencl_translator.py
  devcovenant/docs/profiles.md
  devcovenant/docs/translators.md
  tests/devcovenant/builtin/profiles/opencl/test_opencl_translator.py
  tests/devcovenant/core/services/test_profile_registry.py

- 2026-02-28:
  Change: Fixed managed-environment re-exec for lifecycle bootstrap commands
    and strengthened unmanaged-doc refresh sync to inject managed headers/
    blocks while preserving existing body content.
  Why: Fresh non-venv repos could fail lifecycle bootstrap before local policy
    scripts existed, `update_lock` required a tool that was not installed, and
    existing unmanaged docs did not receive managed headers/blocks on deploy.
  Impact: Improved machine-install reliability for lifecycle/update commands
    and preserved existing repo docs while standardizing managed headers/
    blocks during install/deploy/refresh.
  Files:
  CHANGELOG.md
  README.md
  devcovenant/cli.py
  devcovenant/core/flow/refresh.py
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/workflow.md
  licenses/THIRD_PARTY_LICENSES.md
  pyproject.toml
  requirements.in
  requirements.lock
  tests/devcovenant/test_cli.py
  tests/devcovenant/test_refresh.py

- 2026-02-27:
  Change: Updated repository documentation through a full `.md` sweep,
    standardized required `gate --mid` guidance across stale docs/templates,
    and removed the `audit_digest` runtime feature, code paths, and related
    tests from the refresh/registry surface.
  Why: Removed non-canonical drift artifacts and aligned release docs with the
    current gate/runtime contracts before the 1.0.0 baseline publish flow.
  Impact: Improved operator clarity, reduced maintenance surface, and kept one
    canonical workflow authority in AGENTS while preserving gate/test evidence
    behavior.
  Files:
  CHANGELOG.md
  PLAN.md
  README.md
  devcovenant/builtin/policies/README.md
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/global/assets/config.yaml
  devcovenant/core/README.md
  devcovenant/core/flow/refresh.py
  devcovenant/core/services/audit_digest.py
  devcovenant/core/services/registry.py
  devcovenant/custom/README.md
  devcovenant/custom/policies/README.md
  devcovenant/custom/profiles/README.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/installation.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/refresh.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/registry.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/troubleshooting.md
  devcovenant/custom/profiles/devcovrepo/assets/docs/workflow.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/profiles.md
  devcovenant/docs/registry.md
  devcovenant/docs/workflow.md
  devcovenant/registry/README.md
  tests/devcovenant/core/services/test_audit_digest.py
  tests/devcovenant/core/services/test_registry.py

- 2026-02-27:
  Change: Updated README banner tags to one-line absolute GitHub raw URLs,
    enabled defaults profile long-line escape toggles, and fixed policy-def
    metadata parsing so colon-containing continuation values stay intact for
    URL prefixes and long-line marker lists.
  Why: Fixed README/PyPI image rendering and removed parser drift that could
    truncate `allow_long_url_lines`, `long_lines_contain`, and
    `long_lines_between` metadata values.
  Impact: Improved release-readme reliability and strengthened line-length
    escape-hatch behavior so both long-line regimes and URL-based allowances
    apply consistently from managed policy metadata.
  Files:
  AGENTS.md
  CHANGELOG.md
  README.md
  devcovenant/builtin/profiles/defaults/defaults.yaml
  devcovenant/config.yaml
  devcovenant/core/services/policy_parse.py
  devcovenant/docs/architecture.md
  devcovenant/docs/profiles.md
  tests/devcovenant/core/services/test_policy_parse.py

- 2026-02-27:
  Change: Standardized the public `1.0.0` changelog surface by removing
    pre-1.0 internal history and keeping release-baseline entries only.
  Why: Clarified external release documentation and removed internal
    stabilization details from the public narrative.
  Impact: Reduced historical exposure while preserving `1.0.0` baseline
    traceability for current operators.
  Files:
  AGENTS.md
  CHANGELOG.md

- 2026-02-27:
  Change: Updated repository and package version surfaces from `0.2.6` to
    `1.0.0` across runtime metadata, docs headers, and global template assets.
  Why: Aligned stabilization state with release intent before mainline
    orchestration and cleanup decisions.
  Impact: Strengthened a consistent 1.0.0 baseline without changing runtime
    semantics or API contracts.
  Files:
  AGENTS.md
  CHANGELOG.md
  CONTRIBUTING.md
  LICENSE
  PLAN.md
  POLICY_MAP.md
  PROFILE_MAP.md
  README.md
  SPEC.md
  devcovenant/VERSION
  devcovenant/__init__.py
  devcovenant/builtin/policies/README.md
  devcovenant/builtin/profiles/README.md
  devcovenant/builtin/profiles/global/assets/AGENTS.yaml
  devcovenant/builtin/profiles/global/assets/CHANGELOG.yaml
  devcovenant/builtin/profiles/global/assets/CONTRIBUTING.yaml
  devcovenant/builtin/profiles/global/assets/LICENSE.yaml
  devcovenant/builtin/profiles/global/assets/PLAN.yaml
  devcovenant/builtin/profiles/global/assets/README.yaml
  devcovenant/builtin/profiles/global/assets/SPEC.yaml
  devcovenant/builtin/profiles/global/assets/devcovenant/README.yaml
  devcovenant/core/README.md
  devcovenant/custom/README.md
  devcovenant/custom/policies/README.md
  devcovenant/custom/profiles/README.md
  devcovenant/docs/architecture.md
  devcovenant/docs/config.md
  devcovenant/docs/installation.md
  devcovenant/docs/policies.md
  devcovenant/docs/profiles.md
  devcovenant/docs/refresh.md
  devcovenant/docs/registry.md
  devcovenant/docs/translators.md
  devcovenant/docs/troubleshooting.md
  devcovenant/docs/workflow.md
  devcovenant/registry/README.md
  licenses/THIRD_PARTY_LICENSES.md
  pyproject.toml
