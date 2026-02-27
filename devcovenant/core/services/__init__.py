"""Service-layer package exports for policy/profile/runtime services."""

from __future__ import annotations

import importlib

_MODULE_MAP = {
    "event": "devcovenant.core.services.event",
    "metadata": "devcovenant.core.services.metadata",
    "policy_block_refresh": "devcovenant.core.services.policy_block_refresh",
    "policy_engine": "devcovenant.core.services.policy_engine",
    "policy_parse": "devcovenant.core.services.policy_parse",
    "profile_registry": "devcovenant.core.services.profile_registry",
    "registry": "devcovenant.core.services.registry",
    "translator_engine": "devcovenant.core.services.translator_engine",
}


def __getattr__(name: str):
    """Lazily resolve service-layer modules for compatibility."""
    module_path = _MODULE_MAP.get(name)
    if module_path is None:
        raise AttributeError(name)
    module = importlib.import_module(module_path)
    globals()[name] = module
    return module


__all__ = sorted(_MODULE_MAP)
