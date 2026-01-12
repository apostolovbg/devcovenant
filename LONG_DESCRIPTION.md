DevCovenant is a self-enforcing policy engine that aligns documentation,
policy prose, and automated enforcement. Install the CLI, target a repository,
and DevCovenant manages the full DevFlow gate sequence. It runs the registered
pre-commit hooks at the beginning of a change window, launches every configured
test suite, and finishes with the closing pre-commit run, all while recording
those runs inside `devcovenant/test_status.json`.

Policy definitions live in `AGENTS.md`, so the human-readable rules stay
in sync with the scripts that enforce them. DevCovenant reads those policy
blocks, loads the matching scripts under `devcovenant/core/policy_scripts`,
applies optional fixers from `devcovenant/core/fixers`.
DevCovenant also tracks every hash in `devcovenant/registry.json` to prevent
drift. Custom repo checks belong under `devcovenant/custom/policy_scripts` and
`devcovenant/custom/fixers`, and the installer keeps these directories intact
via `--preserve-custom` when updating.

Installing DevCovenant injects helper scripts such as `tools/run_pre_commit.py`
and `tools/run_tests.py` plus the manifest tracking files so you can cleanly
undo the install. The published package also exposes `devcov_check.py` for gate
automation and a `publish.yml` workflow that builds the wheel/sdist, verifies
them with `twine check`, and uploads to PyPI when you tag a release.
