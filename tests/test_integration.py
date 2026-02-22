# pyright: reportMissingImports=false, reportUnknownVariableType=false

# tests/test_integration.py
"""Integration smoke test - verify all modules can be imported."""

import importlib
import sys
from pathlib import Path

# Make paper_digest package importable when running from paper_digest/ root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_imports_work():
    """Smoke test: verify all modules can be imported without network calls."""
    module_names = [
        "paper_digest.config",
        "paper_digest.models",
        "paper_digest.storage",
        "paper_digest.emailer",
        "paper_digest.runner",
        "paper_digest.fetchers.arxiv",
        "paper_digest.fetchers.nature",
        "paper_digest.fetchers.rss",
        "paper_digest.fetchers.aps_prl_rss",
        "paper_digest.fetchers.nature_journal_rss",
    ]

    imported_modules = [importlib.import_module(name) for name in module_names]
    assert all(module is not None for module in imported_modules)
