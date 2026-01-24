"""Tests for stock-policy-text-sync policy."""

from pathlib import Path

import yaml

from devcovenant.core.base import CheckContext
from devcovenant.core.policies.stock_policy_text_sync import (
    stock_policy_text_sync,
)


def _write_agents(path: Path, text: str) -> None:
    """Write the sample policy definition to AGENTS.md."""
    path.write_text(text, encoding="utf-8")


def _write_stock_texts(path: Path, mapping: dict[str, str]) -> None:
    """Persist the stock policy text mapping to disk."""
    payload = yaml.safe_dump(
        mapping,
        sort_keys=True,
        allow_unicode=False,
        width=60,
    )
    path.write_text(payload, encoding="utf-8")


def test_stock_policy_text_matches(tmp_path: Path) -> None:
    """Matching stock text should pass."""
    agents_path = tmp_path / "AGENTS.md"
    stock_path = (
        tmp_path / "devcovenant" / "registry" / "stock_policy_texts.yaml"
    )
    stock_path.parent.mkdir(parents=True)
    _write_stock_texts(stock_path, {"example-policy": "Stock text"})
    _write_agents(
        agents_path,
        """
## Policy: Example

```policy-def
id: example-policy
status: active
severity: warning
auto_fix: false
updated: false
```

Stock text

---
""".strip()
        + "\n",
    )

    checker = stock_policy_text_sync.StockPolicyTextSyncCheck()
    checker.set_options(
        {
            "policy_definitions": "AGENTS.md",
            "stock_texts_file": "devcovenant/registry/stock_policy_texts.yaml",
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, changed_files=[agents_path])

    assert checker.check(context) == []


def test_stock_policy_text_differs(tmp_path: Path) -> None:
    """Different stock text should raise a violation."""
    agents_path = tmp_path / "AGENTS.md"
    stock_path = (
        tmp_path / "devcovenant" / "registry" / "stock_policy_texts.yaml"
    )
    stock_path.parent.mkdir(parents=True)
    _write_stock_texts(stock_path, {"example-policy": "Stock text"})
    _write_agents(
        agents_path,
        """
## Policy: Example

```policy-def
id: example-policy
status: active
severity: warning
auto_fix: false
updated: false
```

Custom text

---
""".strip()
        + "\n",
    )

    checker = stock_policy_text_sync.StockPolicyTextSyncCheck()
    checker.set_options(
        {
            "policy_definitions": "AGENTS.md",
            "stock_texts_file": "devcovenant/registry/stock_policy_texts.yaml",
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, changed_files=[agents_path])
    violations = checker.check(context)

    assert violations
    assert "Stock policy text differs" in violations[0].message


def test_missing_stock_text_file(tmp_path: Path) -> None:
    """Missing stock file should raise an error."""
    agents_path = tmp_path / "AGENTS.md"
    _write_agents(
        agents_path,
        """
## Policy: Example

```policy-def
id: example-policy
status: active
severity: warning
auto_fix: false
updated: false
```

Stock text

---
""".strip()
        + "\n",
    )

    checker = stock_policy_text_sync.StockPolicyTextSyncCheck()
    checker.set_options(
        {
            "policy_definitions": "AGENTS.md",
            "stock_texts_file": "devcovenant/registry/stock_policy_texts.yaml",
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, changed_files=[agents_path])
    violations = checker.check(context)

    assert violations
    assert "Stock policy text map" in violations[0].message


def test_custom_policy_skips_stock_text_check(tmp_path: Path) -> None:
    """Custom policies should skip stock text sync."""
    agents_path = tmp_path / "AGENTS.md"
    stock_path = (
        tmp_path / "devcovenant" / "registry" / "stock_policy_texts.yaml"
    )
    stock_path.parent.mkdir(parents=True)
    _write_stock_texts(stock_path, {"example-policy": "Stock text"})
    _write_agents(
        agents_path,
        """
## Policy: Example

```policy-def
id: example-policy
status: active
severity: warning
auto_fix: false
updated: false
custom: true
```

Custom text

---
""".strip()
        + "\n",
    )

    checker = stock_policy_text_sync.StockPolicyTextSyncCheck()
    checker.set_options(
        {
            "policy_definitions": "AGENTS.md",
            "stock_texts_file": "devcovenant/registry/stock_policy_texts.yaml",
        },
        {},
    )
    context = CheckContext(repo_root=tmp_path, changed_files=[agents_path])
    assert checker.check(context) == []
