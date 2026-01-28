"""
Tests for the custom profile-policy map synchronization policy.
"""

from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.custom.policies.profile_policy_map.profile_policy_map import (
    ProfilePolicyMapCheck,
)


def _repo_root() -> Path:
    """Find the repository root by walking up from this test file."""

    path = Path(__file__).resolve()
    while path.name != "tests":
        path = path.parent
    return path.parent


def test_profile_policy_map_succeeds():
    """The repository ships maps that cover every shipped profile
    and policy.
    """

    context = CheckContext(
        repo_root=_repo_root(),
    )
    check = ProfilePolicyMapCheck()
    assert not check.check(context)
