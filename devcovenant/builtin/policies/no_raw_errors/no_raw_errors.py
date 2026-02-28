"""Policy: detect raw error anti-patterns in Python source files."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import List

from devcovenant.core.contracts.policy import (
    CheckContext,
    PolicyCheck,
    Violation,
)
from devcovenant.core.lib.selectors import SelectorSet

_VALID_SEVERITIES = {"critical", "error", "warning", "info"}


def _coerce_bool(value: object, *, default: bool) -> bool:
    """Return a bool parsed from metadata/config values."""
    if isinstance(value, bool):
        return value
    token = str(value).strip().lower()
    if token in {"true", "1", "yes", "on", "enabled"}:
        return True
    if token in {"false", "0", "no", "off", "disabled"}:
        return False
    return default


def _is_exception_name(node: ast.AST | None) -> bool:
    """Return True when node represents Exception/BaseException."""
    if isinstance(node, ast.Name):
        return node.id in {"Exception", "BaseException"}
    return False


def _is_broad_exception_handler(node: ast.ExceptHandler) -> bool:
    """Return True when except handler targets Exception/BaseException."""
    if node.type is None:
        return False
    if _is_exception_name(node.type):
        return True
    if isinstance(node.type, ast.Tuple):
        return any(_is_exception_name(item) for item in node.type.elts)
    return False


def _is_generic_exception_raise(node: ast.Raise) -> bool:
    """Return True when raise targets Exception/BaseException constructors."""
    target = node.exc
    if target is None:
        return False
    if _is_exception_name(target):
        return True
    if isinstance(target, ast.Call):
        return _is_exception_name(target.func)
    return False


def _is_silent_pass_handler(node: ast.ExceptHandler) -> bool:
    """Return True for handlers that only contain `pass`."""
    return len(node.body) == 1 and isinstance(node.body[0], ast.Pass)


class NoRawErrorsCheck(PolicyCheck):
    """Block raw error anti-patterns that hide explicit failure intent."""

    policy_id = "no-raw-errors"
    version = "1.0.0"

    def _severity(self) -> str:
        """Return normalized policy severity."""
        raw = str(self.get_option("severity", "error")).strip().lower()
        if raw in _VALID_SEVERITIES:
            return raw
        return "error"

    def _selector(self) -> SelectorSet:
        """Return merged selector metadata for this policy."""
        defaults = {"include_suffixes": [".py"], "include_globs": ["*.py"]}
        return SelectorSet.from_policy(self, defaults=defaults)

    def check(self, context: CheckContext) -> List[Violation]:
        """Scan in-scope Python files for raw error anti-patterns."""
        files = context.all_files or context.changed_files or []
        selector = self._selector()
        severity = self._severity()
        forbid_bare_except = _coerce_bool(
            self.get_option("forbid_bare_except", True),
            default=True,
        )
        forbid_raise_exception = _coerce_bool(
            self.get_option("forbid_raise_exception", True),
            default=True,
        )
        forbid_silent_exception_pass = _coerce_bool(
            self.get_option("forbid_silent_exception_pass", True),
            default=True,
        )

        violations: List[Violation] = []
        for path in files:
            candidate = Path(path)
            if candidate.suffix.lower() != ".py":
                continue
            if not selector.matches(candidate, context.repo_root):
                continue
            try:
                source = candidate.read_text(encoding="utf-8")
            except OSError as error:
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity=severity,
                        file_path=candidate,
                        message=(
                            "Unable to read Python source while validating "
                            f"raw errors: {error}"
                        ),
                        suggestion=(
                            "Restore readable UTF-8 source and rerun checks."
                        ),
                    )
                )
                continue
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    if forbid_bare_except and node.type is None:
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity=severity,
                                file_path=candidate,
                                line_number=node.lineno,
                                message=(
                                    "Bare `except:` is not allowed; catch "
                                    "specific exception types."
                                ),
                                suggestion=(
                                    "Catch explicit exception classes and "
                                    "raise/report explicit failures."
                                ),
                            )
                        )
                    if (
                        forbid_silent_exception_pass
                        and _is_broad_exception_handler(node)
                        and _is_silent_pass_handler(node)
                    ):
                        violations.append(
                            Violation(
                                policy_id=self.policy_id,
                                severity=severity,
                                file_path=candidate,
                                line_number=node.lineno,
                                message=(
                                    "Silent `except Exception: pass` hides "
                                    "failures."
                                ),
                                suggestion=(
                                    "Handle explicitly with error context or "
                                    "narrow the exception to expected cases."
                                ),
                            )
                        )
                    continue

                if (
                    forbid_raise_exception
                    and isinstance(node, ast.Raise)
                    and _is_generic_exception_raise(node)
                ):
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity=severity,
                            file_path=candidate,
                            line_number=node.lineno,
                            message=(
                                "Generic `raise Exception(...)` is not "
                                "allowed."
                            ),
                            suggestion=(
                                "Raise a specific exception type with "
                                "explicit failure context."
                            ),
                        )
                    )

        return violations
