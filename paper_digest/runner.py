"""Fetch snapshots and persist discoveries for local review."""

import argparse
import logging
from collections.abc import Callable

from paper_digest.config import Config
from paper_digest.config import STATE_FILE
from paper_digest.config import get_config
from paper_digest.fetchers.aps_prl_rss import ApsPrlRssFetcher
from paper_digest.fetchers.arxiv import ArxivFetcher
from paper_digest.fetchers.nature import NatureFetcher
from paper_digest.fetchers.nature_journal_rss import NatureJournalRssFetcher
from paper_digest.fetchers.rss_feeds import RssFeedFetcher
from paper_digest.models import FetchResult
from paper_digest.review_web import serve_review
from paper_digest.storage import locked_storage
from paper_digest.storage import utc_now

logger = logging.getLogger(__name__)


def run_digest(config: Config) -> int:
    """Persist matching papers and per-source outcomes for local review."""
    try:
        with locked_storage(STATE_FILE) as storage:
            started_at = utc_now()
            sources: list[tuple[str, str, Callable[[], FetchResult]]] = [
                ("arxiv", config.arxiv_url, ArxivFetcher(config).fetch),
                ("nature", config.nature_url, NatureFetcher(config).fetch),
                ("aps-prl", config.aps_prl_rss_url, ApsPrlRssFetcher(config).fetch),
                ("nature-journal", config.nature_journal_rss_url,
                 NatureJournalRssFetcher(config).fetch),
            ]
            sources.extend(
                (feed_id, url, RssFeedFetcher(config, feed_id, url).fetch)
                for feed_id, url in config.rss_feeds
            )
            incomplete = False
            for source, url, fetch in sources:
                try:
                    result = fetch()
                    status = "partial" if result.error else "success"
                except Exception as exc:
                    logger.exception("Fetcher failed: %s", source)
                    result = FetchResult(error=f"{type(exc).__name__}: {exc}")
                    status = "failed"
                for paper in result.papers:
                    storage.discover(paper, started_at)
                storage.record_source(
                    source, url, started_at, status, result.error, len(result.papers)
                )
                # Commit candidates and their source outcome together.
                storage.save()
                if status != "success":
                    incomplete = True
                    logger.warning("Source %s: %s (%s)", source, status, result.error)
                else:
                    logger.info("Source %s: success, %d matches", source, len(result.papers))

            return 1 if incomplete else 0
    except Exception:
        logger.exception("Fatal error while running digest")
        return 1


def main(argv: list[str] | None = None) -> int:
    """Fetch papers or manage selections from stored metadata."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    parser = argparse.ArgumentParser(description="Paper digest and selection tracking")
    commands = parser.add_subparsers(dest="command")
    review = commands.add_parser("review", help="List stored metadata; default: pending")
    review.add_argument("--status", choices=["pending", "accepted", "skipped", "all"],
                        default="pending")
    review.add_argument("--web", action="store_true",
                        help="Open a local browser window for all pending papers")
    review.add_argument("--no-browser", action="store_true",
                        help="With --web, print the URL without opening a browser")
    decide = commands.add_parser("decide", help="Record a selection by exact review ID")
    decide.add_argument("paper_id")
    decide.add_argument("decision", choices=["accept", "skip"])
    commands.add_parser("status", help="Show source coverage and selection counts")
    args = parser.parse_args(argv)
    if args.command is None:
        return run_digest(get_config())
    if args.command == "review":
        if args.no_browser and not args.web:
            parser.error("--no-browser requires --web")
        if args.web and args.status != "pending":
            parser.error("--web reviews pending papers; use text review for other statuses")
    try:
        if args.command == "review" and args.web:
            return serve_review(STATE_FILE, open_browser=not args.no_browser)
        with locked_storage(STATE_FILE) as storage:
            if args.command == "decide":
                decision = "accepted" if args.decision == "accept" else "skipped"
                storage.decide(args.paper_id, decision)
                print(f"{args.paper_id}: {decision}")
            elif args.command == "review":
                count = 0
                for item_id, record in storage.state["papers"].items():
                    if args.status != "all" and record["decision"] != args.status:
                        continue
                    paper = record["paper"]
                    print(f"{item_id} [{record['decision']}]")
                    print(f"  {paper['title']} ({paper['published_date'] or 'date unknown'})")
                    print(f"  {paper['link']}")
                    count += 1
                print(f"{count} paper(s).")
            else:
                for source, record in storage.state["sources"].items():
                    print(f"{source}: {record['status']}; "
                          f"last successful check: {record['last_success'] or 'never'}")
                    if record["error"]:
                        print(f"  {record['error']}")
                print(f"Tracked papers: {len(storage.state['papers'])}")
                for decision in ("pending", "accepted", "skipped"):
                    count = sum(record["decision"] == decision
                                for record in storage.state["papers"].values())
                    print(f"{decision}: {count}")
        return 0
    except (OSError, ValueError, RuntimeError):
        logger.exception("Cannot update or read paper tracking")
        return 1
