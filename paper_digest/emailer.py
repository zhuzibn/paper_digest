# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownParameterType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnusedCallResult=false

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from paper_digest.config import Config
from paper_digest.models import Paper


class Emailer:
    def __init__(self, config: Config) -> None:
        self.config: Config = config

    def send_digest(self, papers: list[Paper]) -> bool:
        if not papers:
            return False

        message = self._build_message(papers)
        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as smtp:
            _ = smtp.starttls()
            _ = smtp.login(self.config.smtp_user, self.config.smtp_password)
            _ = smtp.send_message(message)
        return True

    def _build_message(self, papers: list[Paper]) -> MIMEMultipart:
        matched_keywords = self._matched_keywords(papers)
        message = MIMEMultipart("alternative")
        message["Subject"] = (
            f"Paper Digest ({len(papers)}): {', '.join(matched_keywords)}"
        )
        message["From"] = self.config.email_from
        message["To"] = self.config.email_to
        message.attach(
            MIMEText(self._build_plain_body(papers, matched_keywords), "plain")
        )
        message.attach(
            MIMEText(self._build_html_body(papers, matched_keywords), "html")
        )
        return message

    def _build_plain_body(
        self, papers: list[Paper], matched_keywords: list[str]
    ) -> str:
        lines: list[str] = ["Daily Paper Digest", ""]

        source_counts = self._source_counts(papers)
        source_descriptions = self._get_source_descriptions()
        lines.append(f"Sources checked: {', '.join(source_descriptions)}")
        lines.append(f"Related papers found: {len(papers)}")
        lines.append("")
        # Add per-source counts
        ordered_sources = [
            ("arxiv", "arXiv (cond-mat/new)"),
            ("nature", "Nature Communications"),
            ("aps-prl", "Physical Review Letters"),
            ("nature-journal", "Nature (journal)"),
        ] + [
            (feed_id, feed_id)  # Use feed_id as label since we no longer have hardcoded labels
            for feed_id, _ in self.config.rss_feeds
        ]
        for source_id, source_label in ordered_sources:
            lines.append(f"{source_label}: {source_counts.get(source_id, 0)}")
        lines.append("")

        for paper in papers:
            authors = ", ".join(paper.authors) if paper.authors else "N/A"
            paper_keywords = ", ".join(paper.keywords_matched)
            lines.extend(
                [
                    f"Title: {paper.title}",
                    f"Authors: {authors}",
                    f"Link: {paper.link}",
                    f"Date: {paper.published_date}",
                    f"Keywords: {paper_keywords}",
                    "",
                ]
            )

        lines.append(f"Matched keywords: {', '.join(matched_keywords)}")
        return "\n".join(lines)

    def _build_html_body(self, papers: list[Paper], matched_keywords: list[str]) -> str:
        source_counts = self._source_counts(papers)
        items: list[str] = []
        for paper in papers:
            authors = ", ".join(paper.authors) if paper.authors else "N/A"
            paper_keywords = ", ".join(paper.keywords_matched)
            item = (
                "<li>"
                + f"<strong>{paper.title}</strong><br/>"
                + f"Authors: {authors}<br/>"
                + f'Link: <a href="{paper.link}">{paper.link}</a><br/>'
                + f"Date: {paper.published_date}<br/>"
                + f"Keywords: {paper_keywords}"
                + "</li>"
            )
            items.append(item)

        source_descriptions = self._get_source_descriptions()
        sources_checked_str = ", ".join(source_descriptions)
        # Prepare source labels in order for counting
        ordered_sources = [
            ("arxiv", "arXiv (cond-mat/new)"),
            ("nature", "Nature Communications"),
            ("aps-prl", "Physical Review Letters"),
            ("nature-journal", "Nature (journal)"),
        ] + [
            (feed_id, feed_id)  # Use feed_id as label since we no longer have hardcoded labels
            for feed_id, _ in self.config.rss_feeds
        ]
        # Build source counts HTML
        source_count_items = []
        for source_id, source_label in ordered_sources:
            source_count_items.append(
                f"<li>{source_label}: {source_counts.get(source_id, 0)}</li>"
            )

        return (
            "<html><body>"
            + "<h2>Daily Paper Digest</h2>"
            + f"<p><strong>Sources checked:</strong> {sources_checked_str}</p>"
            + f"<p><strong>Related papers found:</strong> {len(papers)}</p>"
            + "<ul>"
            + "".join(source_count_items)
            + "</ul>"
            + f"<p>Matched keywords: {', '.join(matched_keywords)}</p>"
            + "<ul>"
            + "".join(items)
            + "</ul></body></html>"
        )

    def _matched_keywords(self, papers: list[Paper]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for paper in papers:
            for keyword in paper.keywords_matched:
                if keyword not in seen:
                    seen.add(keyword)
                    ordered.append(keyword)
        return ordered

    def _source_counts(self, papers: list[Paper]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for paper in papers:
            counts[paper.source] = counts.get(paper.source, 0) + 1
        return counts

    def _get_source_descriptions(self) -> list[str]:
        """Get list of source descriptions for display, including RSS feeds from config."""
        descriptions = [
            "arXiv (cond-mat/new)",
            "Nature Communications",
            "Physical Review Letters",
            "Nature (journal)",
        ]

        # Add additional RSS feed IDs from configuration
        for feed_id, _ in self.config.rss_feeds:
            descriptions.append(feed_id)

        return descriptions
        return descriptions
