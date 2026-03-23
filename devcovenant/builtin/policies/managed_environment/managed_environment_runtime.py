"""Runtime helpers owned by managed-environment policy."""

from __future__ import annotations

import os
import re
import shlex
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

import devcovenant.core.services.metadata as metadata_runtime_module
import devcovenant.core.services.registry as registry_runtime_module
from devcovenant.core.runtime.execution import (
    run_child_command_with_output_policy,
    runtime_print,
)
from devcovenant.core.services import yaml_cache as yaml_cache_service

POLICY_ID = "managed-environment"
RUNTIME_ACTION_RESOLVE_STAGE = "resolve-stage"
_MANAGED_ENV_STAGES = frozenset({"start", "test", "end", "command", "all"})
_MANAGED_STAGE_RUNS_ENV = "DEVCOV_MANAGED_STAGE_RUNS"
_GUIDANCE_TOKEN_PATTERN = re.compile(r"{([a-zA-Z0-9_]+)}")


def _load_policy_entry(repo_root: Path) -> dict[str, Any] | None:
    """Load managed-environment policy entry from the tracked registry."""
    registry_path = registry_runtime_module.policy_registry_path(repo_root)
    if not registry_path.exists():
        config_path = repo_root / "devcovenant" / "config.yaml"
        if not config_path.exists():
            raise ValueError(
                "managed-environment runtime requires tracked registry "
                f"at {registry_path}. Run `devcovenant refresh`."
            )
        descriptor = registry_runtime_module.load_policy_descriptor(
            repo_root,
            POLICY_ID,
        )
        if descriptor is None:
            return None
        current_order, current_values = (
            metadata_runtime_module.descriptor_metadata_order_values(
                descriptor
            )
        )
        context = metadata_runtime_module.build_metadata_context(repo_root)
        bundle = metadata_runtime_module.resolve_policy_metadata_bundle(
            POLICY_ID,
            current_order,
            current_values,
            descriptor,
            context,
        )
        enabled_token = bundle.string_map.get("enabled", "")
        return {
            "enabled": enabled_token,
            "metadata": dict(bundle.string_map),
        }

    try:
        registry_data = yaml_cache_service.load_yaml(registry_path)
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
    entry = policies.get(POLICY_ID)
    if not isinstance(entry, dict):
        return None
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


def _resolve_metadata_paths(
    repo_root: Path,
    entries: list[str],
    *,
    resolve_symlinks: bool = True,
) -> list[Path]:
    """Resolve metadata path entries relative to repo root."""
    resolved: list[Path] = []
    for entry in entries:
        token = entry.strip()
        if not token:
            continue
        path = Path(token)
        if not path.is_absolute():
            path = repo_root / path
        if resolve_symlinks:
            try:
                resolved.append(path.resolve())
            except OSError:
                resolved.append(path)
            continue
        resolved.append(Path(os.path.abspath(str(path))))
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


def _select_managed_command_for_stage(
    managed_commands: list[tuple[str, str]],
    *,
    target_stage: str,
) -> str | None:
    """Select one stage command, preferring exact stage over `all`."""
    for command_stage, command_text in managed_commands:
        if command_stage == target_stage:
            return command_text
    for command_stage, command_text in managed_commands:
        if command_stage == "all":
            return command_text
    return None


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
            return posix_candidate, root
        windows_candidate = root / "Scripts" / "python.exe"
        if windows_candidate.exists():
            return windows_candidate, root
    return None, None


def _guidance_token_value(
    token: str,
    repo_root: Path,
    managed_python: Path | None,
    managed_root: Path | None,
) -> str:
    """Return rendered guidance token values with safe placeholders."""
    normalized = str(token or "").strip()
    if normalized == "repo_root":
        return str(repo_root)
    if normalized == "managed_root":
        if managed_root is None:
            return "<managed_root>"
        return str(managed_root)
    if normalized == "managed_python":
        if managed_python is None:
            return "<managed_python>"
        return str(managed_python)
    if normalized == "managed_bin":
        if managed_python is None:
            return "<managed_bin>"
        return str(managed_python.parent)
    if normalized:
        return f"<{normalized}>"
    return "<token>"


