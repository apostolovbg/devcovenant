"""Execution helpers for command entrypoints and test orchestration."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Protocol, Sequence, TextIO

import yaml

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    tqdm = None

from devcovenant import __version__ as package_version
from devcovenant.core import event_runtime as event_runtime_module
from devcovenant.core import registry_runtime as registry_runtime_module

OutputMode = Literal["normal", "verbose"]
_OUTPUT_MODE_DEFAULT: OutputMode = "verbose"
_OUTPUT_MODE_ALLOWED = frozenset({"normal", "verbose"})
_MANAGED_ENV_POLICY_ID = "managed-environment"
_MANAGED_ENV_STAGES = frozenset({"start", "test", "end", "all"})
_TEST_COMMAND_OUTPUT_MODE: OutputMode | None = None
_TEST_COMMAND_LABEL = ""
_PYTEST_PROGRESS_PATTERN = re.compile(r"\[\s*(\d+)%\]")
_PYTEST_PASSED_PATTERN = re.compile(r"\b(\d+)\s+passed\b")
_UNITTEST_RESULT_PATTERN = re.compile(
    r"\.\.\.\s+(ok|FAIL|ERROR|skipped|expected failure|unexpected success)$",
    flags=re.IGNORECASE,
)
_UNITTEST_SUMMARY_PATTERN = re.compile(r"^Ran\s+(\d+)\s+tests?")


def _normalize_output_mode(raw_value: str | None) -> OutputMode:
    """Normalize an output mode token to one of the allowed runtime modes."""
    token = str(raw_value or "").strip().lower()
    if token in _OUTPUT_MODE_ALLOWED:
        return token  # type: ignore[return-value]
    return _OUTPUT_MODE_DEFAULT


class Reporter(Protocol):
    """Output boundary contract for user-visible runtime messages."""

    mode: OutputMode

    def emit(
        self,
        message: str,
        *,
        stream: TextIO | None = None,
        end: str = "\n",
        flush: bool = False,
        verbose_only: bool = False,
    ) -> None:
        """Emit one message through the configured output boundary."""

    def banner(self, title: str, emoji: str) -> None:
        """Emit a stage banner message."""

    def step(
        self, message: str, emoji: str = "•", *, verbose_only: bool = False
    ) -> None:
        """Emit a short status step."""


class ConsoleReporter:
    """Console output adapter implementing the runtime Reporter contract."""

    def __init__(self, mode: OutputMode) -> None:
        """Initialize reporter with one deterministic output mode."""
        self.mode = mode

    def emit(
        self,
        message: str,
        *,
        stream: TextIO | None = None,
        end: str = "\n",
        flush: bool = False,
        verbose_only: bool = False,
    ) -> None:
        """Write one message to stdout/stderr with mode-aware filtering."""
        if verbose_only and self.mode != "verbose":
            return
        target = stream if stream is not None else sys.stdout
        target.write(f"{message}{end}")
        if flush:
            target.flush()

    def banner(self, title: str, emoji: str) -> None:
        """Emit a decorative stage banner in verbose mode only."""
        self.emit("\n" + "=" * 70, verbose_only=True)
        self.emit(f"{emoji} {title}", verbose_only=True)
        self.emit("=" * 70, verbose_only=True)

    def step(
        self, message: str, emoji: str = "•", *, verbose_only: bool = False
    ) -> None:
        """Emit a one-line status message."""
        self.emit(f"{emoji} {message}", verbose_only=verbose_only)


_OUTPUT_MODE: OutputMode = _OUTPUT_MODE_DEFAULT
_REPORTER: Reporter = ConsoleReporter(_OUTPUT_MODE)


def configure_output_mode(mode: str | None) -> OutputMode:
    """Configure global output mode for this process runtime."""
    global _OUTPUT_MODE, _REPORTER
    normalized = (
        _normalize_output_mode(mode)
        if mode is not None
        else _OUTPUT_MODE_DEFAULT
    )
    _OUTPUT_MODE = normalized
    _REPORTER = ConsoleReporter(normalized)
    return normalized


def get_output_mode() -> OutputMode:
    """Return active runtime output mode."""
    return _OUTPUT_MODE


def _read_engine_config(repo_root: Path) -> dict[str, Any]:
    """Read `engine` config mapping from repo config when available."""
    config_path = repo_root / "devcovenant" / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    if not isinstance(payload, dict):
        return {}
    engine_cfg = payload.get("engine")
    if not isinstance(engine_cfg, dict):
        return {}
    return engine_cfg


def _read_output_mode_from_config(repo_root: Path) -> str | None:
    """Read optional `engine.output_mode` from repo config."""
    engine_cfg = _read_engine_config(repo_root)
    token = str(engine_cfg.get("output_mode", "")).strip()
    return token or None


def _read_tests_output_mode_from_config(repo_root: Path) -> str | None:
    """
    Read optional `engine.tests_output_mode` from repo config.

    Compatibility fallback:
    - If `tests_output_mode` is unset, reuse `output_mode`.
    """
    engine_cfg = _read_engine_config(repo_root)
    tests_token = str(engine_cfg.get("tests_output_mode", "")).strip()
    if tests_token:
        return tests_token
    output_token = str(engine_cfg.get("output_mode", "")).strip()
    return output_token or None


def configure_output_mode_from_config(repo_root: Path) -> OutputMode:
    """Configure output mode from `devcovenant/config.yaml`."""
    return configure_output_mode(_read_output_mode_from_config(repo_root))


def resolve_tests_output_mode(repo_root: Path) -> OutputMode:
    """Resolve tests output mode from config with compatibility fallback."""
    return _normalize_output_mode(
        _read_tests_output_mode_from_config(repo_root)
    )


def runtime_print(
    *args: object,
    sep: str = " ",
    end: str = "\n",
    file: TextIO | None = None,
    flush: bool = False,
    verbose_only: bool = False,
) -> None:
    """
    Print via the output boundary with built-in-print-compatible semantics.

    Existing runtime call sites can migrate from direct `print()` usage
    without changing caller-side argument shapes.
    """
    message = sep.join(str(arg) for arg in args)
    stream = file if file is not None else sys.stdout
    if stream in {sys.stdout, sys.stderr}:
        _REPORTER.emit(
            message,
            stream=stream,
            end=end,
            flush=flush,
            verbose_only=verbose_only,
        )
        return
    if verbose_only and _OUTPUT_MODE != "verbose":
        return
    stream.write(f"{message}{end}")
    if flush:
        stream.flush()


def print_banner(title: str, emoji: str) -> None:
    """Print a readable stage banner via the output boundary."""
    _REPORTER.banner(title, emoji)


def print_step(message: str, emoji: str = "•") -> None:
    """Print a short, single-line status step via output boundary."""
    _REPORTER.step(message, emoji)


def find_git_root(path: Path) -> Path | None:
    """Return the nearest git root for a path."""
    current = path.resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def resolve_repo_root(*, require_install: bool = False) -> Path:
    """Resolve and validate the current git repository root."""
    repo_root = find_git_root(Path.cwd())
    if repo_root is None:
        raise SystemExit(
            "DevCovenant commands must run inside a git repository."
        )
    if require_install and not (repo_root / "devcovenant").exists():
        raise SystemExit(
            "DevCovenant is not installed in this repo. "
            "Run `devcovenant install` first."
        )
    configure_output_mode_from_config(repo_root)
    return repo_root


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
_DOC_ALLOWLIST_MANAGED_MARKERS = (
    ("<!-- DEVCOV:BEGIN -->", "<!-- DEVCOV:END -->"),
    ("<!-- DEVCOV-WORKFLOW:BEGIN -->", "<!-- DEVCOV-WORKFLOW:END -->"),
    ("<!-- DEVCOV-POLICIES:BEGIN -->", "<!-- DEVCOV-POLICIES:END -->"),
)


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
    """Return snapshot paths whose mtime is at or after the given epoch."""
    if epoch < 0:
        raise ValueError("Snapshot epoch must be non-negative.")
    ignored_dirs = _snapshot_ignored_dirs(repo_root)
    files = _snapshot_files(repo_root, ignored_dirs)
    changed: set[str] = set()
    for file_path in files:
        rel = file_path.relative_to(repo_root).as_posix()
        if rel in _SNAPSHOT_IGNORED_FILES:
            continue
        try:
            mtime = file_path.stat().st_mtime
        except OSError as exc:
            raise ValueError(
                f"Unable to stat snapshot file {file_path}: {exc}"
            ) from exc
        if mtime >= epoch:
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


def _marker_signature(content: str) -> str:
    """Return a deterministic managed-marker sequence signature."""
    tokens: list[str] = []
    for line in content.splitlines():
        for marker_index, (begin_marker, end_marker) in enumerate(
            _DOC_ALLOWLIST_MANAGED_MARKERS
        ):
            if begin_marker in line:
                tokens.append(f"{marker_index}:begin")
            if end_marker in line:
                tokens.append(f"{marker_index}:end")
    return _hash_lines(tokens)


def _managed_ranges(content: str) -> list[tuple[int, int]]:
    """Return line ranges covered by managed block markers."""
    ranges: list[tuple[int, int]] = []
    lines = content.splitlines()
    for begin_marker, end_marker in _DOC_ALLOWLIST_MANAGED_MARKERS:
        start_line: int | None = None
        for index, line in enumerate(lines, start=1):
            if start_line is None and begin_marker in line:
                start_line = index
            elif start_line is not None and end_marker in line:
                ranges.append((start_line, index))
                start_line = None
    return ranges


def _is_header_key_line(line: str, header_keys: set[str]) -> bool:
    """Return True when a line starts with an allowed header key."""
    match = re.match(
        r"^\*{0,2}\s*([a-z][a-z \-]+?)\s*:\*{0,2}\s*",
        line.strip(),
        flags=re.IGNORECASE,
    )
    if not match:
        return False
    return match.group(1).strip().lower() in header_keys


def _document_header_ranges(
    content: str,
    *,
    header_keys: set[str],
    header_scan_lines: int,
) -> list[tuple[int, int]]:
    """Return top-of-file header line ranges eligible for changelog skip."""
    lines = content.splitlines()
    ranges: list[tuple[int, int]] = []
    for line_number, line in enumerate(lines[:header_scan_lines], start=1):
        if _is_header_key_line(line, header_keys):
            ranges.append((line_number, line_number))
    return ranges


def _line_in_ranges(line_number: int, ranges: list[tuple[int, int]]) -> bool:
    """Return True when the line falls inside any allowlisted range."""
    for start, end in ranges:
        if start <= line_number <= end:
            return True
    return False


def _non_exempt_content_hash(
    content: str,
    relative_path: str,
    *,
    header_doc_suffixes: set[str],
    header_keys: set[str],
    header_scan_lines: int,
) -> str:
    """Return hash for lines outside managed/header allowlisted ranges."""
    ranges = _managed_ranges(content)
    suffix = Path(relative_path).suffix.lower()
    if suffix in header_doc_suffixes:
        ranges.extend(
            _document_header_ranges(
                content,
                header_keys=header_keys,
                header_scan_lines=header_scan_lines,
            )
        )
    lines = content.splitlines()
    visible = [
        line
        for line_number, line in enumerate(lines, start=1)
        if not _line_in_ranges(line_number, ranges)
    ]
    return _hash_lines(visible)


def document_exemption_fingerprint_for_path(
    repo_root: Path,
    relative_path: str,
    *,
    header_doc_suffixes: set[str],
    header_keys: set[str],
    header_scan_lines: int,
) -> dict[str, str] | None:
    """Return allowlist fingerprint entry for one document path."""
    path = repo_root / relative_path
    if not path.exists() or not path.is_file():
        return None
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return {
        "non_exempt_content_sha256": _non_exempt_content_hash(
            content,
            relative_path,
            header_doc_suffixes=header_doc_suffixes,
            header_keys=header_keys,
            header_scan_lines=header_scan_lines,
        ),
        "managed_marker_signature": _marker_signature(content),
    }


def capture_document_exemption_baseline(
    repo_root: Path,
    *,
    header_doc_suffixes: list[str],
    header_keys: list[str],
    header_scan_lines: int,
) -> dict[str, dict[str, str]]:
    """Capture lightweight document baseline for header/managed exemptions."""
    suffixes = {
        entry.strip().lower() for entry in header_doc_suffixes if entry
    }
    keys = {entry.strip().lower() for entry in header_keys if entry}
    scan_lines = max(int(header_scan_lines), 0)
    if not suffixes or not keys or scan_lines <= 0:
        return {}

    ignored_dirs = _snapshot_ignored_dirs(repo_root)
    baseline: dict[str, dict[str, str]] = {}
    for path in _snapshot_files(repo_root, ignored_dirs):
        rel = path.relative_to(repo_root).as_posix()
        if path.suffix.lower() not in suffixes:
            continue
        entry = document_exemption_fingerprint_for_path(
            repo_root,
            rel,
            header_doc_suffixes=suffixes,
            header_keys=keys,
            header_scan_lines=scan_lines,
        )
        if entry is not None:
            baseline[rel] = entry
    return baseline


def read_local_version(repo_root: Path) -> str | None:
    """Read the local devcovenant version from repo_root."""
    init_path = repo_root / "devcovenant" / "__init__.py"
    if not init_path.exists():
        return None
    pattern = re.compile(r'__version__\s*=\s*["\']([^"\']+)["\']')
    match = pattern.search(init_path.read_text(encoding="utf-8"))
    if match:
        return match.group(1).strip()
    return None


def warn_version_mismatch(repo_root: Path) -> None:
    """Warn when the local devcovenant version differs from the CLI."""
    local_version = read_local_version(repo_root)
    if not local_version:
        return
    if local_version != package_version:
        message = (
            "⚠️  Local DevCovenant version differs from CLI.\n"
            f"   Local: {local_version}\n"
            f"   CLI:   {package_version}\n"
            "Use the local version via `python3 -m devcovenant` or update."
        )
        runtime_print(message)


def run_bootstrap_registry_refresh(repo_root: Path) -> None:
    """Run lightweight registry refresh for command startup."""
    print_step("Refreshing local registry", "🔄")
    from devcovenant.core.refresh_runtime import refresh_policy_registry

    refresh_exit = refresh_policy_registry(repo_root)
    if refresh_exit != 0:
        raise SystemExit("Registry refresh failed.")
    print_step("Registry refresh complete", "✅")


def _load_policy_registry(repo_root: Path) -> dict[str, Any]:
    """Load `policies` mapping from the local policy registry."""
    registry_path = registry_runtime_module.policy_registry_path(repo_root)
    if not registry_path.exists():
        raise ValueError(
            "Missing policy registry file; run `devcovenant refresh`."
        )

    try:
        registry_data = yaml.safe_load(
            registry_path.read_text(encoding="utf-8")
        )
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Invalid YAML in policy registry {registry_path}: {exc}"
        ) from exc
    except OSError as exc:
        raise ValueError(
            f"Unable to read policy registry {registry_path}: {exc}"
        ) from exc

    if not isinstance(registry_data, dict):
        raise ValueError(
            f"Invalid policy registry payload in {registry_path}: "
            "expected a mapping."
        )

    policies = registry_data.get("policies")
    if not isinstance(policies, dict):
        raise ValueError(
            "Invalid policy registry payload: `policies` must be a mapping."
        )
    return policies


def _policy_metadata(repo_root: Path, policy_id: str) -> dict[str, Any]:
    """Return metadata mapping for one policy from local registry."""
    policies = _load_policy_registry(repo_root)
    entry = policies.get(policy_id)
    if not isinstance(entry, dict):
        raise ValueError(
            "Invalid policy registry payload: "
            f"`{policy_id}` must be a mapping."
        )
    metadata_map = entry.get("metadata")
    if not isinstance(metadata_map, dict):
        raise ValueError(
            "Invalid policy registry payload: "
            f"`{policy_id}.metadata` must be a mapping."
        )
    return metadata_map


def _policy_entry(repo_root: Path, policy_id: str) -> dict[str, Any]:
    """Return one policy entry mapping from local registry."""
    policies = _load_policy_registry(repo_root)
    entry = policies.get(policy_id)
    if not isinstance(entry, dict):
        raise ValueError(
            "Invalid policy registry payload: "
            f"`{policy_id}` must be a mapping."
        )
    return entry


def _normalize_metadata_tokens(raw_value: object) -> list[str]:
    """Normalize metadata values into non-empty string tokens."""
    if raw_value is None:
        return []
    if isinstance(raw_value, str):
        return [item.strip() for item in raw_value.split(",") if item.strip()]
    if isinstance(raw_value, list):
        return [str(item).strip() for item in raw_value if str(item).strip()]
    token = str(raw_value).strip()
    return [token] if token else []


def _is_enabled_token(raw_value: object) -> bool:
    """Normalize enabled-like metadata tokens to bool."""
    if isinstance(raw_value, bool):
        return raw_value
    token = str(raw_value or "").strip().lower()
    return token in {"1", "true", "yes", "on"}


def _resolve_metadata_paths(repo_root: Path, entries: list[str]) -> list[Path]:
    """Resolve metadata path entries relative to repo root."""
    resolved: list[Path] = []
    for entry in entries:
        token = entry.strip()
        if not token:
            continue
        path = Path(token)
        if not path.is_absolute():
            path = repo_root / path
        try:
            resolved.append(path.resolve())
        except OSError:
            resolved.append(path)
    return resolved


def _parse_managed_commands(entries: list[str]) -> list[tuple[str, str]]:
    """Parse metadata-managed command entries into stage/command pairs."""
    parsed: list[tuple[str, str]] = []
    for entry in entries:
        stage = "start"
        command_text = entry.strip()
        if "=>" in command_text:
            raw_stage, raw_command = command_text.split("=>", 1)
            stage = raw_stage.strip().lower()
            command_text = raw_command.strip()
        if stage not in _MANAGED_ENV_STAGES:
            allowed = ", ".join(sorted(_MANAGED_ENV_STAGES))
            raise ValueError(
                "Invalid managed command stage "
                f"`{stage}`. Allowed values: {allowed}."
            )
        if not command_text:
            raise ValueError("Managed command entry is empty.")
        parsed.append((stage, command_text))
    return parsed


def _detect_managed_python(
    expected_interpreters: list[Path],
    expected_paths: list[Path],
) -> tuple[Path | None, Path | None]:
    """Detect managed interpreter and root from expected metadata paths."""
    for interpreter in expected_interpreters:
        if interpreter.exists():
            for root in expected_paths:
                if root == interpreter or root in interpreter.parents:
                    return interpreter, root
            parent_name = interpreter.parent.name.lower()
            if parent_name in {"bin", "scripts"}:
                return interpreter, interpreter.parent.parent
            return interpreter, None

    for root in expected_paths:
        if not root.exists():
            continue
        posix_candidate = root / "bin" / "python"
        if posix_candidate.exists():
            return posix_candidate.resolve(), root
        windows_candidate = root / "Scripts" / "python.exe"
        if windows_candidate.exists():
            return windows_candidate.resolve(), root
    return None, None


def _managed_guidance_suffix(manual_commands: list[str]) -> str:
    """Build manual-commands suffix for managed-environment errors."""
    if not manual_commands:
        return ""
    return " Manual commands: " + " | ".join(manual_commands)


def _apply_managed_env(
    env: Mapping[str, str],
    interpreter: Path,
    root: Path | None,
) -> dict[str, str]:
    """Return env with managed interpreter PATH and identity markers."""
    updated = dict(env)
    bin_dir = str(interpreter.parent)
    existing_path = updated.get("PATH", "").strip()
    if existing_path:
        updated["PATH"] = f"{bin_dir}{os.pathsep}{existing_path}"
    else:
        updated["PATH"] = bin_dir
    updated["DEVCOV_MANAGED_PYTHON"] = str(interpreter)
    if root is not None:
        updated["VIRTUAL_ENV"] = str(root)
    return updated


def _expand_managed_command_tokens(
    command_text: str,
    repo_root: Path,
    managed_python: Path | None,
) -> list[str]:
    """Expand managed-command placeholders and return argv tokens."""
    tokens = shlex.split(command_text)
    expanded: list[str] = []
    for token in tokens:
        resolved = token.replace("{repo_root}", str(repo_root))
        if "{managed_python}" in resolved:
            if managed_python is None:
                raise ValueError(
                    "Managed command uses `{managed_python}` before an "
                    "expected interpreter exists. Run bootstrap commands "
                    "first."
                )
            resolved = resolved.replace(
                "{managed_python}", str(managed_python)
            )
        expanded.append(resolved)
    return expanded


def resolve_managed_environment_for_stage(
    repo_root: Path,
    stage: str,
    *,
    base_env: Mapping[str, str] | None = None,
) -> tuple[dict[str, str] | None, str | None]:
    """Resolve and optionally prepare managed-environment execution state."""
    stage_token = str(stage or "").strip().lower()
    if stage_token not in {"start", "test", "end"}:
        raise ValueError(
            "Invalid managed-environment stage "
            f"`{stage}`. Allowed: start, test, end."
        )
    try:
        entry = _policy_entry(repo_root, _MANAGED_ENV_POLICY_ID)
    except ValueError:
        return None, None
    if not _is_enabled_token(entry.get("enabled")):
        return None, None
    metadata_map = entry.get("metadata")
    if not isinstance(metadata_map, dict):
        raise ValueError(
            "Invalid policy registry payload: "
            "`managed-environment.metadata` must be a mapping."
        )

    expected_path_tokens = _normalize_metadata_tokens(
        metadata_map.get("expected_paths")
    )
    expected_interpreter_tokens = _normalize_metadata_tokens(
        metadata_map.get("expected_interpreters")
    )
    manual_commands = _normalize_metadata_tokens(
        metadata_map.get("manual_commands")
    )
    managed_commands_raw = _normalize_metadata_tokens(
        metadata_map.get("managed_commands")
    )
    managed_commands = _parse_managed_commands(managed_commands_raw)

    expected_paths = _resolve_metadata_paths(repo_root, expected_path_tokens)
    expected_interpreters = _resolve_metadata_paths(
        repo_root, expected_interpreter_tokens
    )
    if not expected_paths and not expected_interpreters:
        guidance = _managed_guidance_suffix(manual_commands)
        raise ValueError(
            "managed-environment is enabled, but no expected_paths or "
            f"expected_interpreters are configured.{guidance}"
        )

    env: dict[str, str] = dict(base_env or os.environ)
    for command_stage, command_text in managed_commands:
        if command_stage not in {"all", stage_token}:
            continue
        managed_python, managed_root = _detect_managed_python(
            expected_interpreters,
            expected_paths,
        )
        if managed_python is not None:
            env = _apply_managed_env(env, managed_python, managed_root)
        command_tokens = _expand_managed_command_tokens(
            command_text,
            repo_root,
            managed_python,
        )
        runtime_print(
            "Running managed-environment command "
            f"({stage_token}): {' '.join(command_tokens)}",
            verbose_only=True,
        )
        _run_command(
            command_tokens,
            allow_codes={0},
            env=env,
            cwd=repo_root,
        )

    managed_python, managed_root = _detect_managed_python(
        expected_interpreters,
        expected_paths,
    )
    if managed_python is None:
        guidance = _managed_guidance_suffix(manual_commands)
        raise ValueError(
            "managed-environment is enabled, but no expected interpreter was "
            f"found.{guidance}"
        )
    env = _apply_managed_env(env, managed_python, managed_root)
    return env, str(managed_python)


def _looks_like_python_launcher(token: str) -> bool:
    """Return True when token points to a Python launcher."""
    name = Path(str(token).strip()).name.lower()
    if name in {"py", "py.exe"}:
        return True
    return name.startswith("python")


def rewrite_command_for_managed_python(
    command: Sequence[str],
    managed_python: str | None,
) -> list[str]:
    """Replace command python launcher with managed interpreter path."""
    rewritten = [str(token) for token in command]
    if not rewritten or not managed_python:
        return rewritten
    if not _looks_like_python_launcher(rewritten[0]):
        return rewritten
    rewritten[0] = managed_python
    return rewritten


def rewrite_command_string_for_managed_python(
    command: str,
    managed_python: str | None,
) -> str:
    """Rewrite shell command string with managed Python launcher."""
    if not managed_python:
        return command
    tokens = shlex.split(command)
    rewritten = rewrite_command_for_managed_python(tokens, managed_python)
    return shlex.join(rewritten)


def _normalize_relative_dir_token(token: str, *, field_name: str) -> str:
    """Validate one repo-relative directory token from metadata."""
    normalized = token.replace("\\", "/").strip().strip("/")
    if not normalized:
        raise ValueError(
            f"Invalid `{field_name}` entry: empty directory token."
        )
    if normalized.startswith("..") or "/../" in normalized:
        raise ValueError(
            f"Invalid `{field_name}` entry: `{token}` escapes repo root."
        )
    if Path(normalized).is_absolute():
        raise ValueError(
            f"Invalid `{field_name}` entry: `{token}` must be relative."
        )
    return normalized


def registry_tests_coverage_roots(repo_root: Path) -> list[str]:
    """Resolve tests root directories from tests-coverage metadata."""
    metadata_map = _policy_metadata(repo_root, "tests-coverage")
    tests_watch_dirs = _normalize_metadata_tokens(
        metadata_map.get("tests_watch_dirs")
    )
    watch_dirs = _normalize_metadata_tokens(metadata_map.get("watch_dirs"))
    raw_roots = tests_watch_dirs or watch_dirs or ["tests"]
    normalized: list[str] = []
    for token in raw_roots:
        normalized.append(
            _normalize_relative_dir_token(
                token,
                field_name="tests-coverage.watch_dirs",
            )
        )
    deduped: list[str] = []
    seen: set[str] = set()
    for entry in normalized:
        if entry in seen:
            continue
        deduped.append(entry)
        seen.add(entry)
    return deduped


def registry_required_commands(repo_root: Path) -> list[tuple[str, list[str]]]:
    """Read required commands from devflow-run-gates metadata."""
    commands, _, _ = resolve_required_test_commands(repo_root)
    return commands


def _normalize_required_commands(
    raw_commands: object,
    *,
    field_name: str,
) -> list[tuple[str, list[str]]]:
    """Normalize one command metadata field into raw/tokens tuples."""
    if isinstance(raw_commands, str):
        raw_commands = [
            item.strip()
            for item in raw_commands.replace("\n", ",").split(",")
            if item.strip()
        ]
    elif isinstance(raw_commands, list):
        normalized: list[object] = []
        for command_entry in raw_commands:
            if isinstance(command_entry, str):
                normalized.extend(
                    entry.strip()
                    for entry in command_entry.replace("\n", ",").split(",")
                    if entry.strip()
                )
            else:
                normalized.append(command_entry)
        raw_commands = normalized
    else:
        raise ValueError(
            f"Invalid `{field_name}` payload: expected string or list."
        )

    commands: list[tuple[str, list[str]]] = []
    for entry in raw_commands:
        if isinstance(entry, list):
            raw = " ".join(
                str(part).strip() for part in entry if str(part).strip()
            )
        else:
            raw = str(entry).strip()
        if not raw:
            raise ValueError(f"Invalid `{field_name}` command: empty token.")
        tokens = shlex.split(raw)
        if not tokens:
            raise ValueError(f"Invalid `{field_name}` command: `{raw}`.")
        commands.append((raw, tokens))
    return commands


def resolve_required_test_commands(
    repo_root: Path,
    *,
    tests_mode: OutputMode | None = None,
) -> tuple[list[tuple[str, list[str]]], OutputMode, str]:
    """Resolve required test commands for one tests output mode."""
    metadata_map = _policy_metadata(repo_root, "devflow-run-gates")
    resolved_mode = tests_mode or resolve_tests_output_mode(repo_root)
    source_field = "required_commands"
    raw_commands = metadata_map.get(source_field)
    if raw_commands is None:
        raise ValueError(
            "Missing `devflow-run-gates` required command metadata in "
            "policy registry. Expected `required_commands`."
        )
    commands = _normalize_required_commands(
        raw_commands,
        field_name=source_field,
    )
    return commands, resolved_mode, source_field


def _is_pytest_command(command: Sequence[str]) -> bool:
    """Return True when command tokens look like a pytest invocation."""
    for token in command:
        name = Path(str(token).strip()).name.lower()
        if name.startswith("pytest"):
            return True
    return False


def _is_unittest_command(command: Sequence[str]) -> bool:
    """Return True when command tokens look like unittest invocation."""
    joined = " ".join(str(token).strip().lower() for token in command)
    return "unittest" in joined


class _CommandOutputProgress:
    """Consume command output and render per-command progress in normal mode."""

    def __init__(self, command: Sequence[str], description: str) -> None:
        """Initialize one command progress tracker."""
        self._kind = "generic"
        if _is_pytest_command(command):
            self._kind = "pytest"
        elif _is_unittest_command(command):
            self._kind = "unittest"
        self._count = 0
        self._bar = None
        if tqdm is None or not _stdout_is_tty():
            return
        if self._kind == "pytest":
            self._bar = tqdm(
                total=100,
                desc=description,
                unit="%",
                leave=False,
                ncols=60,
            )
            return
        unit = "test" if self._kind == "unittest" else "line"
        self._bar = tqdm(
            total=0,
            desc=description,
            unit=unit,
            leave=False,
            ncols=60,
        )

    def consume_line(self, line: str) -> None:
        """Update bar state from one captured output line."""
        if self._bar is None:
            return
        if self._kind == "pytest":
            percent_match = _PYTEST_PROGRESS_PATTERN.search(line)
            if percent_match:
                percent = int(percent_match.group(1))
                if self._bar.n < percent:
                    self._bar.n = percent
                    self._bar.refresh()
                return
            passed_match = _PYTEST_PASSED_PATTERN.search(line)
            if passed_match and self._bar.n < 100:
                self._bar.n = 100
                self._bar.refresh()
            return

        if self._kind == "unittest":
            if _UNITTEST_RESULT_PATTERN.search(line.strip()):
                self._count += 1
                if (self._bar.total or 0) < self._count:
                    self._bar.total = self._count
                self._bar.update(1)
            summary_match = _UNITTEST_SUMMARY_PATTERN.match(line.strip())
            if summary_match:
                total = int(summary_match.group(1))
                if (self._bar.total or 0) < total:
                    self._bar.total = total
            return

        if line.strip():
            self._count += 1
            if (self._bar.total or 0) < self._count:
                self._bar.total = self._count
            self._bar.update(1)

    def close(self, return_code: int) -> None:
        """Finalize and close bar resources."""
        if self._bar is None:
            return
        if return_code == 0 and self._kind == "pytest":
            self._bar.n = max(self._bar.n, 100)
        elif return_code == 0 and self._bar.total:
            self._bar.n = max(self._bar.n, self._bar.total)
        self._bar.refresh()
        self._bar.close()
        self._bar = None


def _run_command_with_consumed_output(
    command: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run one command while consuming output into progress bars."""
    command_env = dict(env or os.environ)
    label = _TEST_COMMAND_LABEL or " ".join(str(token) for token in command)
    progress = _CommandOutputProgress(command, label)
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=command_env,
        cwd=cwd,
        bufsize=1,
    )
    try:
        if process.stdout is not None:
            for line in process.stdout:
                progress.consume_line(line.rstrip("\n"))
        process.wait()
    finally:
        if process.stdout is not None:
            process.stdout.close()
    return_code = int(process.returncode or 0)
    progress.close(return_code)
    return subprocess.CompletedProcess(command, return_code)


