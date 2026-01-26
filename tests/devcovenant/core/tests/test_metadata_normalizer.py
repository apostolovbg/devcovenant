"""Tests for metadata normalization helpers."""

from pathlib import Path

from devcovenant.core.metadata_normalizer import normalize_agents_metadata


def _write_agents(path: Path, metadata: str) -> None:
    """Write a minimal AGENTS.md file with one policy."""
    text = (
        "# AGENTS\n\n"
        "## Policy: Sample\n\n"
        "```policy-def\n"
        f"{metadata}\n"
        "```\n\n"
        "Policy description.\n"
    )
    path.write_text(text, encoding="utf-8")


def _write_schema(path: Path, policy_id: str) -> None:
    """Write a minimal schema AGENTS file."""
    metadata = (
        f"id: {policy_id}\n"
        "status: active\n"
        "severity: error\n"
        "auto_fix: false\n"
        "updated: false\n"
        "applies_to: *.py\n"
        "enforcement: active\n"
        "apply: true\n"
        "custom: false\n"
        "sample_option: alpha\n"
    )
    text = (
        "# AGENTS\n\n"
        "## Policy: Sample\n\n"
        "```policy-def\n"
        f"{metadata}"
        "```\n\n"
        "Policy description.\n"
    )
    path.write_text(text, encoding="utf-8")


def test_normalize_adds_missing_keys(tmp_path: Path) -> None:
    """Missing keys are added and updated is set when normalized."""
    agents_path = tmp_path / "AGENTS.md"
    schema_path = tmp_path / "schema.md"
    _write_schema(schema_path, "sample-policy")
    _write_agents(
        agents_path,
        "id: sample-policy\n"
        "status: active\n"
        "severity: error\n"
        "auto_fix: false\n"
        "updated: false\n"
        "applies_to: *.py\n"
        "enforcement: active\n",
    )

    result = normalize_agents_metadata(agents_path, schema_path)
    updated = agents_path.read_text(encoding="utf-8")

    assert result.updated is True
    assert "apply: true" in updated
    assert "custom: false" in updated
    assert "sample_option: alpha" in updated
    assert "updated: true" in updated


def test_normalize_uses_common_defaults(tmp_path: Path) -> None:
    """Unknown policy ids still receive common metadata keys."""
    agents_path = tmp_path / "AGENTS.md"
    schema_path = tmp_path / "schema.md"
    _write_schema(schema_path, "other-policy")
    _write_agents(agents_path, "id: custom-policy\n")

    result = normalize_agents_metadata(agents_path, schema_path)
    updated = agents_path.read_text(encoding="utf-8")

    assert result.updated is True
    assert "status: active" in updated
    assert "severity: warning" in updated
    assert "apply: true" in updated


def test_normalize_respects_no_updated(tmp_path: Path) -> None:
    """Updated flags are not forced when set_updated is false."""
    agents_path = tmp_path / "AGENTS.md"
    schema_path = tmp_path / "schema.md"
    _write_schema(schema_path, "sample-policy")
    _write_agents(agents_path, "id: sample-policy\n")

    result = normalize_agents_metadata(
        agents_path, schema_path, set_updated=False
    )
    updated = agents_path.read_text(encoding="utf-8")

    assert result.updated is True
    assert "updated: true" not in updated
    assert "updated: false" in updated


def test_normalize_adds_selector_roles(tmp_path: Path) -> None:
    """Selector roles are inferred from legacy selector keys."""
    agents_path = tmp_path / "AGENTS.md"
    schema_path = tmp_path / "schema.md"
    _write_schema(schema_path, "sample-policy")
    _write_agents(
        agents_path,
        "id: sample-policy\n"
        "include_prefixes: app\n"
        "include_suffixes: .py\n",
    )

    normalize_agents_metadata(agents_path, schema_path)
    updated = agents_path.read_text(encoding="utf-8")

    assert "selector_roles: include" in updated
    assert "include_globs: app/**" in updated
    assert "  *.py" in updated
    assert "include_files:" in updated
    assert "include_dirs:" in updated


