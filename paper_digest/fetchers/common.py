import re

from dateutil import parser as date_parser

from paper_digest.identity import canonical_url


def match_keywords(text: str, keywords: list[str]) -> list[str]:
    content = text.lower()
    matched: list[str] = []
    seen_lower: set[str] = set()

    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in seen_lower:
            continue
        if keyword_lower in content:
            matched.append(keyword)
            seen_lower.add(keyword_lower)

    return matched


def normalize_date(date_input: str) -> str:
    if not date_input:
        return ""
    try:
        return date_parser.parse(date_input, fuzzy=True).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        match = re.search(r"\d{4}-\d{2}-\d{2}", date_input)
        return match.group(0) if match else date_input


def canonicalize_link(url: str) -> str:
    """Normalize links consistently with persisted paper identities."""
    return canonical_url(url)
