"""Tests for the name clarity policy."""

import tempfile
import unittest
from pathlib import Path

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.name_clarity import name_clarity
from devcovenant.core.translator_runtime import TranslatorRuntime

NameClarityCheck = name_clarity.NameClarityCheck


def _configured_policy() -> NameClarityCheck:
    """Return a policy instance scoped to the project_lib tree."""
    policy = NameClarityCheck()
    policy.set_options(
        {
            "include_prefixes": ["project_lib"],
            "include_suffixes": [".py"],
            "exclude_prefixes": ["project_lib/vendor"],
        },
        {},
    )
    return policy


def _build_module(tmp_path: Path, source: str) -> Path:
    """Create a sample module under the project_lib tree."""
    path = tmp_path / "project_lib" / "helpers" / "naming.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def _build_runtime(
    profile_name: str, suffixes: list[str]
) -> TranslatorRuntime:
    """Return a translator runtime with one language-profile declaration."""
    registry = {
        profile_name: {
            "category": "language",
            "path": f"devcovenant/core/profiles/{profile_name}",
            "translators": [
                {
                    "id": profile_name,
                    "extensions": suffixes,
                    "can_handle": {
                        "strategy": "module_function",
                        "entrypoint": "translator.py:can_handle",
                    },
                    "translate": {
                        "strategy": "module_function",
                        "entrypoint": "translator.py:translate",
                    },
                }
            ],
        }
    }
    return TranslatorRuntime(
        repo_root=Path.cwd(),
        profile_registry=registry,
        active_profiles=[profile_name],
    )


def _unit_test_detects_placeholder_identifiers(tmp_path: Path):
    """Placeholders should trigger name clarity warnings."""
    source = "def foo():\n    tmp = 1\n"
    target = _build_module(tmp_path, source)
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
        translator_runtime=_build_runtime("python", [".py"]),
    )

    violations = _configured_policy().check(context)
    assert len(violations) >= 2
    assert any("foo" in v.message for v in violations)
    assert all(v.severity == "warning" for v in violations)


def _unit_test_accepts_short_loop_counters(tmp_path: Path):
    """Loop counters should not trigger name clarity warnings."""
    source = "for i in range(3):\n    pass\n"
    target = _build_module(tmp_path, source)
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
        translator_runtime=_build_runtime("python", [".py"]),
    )

    assert _configured_policy().check(context) == []


def _unit_test_allows_explicit_override(tmp_path: Path):
    """Allow comments should silence name clarity warnings."""
    source = "foo = 1  # name-clarity: allow\n"
    target = _build_module(tmp_path, source)
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[target],
        translator_runtime=_build_runtime("python", [".py"]),
    )

    assert _configured_policy().check(context) == []


def _unit_test_ignores_vendor_files(tmp_path: Path):
    """Vendor directories should be exempt from name clarity checks."""
    path = (
        tmp_path
        / "project_lib"
        / "vendor"
        / "third_party"
        / "example"
        / "module.py"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("foo = 1\n", encoding="utf-8")
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[path],
        translator_runtime=_build_runtime("python", [".py"]),
    )

    assert _configured_policy().check(context) == []


def _unit_test_non_python_files_use_translators(tmp_path: Path):
    """Non-Python files should be checked via translators."""
    cases = [
        (".js", "const foo = 1;", "javascript"),
        (".ts", "const foo: number = 1;", "typescript"),
        (".go", "package main\nfunc main() { var foo = 1 }", "go"),
        (".rs", "fn main() { let foo = 1; }", "rust"),
        (".java", "class Demo { void run() { int foo = 1; } }", "java"),
        (".cs", "class Demo { void Run() { var foo = 1; } }", "csharp"),
    ]

    for suffix, code, translator_id in cases:
        path = tmp_path / "project_lib" / f"sample{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")

        policy = NameClarityCheck()
        policy.set_options(
            {
                "include_suffixes": [suffix],
                "include_prefixes": ["project_lib"],
                "exclude_prefixes": [],
            },
            {},
        )
        context = CheckContext(
            repo_root=tmp_path,
            changed_files=[path],
            translator_runtime=_build_runtime(translator_id, [suffix]),
        )
        violations = policy.check(context)
        assert violations, f"expected violation for {suffix}"


