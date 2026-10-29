"""Exercise fetch outcomes with real persisted state and mocked sources."""

from unittest.mock import Mock

import pytest

from paper_digest import runner
from paper_digest.config import Config
from paper_digest.models import FetchResult
from paper_digest.models import Paper
from paper_digest.storage import PaperStorage


def _config() -> Config:
    return Config(
        arxiv_url="https://arxiv.org/list/cond-mat/new",
        nature_url="https://www.nature.com/ncomms.rss", user_agent="Test/1.0",
        keywords=["mram"],
    )


def _paper(link: str = "https://arxiv.org/abs/2401.00001v1", source: str = "arxiv") -> Paper:
    return Paper("MRAM", ["A"], link, "2024-01-15", source, ["mram"])


@pytest.fixture
def workflow(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(runner, "STATE_FILE", state_file)
    fetches = []
    for cls in (runner.ArxivFetcher, runner.NatureFetcher, runner.ApsPrlRssFetcher,
                runner.NatureJournalRssFetcher):
        fetch = Mock(return_value=FetchResult())
        monkeypatch.setattr(cls, "fetch", fetch)
        fetches.append(fetch)
    return state_file, fetches


def test_discovery_stays_pending_and_survives_leaving_feed(workflow):
    state_file, fetches = workflow
    fetches[0].return_value = FetchResult([_paper()])
    assert runner.run_digest(_config()) == 0
    records = PaperStorage(state_file).state["papers"]
    assert len(records) == 1
    assert next(iter(records.values()))["decision"] == "pending"

    fetches[0].return_value = FetchResult()
    assert runner.run_digest(_config()) == 0
    assert PaperStorage(state_file).state["papers"] == records


def test_duplicate_doi_and_arxiv_versions_are_stored_only_once(workflow):
    state_file, fetches = workflow
    fetches[0].return_value = FetchResult([
        _paper(), _paper("http://export.arxiv.org/pdf/2401.00001v2.pdf"),
    ])
    fetches[1].return_value = FetchResult([
        _paper("https://doi.org/10.1103/PhysRevLett.1", "nature"),
    ])
    fetches[2].return_value = FetchResult([
        _paper("https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.1", "aps-prl"),
    ])
    assert runner.run_digest(_config()) == 0
    assert len(PaperStorage(state_file).state["papers"]) == 2
    assert runner.run_digest(_config()) == 0
    assert len(PaperStorage(state_file).state["papers"]) == 2


def test_partial_and_failed_sources_preserve_last_success_and_save_candidates(workflow):
    state_file, fetches = workflow
    assert runner.run_digest(_config()) == 0
    old = PaperStorage(state_file).state["sources"]
    fetches[0].side_effect = OSError("offline")
    fetches[1].return_value = FetchResult([_paper(source="nature")], "truncated feed")
    assert runner.run_digest(_config()) == 1
    current = PaperStorage(state_file).state["sources"]
    for source in ("arxiv", "nature"):
        assert current[source]["last_success"] == old[source]["last_success"]
    assert current["arxiv"]["status"] == "failed"
    assert current["nature"]["status"] == "partial"
    assert current["aps-prl"]["status"] == "success"
    assert len(PaperStorage(state_file).state["papers"]) == 1


def test_empty_success_differs_from_failed_fetch(workflow):
    state_file, fetches = workflow
    fetches[0].side_effect = ValueError("not a feed")
    assert runner.run_digest(_config()) == 1
    sources = PaperStorage(state_file).state["sources"]
    assert sources["arxiv"]["last_success"] == ""
    assert sources["nature"]["last_success"]


def test_each_additional_feed_has_an_independent_result(workflow, monkeypatch):
    state_file, _ = workflow
    config = _config()
    config.rss_feeds = [("feed-a", "https://example.com/a"),
                        ("feed-b", "https://example.com/b")]

    def fetch(self):
        if self.feed_id == "feed-a":
            raise OSError("offline")
        return FetchResult([_paper(source=self.feed_id)])

    monkeypatch.setattr(runner.RssFeedFetcher, "fetch", fetch)
    assert runner.run_digest(config) == 1
    sources = PaperStorage(state_file).state["sources"]
    assert sources["feed-a"]["status"] == "failed"
    assert sources["feed-b"]["status"] == "success"
    records = PaperStorage(state_file).state["papers"]
    assert next(iter(records.values()))["paper"]["source"] == "feed-b"


def test_old_and_undated_discoveries_are_not_filtered_by_last_check(workflow):
    state_file, fetches = workflow
    assert runner.run_digest(_config()) == 0
    paper = _paper()
    paper.published_date = ""
    fetches[0].return_value = FetchResult([paper, _paper("https://example.com/old")])
    assert runner.run_digest(_config()) == 0
    assert len(PaperStorage(state_file).state["papers"]) == 2


def test_save_failure_preserves_previous_state(workflow, monkeypatch):
    state_file, fetches = workflow
    assert runner.run_digest(_config()) == 0
    fetches[0].return_value = FetchResult([_paper()])
    monkeypatch.setattr(PaperStorage, "save", Mock(side_effect=OSError("disk full")))
    assert runner.run_digest(_config()) == 1
    assert PaperStorage(state_file).state["papers"] == {}


def test_corrupted_state_stops_before_fetch(workflow):
    state_file, fetches = workflow
    state_file.write_text("{broken")
    assert runner.run_digest(_config()) == 1
    for fetch in fetches:
        fetch.assert_not_called()
    assert state_file.read_text() == "{broken"
