# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false

import json
from unittest.mock import patch

import pytest

from paper_digest.models import Paper
from paper_digest.storage import PaperStorage
from paper_digest.storage import locked_storage


def make_paper(link: str) -> Paper:
    return Paper(
        title="Test",
        authors=[],
        link=link,
        published_date="2024-01-15",
        source="arxiv",
        keywords_matched=[],
    )


def test_storage_initialization_creates_empty_state(tmp_path):
    state_file = tmp_path / "seen.json"

    _ = PaperStorage(state_file)

    assert state_file.exists()
    loaded: object = json.loads(state_file.read_text(encoding="utf-8"))  # pyright: ignore[reportAny]
    assert isinstance(loaded, dict)
    data = loaded
    assert data["seen_links"] == []
    assert data["papers"] == {}
    assert data["version"] == 3


def test_discovery_persists_without_inventing_a_decision(tmp_path):
    state_file = tmp_path / "seen.json"
    paper = make_paper("https://arxiv.org/abs/2401.00001")
    storage = PaperStorage(state_file)
    item_id = storage.discover(paper, "first")
    storage.save()

    reloaded = PaperStorage(state_file)
    assert reloaded.discover(paper, "again") == item_id
    assert len(reloaded.state["papers"]) == 1
    assert reloaded.state["papers"][item_id]["decision"] == "pending"


@pytest.mark.parametrize("raw", ["{broken", "[]", '{"seen_links": "invalid"}',
                                  '{"seen_links": [], "version": 99}'])
def test_corrupted_state_is_preserved_and_never_reset(tmp_path, raw):
    state_file = tmp_path / "seen.json"
    state_file.write_text(raw)
    with pytest.raises(ValueError):
        PaperStorage(state_file)
    assert state_file.read_text() == raw


def test_legacy_links_migrate_as_exclusions_without_invented_decisions(tmp_path):
    state_file = tmp_path / "seen.json"
    legacy = {"seen_links": ["http://arxiv.org/abs/2401.00001v1"]}
    state_file.write_text(json.dumps(legacy))
    storage = PaperStorage(state_file)
    paper = make_paper("https://arxiv.org/pdf/2401.00001v3.pdf")
    assert storage.discover(paper, "now") is None
    storage.save()
    assert storage.state["papers"] == {}
    assert PaperStorage(state_file).state["seen_links"] == legacy["seen_links"]


def test_decisions_survive_rediscovery_and_preserve_corrections(tmp_path):
    state_file = tmp_path / "seen.json"
    storage = PaperStorage(state_file)
    paper = make_paper("https://arxiv.org/abs/2401.00001v1")
    item_id = storage.discover(paper, "now")
    storage.decide(item_id, "skipped")
    storage = PaperStorage(state_file)
    later = make_paper("https://arxiv.org/abs/2401.00001v2")
    assert storage.discover(later, "later") == item_id
    assert storage.state["papers"][item_id]["decision"] == "skipped"
    storage.decide(item_id, "accepted")
    record = PaperStorage(state_file).state["papers"][item_id]
    assert record["decision"] == "accepted"
    assert [event["status"] for event in record["decisions"]] == ["skipped", "accepted"]


def test_unknown_decisions_are_rejected_and_other_papers_stay_pending(tmp_path):
    storage = PaperStorage(tmp_path / "seen.json")
    item_id = storage.discover(make_paper("https://example.com/1"), "now")
    other_id = storage.discover(make_paper("https://example.com/2"), "now")
    with pytest.raises(ValueError):
        storage.decide("unknown", "accepted")
    with pytest.raises(ValueError):
        storage.decide(item_id, "maybe")
    storage.decide(item_id, "accepted")
    assert storage.state["papers"][other_id]["decision"] == "pending"


def test_doi_enrichment_retains_original_review_id(tmp_path):
    storage = PaperStorage(tmp_path / "seen.json")
    paper = make_paper("https://example.com/article")
    original_id = storage.discover(paper, "first")
    paper.doi = "10.1234/abc"
    assert storage.discover(paper, "second") == original_id
    doi_link = make_paper("https://doi.org/10.1234/ABC")
    assert storage.discover(doi_link, "third") == original_id
    assert len(storage.state["papers"]) == 1


def test_atomic_replace_failure_preserves_previous_state(tmp_path):
    state_file = tmp_path / "seen.json"
    storage = PaperStorage(state_file)
    original = state_file.read_bytes()
    storage.discover(make_paper("https://example.com/1"), "now")
    with patch("pathlib.Path.replace", side_effect=OSError("disk failure")):
        with pytest.raises(OSError):
            storage.save()
    assert state_file.read_bytes() == original
    assert list(tmp_path.glob("*.tmp")) == []


def test_lock_excludes_concurrent_runs_and_never_removes_an_existing_lock(tmp_path):
    state_file = tmp_path / "seen.json"
    with locked_storage(state_file):
        lock = tmp_path / "seen.json.lock"
        original = lock.read_text()
        with pytest.raises(RuntimeError, match="locked"):
            with locked_storage(state_file):
                pytest.fail("Concurrent lock acquired")
        assert lock.read_text() == original
    assert not lock.exists()


def test_source_url_change_resets_previous_endpoint_success(tmp_path):
    storage = PaperStorage(tmp_path / "seen.json")
    storage.record_source("feed", "https://example.com/old", "first", "success", "", 0)
    storage.record_source("feed", "https://example.com/new", "second", "failed", "offline", 0)
    assert storage.state["sources"]["feed"]["last_success"] == ""


@pytest.mark.parametrize("decision", ["pending", "accepted", "skipped"])
@pytest.mark.parametrize("emailed_at", ["", "sent-earlier"])
def test_version_two_migration_keeps_papers_decisions_and_sources(
    tmp_path, decision, emailed_at,
):
    """Retire delivery state without losing either reviewed or unreviewed papers."""
    state_file = tmp_path / "seen.json"
    storage = PaperStorage(state_file)
    paper = make_paper("https://example.com/paper")
    item_id = storage.discover(paper, "discovered-earlier")
    if decision != "pending":
        storage.decide(item_id, decision)
    storage.record_source("arxiv", "https://arxiv.org/list/test/new", "checked", "success", "", 1)
    old = json.loads(json.dumps(storage.state))
    old["version"] = 2
    old["delivery_error"] = "previous SMTP error"
    old["papers"][item_id]["emailed_at"] = emailed_at
    state_file.write_text(json.dumps(old))
    original = state_file.read_bytes()

    migrated = PaperStorage(state_file)
    assert state_file.read_bytes() == original  # Read-only commands defer migration writes.
    assert migrated.state == storage.state
    assert migrated.discover(paper, "now") == item_id
    migrated.save()
    reloaded = PaperStorage(state_file)
    assert reloaded.state["version"] == 3
    assert "delivery_error" not in reloaded.state
    assert "emailed_at" not in reloaded.state["papers"][item_id]
    assert reloaded.state["papers"][item_id]["decision"] == decision
