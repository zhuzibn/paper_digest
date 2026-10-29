"""Review and selection commands operate entirely on local metadata."""

from unittest.mock import Mock

from paper_digest import runner
from paper_digest.models import Paper
from paper_digest.storage import PaperStorage


def test_review_decide_and_status_use_local_metadata(tmp_path, monkeypatch, capsys):
    state_file = tmp_path / "seen.json"
    monkeypatch.setattr(runner, "STATE_FILE", state_file)
    digest = Mock(side_effect=AssertionError("Review must stay offline"))
    monkeypatch.setattr(runner, "run_digest", digest)
    storage = PaperStorage(state_file)
    first = storage.discover(Paper("First", [], "https://example.com/a", "", "test"), "now")
    second = storage.discover(Paper("Second", [], "https://example.com/b", "", "test"), "now")
    storage.save()
    assert runner.main(["review"]) == 0
    output = capsys.readouterr().out
    assert first in output and second in output
    assert "date unknown" in output
    assert runner.main(["decide", first, "accept"]) == 0
    capsys.readouterr()
    assert runner.main(["review"]) == 0
    output = capsys.readouterr().out
    assert first not in output and second in output
    assert runner.main(["decide", second, "skip"]) == 0
    assert runner.main(["review", "--status", "all"]) == 0
    assert runner.main(["status"]) == 0
    output = capsys.readouterr().out
    assert "Tracked papers: 2" in output
    assert "email" not in output.lower()
    assert "pending: 0" in output
    assert "accepted: 1" in output and "skipped: 1" in output
    digest.assert_not_called()


def test_unknown_id_does_not_change_state(tmp_path, monkeypatch):
    state_file = tmp_path / "seen.json"
    PaperStorage(state_file)
    original = state_file.read_bytes()
    monkeypatch.setattr(runner, "STATE_FILE", state_file)
    assert runner.main(["decide", "unknown", "accept"]) == 1
    assert state_file.read_bytes() == original
