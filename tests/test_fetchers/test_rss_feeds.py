# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false

from unittest.mock import Mock, patch

from paper_digest.config import Config
from paper_digest.fetchers.rss_feeds import RssFeedsFetcher


def _config() -> Config:
    return Config(
        smtp_host="",
        smtp_port=587,
        smtp_user="",
        smtp_password="",
        email_from="",
        email_to="",
        arxiv_url="https://arxiv.org/list/cond-mat/new",
        nature_url="https://www.nature.com/ncomms.rss",
        user_agent="PaperDigestTest/1.0",
        keywords=["spintronics", "spin-orbit torque", "mram"],
        aps_prl_rss_url="https://feeds.aps.org/rss/recent/prl.xml",
        aps_prl_section_filter="Condensed Matter and Materials",
        nature_journal_rss_url="https://www.nature.com/nature/current_issue/rss",
        nature_journal_category_allowlist=[],
        rss_max_entries=50,
        rss_feeds=[],
    )


@patch("paper_digest.fetchers.rss_feeds.fetch_feed_entries")
def test_fetch_returns_empty_list_when_no_rss_feeds_configured(
    mock_fetch: Mock,
) -> None:
    config = _config()
    config.rss_feeds = []  # Empty list

    papers = RssFeedsFetcher(config).fetch()

    # Verify fetch_feed_entries was not called since there are no feeds
    mock_fetch.assert_not_called()
    assert papers == []


@patch("paper_digest.fetchers.rss_feeds.fetch_feed_entries")
def test_fetch_processes_keyword_filtering_and_sets_source_correctly(mock_fetch: Mock) -> None:
    # Mock data for the feeds

    mock_feed_1_data = [
        {
            "title": "Spin-orbit torque switching in MRAM devices",
            "link": "https://example.com/paper1",
            "published": "2024-01-15",
            "authors": ["Alice", "Bob"],
            "summary": "We demonstrate spin-orbit torque switching suitable for MRAM applications.",
            "categories": ["Research"],
            "raw": {},
        }
    ]

    mock_feed_2_data = [
        {
            "title": "Advanced materials for spintronics",
            "link": "https://example.com/paper2",
            "published": "2024-01-16",
            "authors": ["Carol"],
            "summary": "Materials for spintronics applications.",
            "categories": ["Review"],
            "raw": {},
        },
        {
            "title": "Non-related paper",
            "link": "https://example.com/paper3",
            "published": "2024-01-17",
            "authors": ["Dave"],
            "summary": "This paper doesn't match keywords.",
            "categories": ["News"],
            "raw": {},
        }
    ]

    # Set up mock to return different data depending on the feed
    def side_effect(url, user_agent, max_entries=200):
        if "feed1" in url:
            return mock_feed_1_data
        else:
            return mock_feed_2_data

    mock_fetch.side_effect = side_effect

    config = _config()
    config.rss_feeds = [
        ("feed-id-1", "https://example.com/feed1"),
        ("feed-id-2", "https://example.com/feed2"),
    ]

    papers = RssFeedsFetcher(config).fetch()

    # Verify fetch_feed_entries was called for each feed
    assert mock_fetch.call_count == 2
    mock_fetch.assert_any_call(
        "https://example.com/feed1",
        config.user_agent,
        max_entries=config.rss_max_entries,
    )
    mock_fetch.assert_any_call(
        "https://example.com/feed2",
        config.user_agent,
        max_entries=config.rss_max_entries,
    )

    # Should have 2 papers matching different keywords
    # 1 from feed 1 (matches "mram" and "spin-orbit torque")
    # 1 from feed 2 (matches "spintronics")
    assert len(papers) == 2
    # Check first paper from feed-id-1
    assert papers[0].title == "Spin-orbit torque switching in MRAM devices"
    assert papers[0].source == "feed-id-1"
    assert set(papers[0].keywords_matched) == {"spin-orbit torque", "mram"}

    # Check second paper from feed-id-2
    assert papers[1].title == "Advanced materials for spintronics"
    assert papers[1].source == "feed-id-2"
    assert papers[1].keywords_matched == ["spintronics"]
@patch("paper_digest.fetchers.rss_feeds.fetch_feed_entries")
def test_fetch_continues_processing_other_feeds_on_request_exception(
    mock_fetch: Mock
) -> None:
    # Simulate first feed raising RequestException and second feed succeeding
    
    # Make the first call raise RequestException, second call succeeds
    def raise_exception(url, user_agent, max_entries=200):
        if "feed1" in url:
            from requests import RequestException
            raise RequestException("Network error")
        else:
            return [
                {
                    "title": "Valid paper from second feed",
                    "link": "https://example.com/paper2",
                    "published": "2024-01-16",
                    "authors": ["Carol"],
                    "summary": "This is about spintronics.",
                    "categories": ["Research"],
                    "raw": {},
                }
            ]
    
    mock_fetch.side_effect = raise_exception
    
    config = _config()
    config.rss_feeds = [
        ("feed-1", "https://example.com/feed1"),
        ("feed-2", "https://example.com/feed2"),
    ]
    
    papers = RssFeedsFetcher(config).fetch()
    
    # Both feeds should have been attempted to process
    assert mock_fetch.call_count == 2
    
    # Only results from the successful feed should be returned
    assert len(papers) == 1
    assert papers[0].title == "Valid paper from second feed"
    assert papers[0].source == "feed-2"
    assert papers[0].keywords_matched == ["spintronics"]
