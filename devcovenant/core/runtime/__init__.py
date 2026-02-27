"""Runtime-layer package exports for execution and snapshot boundaries."""

from __future__ import annotations

import importlib

_MODULE_MAP = {
    "execution": "devcovenant.core.runtime.execution",
    "run_logging": "devcovenant.core.runtime.run_logging",
    "session_snapshot": "devcovenant.core.runtime.session_snapshot",
}


def __getattr__(name: str):
    """Lazily resolve runtime-layer modules for compatibility."""
    module_path = _MODULE_MAP.get(name)
    if module_path is None:
        raise AttributeError(name)
    module = importlib.import_module(module_path)
    globals()[name] = module
    return module


__all__ = sorted(_MODULE_MAP)
