"""Sanity and behavior checks for devcovenant.core.run_logs."""

from __future__ import annotations

import datetime as dt
import importlib
import json
import tempfile
import unittest
from pathlib import Path

MODULE = "devcovenant.core.run_logs"


def _load_json(path: Path) -> dict:
    """Load one JSON file into a mapping."""
    return json.loads(path.read_text(encoding="utf-8"))


def _fixed_start() -> dt.datetime:
    """Return a stable UTC timestamp for deterministic tests."""
    return dt.datetime(2026, 2, 25, 12, 0, 0, 123456, tzinfo=dt.timezone.utc)


def _unit_test_module_importable() -> None:
    """Module should import cleanly."""
    module = importlib.import_module(MODULE)
    assert module is not None


def _unit_test_module_has_public_symbols() -> None:
    """Module should expose at least one public symbol."""
    module = importlib.import_module(MODULE)
    public_symbols = [name for name in dir(module) if not name.startswith("_")]
    assert public_symbols


def _unit_test_run_logging_symbol_contract_is_stable() -> None:
    """Run logging runtime helpers should remain available."""
    module = importlib.import_module(MODULE)
    expected = [
        "RUN_LOG_SCHEMA_VERSION",
        "RunLogContext",
        "RunLogPaths",
        "append_run_stream_output",
        "create_run_log_context",
        "finalize_run_log_context",
        "latest_run_pointer_path",
        "load_run_log_context",
        "prune_run_log_directories",
        "record_latest_run_pointer",
        "resolve_run_logs_root",
        "write_run_summary_json",
        "write_run_summary_text",
        "write_run_tail",
    ]
    for symbol in expected:
        assert hasattr(module, symbol), symbol


def _unit_test_create_run_log_context_initializes_artifacts() -> None:
    """Creating a run context should initialize the standard artifacts."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        context = module.create_run_log_context(
            repo_root,
            "run",
            ["python3", "-m", "devcovenant", "run"],
            started_at=_fixed_start(),
            metadata={"slice": "item2"},
        )

        logs_root = repo_root / "devcovenant" / "logs"
        assert module.resolve_run_logs_root(repo_root) == logs_root
        assert context.logs_root == logs_root
        assert context.require_paths().run_dir.is_dir()
        assert context.require_paths().run_json.exists()
        assert context.require_paths().summary_txt.exists()
        assert context.require_paths().summary_json.exists()
        assert context.require_paths().stdout_log.exists()
        assert context.require_paths().stderr_log.exists()
        assert context.require_paths().tail_txt.exists()

        run_payload = _load_json(context.require_paths().run_json)
        assert run_payload["status"] == "running"
        assert run_payload["exit_code"] is None
        assert run_payload["command_name"] == "run"
        assert run_payload["metadata"]["slice"] == "item2"
        assert run_payload["run_dir"].startswith("devcovenant/logs/")

        summary_payload = _load_json(context.require_paths().summary_json)
        assert summary_payload["status"] == "running"

        latest_payload = _load_json(module.latest_run_pointer_path(repo_root))
        assert latest_payload["run_id"] == context.run_id
        assert latest_payload["status"] == "running"


def _unit_test_run_id_collision_appends_numeric_suffix() -> None:
    """Repeated allocations should use deterministic collision suffixes."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        first = module.create_run_log_context(
            repo_root,
            "gate",
            ["devcovenant", "gate", "--start"],
            started_at=_fixed_start(),
        )
        second = module.create_run_log_context(
            repo_root,
            "gate",
            ["devcovenant", "gate", "--start"],
            started_at=_fixed_start(),
        )

        assert first.run_id != second.run_id
        assert second.run_id.endswith("-002")


