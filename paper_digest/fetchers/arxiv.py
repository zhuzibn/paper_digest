# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownParameterType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import logging

import requests
from bs4 import BeautifulSoup

from paper_digest.config import Config
from paper_digest.fetchers.common import match_keywords, normalize_date
from paper_digest.models import Paper

logger = logging.getLogger(__name__)


class ArxivFetcher:
    def __init__(self, config: Config):
        self.config: Config = config

    def fetch(self) -> list[Paper]:
        try:
            response = requests.get(
                self.config.arxiv_url,
                headers={"User-Agent": self.config.user_agent},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("Failed to fetch arXiv page")
            return []

        return self._parse_html(response.text)

    def _parse_html(self, html_content: str) -> list[Paper]:
        soup = BeautifulSoup(html_content, "lxml")
        papers: list[Paper] = []

        dts = soup.select("dl dt")
        dds = soup.select("dl dd")

        for dt, dd in zip(dts, dds):
            link_elem = dt.select_one("a[href*='/abs/']")
            if link_elem is None:
                continue

            href_obj: object = link_elem.get("href", "")
            if not isinstance(href_obj, str) or not href_obj:
                continue

            href = href_obj
            link = href if href.startswith("http") else f"https://arxiv.org{href}"

            title_elem = dd.select_one(".list-title")
            title = ""
            if title_elem is not None:
                title = (
                    title_elem.get_text(" ", strip=True).replace("Title:", "").strip()
                )

            abstract = ""
            abstract_elem = dd.select_one(".list-abstract") or dd.select_one(
                "p.mathjax"
            )
            if abstract_elem is not None:
                abstract = (
                    abstract_elem.get_text(" ", strip=True)
                    .replace("Abstract:", "")
                    .strip()
                )

            authors = [a.get_text(strip=True) for a in dd.select(".list-authors a")]

            date_text = ""
            date_elem = dd.select_one(".list-date") or dd.select_one(".dateline")
            if date_elem is not None:
                date_text = self._parse_date(date_elem.get_text(" ", strip=True))

            matched = self._match_keywords(title, self.config.keywords, abstract)
            if not matched:
                continue

            papers.append(
                Paper(
                    title=title,
                    authors=authors,
                    link=link,
                    published_date=date_text,
                    source="arxiv",
                    keywords_matched=matched,
                )
            )

        return papers

    def _match_keywords(
        self, title: str, keywords: list[str], abstract: str = ""
    ) -> list[str]:
        return match_keywords(f"{title} {abstract}", keywords)

    def _parse_date(self, date_input: str) -> str:
        return normalize_date(date_input)