def _expand_guidance_command_tokens(
    command_text: str,
    repo_root: Path,
    managed_python: Path | None,
    managed_root: Path | None,
) -> str:
    """Expand guidance tokens with safe placeholders for missing context."""
    if "{" not in command_text:
        return command_text
    return _GUIDANCE_TOKEN_PATTERN.sub(
        lambda match: _guidance_token_value(
            match.group(1),
            repo_root,
            managed_python,
            managed_root,
        ),
        command_text,
    )


def _managed_guidance_suffix(
    manual_commands: list[str],
    *,
    repo_root: Path,
    managed_python: Path | None,
    managed_root: Path | None,
) -> str:
    """Build manual-commands suffix for managed-environment errors."""
    if not manual_commands:
        return ""
    expanded = [
        _expand_guidance_command_tokens(
            command,
            repo_root,
            managed_python,
            managed_root,
        )
        for command in manual_commands
    ]
    return " Manual commands: " + " | ".join(expanded)


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


def _read_managed_stage_runs(env: Mapping[str, str]) -> set[str]:
    """Return normalized set of stages already prepared in this process env."""
    raw = str(env.get(_MANAGED_STAGE_RUNS_ENV, "")).strip()
    if not raw:
        return set()
    stages: set[str] = set()
    for token in raw.split(","):
        stage = token.strip().lower()
        if stage in _MANAGED_ENV_STAGES:
            stages.add(stage)
    return stages


def _write_managed_stage_runs(env: dict[str, str], stages: set[str]) -> None:
    """Persist prepared-stage set into process environment."""
    ordered = [
        stage
        for stage in ("start", "test", "end", "command", "all")
        if stage in stages
    ]
    env[_MANAGED_STAGE_RUNS_ENV] = ",".join(ordered)


def _expand_managed_command_tokens(
    command_text: str,
    repo_root: Path,
    managed_python: Path | None,
    managed_root: Path | None,
) -> list[str]:
    """Expand managed-command placeholders and return argv tokens."""
    tokens = shlex.split(command_text)
    expanded: list[str] = []
    for token in tokens:
        resolved = token.replace("{repo_root}", str(repo_root))
        if "{managed_root}" in resolved:
            if managed_root is None:
                raise ValueError(
                    "Managed command uses `{managed_root}` before a "
                    "managed root exists. Run bootstrap commands first."
                )
            resolved = resolved.replace("{managed_root}", str(managed_root))
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
        if "{managed_bin}" in resolved:
            if managed_python is None:
                raise ValueError(
                    "Managed command uses `{managed_bin}` before an "
                    "expected interpreter exists. Run bootstrap commands "
                    "first."
                )
            resolved = resolved.replace(
                "{managed_bin}", str(managed_python.parent)
            )
        expanded.append(resolved)
    return expanded


def _run_command(
    command: Sequence[str],
    *,
    env: Mapping[str, str],
    cwd: Path,
) -> None:
    """Run one command and raise ValueError when it fails."""
    command_list = list(command)
    result, _ = run_child_command_with_output_policy(
        command_list,
        channel="managed_child",
        env=env,
        cwd=cwd,
        capture_combined_output=False,
        verbose_only_console=False,
    )
    return_code = int(result.returncode or 0)
    if return_code != 0:
        rendered = " ".join(command_list)
        raise ValueError(
            "Managed-environment command failed "
            f"({return_code}): {rendered}"
        )


def _run_managed_commands_for_stage(
    repo_root: Path,
    env: dict[str, str],
    managed_commands: list[tuple[str, str]],
    *,
    target_stage: str,
    expected_interpreters: list[Path],
    expected_paths: list[Path],
    include_all_stage: bool,
) -> tuple[dict[str, str], bool]:
    """Run managed commands for a stage and return updated environment."""
    updated_env = dict(env)
    ran_commands = False
    for command_stage, command_text in managed_commands:
        if include_all_stage:
            if command_stage not in {"all", target_stage}:
                continue
        elif command_stage != target_stage:
            continue
        ran_commands = True
        managed_python, managed_root = _detect_managed_python(
            expected_interpreters,
            expected_paths,
        )
        if managed_python is not None:
            updated_env = _apply_managed_env(
                updated_env,
                managed_python,
                managed_root,
            )
        command_tokens = _expand_managed_command_tokens(
            command_text,
            repo_root,
            managed_python,
            managed_root,
        )
        runtime_print(
            "Running managed-environment command "
            f"({target_stage}): {' '.join(command_tokens)}",
            verbose_only=True,
        )
        _run_command(command_tokens, env=updated_env, cwd=repo_root)
    return updated_env, ran_commands


