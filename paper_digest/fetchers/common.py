import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dateutil import parser as date_parser


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
    stripped = url.strip()
    parts = urlsplit(stripped)
    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    query = urlencode(filtered_query, doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))
