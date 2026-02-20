# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownParameterType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import logging
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from paper_digest.config import Config
from paper_digest.models import Paper

logger = logging.getLogger(__name__)


class NatureFetcher:
    def __init__(self, config: Config):
        self.config: Config = config

    def fetch(self) -> list[Paper]:
        try:
            response = requests.get(
                self.config.nature_url,
                headers={"User-Agent": self.config.user_agent},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("Failed to fetch Nature page")
            return []

        return self._parse_html(response.text)

    def _parse_html(self, html_content: str) -> list[Paper]:
        soup = BeautifulSoup(html_content, "lxml")
        papers: list[Paper] = []

        for article in soup.select("article.c-article-item"):
            title_elem = article.select_one("h3 a") or article.select_one(
                ".c-article-item__title a"
            )
            if title_elem is None:
                continue

            title = title_elem.get_text(" ", strip=True)

            href_obj: object = title_elem.get("href", "")
            if not isinstance(href_obj, str) or not href_obj:
                continue
            link = urljoin("https://www.nature.com", href_obj)

            summary = ""
            summary_elem = article.select_one(
                ".c-article-item__summary, .c-article-item__description"
            )
            if summary_elem is not None:
                summary = summary_elem.get_text(" ", strip=True)

            authors = [
                elem.get_text(" ", strip=True)
                for elem in article.select(
                    ".c-article-item__authors li, .c-author-list li"
                )
            ]

            published_date = ""
            date_elem = article.select_one("time")
            if date_elem is not None:
                date_raw_obj: object = date_elem.get("datetime") or date_elem.get_text(
                    " ", strip=True
                )
                if isinstance(date_raw_obj, str):
                    published_date = self._parse_date(date_raw_obj)

            matched = self._match_keywords(title, self.config.keywords, summary)
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
        content = f"{title} {summary}".lower()
        return [kw for kw in keywords if kw.lower() in content]

    def _parse_date(self, date_input: str) -> str:
        if not date_input:
            return ""
        try:
            return date_parser.parse(date_input, fuzzy=True).strftime("%Y-%m-%d")
        except (TypeError, ValueError):
            match = re.search(r"\d{4}-\d{2}-\d{2}", date_input)
            return match.group(0) if match else date_input
