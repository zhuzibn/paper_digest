# pyright: reportMissingImports=false, reportUnknownVariableType=false

# tests/test_integration.py
"""Integration smoke test - verify all modules can be imported."""

import sys
from pathlib import Path

# Make paper_digest package importable when running from paper_digest/ root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_imports_work():
    """Smoke test: verify all modules can be imported without network calls."""
    from paper_digest import config, models, storage, emailer, runner  # noqa: F401
    from paper_digest.fetchers import arxiv, nature  # noqa: F401

    assert True  # If we get here, imports work