def resolve_managed_environment_for_stage(
    repo_root: Path,
    stage: str,
    *,
    base_env: Mapping[str, str] | None = None,
) -> tuple[dict[str, str] | None, str | None]:
    """Resolve and optionally prepare managed-environment execution state."""
    stage_token = str(stage or "").strip().lower()
    if stage_token not in {"start", "test", "end", "command"}:
        raise ValueError(
            "Invalid managed-environment stage "
            f"`{stage}`. Allowed: start, test, end, command."
        )
    entry = _load_policy_entry(repo_root)
    if entry is None:
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
        repo_root,
        expected_interpreter_tokens,
        resolve_symlinks=False,
    )
    if not expected_paths and not expected_interpreters:
        guidance = _managed_guidance_suffix(
            manual_commands,
            repo_root=repo_root,
            managed_python=None,
            managed_root=None,
        )
        raise ValueError(
            "managed-environment is enabled, but no expected_paths or "
            f"expected_interpreters are configured.{guidance}"
        )

    env: dict[str, str] = (
        dict(base_env) if base_env is not None else dict(os.environ)
    )
    prepared_stages = _read_managed_stage_runs(env)
    if stage_token not in prepared_stages:
        env, ran_stage_commands = _run_managed_commands_for_stage(
            repo_root,
            env,
            managed_commands,
            target_stage=stage_token,
            expected_interpreters=expected_interpreters,
            expected_paths=expected_paths,
            include_all_stage=True,
        )
        if ran_stage_commands:
            prepared_stages.add(stage_token)
            _write_managed_stage_runs(env, prepared_stages)

    managed_python, managed_root = _detect_managed_python(
        expected_interpreters,
        expected_paths,
    )
    if (
        managed_python is None
        and stage_token != "start"
        and "start" not in prepared_stages
    ):
        env, ran_start_commands = _run_managed_commands_for_stage(
            repo_root,
            env,
            managed_commands,
            target_stage="start",
            expected_interpreters=expected_interpreters,
            expected_paths=expected_paths,
            include_all_stage=False,
        )
        if ran_start_commands:
            prepared_stages.add("start")
            _write_managed_stage_runs(env, prepared_stages)
        managed_python, managed_root = _detect_managed_python(
            expected_interpreters,
            expected_paths,
        )
    if managed_python is None:
        guidance = _managed_guidance_suffix(
            manual_commands,
            repo_root=repo_root,
            managed_python=managed_python,
            managed_root=managed_root,
        )
        raise ValueError(
            "managed-environment is enabled, but no expected interpreter was "
            f"found.{guidance}"
        )
    env = _apply_managed_env(env, managed_python, managed_root)
    return env, str(managed_python)


def resolve_cleanup_protected_paths(repo_root: Path) -> tuple[Path, ...]:
    """Return cleanup-protected roots from managed-environment metadata."""
    entry = _load_policy_entry(repo_root)
    if entry is None:
        return ()
    if not _is_enabled_token(entry.get("enabled")):
        return ()

    metadata_map = entry.get("metadata")
    if not isinstance(metadata_map, dict):
        raise ValueError(
            "Invalid policy registry payload: "
            "`managed-environment.metadata` must be a mapping."
        )

    cleanup_tokens = _normalize_metadata_tokens(
        metadata_map.get("cleanup_protected_paths")
    )
    if cleanup_tokens:
        return tuple(_resolve_metadata_paths(repo_root, cleanup_tokens))

    expected_path_tokens = _normalize_metadata_tokens(
        metadata_map.get("expected_paths")
    )
    expected_paths = _resolve_metadata_paths(repo_root, expected_path_tokens)
    if expected_paths:
        return tuple(expected_paths)

    expected_interpreter_tokens = _normalize_metadata_tokens(
        metadata_map.get("expected_interpreters")
    )
    expected_interpreters = _resolve_metadata_paths(
        repo_root,
        expected_interpreter_tokens,
        resolve_symlinks=False,
    )
    managed_python, managed_root = _detect_managed_python(
        expected_interpreters,
        expected_paths,
    )
    if managed_root is not None:
        return (managed_root,)
    if managed_python is not None:
        return (managed_python,)
    return tuple(expected_interpreters)
