from paper_digest.fetchers.common import (
    canonicalize_link,
    match_keywords,
    normalize_date,
)


def test_match_keywords_preserves_keyword_order_case_insensitive_and_dedupes() -> None:
    matched = match_keywords(
        text="Spin-Orbit torque switching in MRAM materials",
        keywords=["mram", "SPIN-ORBIT TORQUE", "mram", "spintronics"],
    )

    assert matched == ["mram", "SPIN-ORBIT TORQUE"]


def test_normalize_date_uses_dateutil_when_possible() -> None:
    assert normalize_date("15 Jan 2024") == "2024-01-15"


def test_normalize_date_falls_back_to_regex_and_raw_input() -> None:
    assert normalize_date("released around 2024-03-11 maybe") == "2024-03-11"
    assert normalize_date("not-a-date") == "not-a-date"
    assert normalize_date("") == ""


def test_canonicalize_link_removes_fragment() -> None:
    assert (
        canonicalize_link("https://example.com/paper?id=123#section")
        == "https://example.com/paper?id=123"
    )


def test_canonicalize_link_removes_only_utm_query_params() -> None:
    assert (
        canonicalize_link(
            "  https://example.com/paper?utm_source=x&id=1&utm_medium=email&ref=abc  "
        )
        == "https://example.com/paper?id=1&ref=abc"
    )
