#!/usr/bin/env python3
"""Install or update DevCovenant in a target repository."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DEV_COVENANT_DIR = "devcovenant"
CORE_PATHS = [
    DEV_COVENANT_DIR,
    "devcov_check.py",
    "tools/run_pre_commit.py",
    "tools/run_tests.py",
    "tools/update_test_status.py",
]

CONFIG_PATHS = [
    ".pre-commit-config.yaml",
    ".github/workflows/ci.yml",
    ".gitignore",
]

DOC_PATHS = [
    "AGENTS.md",
    "README.md",
    "DEVCOVENANT.md",
    "CONTRIBUTING.md",
    "SPEC.md",
    "PLAN.md",
    "CHANGELOG.md",
]

METADATA_PATHS = [
    "VERSION",
    "LICENSE",
    "CITATION.cff",
    "pyproject.toml",
]

MANIFEST_PATH = ".devcov/install_manifest.json"
LEGACY_MANIFEST_PATH = ".devcovenant/install_manifest.json"
BLOCK_BEGIN = "<!-- DEVCOV:BEGIN -->"
BLOCK_END = "<!-- DEVCOV:END -->"
LICENSE_TEMPLATE = "tools/templates/LICENSE_GPL-3.0.txt"
DEFAULT_PRESERVE_PATHS = [
    "custom/policy_scripts",
    "common_policy_patches",
    "config.yaml",
]
DOC_BLOCKS = {
    "README.md": (
        f"{BLOCK_BEGIN}\n"
        "**Read first:** `AGENTS.md` is the canonical source of truth. "
        "See `DEVCOVENANT.md` for architecture and lifecycle details.\n"
        f"{BLOCK_END}\n"
    ),
    "CONTRIBUTING.md": (
        f"{BLOCK_BEGIN}\n"
        "**Read first:** `AGENTS.md` is canonical. `DEVCOVENANT.md` explains "
        "the architecture and lifecycle.\n"
        f"{BLOCK_END}\n"
    ),
}

_CORE_CONFIG_INCLUDE_KEY = "devcov_core_include:"
_CORE_CONFIG_PATHS_KEY = "devcov_core_paths:"
_DEFAULT_CORE_PATHS = [
    "devcovenant/core",
    "devcovenant/__init__.py",
    "devcovenant/__main__.py",
    "devcovenant/cli.py",
    "devcov_check.py",
    "tools/run_pre_commit.py",
    "tools/run_tests.py",
    "tools/update_test_status.py",
    "tools/install_devcovenant.py",
    "tools/uninstall_devcovenant.py",
]


def _normalize_core_paths(paths: list[str]) -> list[str]:
    """Return cleaned core path entries."""
    cleaned: list[str] = []
    for entry in paths:
        text = str(entry).strip()
        if text:
            cleaned.append(text)
    return cleaned or list(_DEFAULT_CORE_PATHS)


def _update_core_config_text(
    text: str, include_core: bool, core_paths: list[str]
) -> tuple[str, bool]:
    """Update devcov core configuration values in config.yaml."""
    lines = text.splitlines()
    updated_lines: list[str] = []
    found_include = False
    found_paths = False
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith(_CORE_CONFIG_INCLUDE_KEY):
            updated_lines.append(
                f"devcov_core_include: {'true' if include_core else 'false'}"
            )
            found_include = True
            index += 1
            continue
        if stripped.startswith(_CORE_CONFIG_PATHS_KEY):
            updated_lines.append("devcov_core_paths:")
            found_paths = True
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if next_line.strip().startswith("-"):
                    index += 1
                    continue
                break
            for path in _normalize_core_paths(core_paths):
                updated_lines.append(f"  - {path}")
            continue
        updated_lines.append(line)
        index += 1

    if found_include and found_paths:
        updated = "\n".join(updated_lines) + "\n"
        return updated, updated != text

    insert_block = [
        "# DevCovenant core exclusion guard.",
        "devcov_core_include: " + ("true" if include_core else "false"),
        "devcov_core_paths:",
    ]
    insert_block.extend(
        f"  - {path}" for path in _normalize_core_paths(core_paths)
    )
    insert_block.append("")
    insert_at = 0
    for idx, line in enumerate(updated_lines):
        if line.strip() and not line.strip().startswith("#"):
            insert_at = idx
            break
    updated_lines[insert_at:insert_at] = insert_block
    updated = "\n".join(updated_lines) + "\n"
    return updated, updated != text


def _apply_core_config(target_root: Path, include_core: bool) -> bool:
    """Ensure devcov core config matches the install target."""
    config_path = target_root / DEV_COVENANT_DIR / "config.yaml"
    if not config_path.exists():
        return False
    text = config_path.read_text(encoding="utf-8")
    updated, changed = _update_core_config_text(
        text,
        include_core=include_core,
        core_paths=_DEFAULT_CORE_PATHS,
    )
    if not changed:
        return False
    config_path.write_text(updated, encoding="utf-8")
    return True


def _copy_path(source: Path, target: Path) -> None:
    """Copy a file or directory from source to target."""
    if source.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        return
    if target.exists():
        _rename_existing_file(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _rename_existing_file(target: Path) -> None:
    """Rename an existing file to preserve it before overwriting."""
    if not target.exists() or target.is_dir():
        return
    suffix = target.suffix
    stem = target.stem
    candidate = target.with_name(f"{stem}_old{suffix}")
    index = 2
    while candidate.exists():
        candidate = target.with_name(f"{stem}_old{index}{suffix}")
        index += 1
    target.rename(candidate)


def _copy_dir_contents(source: Path, target: Path) -> None:
    """Copy contents of source dir into target dir."""
    if not source.exists():
        return
    target.mkdir(parents=True, exist_ok=True)
    for entry in source.iterdir():
        dest = target / entry.name
        if entry.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(entry, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, dest)


def _backup_paths(root: Path, paths: list[str], backup_root: Path) -> None:
    """Backup selected paths into backup_root."""
    for rel in paths:
        src = root / rel
        if not src.exists():
            continue
        dest = backup_root / rel
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def _restore_paths(backup_root: Path, root: Path, paths: list[str]) -> None:
    """Restore backed-up paths into root."""
    for rel in paths:
        src = backup_root / rel
        if not src.exists():
            continue
        dest = root / rel
        if src.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


def _install_devcovenant_dir(
    source_root: Path,
    target_root: Path,
    preserve_paths: list[str],
    preserve_existing: bool,
) -> list[str]:
    """Install the devcovenant directory while preserving custom paths."""
    source = source_root / DEV_COVENANT_DIR
    target = target_root / DEV_COVENANT_DIR
    installed: list[str] = []
    if not source.exists():
        return installed

    if not target.exists() or not preserve_existing:
        _copy_path(source, target)
        installed.append(DEV_COVENANT_DIR)
        return installed

    with tempfile.TemporaryDirectory() as tmpdir:
        backup_root = Path(tmpdir)
        _backup_paths(target, preserve_paths, backup_root)
        _copy_path(source, target)
        _restore_paths(backup_root, target, preserve_paths)

    installed.append(DEV_COVENANT_DIR)
    return installed


def _install_paths(
    repo_root: Path,
    target_root: Path,
    paths: list[str],
    skip_existing: bool,
    source_overrides: dict[str, Path] | None = None,
) -> list[str]:
    """Copy paths and return installed file list."""
    installed: list[str] = []
    overrides = source_overrides or {}
    for rel_path in paths:
        source = overrides.get(rel_path, repo_root / rel_path)
        target = target_root / rel_path
        if not source.exists():
            continue
        if skip_existing and target.exists():
            continue
        _copy_path(source, target)
        installed.append(rel_path)
    return installed


def _inject_block(path: Path, block: str) -> bool:
    """Insert or replace a DevCovenant block in a documentation file."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    if BLOCK_BEGIN in text and BLOCK_END in text:
        before, _rest = text.split(BLOCK_BEGIN, 1)
        _old_block, after = _rest.split(BLOCK_END, 1)
        updated = f"{before}{block}{after}"
        if updated == text:
            return False
        path.write_text(updated, encoding="utf-8")
        return True

    lines = text.splitlines(keepends=True)
    insert_at = 0
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            insert_at = index + 1
            break
    lines.insert(insert_at, block)
    path.write_text("".join(lines), encoding="utf-8")
    return True


