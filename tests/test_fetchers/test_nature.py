# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportPrivateUsage=false

from unittest.mock import Mock, patch

from paper_digest.config import Config
from paper_digest.fetchers.nature import NatureFetcher


def _config() -> Config:
    return Config(
        smtp_host="",
        smtp_port=587,
        smtp_user="",
        smtp_password="",
        email_from="",
        email_to="",
        arxiv_url="https://arxiv.org/list/cond-mat/new",
        nature_url="https://www.nature.com/subjects/physical-sciences/ncomms",
        user_agent="PaperDigestTest/1.0",
        keywords=["spintronics", "spin-orbit torque", "antiferromagnet", "mram"],
    )


def test_match_keywords_uses_title_and_summary() -> None:
    fetcher = NatureFetcher(_config())

    matched = fetcher._match_keywords(
        title="Novel Device Architecture",
        keywords=["spin-orbit torque", "antiferromagnet", "mram"],
        summary="We demonstrate spin-orbit torque switching in antiferromagnet-based MRAM cells.",
    )

    assert matched == ["spin-orbit torque", "antiferromagnet", "mram"]


def test_parse_date_handles_common_inputs() -> None:
    fetcher = NatureFetcher(_config())

    assert fetcher._parse_date("15 January 2024") == "2024-01-15"
    assert fetcher._parse_date("2024-01-15T12:00:00Z") == "2024-01-15"
    assert fetcher._parse_date("2024-01-15") == "2024-01-15"


@patch("paper_digest.fetchers.nature.fetch_feed_entries")
def test_fetch_rss_returns_only_keyword_matches(
    mock_fetch_feed_entries: Mock,
) -> None:
    mock_fetch_feed_entries.return_value = [
        {
            "title": "Spin-orbit torque in antiferromagnetic devices",
            "link": "https://www.nature.com/articles/s41586-024-12345",
            "published": "2024-01-15",
            "authors": ["Alice", "Bob"],
            "summary": "<p>A route to MRAM-compatible switching.</p>",
            "categories": ["physics"],
            "raw": {},
        },
        {
            "title": "Thermal transport in thin films",
            "link": "https://www.nature.com/articles/s41586-024-54321",
            "published": "2024-01-16",
            "authors": ["Carol"],
            "summary": "No matching terms here.",
            "categories": ["materials"],
            "raw": {},
        },
    ]

    config = _config()
    config.nature_url = "https://www.nature.com/ncomms.rss"
    fetcher = NatureFetcher(config)

    papers = fetcher.fetch()

    mock_fetch_feed_entries.assert_called_once_with(
        config.nature_url,
        config.user_agent,
        max_entries=config.rss_max_entries,
    )
    assert len(papers) == 1
    assert papers[0].title == "Spin-orbit torque in antiferromagnetic devices"
    assert papers[0].authors == ["Alice", "Bob"]
    assert papers[0].link == "https://www.nature.com/articles/s41586-024-12345"
    assert papers[0].published_date == "2024-01-15"
    assert papers[0].source == "nature"
    assert papers[0].keywords_matched == [
        "spin-orbit torque",
        "antiferromagnet",
        "mram",
    ]


@patch("paper_digest.fetchers.nature.requests.get")
@patch("paper_digest.fetchers.nature.fetch_feed_entries")
def test_fetch_returns_empty_for_non_rss_url(
    mock_fetch_feed_entries: Mock,
    mock_get: Mock,
) -> None:
    config = _config()
    config.nature_url = "https://www.nature.com/subjects/physical-sciences/ncomms"
    fetcher = NatureFetcher(config)

    papers = fetcher.fetch()

    mock_fetch_feed_entries.assert_not_called()
    mock_get.assert_not_called()
    assert papers == []
