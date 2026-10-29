"""Conservative identifiers for matching paper metadata across feeds."""

import hashlib
import re
from urllib.parse import parse_qsl
from urllib.parse import unquote
from urllib.parse import urlencode
from urllib.parse import urlsplit
from urllib.parse import urlunsplit


def canonical_url(url: str) -> str:
    """Normalize a URL while retaining query parameters that may identify items."""
    parts = urlsplit(url.strip())
    query = sorted(
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
        and key.lower() not in {"fbclid", "gclid"}
    )
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path,
         urlencode(query), "")
    )


def normalize_doi(value: str) -> str:
    """Extract a DOI from an explicit DOI value or resolver URL."""
    value = unquote(value.strip())
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value,
                   flags=re.IGNORECASE)
    return value.lower() if re.fullmatch(r"10\.\d{4,9}/\S+", value) else ""


def identity_keys(link: str, doi: str = "") -> list[str]:
    """Return DOI/arXiv keys plus a URL alias; never guess from a title."""
    url = canonical_url(link)
    parts = urlsplit(url)
    path = unquote(parts.path)
    keys: list[str] = []
    normalized_doi = normalize_doi(doi)
    if not normalized_doi and parts.hostname in {"doi.org", "dx.doi.org"}:
        normalized_doi = normalize_doi(path.lstrip("/"))
    if not normalized_doi and parts.hostname == "journals.aps.org":
        match = re.search(r"/(10\.\d{4,9}/.+)$", path)
        if match:
            normalized_doi = normalize_doi(match.group(1))
    if not normalized_doi and parts.hostname in {"nature.com", "www.nature.com"}:
        match = re.fullmatch(r"/articles/([^/]+?)(?:\.pdf)?/?", path)
        if match:
            normalized_doi = normalize_doi("10.1038/" + match.group(1))
    if normalized_doi:
        keys.append("doi:" + normalized_doi)
    if parts.hostname in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"}:
        match = re.fullmatch(
            r"/(?:abs|pdf)/((?:\d{4}\.\d{4,5}|[a-z.-]+/\d{7}))"
            r"(?:v\d+)?(?:\.pdf)?/?", path, flags=re.IGNORECASE
        )
        if match:
            keys.append("arxiv:" + match.group(1).lower())
    keys.append("url:" + url)
    return keys


def paper_id(link: str, doi: str = "") -> str:
    """Create a short stable ID from the strongest available identity."""
    key = identity_keys(link, doi)[0]
    return "p-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
