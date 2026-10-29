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
        "paper_digest.runner",
        "paper_digest.fetchers.arxiv",
        "paper_digest.fetchers.nature",
        "paper_digest.fetchers.aps_prl_rss",
        "paper_digest.fetchers.nature_journal_rss",
        "paper_digest.fetchers.rss_feeds",
    ]


    imported_modules = [importlib.import_module(name) for name in module_names]
    assert all(module is not None for module in imported_modules)


def test_fetch_to_review_workflow_never_sends_email(tmp_path, monkeypatch):
    """Use real parsers and storage; reject any attempt to connect to SMTP."""
    from unittest.mock import Mock

    import requests

    from paper_digest import runner
    from paper_digest.config import Config
    from paper_digest.storage import PaperStorage

    state_file = tmp_path / "state.json"
    monkeypatch.setattr(runner, "STATE_FILE", state_file)
    config = Config("https://arxiv.org/list/test/new",
                    "https://www.nature.com/ncomms.rss", "Test", ["mram"],
                    aps_prl_section_filter="")
    arxiv = '''<html><dl><dt><a href="/abs/2401.00001">Paper</a></dt>
    <dd><div class="list-title">Title: MRAM</div></dd></dl></html>'''
    rss = '''<rss version="2.0"><channel><title>Feed</title><item>
    <title>MRAM journal paper</title><link>https://doi.org/10.1234/ABC</link>
    </item></channel></rss>'''

    def get(url, **kwargs):
        return Mock(text=arxiv if "arxiv.org" in url else rss)

    monkeypatch.setattr(requests, "get", get)
    smtp_cls = Mock(side_effect=AssertionError("Email delivery was removed"))
    monkeypatch.setattr("smtplib.SMTP", smtp_cls)
    assert runner.run_digest(config) == 0
    storage = PaperStorage(state_file)
    assert len(storage.state["papers"]) == 2
    assert len(storage.state["sources"]) == 4
    item_id = next(iter(storage.state["papers"]))
    assert runner.main(["decide", item_id, "accept"]) == 0
    assert runner.run_digest(config) == 0
    smtp_cls.assert_not_called()
    assert PaperStorage(state_file).state["papers"][item_id]["decision"] == "accepted"
