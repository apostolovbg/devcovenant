"""Compatibility shim; import from common_policy_scripts."""

from devcovenant.common_policy_scripts import line_length_limit as _policy

__all__ = [name for name in _policy.__dict__ if not name.startswith("__")]

for name in __all__:
    globals()[name] = getattr(_policy, name)
