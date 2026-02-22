# pyright: reportMissingImports=false, reportUnknownVariableType=false

from paper_digest.fetchers.arxiv import ArxivFetcher
from paper_digest.fetchers.aps_prl_rss import ApsPrlRssFetcher
from paper_digest.fetchers.nature import NatureFetcher
from paper_digest.fetchers.nature_journal_rss import NatureJournalRssFetcher

__all__ = [
    "ArxivFetcher",
    "ApsPrlRssFetcher",
    "NatureFetcher",
    "NatureJournalRssFetcher",
]
