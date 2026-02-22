# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import logging
import re

import requests

from paper_digest.config import Config
from paper_digest.fetchers.common import match_keywords, normalize_date
from paper_digest.fetchers.rss import fetch_feed_entries
from paper_digest.models import Paper

logger = logging.getLogger(__name__)


class ApsPrlRssFetcher:
    def __init__(self, config: Config):
        self.config: Config = config

    def fetch(self) -> list[Paper]:
        try:
            entries = fetch_feed_entries(
                self.config.aps_prl_rss_url,
                self.config.user_agent,
                max_entries=self.config.rss_max_entries,
            )
        except requests.RequestException:
            logger.exception("Failed to fetch APS PRL RSS feed")
            return []

        papers: list[Paper] = []
        for entry in entries:
            title = str(entry.get("title", "")).strip()
            link = str(entry.get("link", "")).strip()
            if not title or not link:
                continue

            raw = entry.get("raw")
            if not self._matches_section_filter(entry, raw):
                continue

            summary = str(entry.get("summary", "")).strip()
            keywords_matched = match_keywords(
                f"{title} {summary}", self.config.keywords
            )
            if not keywords_matched:
                continue

            published = str(entry.get("published", "")).strip()
            if not published:
                published = self._fallback_published(raw)

            authors = entry.get("authors")
            author_list = authors if isinstance(authors, list) else []
            if not author_list:
                author_list = self._fallback_authors(raw)

            papers.append(
                Paper(
                    title=title,
                    authors=author_list,
                    link=link,
                    published_date=published,
                    source="aps-prl",
                    keywords_matched=keywords_matched,
                )
            )

        return papers

    def _matches_section_filter(self, entry: object, raw: object) -> bool:
        section_filter = self.config.aps_prl_section_filter.strip().lower()
        if not section_filter:
            return True

        haystacks: list[str] = []

        categories = self._raw_get(entry, "categories")
        if isinstance(categories, list):
            haystacks.extend(str(category) for category in categories)

        for key in ("dc_subject", "prism_section", "dc:subject", "prism:section"):
            value = self._raw_get(raw, key)
            if isinstance(value, list):
                haystacks.extend(str(item) for item in value)
            elif value is not None:
                haystacks.append(str(value))

        return any(section_filter in item.lower() for item in haystacks)

    def _fallback_published(self, raw: object) -> str:
        for key in (
            "dc_date",
            "dc:date",
            "prism_publicationdate",
            "prism:publicationdate",
            "prism_publicationDate",
            "prism:publicationDate",
        ):
            raw_value = self._raw_get(raw, key)
            if raw_value is None:
                continue
            normalized = normalize_date(str(raw_value).strip())
            if normalized:
                return normalized
        return ""

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
