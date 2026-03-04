import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

_ = load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"
STATE_FILE = STATE_DIR / "seen_papers.json"

# Define constants
BUILTIN_RSS_OVERRIDE_IDS = {"nature", "aps-prl", "nature-journal"}
RESERVED_RSS_FEED_IDS = {"arxiv"}

logger = logging.getLogger(__name__)


def _is_valid_http_url(url: str) -> bool:
    parsed = urlsplit(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _parse_rss_feeds(raw: str) -> tuple[list[tuple[str, str]], dict[str, str]]:
    """Parse RSS feeds from a string in the format 'id=url;id2=url2'.

    Args:
        raw: Raw RSS feeds string

    Returns:
        Tuple of:
        - Additional RSS feeds as (feed_id, url) tuples
        - Built-in RSS override map keyed by feed ID
    """
    rss_feeds: list[tuple[str, str]] = []
    builtin_overrides: dict[str, str] = {}
    seen_ids: set[str] = set()

    # Split on both semicolon and newline
    segments: list[str] = []
    for segment in re.split(r"[;\n]", raw):
        segment = segment.strip()
        if segment:
            segments.append(segment)

    for segment in segments:
        if "=" not in segment:
            logger.warning("Invalid RSS feed format, skipping: %s", segment)
            continue

        # Split on first '=' only - in case URL or id itself has `=` character
        parts: list[str] = segment.split("=", 1)
        feed_id: str = parts[0].strip()
        url: str = parts[1].strip()

        # Validate feed_id
        feed_id = feed_id.strip().lower()

        # Check if it's a reserved ID
        if feed_id in RESERVED_RSS_FEED_IDS:
            logger.warning("RSS feed ID '%s' is reserved and will be ignored", feed_id)
            continue

        if feed_id in BUILTIN_RSS_OVERRIDE_IDS:
            if not _is_valid_http_url(url):
                logger.warning(
                    "Invalid built-in override URL for %s, ignoring override: %s",
                    feed_id,
                    url,
                )
                continue
            builtin_overrides[feed_id] = url
            continue

        # Validate feed_id format: starts with alphanumeric, then alphanumeric + hyphens
        if not re.match(r"^[a-z0-9][a-z0-9-]*$", feed_id):
            logger.warning(
                "Invalid RSS feed ID format, skipping: %s. Must match regex ^[a-z0-9][a-z0-9-]*$",
                feed_id,
            )
            continue

        # Validate URL
        if not _is_valid_http_url(url):
            logger.warning("Invalid URL format for %s, skipping: %s", feed_id, url)
            continue

        # Handle duplicate IDs - keep first occurrence but update URL in-place
        if feed_id in seen_ids:
            # Find the index and update
            for i, (existing_id, _) in enumerate(rss_feeds):
                if existing_id == feed_id:
                    rss_feeds[i] = (feed_id, url)
                    break

        else:
            rss_feeds.append((feed_id, url))
            seen_ids.add(feed_id)

    return rss_feeds, builtin_overrides


@dataclass
class Config:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    email_from: str
    email_to: str
    arxiv_url: str
    nature_url: str
    user_agent: str
    keywords: list[str]
    aps_prl_rss_url: str = "https://feeds.aps.org/rss/recent/prl.xml"
    aps_prl_section_filter: str = "Condensed Matter and Materials"
    nature_journal_rss_url: str = "https://www.nature.com/nature/current_issue/rss"
    nature_journal_category_allowlist: list[str] = field(default_factory=list)
    rss_max_entries: int = 200
    rss_feeds: list[tuple[str, str]] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "Config":
        keywords_raw = os.getenv("KEYWORDS", "")
        keywords = [
            part.strip().lower() for part in keywords_raw.split(",") if part.strip()
        ]
        nature_journal_category_allowlist_raw = os.getenv(
            "NATURE_JOURNAL_CATEGORY_ALLOWLIST", ""
        )
        nature_journal_category_allowlist = [
            part.strip().lower()
            for part in nature_journal_category_allowlist_raw.split(",")
            if part.strip()
        ]

        # Handle RSS feeds
        rss_feed_raw = os.getenv("RSS_FEEDS", "")
        builtin_overrides: dict[str, str] = {}
        if "RSS_FEEDS" not in os.environ:
            rss_feeds = []  # Disabled by default for backward compatibility
        elif not rss_feed_raw.strip():  # Empty or whitespace
            rss_feeds = []
        else:
            rss_feeds, builtin_overrides = _parse_rss_feeds(rss_feed_raw)

        return cls(
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            email_from=os.getenv("EMAIL_FROM", ""),
            email_to=os.getenv("EMAIL_TO", ""),
            arxiv_url=os.getenv("ARXIV_URL", "https://arxiv.org/list/cond-mat/new"),
            nature_url=builtin_overrides.get(
                "nature",
                os.getenv("NATURE_URL", "https://www.nature.com/ncomms.rss"),
            ),
            aps_prl_rss_url=builtin_overrides.get(
                "aps-prl",
                os.getenv(
                    "APS_PRL_RSS_URL", "https://feeds.aps.org/rss/recent/prl.xml"
                ),
            ),
            aps_prl_section_filter=os.getenv(
                "APS_PRL_SECTION_FILTER", "Condensed Matter and Materials"
            ).strip(),
            nature_journal_rss_url=builtin_overrides.get(
                "nature-journal",
                os.getenv(
                    "NATURE_JOURNAL_RSS_URL",
                    "https://www.nature.com/nature/current_issue/rss",
                ),
            ),
            nature_journal_category_allowlist=nature_journal_category_allowlist,
            rss_max_entries=int(os.getenv("RSS_MAX_ENTRIES", "200")),
            rss_feeds=rss_feeds,
            user_agent=os.getenv(
                "USER_AGENT", "Mozilla/5.0 (compatible; PaperDigest/1.0)"
            ),
            keywords=keywords,
        )


def get_config() -> Config:
    return Config.from_env()
