"""Detect custom edits to stock policy text."""

from pathlib import Path
from typing import List

from devcovenant.core.base import CheckContext, PolicyCheck, Violation
from devcovenant.core.parser import PolicyParser
from devcovenant.core.policy_texts import load_stock_texts


def _normalize(text: str) -> str:
    """Normalize policy text for comparison."""
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


class StockPolicyTextSyncCheck(PolicyCheck):
    """Warn when stock policy text differs from canonical text."""

    policy_id = "stock-policy-text-sync"
    version = "1.0.0"

    def check(self, context: CheckContext) -> List[Violation]:
        """Compare policy text to the stock text map."""
        agents_rel = Path(self.get_option("policy_definitions", "AGENTS.md"))
        stock_rel = self.get_option(
            "stock_texts_file", "devcovenant/core/stock_policy_texts.json"
        )
        agents_path = context.repo_root / agents_rel
        if not agents_path.exists():
            return []

        stock_texts = load_stock_texts(context.repo_root, stock_rel)
        if not stock_texts:
            return [
                Violation(
                    policy_id=self.policy_id,
                    severity="error",
                    file_path=agents_path,
                    message=(
                        "Stock policy text map is missing. Regenerate "
                        "devcovenant/core/stock_policy_texts.json."
                    ),
                )
            ]

        parser = PolicyParser(agents_path)
        violations: List[Violation] = []
        for policy in parser.parse_agents_md():
            canonical = stock_texts.get(policy.policy_id)
            if canonical is None:
                continue
            if _normalize(policy.description) == _normalize(canonical):
                continue
            violations.append(
                Violation(
                    policy_id=self.policy_id,
                    severity="warning",
                    file_path=agents_path,
                    message=(
                        "Stock policy text differs from canonical. "
                        f"Policy '{policy.policy_id}' should use stock text "
                        "or be patched to match its new meaning."
                    ),
                    suggestion=(
                        "Run `python3 -m devcovenant.cli restore-stock-text "
                        f"--policy {policy.policy_id}` or add a patch that "
                        "aligns enforcement with the edited text."
                    ),
                )
            )
        return violations
