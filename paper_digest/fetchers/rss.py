# pyright: reportMissingImports=false, reportMissingTypeStubs=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from typing import TypedDict

import feedparser
import requests

from paper_digest.fetchers.common import canonicalize_link, normalize_date


class NormalizedFeedEntry(TypedDict):
    title: str
    link: str
    published: str
    authors: list[str]
    summary: str
    categories: list[str]
    raw: object


def fetch_feed_entries(
    url: str,
    user_agent: str,
    max_entries: int = 200,
) -> list[NormalizedFeedEntry]:
    response = requests.get(
        url,
        headers={"User-Agent": user_agent},
        timeout=30,
    )
    response.raise_for_status()
    parsed_feed = feedparser.parse(response.text)

    normalized: list[NormalizedFeedEntry] = []
    for entry in parsed_feed.entries:
        title = str(entry.get("title", "")).strip()
        link = canonicalize_link(str(entry.get("link", "")))
        if not title or not link:
            continue

        published_raw = str(
            entry.get("published") or entry.get("updated") or entry.get("pubDate") or ""
        )
        summary = str(entry.get("summary") or entry.get("description") or "").strip()

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
            }
        )
        if len(normalized) >= max_entries:
            break

    return normalized
