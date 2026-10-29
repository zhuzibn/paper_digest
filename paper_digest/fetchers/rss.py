# pyright: reportMissingImports=false, reportMissingTypeStubs=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from dataclasses import dataclass
from typing import TypedDict
from urllib.parse import urlsplit

import feedparser
import requests

from paper_digest.fetchers.common import canonicalize_link, normalize_date
from paper_digest.identity import normalize_doi


class NormalizedFeedEntry(TypedDict):
    title: str
    link: str
    published: str
    authors: list[str]
    summary: str
    categories: list[str]
    raw: object
    doi: str


@dataclass
class FeedResult:
    """Parsed entries plus a reason when the snapshot was only partly read."""

    entries: list[NormalizedFeedEntry]
    error: str = ""


def fetch_feed_entries(
    url: str,
    user_agent: str,
    max_entries: int = 200,
) -> FeedResult:
    """Fetch a feed, retaining valid entries and reporting incomplete parsing."""
    if max_entries < 1:
        raise ValueError("RSS_MAX_ENTRIES must be positive")
    response = requests.get(
        url,
        headers={"User-Agent": user_agent},
        timeout=30,
    )
    response.raise_for_status()
    parsed_feed = feedparser.parse(response.text)
    if not parsed_feed.version:
        raise ValueError("Response is not a recognized RSS/Atom feed")
    errors: list[str] = []
    if parsed_feed.get("bozo"):
        errors.append("Malformed feed: " + str(parsed_feed.get("bozo_exception")))

    normalized: list[NormalizedFeedEntry] = []
    for entry in parsed_feed.entries:
        title = str(entry.get("title", "")).strip()
        try:
            link = canonicalize_link(str(entry.get("link", "")))
            parts = urlsplit(link)
            if parts.scheme not in {"http", "https"} or not parts.netloc:
                link = ""
        except ValueError:
            link = ""
        if not title or not link:
            errors.append("Feed contains entries without a title or link")
            continue

        published_raw = str(
            entry.get("published") or entry.get("updated") or entry.get("pubDate") or ""
        )
        summary_raw = entry.get("summary") or entry.get("description")
        if not summary_raw:
            content_data = entry.get("content")
            if isinstance(content_data, list) and content_data:
                first_content = content_data[0]
                if hasattr(first_content, "get"):
                    summary_raw = first_content.get("value", "")
        summary = str(summary_raw or "").strip()

        authors: list[str] = []
        authors_data = entry.get("authors")
        if isinstance(authors_data, list):
            for author_obj in authors_data:
                if not hasattr(author_obj, "get"):
                    continue
                name = str(author_obj.get("name", "")).strip()
                if name:
                    authors.append(name)
        if not authors:
            fallback_author = str(entry.get("author", "")).strip()
            if fallback_author:
                authors = [fallback_author]

        categories: list[str] = []
        tags_data = entry.get("tags")
        if isinstance(tags_data, list):
            for tag_obj in tags_data:
                if not hasattr(tag_obj, "get"):
                    continue
                term = str(tag_obj.get("term", "")).strip()
                if term:
                    categories.append(term)
        if not categories:
            category = str(entry.get("category", "")).strip()
            if category:
                categories = [category]

        normalized.append(
            {
                "title": title,
                "link": link,
                "published": normalize_date(published_raw),
                "authors": authors,
                "summary": summary,
                "categories": categories,
                "raw": entry,
                "doi": next(
                    (doi for key in ("prism_doi", "dc_identifier", "id")
                     if (doi := normalize_doi(str(entry.get(key, ""))))), ""
                ),
            }
        )
    if len(normalized) > max_entries:
        errors.append(f"Feed truncated by RSS_MAX_ENTRIES={max_entries}")
    return FeedResult(normalized[:max_entries], "; ".join(dict.fromkeys(errors)))
