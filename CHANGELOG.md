# Changelog
**Doc ID:** CHANGELOG
**Doc Type:** changelog
**Project Version:** 1.0.0
**Project Stage:** stable
**Maintenance Stance:** active
**Compatibility Policy:** breaking-allowed
**Versioning Mode:** versioned
**Last Updated:** 2026-03-24
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
  Why: Clarified how project phase, development stance, and intentionally
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
