# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false

from unittest.mock import patch

from paper_digest.config import Config
from paper_digest.emailer import Emailer
from paper_digest.models import Paper


def _config() -> Config:
    return Config(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="user@example.com",
        smtp_password="secret",
        email_from="from@example.com",
        email_to="to@example.com",
        arxiv_url="https://arxiv.org/list/cond-mat/new",
        nature_url="https://www.nature.com/subjects/physical-sciences/ncomms",
        user_agent="PaperDigestTests/1.0",
        keywords=["spin-orbit torque", "mram"],
    )


def _paper() -> Paper:
    return Paper(
        title="Spin-orbit torque in MRAM",
        authors=["Ada Lovelace", "Grace Hopper"],
        link="https://arxiv.org/abs/2401.00001",
        published_date="2024-01-15",
        source="arxiv",
        keywords_matched=["spin-orbit torque", "mram"],
    )


@patch("smtplib.SMTP")
def test_send_digest_returns_false_and_does_not_send_for_empty_papers(mock_smtp):
    emailer = Emailer(_config())

    result = emailer.send_digest([])

    assert result is False
    mock_smtp.assert_not_called()


@patch("smtplib.SMTP")
def test_send_digest_sends_multipart_email_with_expected_content(mock_smtp):
    emailer = Emailer(_config())

    result = emailer.send_digest([_paper()])

    assert result is True
    mock_smtp.assert_called_once_with("smtp.example.com", 587)
    smtp_server = mock_smtp.return_value.__enter__.return_value
    smtp_server.starttls.assert_called_once_with()
    smtp_server.login.assert_called_once_with("user@example.com", "secret")
    smtp_server.send_message.assert_called_once()

    msg = smtp_server.send_message.call_args.args[0]
    assert msg["From"] == "from@example.com"
    assert msg["To"] == "to@example.com"
    assert "spin-orbit torque" in msg["Subject"].lower()

    parts = msg.get_payload()
    assert len(parts) == 2
    plain_part = parts[0]
    html_part = parts[1]
    assert plain_part.get_content_type() == "text/plain"
    assert html_part.get_content_type() == "text/html"

    plain_text = plain_part.get_payload(decode=True).decode(
        plain_part.get_content_charset()
    )
    html_text = html_part.get_payload(decode=True).decode(
        html_part.get_content_charset()
    )

    for value in [
        "Sources checked:",
        "Related papers found:",
        "arXiv (cond-mat/new): 1",
        "Nature Communications: 0",
        "Physical Review Letters: 0",
        "Nature (journal): 0",
        "Spin-orbit torque in MRAM",
        "Ada Lovelace, Grace Hopper",
        "https://arxiv.org/abs/2401.00001",
        "2024-01-15",
        "spin-orbit torque, mram",
    ]:
        assert value in plain_text
        assert value in html_text
