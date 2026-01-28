"""Tests for patches-txt-sync policy."""

from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.patches_txt_sync import patches_txt_sync

PatchesTxtSyncCheck = patches_txt_sync.PatchesTxtSyncCheck


def _write_patches_file(path: Path, content: str) -> None:
    """Write patches.txt content."""
    path.write_text(content, encoding="utf-8")


def _write_patch_file(root: Path, rel: str) -> Path:
    """Create a dummy patch file."""
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# patch\n", encoding="utf-8")
    return target


def _make_checker() -> PatchesTxtSyncCheck:
    """Return a checker with metadata defaults applied."""
    checker = PatchesTxtSyncCheck()
    checker.set_options(
        {
            "patches_file": "app/gcv_erp_custom/patches.txt",
            "include_globs": ["app/gcv_erp_custom/patches/**/gcv_*.py"],
            "sections": ["pre_model_sync", "post_model_sync"],
            "enforce_missing": True,
            "enforce_unused": True,
            "enforce_duplicates": True,
            "enforce_sorted": True,
            "enforce_sections": True,
        },
        {},
    )
    return checker


def test_missing_patch_entry_detected(tmp_path: Path) -> None:
    """Missing patch file registrations should fail."""
    _write_patch_file(tmp_path, "app/gcv_erp_custom/patches/v0_1/gcv_alpha.py")
    patches_path = tmp_path / "app" / "gcv_erp_custom" / "patches.txt"
    patches_path.parent.mkdir(parents=True, exist_ok=True)
    _write_patches_file(
        patches_path,
        "[post_model_sync]\n",
    )

    checker = _make_checker()
    context = CheckContext(
        repo_root=tmp_path,
        all_files=[
            tmp_path
            / "app"
            / "gcv_erp_custom"
            / "patches"
            / "v0_1"
            / "gcv_alpha.py"
        ],
    )
    violations = checker.check(context)

    assert violations
    assert any("missing" in v.message for v in violations)


def test_unused_patch_entry_detected(tmp_path: Path) -> None:
    """Patch entries without files should fail."""
    patches_path = tmp_path / "app" / "gcv_erp_custom" / "patches.txt"
    patches_path.parent.mkdir(parents=True, exist_ok=True)
    _write_patches_file(
        patches_path,
        "[post_model_sync]\n" "gcv_erp_custom.patches.v0_1.gcv_missing\n",
    )

    checker = _make_checker()
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    assert any("no matching file" in v.message for v in violations)


def test_duplicate_patch_entries_detected(tmp_path: Path) -> None:
    """Duplicate patch entries should fail."""
    patches_path = tmp_path / "app" / "gcv_erp_custom" / "patches.txt"
    patches_path.parent.mkdir(parents=True, exist_ok=True)
    _write_patches_file(
        patches_path,
        "[post_model_sync]\n"
        "gcv_erp_custom.patches.v0_1.gcv_dup\n"
        "gcv_erp_custom.patches.v0_1.gcv_dup\n",
    )

    checker = _make_checker()
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    assert any("duplicated" in v.message for v in violations)


def test_unsorted_section_detected(tmp_path: Path) -> None:
    """Out-of-order patches should fail when sorting is enforced."""
    patches_path = tmp_path / "app" / "gcv_erp_custom" / "patches.txt"
    patches_path.parent.mkdir(parents=True, exist_ok=True)
    _write_patches_file(
        patches_path,
        "[post_model_sync]\n"
        "gcv_erp_custom.patches.v0_1.gcv_zeta\n"
        "gcv_erp_custom.patches.v0_1.gcv_alpha\n",
    )

    checker = _make_checker()
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    assert any("sorted" in v.message for v in violations)


def test_entries_outside_sections_detected(tmp_path: Path) -> None:
    """Patch entries outside section headers should fail."""
    patches_path = tmp_path / "app" / "gcv_erp_custom" / "patches.txt"
    patches_path.parent.mkdir(parents=True, exist_ok=True)
    _write_patches_file(
        patches_path,
        "gcv_erp_custom.patches.v0_1.gcv_orphan\n" "[post_model_sync]\n",
    )

    checker = _make_checker()
    context = CheckContext(repo_root=tmp_path, all_files=[])
    violations = checker.check(context)

    assert violations
    assert any("outside a section" in v.message for v in violations)
