"""Flow-layer package exports for orchestrated command/session behavior."""

from __future__ import annotations

import importlib

_MODULE_MAP = {
    "clean": "devcovenant.core.flow.clean",
    "gate": "devcovenant.core.flow.gate",
    "refresh": "devcovenant.core.flow.refresh",
    "session": "devcovenant.core.flow.session",
}


def __getattr__(name: str):
    """Lazily resolve flow-layer modules for compatibility."""
    module_path = _MODULE_MAP.get(name)
    if module_path is None:
        raise AttributeError(name)
    module = importlib.import_module(module_path)
    globals()[name] = module
    return module


__all__ = sorted(_MODULE_MAP)
