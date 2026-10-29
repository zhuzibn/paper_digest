"""Keyword filtering for one configured additional RSS feed."""

from paper_digest.config import Config
from paper_digest.fetchers.common import match_keywords
from paper_digest.fetchers.rss import fetch_feed_entries
from paper_digest.models import FetchResult
from paper_digest.models import Paper


class RssFeedFetcher:
    def __init__(self, config: Config, feed_id: str, url: str) -> None:
        """Keep one feed's outcome independent of other configured feeds."""
        self.config: Config = config
        self.feed_id: str = feed_id
        self.url: str = url

    def fetch(self) -> FetchResult:
        """Return matching papers and any partial-coverage error."""
        feed = fetch_feed_entries(
            self.url, self.config.user_agent,
            max_entries=self.config.rss_max_entries,
        )
        papers: list[Paper] = []
        for entry in feed.entries:
            matched = match_keywords(
                f"{entry['title']} {entry['summary']}", self.config.keywords
            )
            if matched:
                papers.append(Paper(
                    title=entry["title"], authors=entry["authors"],
                    link=entry["link"], published_date=entry["published"],
                    source=self.feed_id, keywords_matched=matched,
                    doi=entry.get("doi", ""),
                ))
        return FetchResult(papers, feed.error)
