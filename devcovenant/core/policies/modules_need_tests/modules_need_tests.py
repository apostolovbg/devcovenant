"""Ensure in-scope modules carry tests via shared translator LanguageUnit."""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path
from typing import List, Set, Tuple

from devcovenant.core.policy_contracts import (
    CheckContext,
    PolicyCheck,
    Violation,
)
from devcovenant.core.selector_runtime import SelectorSet, build_watchlists

IGNORED_MODULE_STEMS = {"__init__", "__main__"}


def _normalize_mirror_roots(raw_value: object) -> List[Tuple[str, str]]:
    """Parse mirror_roots metadata into (source, tests_root) pairs."""
    if raw_value is None:
        return []
    entries: list[str]
    if isinstance(raw_value, str):
        entries = [raw_value]
    elif isinstance(raw_value, list):
        entries = [str(entry).strip() for entry in raw_value]
    else:
        entries = [str(raw_value).strip()]

    rules: List[Tuple[str, str]] = []
    for raw_entry in entries:
        token = raw_entry.strip()
        if not token:
            continue
        if "=>" in token:
            source, target = token.split("=>", 1)
        elif ":" in token:
            source, target = token.split(":", 1)
        else:
            continue
        source_prefix = source.strip().replace("\\", "/").strip("/")
        target_prefix = target.strip().replace("\\", "/").strip("/")
        if not source_prefix or not target_prefix:
            continue
        rules.append((source_prefix, target_prefix))
    return rules


def _is_under_tests(
    path: Path, repo_root: Path, tests_dirs: List[str]
) -> bool:
    """Return True when path resolves under configured tests roots."""
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        return False
    return any(
        rel == test_dir or rel.startswith(f"{test_dir}/")
        for test_dir in tests_dirs
    )


def _collect_repo_files(repo_root: Path) -> Set[Path]:
    """Return tracked and untracked repository files."""
    files: Set[Path] = set()
    try:
        output = subprocess.check_output(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
            ],
            cwd=repo_root,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        for candidate in repo_root.rglob("*"):
            if candidate.is_file():
                files.add(candidate)
        return files

    for line in output.splitlines():
        normalized = line.strip()
        if not normalized:
            continue
        if len(line) >= 4 and line[2] == " " and line[:2].strip():
            normalized = line[3:].strip()
        candidate = repo_root / normalized
        if candidate.is_file():
            files.add(candidate)
    return files


def _test_roots(policy: PolicyCheck) -> List[str]:
    """Resolve configured tests roots using watch and tests_watch metadata."""
    _, configured_watch_dirs = build_watchlists(
        policy,
        defaults={"watch_dirs": ["tests"]},
    )
    _, prefixed_tests_dirs = build_watchlists(
        policy,
        prefix="tests_",
        defaults={"watch_dirs": configured_watch_dirs or ["tests"]},
    )
    if prefixed_tests_dirs:
        return prefixed_tests_dirs
    if configured_watch_dirs:
        return configured_watch_dirs
    return ["tests"]


def _is_module_candidate(
    path: Path,
    *,
    selector: SelectorSet,
    repo_root: Path,
    tests_dirs: List[str],
) -> bool:
    """Return True when path represents a source module to track."""
    if not path.is_file():
        return False
    if path.name.startswith("test_"):
        return False
    if path.stem in IGNORED_MODULE_STEMS:
        return False
    if _is_under_tests(path, repo_root, tests_dirs):
        return False
    return selector.matches(path, repo_root)


def _list_existing_tests(repo_root: Path, tests_dirs: List[str]) -> list[Path]:
    """Return existing files under configured tests roots."""
    discovered: list[Path] = []
    for tests_dir in tests_dirs:
        root = repo_root / tests_dir
        if not root.exists():
            continue
        for candidate in root.rglob("*"):
            if candidate.is_file():
                discovered.append(candidate)
    return discovered


def _find_related_test(
    module: Path,
    *,
    unit_templates: tuple[str, ...],
    tests: list[Path],
    repo_root: Path,
) -> bool:
    """Return True when one related test exists for module."""
    stem = module.stem
    compact_stem = re.sub(r"[^a-zA-Z0-9]+", "", stem.lower())
    test_set = {
        path.relative_to(repo_root).as_posix().lower() for path in tests
    }

    for template in unit_templates:
        candidate_name = template.format(stem=stem)
        for test in test_set:
            if test.endswith(f"/{candidate_name.lower()}"):
                return True
            if test == candidate_name.lower():
                return True

    for test in test_set:
        test_name = Path(test).name
        if stem.lower() in test_name:
            return True
        compact_test = re.sub(r"[^a-zA-Z0-9]+", "", test_name)
        if compact_stem and compact_stem in compact_test:
            return True

    return False


def _mirror_candidates(
    module: Path,
    *,
    repo_root: Path,
    mirror_roots: list[tuple[str, str]],
) -> list[Path]:
    """Return mirror candidates for configured mirror roots."""
    try:
        rel = module.relative_to(repo_root).as_posix()
    except ValueError:
        return []
    expected: list[Path] = []
    for source_prefix, tests_prefix in mirror_roots:
        if rel != source_prefix and not rel.startswith(f"{source_prefix}/"):
            continue
        remainder = rel[len(source_prefix) :].lstrip("/")
        if not remainder:
            continue
        remainder_path = Path(remainder)
        expected.append(
            repo_root
            / tests_prefix
            / remainder_path.parent
            / f"test_{remainder_path.stem}.py"
        )
    return expected


