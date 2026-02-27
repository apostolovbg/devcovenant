"""Session snapshot and document exemption helpers."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import yaml

from devcovenant.core.lib.document_exemptions import (
    EMPTY_MANAGED_MARKER_SIGNATURE as _EMPTY_MANAGED_MARKER_SIGNATURE,
)
from devcovenant.core.lib.document_exemptions import (
    document_exemption_fingerprint_for_path,
)

_SNAPSHOT_BASE_IGNORED_DIRS = frozenset(
    {
        ".git",
        ".venv",
        ".python",
        "output",
        "logs",
        "build",
        "dist",
        "node_modules",
        "__pycache__",
        ".cache",
        ".ruff_cache",
        ".pytest_cache",
        ".mypy_cache",
        ".venv.lock",
    }
)

_SNAPSHOT_IGNORED_FILES = frozenset(
    {
        "devcovenant/registry/local/gate_status.json",
    }
)

_SNAPSHOT_IGNORED_PREFIXES = ("devcovenant/registry/local/",)
_AGENTS_WORKFLOW_BEGIN = "<!-- DEVCOV-WORKFLOW:BEGIN -->"
_AGENTS_WORKFLOW_END = "<!-- DEVCOV-WORKFLOW:END -->"


def capture_current_numstat_snapshot(repo_root: Path) -> dict[str, str]:
    """
    Return a filesystem snapshot mapping keyed by relative path.

    Snapshot rows are deterministic `sha256<TAB>path` strings. This avoids
    HEAD/working-tree diff logic and lets session policies compare one baseline
    snapshot against the current filesystem state directly.
    """
    rows: dict[str, str] = {}
    ignored_dirs = _snapshot_ignored_dirs(repo_root)
    files = _snapshot_files(repo_root, ignored_dirs)
    for file_path in files:
        rel = file_path.relative_to(repo_root).as_posix()
        if rel in _SNAPSHOT_IGNORED_FILES:
            continue
        if any(
            rel == prefix.rstrip("/") or rel.startswith(prefix)
            for prefix in _SNAPSHOT_IGNORED_PREFIXES
        ):
            continue
        digest = _sha256_file(file_path)
        rows[rel] = f"{digest}\t{rel}"
    return rows


def capture_current_snapshot_paths(repo_root: Path) -> list[str]:
    """Return deterministic repo-relative path list from filesystem scan."""
    ignored_dirs = _snapshot_ignored_dirs(repo_root)
    files = _snapshot_files(repo_root, ignored_dirs)
    return [path.relative_to(repo_root).as_posix() for path in files]


def changed_numstat_paths(
    before: dict[str, str], after: dict[str, str]
) -> set[str]:
    """Return changed paths present in the current snapshot."""
    changed: set[str] = set()
    for path, row in after.items():
        if before.get(path) != row:
            changed.add(path)
    return changed


def diff_snapshot_paths(
    before: dict[str, str], after: dict[str, str]
) -> set[str]:
    """
    Return changed paths across both snapshots, including deletions.

    This helper is used for gate/session drift detection where deletions must
    be treated as real changes, not silently ignored.
    """
    changed: set[str] = set()
    for path in set(before).union(after):
        if before.get(path) != after.get(path):
            changed.add(path)
    return changed


def snapshot_signature(snapshot: dict[str, str]) -> str:
    """
    Return a deterministic signature for one normalized snapshot mapping.

    This is the canonical session-signature API for gate/runtime checks.
    """
    rows = [snapshot[path] for path in sorted(snapshot)]
    payload = "\n".join(rows)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_snapshot_rows(
    raw: object, *, field_name: str = "snapshot"
) -> dict[str, str]:
    """Validate and normalize snapshot payload mappings into strings."""
    if not isinstance(raw, dict):
        raise ValueError(
            "Invalid gate status payload: "
            f"`{field_name}` must be a mapping."
        )
    snapshot: dict[str, str] = {}
    for key, value in raw.items():
        path = str(key).strip()
        row = str(value).strip()
        if not path or not row:
            raise ValueError(
                "Invalid gate status payload: "
                f"`{field_name}` contains empty keys or rows."
            )
        snapshot[path] = row
    return snapshot


def snapshot_row_style(snapshot: dict[str, str]) -> str:
    """Classify snapshot row style for migration-safe delta handling."""
    if not snapshot:
        return "empty"
    tab_counts: list[int] = []
    for row in snapshot.values():
        text = str(row).strip()
        if not text:
            continue
        tab_counts.append(text.count("\t"))
    if not tab_counts:
        return "empty"
    if all(count >= 2 for count in tab_counts):
        return "legacy_numstat"
    if all(count == 1 for count in tab_counts):
        return "filesystem_hash"
    return "mixed"


def session_delta_paths(
    repo_root: Path,
    start_snapshot: dict[str, str],
    current_snapshot: dict[str, str],
    *,
    session_start_epoch: float | None = None,
) -> set[str]:
    """
    Return session delta paths using shared snapshot comparison semantics.

    Legacy gate snapshots (numstat rows) are migration-bridged by epoch-based
    path discovery when compared against current filesystem-hash snapshots.
    """
    start_style = snapshot_row_style(start_snapshot)
    current_style = snapshot_row_style(current_snapshot)
    if start_style == "legacy_numstat" and current_style == "filesystem_hash":
        if session_start_epoch is None:
            raise ValueError(
                "Invalid gate status payload: `session_start_epoch` is "
                "required for legacy snapshot migration."
            )
        return snapshot_paths_changed_since(repo_root, session_start_epoch)
    return changed_numstat_paths(start_snapshot, current_snapshot)


def snapshot_paths_changed_since(repo_root: Path, epoch: float) -> set[str]:
    """Return snapshot paths whose mtime is after the given epoch."""
    if epoch < 0:
        raise ValueError("Snapshot epoch must be non-negative.")
    # Gate/session epochs are persisted with datetime microsecond precision.
    # Compare at the same precision to avoid boundary false-positives caused by
    # float representation drift when values are reloaded from JSON.
    cutoff_micros = int(round(float(epoch) * 1_000_000))
    ignored_dirs = _snapshot_ignored_dirs(repo_root)
    files = _snapshot_files(repo_root, ignored_dirs)
    changed: set[str] = set()
    for file_path in files:
        rel = file_path.relative_to(repo_root).as_posix()
        if rel in _SNAPSHOT_IGNORED_FILES:
            continue
        try:
            mtime_micros = file_path.stat().st_mtime_ns // 1000
        except OSError as exc:
            raise ValueError(
                f"Unable to stat snapshot file {file_path}: {exc}"
            ) from exc
        if mtime_micros > cutoff_micros:
            changed.add(rel)
    return changed


def _snapshot_ignored_dirs(repo_root: Path) -> set[str]:
    """Return snapshot ignored directories from defaults plus config."""
    ignored = set(_SNAPSHOT_BASE_IGNORED_DIRS)
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return ignored
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(
            f"Unable to read snapshot ignore settings from {config_path}: "
            f"{exc}"
        ) from exc
    if not isinstance(payload, dict):
        return ignored
    engine_cfg = payload.get("engine", {})
    if not isinstance(engine_cfg, dict):
        return ignored
    extra = engine_cfg.get("ignore_dirs", [])
    if isinstance(extra, str):
        extra_dirs = [extra]
    elif isinstance(extra, list):
        extra_dirs = extra
    else:
        extra_dirs = []
    for entry in extra_dirs:
        name = str(entry).strip()
        if name:
            ignored.add(name)
    return ignored


def _snapshot_files(repo_root: Path, ignored_dirs: set[str]) -> list[Path]:
    """Collect snapshot files under repo root using ignore-dir filtering."""
    files: list[Path] = []
    for root, dirs, names in os.walk(repo_root):
        root_path = Path(root)
        dirs[:] = [name for name in dirs if name not in ignored_dirs]
        for name in names:
            file_path = root_path / name
            try:
                rel = file_path.relative_to(repo_root).as_posix()
            except ValueError:
                continue
            if rel in _SNAPSHOT_IGNORED_FILES:
                continue
            if any(
                rel == prefix.rstrip("/") or rel.startswith(prefix)
                for prefix in _SNAPSHOT_IGNORED_PREFIXES
            ):
                continue
            if any(part in ignored_dirs for part in file_path.parts):
                continue
            if not file_path.is_file():
                continue
            files.append(file_path)
    files.sort(key=lambda path: path.relative_to(repo_root).as_posix())
    return files


def _sha256_file(path: Path) -> str:
    """Return SHA-256 digest for one file path."""
    digest = hashlib.sha256()
    try:
        with path.open("rb") as file_obj:
            while True:
                chunk = file_obj.read(65536)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:
        raise ValueError(
            f"Unable to read snapshot file {path}: {exc}"
        ) from exc
    return digest.hexdigest()


def _hash_lines(lines: list[str]) -> str:
    """Return deterministic SHA-256 digest for normalized text lines."""
    normalized = "\n".join(line.rstrip() for line in lines)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _split_agents_workflow_lines(content: str) -> tuple[list[str], list[str]]:
    """Split AGENTS text into workflow-block lines and non-workflow lines."""
    workflow_lines: list[str] = []
    non_workflow_lines: list[str] = []
    in_workflow = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == _AGENTS_WORKFLOW_BEGIN:
            in_workflow = True
            workflow_lines.append(line)
            continue
        if stripped == _AGENTS_WORKFLOW_END:
            workflow_lines.append(line)
            in_workflow = False
            continue
        if in_workflow:
            workflow_lines.append(line)
        else:
            non_workflow_lines.append(line)
    return workflow_lines, non_workflow_lines


def capture_agents_section_hashes(repo_root: Path) -> dict[str, str]:
    """Capture deterministic AGENTS full/workflow/non-workflow hashes."""
    payload = {
        "agents_file": "AGENTS.md",
        "agents_full_sha256": "",
        "agents_workflow_sha256": "",
        "agents_non_workflow_sha256": "",
    }
    agents_path = repo_root / "AGENTS.md"
    if not agents_path.exists() or not agents_path.is_file():
        return payload
    try:
        content = agents_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return payload

    payload["agents_full_sha256"] = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()
    workflow_lines, non_workflow_lines = _split_agents_workflow_lines(content)
    payload["agents_workflow_sha256"] = _hash_lines(workflow_lines)
    payload["agents_non_workflow_sha256"] = _hash_lines(non_workflow_lines)
    return payload


def capture_document_exemption_baseline(
    repo_root: Path,
    *,
    header_doc_suffixes: list[str],
    header_keys: list[str],
    header_scan_lines: int,
) -> dict[str, dict[str, str]]:
    """Capture a baseline for header exemptions and managed regenerations."""
    suffixes = {
        entry.strip().lower() for entry in header_doc_suffixes if entry
    }
    keys = {entry.strip().lower() for entry in header_keys if entry}
    scan_lines = max(int(header_scan_lines), 0)

    ignored_dirs = _snapshot_ignored_dirs(repo_root)
    baseline: dict[str, dict[str, str]] = {}
    for path in _snapshot_files(repo_root, ignored_dirs):
        rel = path.relative_to(repo_root).as_posix()
        entry = document_exemption_fingerprint_for_path(
            repo_root,
            rel,
            header_doc_suffixes=suffixes,
            header_keys=keys,
            header_scan_lines=scan_lines,
        )
        if entry is not None:
            is_header_doc = path.suffix.lower() in suffixes
            has_managed_markers = (
                entry.get("managed_marker_signature", "")
                != _EMPTY_MANAGED_MARKER_SIGNATURE
            )
            if not is_header_doc and not has_managed_markers:
                continue
            baseline[rel] = entry
    return baseline
