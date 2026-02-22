# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false

from unittest.mock import Mock, patch

from paper_digest.config import Config
from paper_digest.fetchers.nature_journal_rss import NatureJournalRssFetcher


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
        keywords=["spintronics", "spin-orbit torque", "mram"],
        nature_journal_rss_url="https://www.nature.com/nature/current_issue/rss",
        nature_journal_category_allowlist=[],
        rss_max_entries=50,
    )


@patch("paper_digest.fetchers.nature_journal_rss.fetch_feed_entries")
def test_fetch_matches_keywords_and_builds_nature_journal_paper(
    mock_fetch: Mock,
) -> None:
    mock_fetch.return_value = [
        {
            "title": "Materials advances for storage",
            "link": "https://www.nature.com/articles/s41586-024-12345",
            "published": "2024-01-15",
            "authors": ["Alice", "Bob"],
            "summary": "We demonstrate spin-orbit torque switching suitable for MRAM.",
            "categories": ["Research Highlights"],
            "raw": {},
        }
    ]

    config = _config()
    papers = NatureJournalRssFetcher(config).fetch()

    mock_fetch.assert_called_once_with(
        config.nature_journal_rss_url,
        config.user_agent,
        max_entries=config.rss_max_entries,
    )
    assert len(papers) == 1
    assert papers[0].title == "Materials advances for storage"
    assert papers[0].authors == ["Alice", "Bob"]
    assert papers[0].published_date == "2024-01-15"
    assert papers[0].source == "nature-journal"
    assert papers[0].keywords_matched == ["spin-orbit torque", "mram"]


@patch("paper_digest.fetchers.nature_journal_rss.fetch_feed_entries")
def test_fetch_applies_category_allowlist_when_configured(mock_fetch: Mock) -> None:
    mock_fetch.return_value = [
        {
            "title": "Spintronics roundup",
            "link": "https://www.nature.com/articles/s41586-024-20000",
            "published": "2024-01-16",
            "authors": ["Carol"],
            "summary": "A spintronics overview.",
            "categories": [" News ", "Research"],
            "raw": {},
        },
        {
            "title": "MRAM device physics",
            "link": "https://www.nature.com/articles/s41586-024-20001",
            "published": "2024-01-17",
            "authors": ["Dana"],
            "summary": "MRAM optimization details.",
            "categories": ["Comment"],
            "raw": {},
        },
    ]

    config = _config()
    config.nature_journal_category_allowlist = ["news", "research highlight"]

    papers = NatureJournalRssFetcher(config).fetch()

    assert len(papers) == 1
    assert papers[0].title == "Spintronics roundup"


@patch("paper_digest.fetchers.nature_journal_rss.fetch_feed_entries")
def test_fetch_drops_entries_missing_title_or_link_even_if_keyword_matches(
    mock_fetch: Mock,
) -> None:
    mock_fetch.return_value = [
        {
            "title": "",
            "link": "https://www.nature.com/articles/s41586-024-30000",
            "published": "",
            "authors": [],
            "summary": "spintronics",
            "categories": ["news"],
            "raw": {},
        },
        {
            "title": "Valid title",
            "link": "",
            "published": "",
            "authors": [],
            "summary": "spintronics",
            "categories": ["news"],
            "raw": {},
        },
    ]

    papers = NatureJournalRssFetcher(_config()).fetch()

    assert papers == []