def main(argv=None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Install or update DevCovenant in a target repository."
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Target repository path (default: current directory).",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "empty", "existing"),
        default="auto",
        help="Install mode (auto detects existing installs).",
    )
    parser.add_argument(
        "--docs-mode",
        choices=("preserve", "overwrite"),
        default=None,
        help="How to handle docs in existing repos.",
    )
    parser.add_argument(
        "--config-mode",
        choices=("preserve", "overwrite"),
        default=None,
        help="How to handle config files in existing repos.",
    )
    parser.add_argument(
        "--metadata-mode",
        choices=("preserve", "overwrite", "skip"),
        default=None,
        help="How to handle metadata files in existing repos.",
    )
    parser.add_argument(
        "--license-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        default="inherit",
        help="Override the metadata mode for LICENSE.",
    )
    parser.add_argument(
        "--version-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        default="inherit",
        help="Override the metadata mode for VERSION.",
    )
    parser.add_argument(
        "--pyproject-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        default="inherit",
        help="Override the metadata mode for pyproject.toml.",
    )
    parser.add_argument(
        "--ci-mode",
        choices=("inherit", "preserve", "overwrite", "skip"),
        default="inherit",
        help="Override the config mode for CI workflow files.",
    )
    parser.add_argument(
        "--preserve-custom",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Preserve custom policy scripts and patches during updates.",
    )
    parser.add_argument(
        "--force-docs",
        action="store_true",
        help="Overwrite docs and metadata on update.",
    )
    parser.add_argument(
        "--force-config",
        action="store_true",
        help="Overwrite config files on update.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    target_root = Path(args.target).resolve()
    manifest_file = target_root / MANIFEST_PATH
    legacy_manifest = target_root / LEGACY_MANIFEST_PATH
    has_manifest = manifest_file.exists() or legacy_manifest.exists()
    has_existing = has_manifest or (target_root / DEV_COVENANT_DIR).exists()
    if args.mode == "auto":
        mode = "existing" if has_existing else "empty"
    else:
        mode = args.mode

    docs_mode = args.docs_mode
    config_mode = args.config_mode
    metadata_mode = args.metadata_mode

    if args.force_docs:
        docs_mode = "overwrite"
    if args.force_config:
        config_mode = "overwrite"

    if docs_mode is None:
        docs_mode = "overwrite" if mode == "empty" else "preserve"
    if config_mode is None:
        config_mode = "overwrite" if mode == "empty" else "preserve"
    if metadata_mode is None:
        metadata_mode = "overwrite" if mode == "empty" else "preserve"

    def _resolve_override(override_value: str) -> str:
        """Return the resolved metadata mode for a CLI override."""
        return metadata_mode if override_value == "inherit" else override_value

    license_mode = _resolve_override(args.license_mode)
    version_mode = _resolve_override(args.version_mode)
    pyproject_mode = _resolve_override(args.pyproject_mode)
    ci_mode = config_mode if args.ci_mode == "inherit" else args.ci_mode

    preserve_custom = args.preserve_custom
    if preserve_custom is None:
        preserve_custom = mode == "existing"

    installed: dict[str, list[str]] = {"core": [], "config": [], "docs": []}
    doc_blocks: list[str] = []

    installed["core"].extend(
        _install_devcovenant_dir(
            repo_root,
            target_root,
            DEFAULT_PRESERVE_PATHS if preserve_custom else [],
            preserve_existing=preserve_custom,
        )
    )
    installed["core"].extend(
        _install_paths(
            repo_root,
            target_root,
            [path for path in CORE_PATHS if path != DEV_COVENANT_DIR],
            skip_existing=False,
        )
    )

    config_paths = CONFIG_PATHS[:]
    if ci_mode == "skip":
        config_paths = [
            path for path in config_paths if path != ".github/workflows/ci.yml"
        ]

    installed["config"] = _install_paths(
        repo_root,
        target_root,
        config_paths,
        skip_existing=(mode == "existing" and config_mode == "preserve"),
    )
    include_core = target_root == repo_root
    _apply_core_config(target_root, include_core)

    metadata_paths = METADATA_PATHS[:]
    if metadata_mode == "skip":
        metadata_paths = []
    if license_mode == "skip":
        metadata_paths = [path for path in metadata_paths if path != "LICENSE"]
    if version_mode == "skip":
        metadata_paths = [path for path in metadata_paths if path != "VERSION"]
    if pyproject_mode == "skip":
        metadata_paths = [
            path for path in metadata_paths if path != "pyproject.toml"
        ]

    installed["docs"] = _install_paths(
        repo_root,
        target_root,
        DOC_PATHS,
        skip_existing=(mode == "existing" and docs_mode == "preserve"),
    )
    installed["docs"].extend(
        _install_paths(
            repo_root,
            target_root,
            metadata_paths,
            skip_existing=(mode == "existing" and metadata_mode == "preserve"),
            source_overrides={
                "LICENSE": repo_root / LICENSE_TEMPLATE,
            },
        )
    )

    for doc_name, block in DOC_BLOCKS.items():
        target = target_root / doc_name
        if _inject_block(target, block):
            doc_blocks.append(doc_name)

    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(
        json.dumps(
            {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "mode": "update" if mode == "existing" else "install",
                "installed": installed,
                "doc_blocks": doc_blocks,
                "options": {
                    "docs_mode": docs_mode,
                    "config_mode": config_mode,
                    "metadata_mode": metadata_mode,
                    "license_mode": license_mode,
                    "version_mode": version_mode,
                    "pyproject_mode": pyproject_mode,
                    "ci_mode": ci_mode,
                    "preserve_custom": preserve_custom,
                    "devcov_core_include": include_core,
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