def _validate_unittest_style(path: Path) -> str | None:
    """Return violation message when Python tests are not unittest-style."""
    if path.suffix.lower() != ".py" or not path.name.startswith("test_"):
        return None
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None

    if "export_unittest_cases(" in content:
        return (
            "Remove unittest bridge usage and define explicit "
            "unittest.TestCase tests."
        )

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return None

    has_top_level = any(
        isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        for node in tree.body
    )
    if has_top_level:
        return (
            "Module-level test_* functions are not allowed; "
            "use unittest.TestCase methods."
        )

    has_unittest = False
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        is_testcase = any(
            (
                isinstance(base, ast.Name)
                and base.id == "TestCase"
                or isinstance(base, ast.Attribute)
                and base.attr == "TestCase"
            )
            for base in node.bases
        )
        if not is_testcase:
            continue
        has_method = any(
            isinstance(method, ast.FunctionDef)
            and method.name.startswith("test_")
            for method in node.body
        )
        if has_method:
            has_unittest = True
            break

    if has_unittest:
        return None
    return (
        "Python test modules must define unittest.TestCase "
        "classes with test_* methods."
    )


class ModulesNeedTestsCheck(PolicyCheck):
    """Ensure in-scope modules ship with accompanying tests."""

    policy_id = "modules-need-tests"
    version = "1.5.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Check that in-scope modules have corresponding tests."""
        runtime = context.translator_runtime
        if runtime is None:
            return []

        violations: List[Violation] = []
        repo_files = _collect_repo_files(context.repo_root)
        selector = SelectorSet.from_policy(self)
        tests_dirs = _test_roots(self)
        tests_label = ", ".join(sorted(tests_dirs))
        mirror_roots = _normalize_mirror_roots(
            self.get_option("mirror_roots", [])
        )

        test_files = _list_existing_tests(context.repo_root, tests_dirs)
        module_files = [
            path
            for path in sorted(repo_files)
            if _is_module_candidate(
                path,
                selector=selector,
                repo_root=context.repo_root,
                tests_dirs=tests_dirs,
            )
        ]

        if module_files and not test_files:
            modules = ", ".join(
                path.relative_to(context.repo_root).as_posix()
                for path in module_files
            )
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=module_files[0],
                    message=(
                        f"No tests found under {tests_label}; "
                        "add tests before "
                        f"changing modules:\n{modules}"
                    ),
                )
            )
            return violations

        for module in module_files:
            resolution = runtime.resolve(
                path=module,
                policy_id=self.policy_id,
                context=context,
            )
            if not resolution.is_resolved:
                violations.extend(resolution.violations)
                continue
            source = module.read_text(encoding="utf-8")
            unit = runtime.translate(
                resolution,
                path=module,
                source=source,
                context=context,
            )
            if unit is None:
                continue

            expected = _mirror_candidates(
                module,
                repo_root=context.repo_root,
                mirror_roots=mirror_roots,
            )
            if expected:
                if any(path.exists() for path in expected):
                    continue
                expected_display = ", ".join(
                    sorted(
                        path.relative_to(context.repo_root).as_posix()
                        for path in expected
                    )
                )
                violations.append(
                    Violation(
                        policy_id=self.policy_id,
                        severity="error",
                        file_path=module,
                        message=(
                            "Mirror mode requires tests under mirrored paths. "
                            f"Add one of: {expected_display}"
                        ),
                    )
                )
                continue

            if _find_related_test(
                module,
                unit_templates=unit.test_name_templates,
                tests=test_files,
                repo_root=context.repo_root,
            ):
                continue
            module_rel = module.relative_to(context.repo_root).as_posix()
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=module,
                    message=(
                        f"Add or update related tests under {tests_label}/ "
                        f"for changed module: {module_rel}"
                    ),
                )
            )

        if mirror_roots:
            for test_file in sorted(test_files):
                if test_file.suffix.lower() != ".py":
                    continue
                matched = False
                for source_prefix, tests_prefix in mirror_roots:
                    tests_root = context.repo_root / tests_prefix
                    try:
                        rel = test_file.relative_to(tests_root)
                    except ValueError:
                        continue
                    matched = True
                    if not rel.name.startswith("test_"):
                        break
                    source = (
                        context.repo_root
                        / source_prefix
                        / rel.parent
                        / f"{rel.name[5:-3]}.py"
                    )
                    if source.exists() and _is_module_candidate(
                        source,
                        selector=selector,
                        repo_root=context.repo_root,
                        tests_dirs=tests_dirs,
                    ):
                        break
                    test_rel = test_file.relative_to(
                        context.repo_root
                    ).as_posix()
                    violations.append(
                        Violation(
                            policy_id=self.policy_id,
                            severity="error",
                            file_path=test_file,
                            message=(
                                "Remove stale mirrored test with no valid "
                                f"source module: {test_rel}"
                            ),
                        )
                    )
                    break
                if not matched:
                    continue

        for test_path in sorted(test_files):
            message = _validate_unittest_style(test_path)
            if not message:
                continue
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=test_path,
                    message=message,
                )
            )

        return violations
