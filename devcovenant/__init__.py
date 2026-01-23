"""
DevCovenant - Self-enforcing policy system.

This system parses policy definitions from AGENTS.md, maintains policy
scripts, and enforces policies automatically during development.
"""

__version__ = "0.2.6"

from devcovenant.core.engine import DevCovenantEngine
from devcovenant.core.parser import PolicyParser
from devcovenant.core.registry import PolicyRegistry

__all__ = ["DevCovenantEngine", "PolicyParser", "PolicyRegistry"]
