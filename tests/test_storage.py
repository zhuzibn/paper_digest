# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false

import json
import logging

from paper_digest.models import Paper
from paper_digest.storage import PaperStorage


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
    assert data == {"seen_links": []}


def test_is_seen_false_for_new_paper(tmp_path):
    storage = PaperStorage(tmp_path / "seen.json")
    paper = make_paper("https://arxiv.org/abs/2401.00001")

    assert not storage.is_seen(paper)


def test_mark_seen_marks_link_as_seen(tmp_path):
    storage = PaperStorage(tmp_path / "seen.json")
    paper = make_paper("https://arxiv.org/abs/2401.00001")

    storage.mark_seen(paper)

    assert storage.is_seen(paper)


def test_mark_seen_persists_for_new_storage_instance(tmp_path):
    state_file = tmp_path / "seen.json"
    paper = make_paper("https://arxiv.org/abs/2401.00001")

    storage = PaperStorage(state_file)
    storage.mark_seen(paper)

    storage_reloaded = PaperStorage(state_file)
    assert storage_reloaded.is_seen(paper)


def test_corrupted_state_file_warns_and_starts_fresh(tmp_path, caplog):
    state_file = tmp_path / "seen.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text("{this is not valid json", encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        storage = PaperStorage(state_file)

    assert not storage.is_seen(make_paper("https://arxiv.org/abs/2401.00001"))
    assert "starting fresh" in caplog.text.lower()
