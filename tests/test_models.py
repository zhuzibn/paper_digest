# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from paper_digest.models import Paper


def test_paper_creation_fields():
    paper = Paper(
        title="Novel Spin-Orbit Torque Effects",
        authors=["John Doe", "Jane Smith"],
        link="https://arxiv.org/abs/2401.00001",
        published_date="2024-01-15",
        source="arxiv",
        keywords_matched=["spin-orbit torque"],
    )

    assert paper.title == "Novel Spin-Orbit Torque Effects"
    assert paper.authors == ["John Doe", "Jane Smith"]
    assert paper.source == "arxiv"


def test_paper_equality_uses_normalized_link():
    p1 = Paper(
        title="Title A",
        authors=[],
        link="https://arxiv.org/abs/2401.00001",
        published_date="2024-01-15",
        source="arxiv",
        keywords_matched=[],
    )
    p2 = Paper(
        title="Title B",
        authors=["Someone"],
        link="  https://arxiv.org/abs/2401.00001  ",
        published_date="2024-01-16",
        source="nature",
        keywords_matched=["mram"],
    )

    assert p1 == p2


def test_paper_hash_uses_normalized_link():
    paper = Paper(
        title="Test",
        authors=[],
        link="  https://arxiv.org/abs/2401.00001  ",
        published_date="2024-01-15",
        source="arxiv",
        keywords_matched=[],
    )

    assert hash(paper) == hash("https://arxiv.org/abs/2401.00001")


def test_to_dict_from_dict_round_trip():
    original = Paper(
        title="Spintronic Memory",
        authors=["A", "B"],
        link="https://www.nature.com/articles/example",
        published_date="2024-02-01",
        source="nature",
        keywords_matched=["spintronics", "mram"],
    )

    serialized = original.to_dict()
    restored = Paper.from_dict(serialized)

    assert restored == original
    assert restored.to_dict() == serialized
