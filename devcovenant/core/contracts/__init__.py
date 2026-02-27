"""Contract-layer package exports for shared policy contracts."""

from __future__ import annotations

import importlib

_MODULE_MAP = {
    "policy": "devcovenant.core.contracts.policy",
}


def __getattr__(name: str):
    """Lazily resolve contract-layer modules for compatibility."""
    module_path = _MODULE_MAP.get(name)
    if module_path is None:
        raise AttributeError(name)
    module = importlib.import_module(module_path)
    globals()[name] = module
    return module


__all__ = sorted(_MODULE_MAP)