def _unit_test_finalize_updates_run_metadata_and_pointer() -> None:
    """Finalization should update metadata and latest pointer status."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        started = _fixed_start()
        finished = started + dt.timedelta(seconds=5)
        context = module.create_run_log_context(
            repo_root,
            "check",
            ["devcovenant", "check"],
            started_at=started,
        )
        module.append_run_stream_output(context, "stdout", "hello\n")
        module.write_run_tail(context, "tail line\n")
        module.finalize_run_log_context(
            context,
            exit_code=0,
            finished_at=finished,
            summary_text="summary ok\n",
            summary_data={"status": "custom-success", "hint": "ok"},
            metadata_updates={"autofix": True},
        )

        assert (
            context.require_paths().stdout_log.read_text(encoding="utf-8")
            == "hello\n"
        )
        assert (
            context.require_paths().tail_txt.read_text(encoding="utf-8")
            == "tail line\n"
        )
        assert (
            context.require_paths().summary_txt.read_text(encoding="utf-8")
            == "summary ok\n"
        )

        summary_payload = _load_json(context.require_paths().summary_json)
        assert summary_payload["status"] == "custom-success"
        assert summary_payload["hint"] == "ok"

        run_payload = _load_json(context.require_paths().run_json)
        assert run_payload["status"] == "success"
        assert run_payload["exit_code"] == 0
        assert run_payload["finished_at"] == finished.isoformat()
        assert run_payload["metadata"]["autofix"] is True

        latest_payload = _load_json(module.latest_run_pointer_path(repo_root))
        assert latest_payload["status"] == "success"
        assert latest_payload["exit_code"] == 0
        assert latest_payload["run_id"] == context.run_id


def _unit_test_run_metadata_redacts_secret_like_cli_and_metadata() -> None:
    """Persisted run metadata should redact obvious secret-bearing values."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        context = module.create_run_log_context(
            repo_root,
            "check",
            [
                "devcovenant",
                "check",
                "--token",
                "abc123",
                "--api-key=shh",
                "PASSWORD=hunter2",
            ],
            started_at=_fixed_start(),
            metadata={
                "api_token": "abc123",
                "safe": "visible",
                "nested": {
                    "authorization": "Bearer secret",
                    "safe": "nested-visible",
                },
            },
        )

        run_payload = _load_json(context.require_paths().run_json)
        assert run_payload["argv"] == [
            "devcovenant",
            "check",
            "--token",
            "[REDACTED]",
            "--api-key=[REDACTED]",
            "PASSWORD=[REDACTED]",
        ]
        assert run_payload["metadata"]["api_token"] == "[REDACTED]"
        assert run_payload["metadata"]["safe"] == "visible"
        assert run_payload["metadata"]["nested"]["authorization"] == (
            "[REDACTED]"
        )
        assert run_payload["metadata"]["nested"]["safe"] == "nested-visible"


def _unit_test_load_run_log_context_restores_existing_artifacts() -> None:
    """Loading an existing context should reuse the original run folder."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        original = module.create_run_log_context(
            repo_root,
            "run",
            ["devcovenant", "run"],
            started_at=_fixed_start(),
            metadata={"origin": "create"},
        )
        module.append_run_stream_output(original, "stdout", "hello\n")
        loaded = module.load_run_log_context(repo_root, run_id=original.run_id)

        assert loaded.run_id == original.run_id
        assert loaded.command_name == "run"
        assert loaded.metadata["origin"] == "create"
        assert (
            loaded.require_paths().run_dir == original.require_paths().run_dir
        )
        assert (
            loaded.require_paths().stdout_log.read_text(encoding="utf-8")
            == "hello\n"
        )


def _unit_test_symbol_level_assertions_cover_public_helpers() -> None:
    """Assert public helper symbols directly and exercise summary writers."""
    module = importlib.import_module(MODULE)
    assert module.RunLogContext is not None
    assert module.RunLogPaths is not None
    assert module.create_run_log_context is not None
    assert module.finalize_run_log_context is not None
    assert module.load_run_log_context is not None
    assert module.record_latest_run_pointer is not None
    assert module.write_run_summary_json is not None
    assert module.write_run_summary_text is not None
    assert module.write_run_tail is not None

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        context = module.create_run_log_context(
            repo_root,
            "run",
            ["devcovenant", "run"],
            started_at=_fixed_start(),
        )
        assert isinstance(context, module.RunLogContext)
        assert isinstance(context.require_paths(), module.RunLogPaths)

        module.write_run_summary_text(context, "manual summary\n")
        module.write_run_summary_json(
            context,
            {"status": "manual", "kind": "run"},
        )
        module.write_run_tail(context, "tail preview\n")
        module.record_latest_run_pointer(
            context,
            status="manual",
            exit_code=3,
            finished_at=_fixed_start(),
        )
        module.finalize_run_log_context(
            context,
            exit_code=0,
            summary_text="done\n",
            summary_data={"status": "done"},
        )

        assert (
            context.require_paths().summary_txt.read_text(encoding="utf-8")
            == "done\n"
        )
        summary_payload = _load_json(context.require_paths().summary_json)
        assert summary_payload["status"] == "done"
        assert (
            context.require_paths().tail_txt.read_text(encoding="utf-8")
            == "tail preview\n"
        )
        latest_payload = _load_json(module.latest_run_pointer_path(repo_root))
        assert latest_payload["run_id"] == context.run_id
        assert latest_payload["status"] == "success"


def _unit_test_append_run_stream_output_validates_stream_name() -> None:
    """Unknown stream names should raise a clear validation error."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        context = module.create_run_log_context(
            repo_root,
            "run",
            ["devcovenant", "run"],
            started_at=_fixed_start(),
        )
        try:
            module.append_run_stream_output(context, "nope", "x")
        except ValueError as exc:
            assert "stdout" in str(exc)
            assert "stderr" in str(exc)
        else:  # pragma: no cover - defensive branch
            raise AssertionError("Expected ValueError for invalid stream")


