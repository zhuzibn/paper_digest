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
        lines.append(
            "Sources checked: arXiv (cond-mat/new), Nature Communications, Physical Review Letters, Nature (journal)"
        )
        lines.append(f"Related papers found: {len(papers)}")
        lines.append("")
        lines.append(f"arXiv (cond-mat/new): {source_counts.get('arxiv', 0)}")
        lines.append(f"Nature Communications: {source_counts.get('nature', 0)}")
        lines.append(f"Physical Review Letters: {source_counts.get('aps-prl', 0)}")
        lines.append(f"Nature (journal): {source_counts.get('nature-journal', 0)}")
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

        return (
            "<html><body>"
            + "<h2>Daily Paper Digest</h2>"
            + "<p><strong>Sources checked:</strong> arXiv (cond-mat/new), Nature Communications, Physical Review Letters, Nature (journal)</p>"
            + f"<p><strong>Related papers found:</strong> {len(papers)}</p>"
            + "<ul>"
            + f"<li>arXiv (cond-mat/new): {source_counts.get('arxiv', 0)}</li>"
            + f"<li>Nature Communications: {source_counts.get('nature', 0)}</li>"
            + f"<li>Physical Review Letters: {source_counts.get('aps-prl', 0)}</li>"
            + f"<li>Nature (journal): {source_counts.get('nature-journal', 0)}</li>"
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
