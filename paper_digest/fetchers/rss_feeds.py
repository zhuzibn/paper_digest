# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false
import logging

import requests

from paper_digest.config import Config
from paper_digest.fetchers.common import match_keywords
from paper_digest.fetchers.rss import fetch_feed_entries
from paper_digest.models import Paper

logger = logging.getLogger(__name__)


class RssFeedsFetcher:
    def __init__(self, config: Config):
        self.config: Config = config

    def fetch(self) -> list[Paper]:
        if not self.config.rss_feeds:
            return []

        papers: list[Paper] = []
        for feed_id, url in self.config.rss_feeds:
            try:
                entries = fetch_feed_entries(
                    url,
                    self.config.user_agent,
                    max_entries=self.config.rss_max_entries,
                )
            except requests.RequestException:
                logger.exception(f"Failed to fetch RSS feed: {url}")
                continue

            for entry in entries:
                title = str(entry.get("title", "")).strip()
                link = str(entry.get("link", "")).strip()
                if not title or not link:
                    continue

                summary = str(entry.get("summary", "")).strip()
                keywords_matched = match_keywords(
                    f"{title} {summary}", self.config.keywords
                )
                if not keywords_matched:
                    continue

                author_list = entry.get("authors", [])

                papers.append(
                    Paper(
                        title=title,
                        authors=author_list,
                        link=link,
                        published_date=str(entry.get("published", "")).strip(),
                        source=feed_id,
                        keywords_matched=keywords_matched,
                    )
                )

        return papers