def _unit_test_prune_run_log_directories_keeps_latest_n_runs() -> None:
    """Retention pruning should keep newest runs and preserve helper files."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        logs_root = repo_root / "devcovenant" / "logs"
        logs_root.mkdir(parents=True, exist_ok=True)
        (logs_root / "README.md").write_text("tracked\n", encoding="utf-8")
        runtime_root = repo_root / "devcovenant" / "registry" / "runtime"
        runtime_root.mkdir(parents=True, exist_ok=True)
        (runtime_root / "latest.json").write_text("{}", encoding="utf-8")

        starts = [
            _fixed_start(),
            _fixed_start() + dt.timedelta(seconds=1),
            _fixed_start() + dt.timedelta(seconds=2),
        ]
        runs = []
        for started in starts:
            ctx = module.create_run_log_context(
                repo_root,
                "run",
                ["devcovenant", "run"],
                started_at=started,
            )
            module.finalize_run_log_context(ctx, exit_code=0)
            runs.append(ctx)

        removed = module.prune_run_log_directories(repo_root, keep_last=2)

        assert len(removed) == 1
        assert runs[0].run_id in removed
        assert not (logs_root / runs[0].run_id).exists()
        assert (logs_root / runs[1].run_id).is_dir()
        assert (logs_root / runs[2].run_id).is_dir()
        assert (logs_root / "README.md").is_file()
        assert (runtime_root / "latest.json").is_file()


def _unit_test_prune_run_log_directories_zero_keeps_all() -> None:
    """Retention value `0` should keep all run folders."""
    module = importlib.import_module(MODULE)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        first = module.create_run_log_context(
            repo_root,
            "check",
            ["devcovenant", "check"],
            started_at=_fixed_start(),
        )
        second = module.create_run_log_context(
            repo_root,
            "check",
            ["devcovenant", "check"],
            started_at=_fixed_start() + dt.timedelta(seconds=1),
        )

        removed = module.prune_run_log_directories(repo_root, keep_last=0)

        assert removed == []
        assert first.require_paths().run_dir.is_dir()
        assert second.require_paths().run_dir.is_dir()


class RunLogsTests(unittest.TestCase):
    """unittest wrappers for layered module sanity and behavior checks."""

    def test_module_importable(self):
        """Run module importability sanity check."""
        _unit_test_module_importable()

    def test_module_has_public_symbols(self):
        """Run module public-symbol sanity check."""
        _unit_test_module_has_public_symbols()

    def test_run_logging_symbol_contract_is_stable(self):
        """Run run-logging symbol contract assertions."""
        _unit_test_run_logging_symbol_contract_is_stable()

    def test_create_run_log_context_initializes_artifacts(self):
        """Run artifact initialization assertions."""
        _unit_test_create_run_log_context_initializes_artifacts()

    def test_run_id_collision_appends_numeric_suffix(self):
        """Run deterministic collision suffix assertions."""
        _unit_test_run_id_collision_appends_numeric_suffix()

    def test_finalize_updates_run_metadata_and_pointer(self):
        """Run finalize metadata and pointer update assertions."""
        _unit_test_finalize_updates_run_metadata_and_pointer()

    def test_run_metadata_redacts_secret_like_cli_and_metadata(self):
        """Run persisted run-metadata redaction assertions."""
        _unit_test_run_metadata_redacts_secret_like_cli_and_metadata()

    def test_load_run_log_context_restores_existing_artifacts(self):
        """Run existing-context restoration assertions."""
        _unit_test_load_run_log_context_restores_existing_artifacts()

    def test_symbol_level_assertions_cover_public_helpers(self):
        """Run explicit public-helper symbol assertions and writer coverage."""
        _unit_test_symbol_level_assertions_cover_public_helpers()

    def test_append_run_stream_output_validates_stream_name(self):
        """Run invalid stream-name validation assertions."""
        _unit_test_append_run_stream_output_validates_stream_name()

    def test_prune_run_log_directories_keeps_latest_n_runs(self):
        """Run log-retention pruning assertions for positive keep counts."""
        _unit_test_prune_run_log_directories_keeps_latest_n_runs()

    def test_prune_run_log_directories_zero_keeps_all(self):
        """Run log-retention pruning assertions for keep-all mode."""
        _unit_test_prune_run_log_directories_zero_keeps_all()