def _run_command(
    command: Sequence[str],
    allow_codes: set[int] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    """Execute command and raise when it fails."""
    command_env = dict(env or os.environ)
    if _TEST_COMMAND_OUTPUT_MODE == "normal":
        result = _run_command_with_consumed_output(
            command,
            env=command_env,
            cwd=cwd,
        )
    else:
        result = subprocess.run(
            command,
            check=False,
            env=command_env,
            cwd=cwd,
        )
    allowed = allow_codes or {0}
    if result.returncode not in allowed:
        raise subprocess.CalledProcessError(result.returncode, command)
    return result


def _parse_commands(command: str) -> list[str]:
    """Return an ordered command list parsed from a shell chain."""
    return [part.strip() for part in command.split("&&") if part.strip()]


def record_gate_status(
    repo_root: Path,
    command: str,
    notes: str = "",
    test_events: Iterable[Mapping[str, Any]] | None = None,
    tests_output_mode: str | None = None,
    tests_required_commands_key: str | None = None,
) -> None:
    """Record gate status payload under registry/local/gate_status.json."""
    status_path = registry_runtime_module.gate_status_path(repo_root)
    status_path.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, object] = {}
    if status_path.exists():
        try:
            existing = json.loads(status_path.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                existing = {}
        except json.JSONDecodeError:
            existing = {}

    now = _dt.datetime.now(tz=_dt.timezone.utc)
    payload = {
        **existing,
        "last_run": now.isoformat(),
        "last_run_utc": now.isoformat(),
        "last_run_epoch": now.timestamp(),
        "command": command.strip(),
        "commands": _parse_commands(command),
        "notes": notes.strip(),
    }
    if test_events:
        payload["test_events"] = [dict(entry) for entry in test_events]
    else:
        payload.pop("test_events", None)
    if tests_output_mode:
        payload["tests_output_mode"] = _normalize_output_mode(
            tests_output_mode
        )
    else:
        payload.pop("tests_output_mode", None)
    token = str(tests_required_commands_key or "").strip()
    if token:
        payload["tests_required_commands_key"] = token
    else:
        payload.pop("tests_required_commands_key", None)
    # Purge legacy gate-status keys instead of carrying them forward.
    payload.pop("sha", None)
    payload.pop("tests_coverage_evidence", None)
    payload.pop("changelog_start_diff_numstat", None)
    payload.pop("changelog_start_exemption_fingerprints", None)
    payload.pop("cache_enabled", None)
    payload.pop("cache_control_env", None)
    status_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    runtime_print(
        f"Recorded gate status at {payload['last_run']} "
        f"for command `{payload['command']}`.",
        verbose_only=True,
    )


def _stdout_is_tty() -> bool:
    """Return True when stdout reports interactive output capability."""
    stream = sys.stdout
    return bool(getattr(stream, "isatty", False) and stream.isatty())


class _TestCommandProgress:
    """Track required test commands via optional tqdm-based progress output."""

    def __init__(self, total: int, output_mode: OutputMode):
        """Initialize counter state and decide whether to show a bar."""
        self.total = total
        self._count = 0
        self._bar = None
        self._normal_mode = output_mode == "normal"
        self._enabled = (
            self._normal_mode
            and tqdm is not None
            and _stdout_is_tty()
            and self.total > 0
        )

    def __enter__(self):
        """Create the progress bar when running in normal interactive mode."""
        if self._enabled:
            self._bar = tqdm(
                total=self.total,
                desc="Running tests",
                unit="cmd",
                leave=False,
                ncols=60,
            )
        return self

    def describe(self, description: str) -> None:
        """Update the optional progress bar description for the current
        command.
        """
        if self._bar is not None:
            self._bar.set_description_str(description, refresh=False)

    def complete_step(self, description: str) -> None:
        """Advance the bar or emit deterministic fallback output for normal
        mode.
        """
        self._count += 1
        if self._bar is not None:
            self._bar.update(1)
        elif self._normal_mode:
            runtime_print(f"[{self._count}/{self.total}] {description}")

    def close(self) -> None:
        """Close the progress bar resources when they are no longer needed."""
        if self._bar is not None:
            self._bar.close()
            self._bar = None

    def __exit__(self, exc_type, exc, exc_tb):
        """Ensure the progress bar is closed when exiting the context."""
        self.close()


def _emit_test_runtime_message(
    message: str,
    tests_output_mode: OutputMode,
    *,
    verbose_only: bool = False,
) -> None:
    """Emit one test-runtime line according to the tests output mode."""
    if verbose_only and tests_output_mode != "verbose":
        return
    runtime_print(message)


def run_and_record_tests(repo_root: Path, notes: str = "") -> int:
    """Run required test commands and record their status."""
    global _TEST_COMMAND_OUTPUT_MODE, _TEST_COMMAND_LABEL
    tests_output_mode = resolve_tests_output_mode(repo_root)
    try:
        commands, resolved_mode, source_field = resolve_required_test_commands(
            repo_root,
            tests_mode=tests_output_mode,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if not commands:
        raise SystemExit(
            "No required test commands are configured for "
            f"`engine.tests_output_mode: {resolved_mode}`. Set "
            "`devflow-run-gates.required_commands` in active profile "
            "overlays."
        )
    try:
        managed_env, managed_python = resolve_managed_environment_for_stage(
            repo_root,
            "test",
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    # Clear any stale warnings from prior calls in this process.
    event_runtime_module.consume_test_event_adapter_warnings()
    adapters = event_runtime_module.load_test_event_adapters(repo_root)
    adapter_warnings = (
        event_runtime_module.consume_test_event_adapter_warnings()
    )
    for warning in adapter_warnings:
        runtime_print(
            f"WARNING: test-event adapter load issue: {warning}",
            file=sys.stderr,
        )

    event_manager = event_runtime_module.TestEventManager(adapters)

    with _TestCommandProgress(
        len(commands),
        output_mode=resolved_mode,
    ) as progress:
        for raw, command in commands:
            command_tokens = rewrite_command_for_managed_python(
                command,
                managed_python,
            )
            command_str = " ".join(command_tokens)
            progress.describe(raw)
            _emit_test_runtime_message(
                f"Running: {command_str}",
                resolved_mode,
                verbose_only=True,
            )
            started = _dt.datetime.now(tz=_dt.timezone.utc)
            try:
                run_kwargs: dict[str, Any] = {"allow_codes": {0}}
                if managed_env is not None:
                    run_kwargs["env"] = managed_env
                    run_kwargs["cwd"] = repo_root
                previous_mode = _TEST_COMMAND_OUTPUT_MODE
                previous_label = _TEST_COMMAND_LABEL
                if resolved_mode == "normal":
                    _TEST_COMMAND_OUTPUT_MODE = "normal"
                    _TEST_COMMAND_LABEL = raw
                else:
                    _TEST_COMMAND_OUTPUT_MODE = None
                    _TEST_COMMAND_LABEL = ""
                try:
                    result = _run_command(command_tokens, **run_kwargs)
                finally:
                    _TEST_COMMAND_OUTPUT_MODE = previous_mode
                    _TEST_COMMAND_LABEL = previous_label
            except subprocess.CalledProcessError as exc:
                finished = _dt.datetime.now(tz=_dt.timezone.utc)
                event_manager.record_command(
                    command=command_tokens,
                    command_str=command_str,
                    started=started,
                    finished=finished,
                    exit_code=int(exc.returncode or 1),
                )
                raise
            finished = _dt.datetime.now(tz=_dt.timezone.utc)
            event_manager.record_command(
                command=command_tokens,
                command_str=command_str,
                started=started,
                finished=finished,
                exit_code=result.returncode,
            )
            progress.complete_step(raw)

    command_str = " && ".join(raw for raw, _ in commands)
    _emit_test_runtime_message(
        "Recording gate status…",
        resolved_mode,
        verbose_only=True,
    )
    record_gate_status(
        repo_root,
        command_str,
        notes=notes,
        test_events=[event.to_dict() for event in event_manager.events],
        tests_output_mode=resolved_mode,
        tests_required_commands_key=source_field,
    )
    return 0
