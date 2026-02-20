# pyright: reportMissingImports=false, reportUnknownVariableType=false

from paper_digest.fetchers.arxiv import ArxivFetcher
from paper_digest.fetchers.nature import NatureFetcher

__all__ = ["ArxivFetcher", "NatureFetcher"]
