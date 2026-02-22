# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import logging
import re

import requests

from paper_digest.config import Config
from paper_digest.fetchers.common import match_keywords
from paper_digest.fetchers.rss import fetch_feed_entries
from paper_digest.models import Paper

logger = logging.getLogger(__name__)


class NatureJournalRssFetcher:
    def __init__(self, config: Config):
        self.config: Config = config

    def fetch(self) -> list[Paper]:
        try:
            entries = fetch_feed_entries(
                self.config.nature_journal_rss_url,
                self.config.user_agent,
                max_entries=self.config.rss_max_entries,
            )
        except requests.RequestException:
            logger.exception("Failed to fetch Nature journal RSS feed")
            return []

        papers: list[Paper] = []
        for entry in entries:
            title = str(entry.get("title", "")).strip()
            link = str(entry.get("link", "")).strip()
            if not title or not link:
                continue

            if not self._matches_category_allowlist(entry):
                continue

            summary = str(entry.get("summary", "")).strip()
            keywords_matched = match_keywords(
                f"{title} {summary}", self.config.keywords
            )
            if not keywords_matched:
                continue

            authors = entry.get("authors")
            author_list = authors if isinstance(authors, list) else []
            if not author_list:
                author_list = self._fallback_authors(entry.get("raw"))

            papers.append(
                Paper(
                    title=title,
                    authors=author_list,
                    link=link,
                    published_date=str(entry.get("published", "")).strip(),
                    source="nature-journal",
                    keywords_matched=keywords_matched,
                )
            )

        return papers

    def _matches_category_allowlist(self, entry: dict[str, object]) -> bool:
        if not self.config.nature_journal_category_allowlist:
            return True

        allowlist = {
            category.strip().lower()
            for category in self.config.nature_journal_category_allowlist
            if category.strip()
        }
        if not allowlist:
            return True

        categories = entry.get("categories")
        if not isinstance(categories, list):
            return False

        normalized_categories = {
            str(category).strip().lower() for category in categories
        }
        return any(category in allowlist for category in normalized_categories)

    def _fallback_authors(self, raw: object) -> list[str]:
        for key in ("dc_creator", "dc:creator", "author"):
            raw_value = self._raw_get(raw, key)
            if raw_value is None:
                continue
            pieces = re.split(r"\s+and\s+|,", str(raw_value))
            authors = [piece.strip() for piece in pieces if piece.strip()]
            if authors:
                return authors
        return []

    def _raw_get(self, raw: object, key: str) -> object:
        if raw is None:
            return None
        get_method = getattr(raw, "get", None)
        if not callable(get_method):
            return None
        value = get_method(key)
        return value if value not in (None, "") else None