def test_normalize_migrates_guarded_paths(tmp_path: Path) -> None:
    """Guarded paths are migrated into guarded selector roles."""
    agents_path = tmp_path / "AGENTS.md"
    schema_path = tmp_path / "schema.md"
    _write_schema(schema_path, "sample-policy")
    _write_agents(
        agents_path,
        "id: sample-policy\n" "guarded_paths: secrets/**,ops/**\n",
    )

    normalize_agents_metadata(agents_path, schema_path)
    updated = agents_path.read_text(encoding="utf-8")

    assert "selector_roles: guarded" in updated
    assert "guarded_globs: secrets/**" in updated
    assert "  ops/**" in updated
    assert "guarded_files:" in updated
    assert "guarded_dirs:" in updated


def test_normalize_migrates_user_visible_roles(tmp_path: Path) -> None:
    """User-visible selectors migrate into selector roles."""
    agents_path = tmp_path / "AGENTS.md"
    schema_path = tmp_path / "schema.md"
    _write_schema(schema_path, "sample-policy")
    _write_agents(
        agents_path,
        "id: sample-policy\n"
        "user_visible_files: README.md\n"
        "user_visible_prefixes: docs\n",
    )

    normalize_agents_metadata(agents_path, schema_path)
    updated = agents_path.read_text(encoding="utf-8")

    assert "selector_roles: user_visible" in updated
    assert "user_visible_files: README.md" in updated
    assert "user_visible_dirs: docs/**" in updated
    assert "user_visible_globs:" in updated


def test_normalize_migrates_doc_quality_roles(tmp_path: Path) -> None:
    """Doc-quality selectors migrate into selector roles."""
    agents_path = tmp_path / "AGENTS.md"
    schema_path = tmp_path / "schema.md"
    _write_schema(schema_path, "sample-policy")
    _write_agents(
        agents_path,
        "id: sample-policy\n"
        "doc_quality_files: README.md\n"
        "doc_quality_globs: docs/*.md\n",
    )

    normalize_agents_metadata(agents_path, schema_path)
    updated = agents_path.read_text(encoding="utf-8")

    assert "selector_roles: doc_quality" in updated
    assert "doc_quality_files: README.md" in updated
    assert "doc_quality_globs: docs/*.md" in updated
    assert "doc_quality_dirs:" in updated


def test_normalize_migrates_user_facing_roles(tmp_path: Path) -> None:
    """User-facing selectors migrate into selector roles."""
    agents_path = tmp_path / "AGENTS.md"
    schema_path = tmp_path / "schema.md"
    _write_schema(schema_path, "sample-policy")
    _write_agents(
        agents_path,
        "id: sample-policy\n"
        "user_facing_files: api.py\n"
        "user_facing_suffixes: .py\n"
        "user_facing_exclude_prefixes: tests\n",
    )

    normalize_agents_metadata(agents_path, schema_path)
    updated = agents_path.read_text(encoding="utf-8")

    assert "selector_roles: user_facing,user_facing_exclude" in updated
    assert "user_facing_files: api.py" in updated
    assert "user_facing_globs: *.py" in updated
    assert "user_facing_dirs:" in updated
    assert "user_facing_exclude_dirs: tests/**" in updated
    assert "user_facing_exclude_globs:" in updated


def test_normalize_migrates_exclude_prefixes(tmp_path: Path) -> None:
    """Legacy exclude prefixes should migrate into selector roles."""
    agents_path = tmp_path / "AGENTS.md"
    schema_path = tmp_path / "schema.md"
    _write_schema(schema_path, "sample-policy")
    _write_agents(
        agents_path,
        "id: sample-policy\n" "exclude_prefixes: tests\n",
    )

    normalize_agents_metadata(agents_path, schema_path)
    updated = agents_path.read_text(encoding="utf-8")

    assert "selector_roles: exclude" in updated
    assert "exclude_globs: tests/**" in updated
    assert "exclude_files:" in updated
    assert "exclude_dirs:" in updated
