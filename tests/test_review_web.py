"""Exercise the browser API against disposable ledgers, never live selections."""

import json
import threading
from collections.abc import Iterator
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import Mock

import pytest

from paper_digest import runner
from paper_digest.models import Paper
from paper_digest.review_web import ReviewServer
from paper_digest.storage import PaperStorage


@pytest.fixture
def review_server(tmp_path: Path) -> Iterator[ReviewServer]:
    """Serve three pending papers and one previously accepted paper locally."""
    path = tmp_path / "seen.json"
    storage = PaperStorage(path)
    for index in range(4):
        item_id = storage.discover(Paper(
            f"Paper {index} <script>alert(1)</script>", ["A. Author"],
            f"https://example.com/{index}", "", "arxiv", ["antiferromagnet"],
        ), "now")
        assert item_id is not None
        if index == 3:
            storage.decide(item_id, "accepted")
    storage.save()
    with ReviewServer(path) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server
        finally:
            server.shutdown()
            thread.join(timeout=5)


def _request(
    server: ReviewServer, method: str = "GET", path: str = "/api/papers",
    payload: object = None, headers: dict[str, str] | None = None,
) -> tuple[int, bytes]:
    """Send a real local HTTP request with overridable browser headers."""
    connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    request_headers = {
        "X-Review-Token": server.token, "Content-Type": "application/json",
        "Origin": server.origin,
    }
    request_headers.update(headers or {})
    body = json.dumps(payload).encode() if payload is not None else None
    try:
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def _save(server: ReviewServer, choices: list[dict[str, str]]) -> tuple[int, dict]:
    """Submit a batch and decode the server's acknowledgement."""
    status, body = _request(server, "POST", "/api/decisions", {"decisions": choices})
    return status, json.loads(body)


def test_open_window_is_read_only_and_serves_all_pending(review_server: ReviewServer) -> None:
    """Listing and page assets preserve history and release the lock promptly."""
    original = review_server.state_file.read_bytes()
    status, body = _request(review_server)
    assert status == 200
    papers = json.loads(body)["papers"]
    assert [paper["id"] for paper in papers] == review_server.paper_ids
    assert len(papers) == 3
    assert papers[0]["published_date"] == ""
    assert "<script>" in papers[0]["title"]
    assert papers[0]["keywords_matched"] == ["antiferromagnet"]
    for route in ("/", "/review.css", "/review.js"):
        assert _request(review_server, path=route)[0] == 200
    assert _request(review_server, path="/../state/seen.json")[0] == 404
    assert review_server.state_file.read_bytes() == original
    assert not review_server.state_file.with_suffix(".json.lock").exists()


def test_batch_saves_exact_ids_leaves_others_pending_and_retries_safely(review_server: ReviewServer) -> None:
    """Save and retry decisions without changing unmentioned papers or history."""
    first, second, third = review_server.paper_ids
    choices = [{"id": first, "decision": "accepted"}, {"id": second, "decision": "skipped"}]
    status, result = _save(review_server, choices)
    assert status == 200 and result["saved"] == choices
    original = review_server.state_file.read_bytes()
    assert _save(review_server, choices)[0] == 200
    assert review_server.state_file.read_bytes() == original
    records = PaperStorage(review_server.state_file).state["papers"]
    assert records[first]["decision"] == "accepted"
    assert records[second]["decision"] == "skipped"
    assert records[third]["decision"] == "pending"
    assert len(records[first]["decisions"]) == len(records[second]["decisions"]) == 1
    assert records[third]["decisions"] == []


@pytest.mark.parametrize("bad_choice", [
    {"id": "unknown", "decision": "accepted"},
    {"id": "first", "decision": "pending"},
    {"id": ["invalid"], "decision": "skipped"},
    {"id": "first", "decision": ["accepted"]},
])
def test_invalid_batch_does_not_partially_save(review_server: ReviewServer, bad_choice: dict) -> None:
    """A valid first choice is not saved if a later choice is invalid."""
    first = review_server.paper_ids[0]
    invalid = dict(bad_choice)
    if invalid["id"] == "first":
        invalid["id"] = first
    original = review_server.state_file.read_bytes()
    status, result = _save(review_server, [{"id": first, "decision": "accepted"}, invalid])
    assert status == 400 and result["saved"] == []
    assert review_server.state_file.read_bytes() == original


