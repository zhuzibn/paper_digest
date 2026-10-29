"""Additional feed filtering uses the same partial-coverage contract as built-ins."""

from unittest.mock import patch

import pytest
import requests

from paper_digest.config import Config
from paper_digest.fetchers.rss import FeedResult
from paper_digest.fetchers.rss_feeds import RssFeedFetcher


def _config() -> Config:
    return Config("", "", "Test", ["mram"])


@patch("paper_digest.fetchers.rss_feeds.fetch_feed_entries")
def test_feed_matches_keywords_preserves_doi_and_reports_partial_coverage(fetch):
    fetch.return_value = FeedResult([
        {"title": "New MRAM", "link": "https://example.com/a", "published": "",
         "authors": ["A"], "summary": "", "categories": [], "raw": {},
         "doi": "10.1234/abc"},
        {"title": "Unrelated", "link": "https://example.com/b", "published": "",
         "authors": [], "summary": "", "categories": [], "raw": {}, "doi": ""},
    ], "truncated")
    result = RssFeedFetcher(_config(), "feed-a", "https://example.com/rss").fetch()
    assert len(result.papers) == 1
    assert result.papers[0].source == "feed-a"
    assert result.papers[0].doi == "10.1234/abc"
    assert result.error == "truncated"


@patch("paper_digest.fetchers.rss_feeds.fetch_feed_entries")
def test_feed_failure_is_not_reported_as_no_matches(fetch):
    fetch.side_effect = requests.RequestException("offline")
    with pytest.raises(requests.RequestException):
        RssFeedFetcher(_config(), "feed-a", "https://example.com/rss").fetch()
