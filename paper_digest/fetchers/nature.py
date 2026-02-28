# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownParameterType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import logging

import requests
from bs4 import BeautifulSoup

from paper_digest.config import Config
from paper_digest.fetchers.common import match_keywords, normalize_date
from paper_digest.fetchers.rss import fetch_feed_entries
from paper_digest.models import Paper

logger = logging.getLogger(__name__)


class NatureFetcher:
    def __init__(self, config: Config):
        self.config: Config = config

    def fetch(self) -> list[Paper]:
        if (
            not self.config.nature_url.endswith(".rss")
            and "feeds.nature.com" not in self.config.nature_url
        ):
            logger.error(
                "Nature URL must point to an RSS feed: %s", self.config.nature_url
            )
            return []

        try:
            entries = fetch_feed_entries(
                self.config.nature_url,
                self.config.user_agent,
                max_entries=self.config.rss_max_entries,
            )
        except requests.RequestException:
            logger.exception("Failed to fetch Nature RSS feed")
            return []

        papers: list[Paper] = []

        for entry in entries:
            title = entry["title"]
            link = entry["link"]
            summary = entry["summary"]
            published_date = entry["published"]
            authors = entry["authors"]

            plain_summary = BeautifulSoup(summary, "lxml").get_text(" ", strip=True)
            matched = self._match_keywords(title, self.config.keywords, plain_summary)
            if not matched:
                continue

            papers.append(
                Paper(
                    title=title,
                    authors=authors,
                    link=link,
                    published_date=published_date,
                    source="nature",
                    keywords_matched=matched,
                )
            )

        return papers

    def _match_keywords(
        self, title: str, keywords: list[str], summary: str = ""
    ) -> list[str]:
        return match_keywords(f"{title} {summary}", keywords)

    def _parse_date(self, date_input: str) -> str:
        return normalize_date(date_input)
