# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false

import logging

from paper_digest.config import Config, STATE_FILE, get_config
from paper_digest.emailer import Emailer
from paper_digest.fetchers.arxiv import ArxivFetcher
from paper_digest.fetchers.nature import NatureFetcher
from paper_digest.models import Paper
from paper_digest.storage import PaperStorage

logger = logging.getLogger(__name__)


def run_digest(config: Config) -> int:
    try:
        storage = PaperStorage(STATE_FILE)
        emailer = Emailer(config)
        fetchers = [ArxivFetcher(config), NatureFetcher(config)]

        all_papers: list[Paper] = []
        for fetcher in fetchers:
            try:
                all_papers.extend(fetcher.fetch())
            except Exception:
                logger.exception("Fetcher failed: %s", fetcher.__class__.__name__)

        new_papers = [paper for paper in all_papers if not storage.is_seen(paper)]
        if not new_papers:
            return 0

        sent = emailer.send_digest(new_papers)
        if not sent:
            return 1

        for paper in new_papers:
            storage.mark_seen(paper)
        return 0
    except Exception:
        logger.exception("Fatal error while running digest")
        return 1


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    return run_digest(get_config())