def _unit_test_non_python_short_loop_counters_allowed(
    tmp_path: Path, suffix: str, code: str
):
    """Short loop counters remain allowed across translators."""
    path = tmp_path / "project_lib" / f"loop{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8")

    policy = NameClarityCheck()
    policy.set_options(
        {
            "include_suffixes": [suffix],
            "include_prefixes": ["project_lib"],
            "exclude_prefixes": [],
        },
        {},
    )
    suffix_to_profile = {
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".cs": "csharp",
    }
    context = CheckContext(
        repo_root=tmp_path,
        changed_files=[path],
        translator_runtime=_build_runtime(suffix_to_profile[suffix], [suffix]),
    )
    assert policy.check(context) == []


class GeneratedUnittestCases(unittest.TestCase):
    """unittest wrappers for module-level tests."""

    def test_detects_placeholder_identifiers(self):
        """Run test_detects_placeholder_identifiers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_detects_placeholder_identifiers(tmp_path=tmp_path)

    def test_accepts_short_loop_counters(self):
        """Run test_accepts_short_loop_counters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_accepts_short_loop_counters(tmp_path=tmp_path)

    def test_allows_explicit_override(self):
        """Run test_allows_explicit_override."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_allows_explicit_override(tmp_path=tmp_path)

    def test_ignores_vendor_files(self):
        """Run test_ignores_vendor_files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_ignores_vendor_files(tmp_path=tmp_path)

    def test_non_python_files_use_translators(self):
        """Run test_non_python_files_use_translators."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            _unit_test_non_python_files_use_translators(tmp_path=tmp_path)

    def test_non_python_short_loop_counters_allowed__case_000(self):
        """Run test_non_python_short_loop_counters_allowed__case_000."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            suffix = ".js"
            code = "for (let i = 0; i < 3; i++) { const x = i; }"
            _unit_test_non_python_short_loop_counters_allowed(
                tmp_path=tmp_path, suffix=suffix, code=code
            )

    def test_non_python_short_loop_counters_allowed__case_001(self):
        """Run test_non_python_short_loop_counters_allowed__case_001."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            suffix = ".ts"
            code = "for (let i = 0; i < 3; i++) { const x = i; }"
            _unit_test_non_python_short_loop_counters_allowed(
                tmp_path=tmp_path, suffix=suffix, code=code
            )

    def test_non_python_short_loop_counters_allowed__case_002(self):
        """Run test_non_python_short_loop_counters_allowed__case_002."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            suffix = ".go"
            code = "package main\nfunc main() { for i := 0; i < 3; i++ { } }"
            _unit_test_non_python_short_loop_counters_allowed(
                tmp_path=tmp_path, suffix=suffix, code=code
            )

    def test_non_python_short_loop_counters_allowed__case_003(self):
        """Run test_non_python_short_loop_counters_allowed__case_003."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            suffix = ".rs"
            code = "fn main() { for i in 0..3 { let x = i; } }"
            _unit_test_non_python_short_loop_counters_allowed(
                tmp_path=tmp_path, suffix=suffix, code=code
            )

    def test_non_python_short_loop_counters_allowed__case_004(self):
        """Run test_non_python_short_loop_counters_allowed__case_004."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            suffix = ".java"
            code = "class Demo { void run() { for (int i=0;i<3;i++) {} } }"
            _unit_test_non_python_short_loop_counters_allowed(
                tmp_path=tmp_path, suffix=suffix, code=code
            )

    def test_non_python_short_loop_counters_allowed__case_005(self):
        """Run test_non_python_short_loop_counters_allowed__case_005."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir).resolve()
            suffix = ".cs"
            code = "class Demo { void Run(){ for(int i=0;i<3;i++){} } }"
            _unit_test_non_python_short_loop_counters_allowed(
                tmp_path=tmp_path, suffix=suffix, code=code
            )