def test_duplicate_and_out_of_session_choices_are_rejected(review_server: ReviewServer) -> None:
    """A pending-only session cannot mutate an unrelated prior decision."""
    first = review_server.paper_ids[0]
    choice = {"id": first, "decision": "accepted"}
    assert _save(review_server, [choice, choice])[0] == 400
    storage = PaperStorage(review_server.state_file)
    previous = next(item_id for item_id in storage.state["papers"] if item_id not in review_server.paper_ids)
    assert _save(review_server, [{"id": previous, "decision": "skipped"}])[0] == 400


@pytest.mark.parametrize("headers", [
    {"X-Review-Token": ""}, {"X-Review-Token": "wrong"},
    {"X-Review-Token": "é"}, {"Origin": "https://foreign.example"},
    {"Host": "foreign.example"},
])
def test_foreign_requests_cannot_read_or_write(review_server: ReviewServer, headers: dict[str, str]) -> None:
    """A local listener is not enough: require its host, origin and session token."""
    original = review_server.state_file.read_bytes()
    assert _request(review_server, headers=headers)[0] == 403
    payload = {"decisions": [{"id": review_server.paper_ids[0], "decision": "accepted"}]}
    assert _request(review_server, "POST", "/api/decisions", payload, headers)[0] == 403
    assert review_server.state_file.read_bytes() == original


def test_stale_tab_cannot_overwrite_a_different_decision(review_server: ReviewServer) -> None:
    """Preflight the whole batch against current state before saving anything."""
    first, second, _ = review_server.paper_ids
    PaperStorage(review_server.state_file).decide(second, "skipped")
    original = review_server.state_file.read_bytes()
    status, result = _save(review_server, [
        {"id": first, "decision": "accepted"}, {"id": second, "decision": "accepted"},
    ])
    assert status == 409 and result["saved"] == []
    assert review_server.state_file.read_bytes() == original


def test_lock_and_corrupt_state_are_preserved(review_server: ReviewServer) -> None:
    """Report failures without breaking locks or resetting malformed history."""
    lock = review_server.state_file.with_suffix(".json.lock")
    lock.write_text("another process")
    original = review_server.state_file.read_bytes()
    assert _save(review_server, [{"id": review_server.paper_ids[0], "decision": "accepted"}])[0] == 409
    assert lock.read_text() == "another process"
    assert review_server.state_file.read_bytes() == original
    lock.unlink()
    review_server.state_file.write_text("broken JSON")
    assert _request(review_server)[0] == 409
    assert _save(review_server, [{"id": review_server.paper_ids[0], "decision": "accepted"}])[0] == 409
    assert review_server.state_file.read_text() == "broken JSON"


def test_write_failure_reports_only_completed_decisions(
    review_server: ReviewServer, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failure after one atomic write must report the saved prefix accurately."""
    first, second, _ = review_server.paper_ids
    original_decide = PaperStorage.decide

    def fail_second(storage: PaperStorage, item_id: str, decision: str) -> None:
        """Simulate a disk failure on the second selected paper."""
        if item_id == second:
            raise OSError("Disk full")
        original_decide(storage, item_id, decision)

    monkeypatch.setattr(PaperStorage, "decide", fail_second)
    choices = [{"id": first, "decision": "accepted"}, {"id": second, "decision": "skipped"}]
    status, result = _save(review_server, choices)
    assert status == 409 and result["saved"] == choices[:1]
    records = PaperStorage(review_server.state_file).state["papers"]
    assert records[first]["decision"] == "accepted"
    assert records[second]["decision"] == "pending"


def test_missing_state_stays_missing(tmp_path: Path) -> None:
    """Opening an empty workspace never creates a tracking ledger."""
    path = tmp_path / "absent" / "seen.json"
    with ReviewServer(path) as server:
        assert server.paper_ids == []
    assert not path.parent.exists()


def test_cli_web_does_not_fetch_or_hold_state_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dispatch the web command before entering the CLI's long-lived lock."""
    state_file = tmp_path / "seen.json"
    monkeypatch.setattr(runner, "STATE_FILE", state_file)
    digest = Mock(side_effect=AssertionError("Must not fetch"))
    serve = Mock(return_value=0)
    monkeypatch.setattr(runner, "run_digest", digest)
    monkeypatch.setattr(runner, "serve_review", serve)
    assert runner.main(["review", "--web", "--no-browser"]) == 0
    serve.assert_called_once_with(state_file, open_browser=False)
    digest.assert_not_called()
    assert not state_file.exists()
