"""Tests for common policy patch overrides."""

import tempfile
from pathlib import Path

from devcovenant.core.engine import DevCovenantEngine


def test_patch_overrides_metadata_options():
    """Patch files should override policy metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        devcov_dir = repo_root / "devcovenant"
        devcov_dir.mkdir()
        (devcov_dir / "core" / "policy_scripts").mkdir(parents=True)
        (devcov_dir / "common_policy_patches").mkdir(parents=True)

        agents = repo_root / "AGENTS.md"
        agents.write_text(
            "## Policy: Line Length Limit\n\n"
            "```policy-def\n"
            "id: line-length-limit\n"
            "status: active\n"
            "severity: error\n"
            "auto_fix: false\n"
            "updated: false\n"
            "applies_to: *\n"
            "enforcement: active\n"
            "apply: true\n"
            "max_length: 79\n"
            "include_suffixes: .txt\n"
            "```\n\n"
            "Line length check.\n",
            encoding="utf-8",
        )

        policy_script = (
            devcov_dir / "core" / "policy_scripts" / "line_length_limit.py"
        )
        policy_script.write_text(
            "from devcovenant.core.base import PolicyCheck, Violation\n"
            "class LineLengthLimitCheck(PolicyCheck):\n"
            "    policy_id = 'line-length-limit'\n"
            "    def check(self, context):\n"
            "        max_len = int(self.get_option('max_length', 79))\n"
            "        violations = []\n"
            "        for path in context.all_files:\n"
            "            for line in path.read_text().splitlines():\n"
            "                if len(line) > max_len:\n"
            "                    violations.append(Violation(\n"
            "                        policy_id=self.policy_id,\n"
            "                        severity='error',\n"
            "                        file_path=path,\n"
            "                        message='too long',\n"
            "                    ))\n"
            "        return violations\n",
            encoding="utf-8",
        )

        patch_file = (
            devcov_dir / "common_policy_patches" / "line_length_limit.py"
        )
        patch_file.write_text(
            "def patch_options(options, **kwargs):\n"
            "    return {'max_length': 100}\n",
            encoding="utf-8",
        )

        target = repo_root / "sample.txt"
        target.write_text("x" * 90, encoding="utf-8")

        engine = DevCovenantEngine(repo_root=repo_root)
        policies = engine.parser.parse_agents_md()
        context = engine._build_check_context("normal")
        context.all_files = [target]
        violations = engine.run_policy_checks(policies, "normal", context)

        assert violations == []
