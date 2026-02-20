# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false

from unittest.mock import patch

from paper_digest.config import Config
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


def _paper(link: str, source: str = "arxiv") -> Paper:
    return Paper(
        title="Spin-orbit torque in MRAM",
        authors=["Ada Lovelace", "Grace Hopper"],
        link=link,
        published_date="2024-01-15",
        source=source,
        keywords_matched=["spin-orbit torque", "mram"],
    )


@patch("paper_digest.runner.Emailer")
@patch("paper_digest.runner.PaperStorage")
@patch("paper_digest.runner.NatureFetcher")
@patch("paper_digest.runner.ArxivFetcher")
def test_run_digest_sends_unseen_and_marks_seen_on_success(
    mock_arxiv_fetcher,
    mock_nature_fetcher,
    mock_storage_cls,
    mock_emailer_cls,
):
    from paper_digest.runner import run_digest

    seen_paper = _paper("https://arxiv.org/abs/2401.00001")
    new_paper = _paper("https://www.nature.com/articles/s41467-024-00001", "nature")

    mock_arxiv_fetcher.return_value.fetch.return_value = [seen_paper]
    mock_nature_fetcher.return_value.fetch.return_value = [new_paper]
    storage = mock_storage_cls.return_value
    storage.is_seen.side_effect = [True, False]
    emailer = mock_emailer_cls.return_value
    emailer.send_digest.return_value = True

    code = run_digest(_config())

    assert code == 0
    emailer.send_digest.assert_called_once_with([new_paper])
    storage.mark_seen.assert_called_once_with(new_paper)


@patch("paper_digest.runner.Emailer")
@patch("paper_digest.runner.PaperStorage")
@patch("paper_digest.runner.NatureFetcher")
@patch("paper_digest.runner.ArxivFetcher")
def test_run_digest_does_not_mark_seen_when_email_fails(
    mock_arxiv_fetcher,
    mock_nature_fetcher,
    mock_storage_cls,
    mock_emailer_cls,
):
    from paper_digest.runner import run_digest

    new_paper = _paper("https://arxiv.org/abs/2401.00001")
    mock_arxiv_fetcher.return_value.fetch.return_value = [new_paper]
    mock_nature_fetcher.return_value.fetch.return_value = []
    storage = mock_storage_cls.return_value
    storage.is_seen.return_value = False
    emailer = mock_emailer_cls.return_value
    emailer.send_digest.return_value = False

    code = run_digest(_config())

    assert code == 1
    emailer.send_digest.assert_called_once_with([new_paper])
    storage.mark_seen.assert_not_called()


@patch("paper_digest.runner.Emailer")
@patch("paper_digest.runner.PaperStorage")
@patch("paper_digest.runner.NatureFetcher")
@patch("paper_digest.runner.ArxivFetcher")
def test_run_digest_returns_zero_when_no_new_papers(
    mock_arxiv_fetcher,
    mock_nature_fetcher,
    mock_storage_cls,
    mock_emailer_cls,
):
    from paper_digest.runner import run_digest

    seen_paper = _paper("https://arxiv.org/abs/2401.00001")
    mock_arxiv_fetcher.return_value.fetch.return_value = [seen_paper]
    mock_nature_fetcher.return_value.fetch.return_value = []
    storage = mock_storage_cls.return_value
    storage.is_seen.return_value = True

    code = run_digest(_config())

    assert code == 0
    mock_emailer_cls.return_value.send_digest.assert_not_called()
    storage.mark_seen.assert_not_called()


@patch("paper_digest.runner.Emailer")
@patch("paper_digest.runner.PaperStorage")
@patch("paper_digest.runner.NatureFetcher")
@patch("paper_digest.runner.ArxivFetcher")
def test_run_digest_continues_if_one_fetcher_raises(
    mock_arxiv_fetcher,
    mock_nature_fetcher,
    mock_storage_cls,
    mock_emailer_cls,
):
    from paper_digest.runner import run_digest

    new_paper = _paper("https://www.nature.com/articles/s41467-024-00001", "nature")
    mock_arxiv_fetcher.return_value.fetch.side_effect = RuntimeError("arxiv boom")
    mock_nature_fetcher.return_value.fetch.return_value = [new_paper]
    storage = mock_storage_cls.return_value
    storage.is_seen.return_value = False
    emailer = mock_emailer_cls.return_value
    emailer.send_digest.return_value = True

    code = run_digest(_config())

    assert code == 0
    emailer.send_digest.assert_called_once_with([new_paper])
    storage.mark_seen.assert_called_once_with(new_paper)


@patch("paper_digest.runner.PaperStorage", side_effect=RuntimeError("fatal"))
def test_run_digest_returns_one_on_fatal_error(_mock_storage_cls):
    from paper_digest.runner import run_digest

    code = run_digest(_config())

    assert code == 1
