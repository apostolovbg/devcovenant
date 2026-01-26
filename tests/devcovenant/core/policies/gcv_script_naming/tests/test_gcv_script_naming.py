"""Tests for the gcv script naming policy."""

from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.gcv_script_naming import gcv_script_naming

GcvScriptNamingCheck = gcv_script_naming.GcvScriptNamingCheck


def _touch_file(root: Path, rel: str) -> Path:
    """Create a stub Python file under the temporary repo root."""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# stub\n")
    return path


def test_prefixed_file_in_custom_app_passes(tmp_path: Path) -> None:
    """Enforce that properly prefixed files raise no violations."""
    file_path = _touch_file(tmp_path, "app/gcv_erp_custom/gcv_valid.py")
    checker = GcvScriptNamingCheck()
    context = CheckContext(repo_root=tmp_path, all_files=[file_path])

    violations = checker.check(context)

    assert violations == []


def test_missing_prefix_in_custom_app_detected(tmp_path: Path) -> None:
    """Detect files in the custom app that lack the required prefix."""
    file_path = _touch_file(tmp_path, "app/gcv_erp_custom/bad.py")
    checker = GcvScriptNamingCheck()
    context = CheckContext(repo_root=tmp_path, all_files=[file_path])

    violations = checker.check(context)

    assert len(violations) == 1
    violation = violations[0]
    assert violation.policy_id == "gcv-script-naming"
    assert "bad.py" in violation.message


def test_init_file_exempt(tmp_path: Path) -> None:
    """Allow package init files to skip the naming rule."""
    file_path = _touch_file(tmp_path, "app/gcv_erp_custom/__init__.py")
    checker = GcvScriptNamingCheck()
    context = CheckContext(repo_root=tmp_path, all_files=[file_path])

    violations = checker.check(context)

    assert violations == []


def test_files_outside_custom_app_ignored(tmp_path: Path) -> None:
    """Skip files that live outside the targeted directory."""
    file_path = _touch_file(tmp_path, "app/another/gcv_custom.py")
    checker = GcvScriptNamingCheck()
    context = CheckContext(repo_root=tmp_path, all_files=[file_path])

    violations = checker.check(context)

    assert violations == []


def test_doctype_controller_is_exempt(tmp_path: Path) -> None:
    """Allow DocType controllers to follow Frappe naming."""
    file_path = _touch_file(
        tmp_path,
        "app/gcv_erp_custom/gcv_erp_custom/doctype/pack_family/pack_family.py",
    )
    checker = GcvScriptNamingCheck()
    context = CheckContext(repo_root=tmp_path, all_files=[file_path])

    violations = checker.check(context)

    assert violations == []
