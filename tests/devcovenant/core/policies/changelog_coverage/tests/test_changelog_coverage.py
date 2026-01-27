"""Mirror for the changelog-coverage tests living inside the policy package."""

from importlib import import_module

_module = import_module(
    "tests.devcovenant.core.policies.changelog_coverage.tests."
    "changelog_coverage_impl"
)
for _name in dir(_module):
    if _name.startswith("test_"):
        globals()[_name] = getattr(_module, _name)
