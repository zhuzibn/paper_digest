# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false

from unittest.mock import Mock, patch

from paper_digest.config import Config
from paper_digest.fetchers.arxiv import ArxivFetcher


def _config() -> Config:
    return Config(
        smtp_host="",
        smtp_port=587,
        smtp_user="",
        smtp_password="",
        email_from="",
        email_to="",
        arxiv_url="https://arxiv.org/list/cond-mat/new",
        nature_url="https://www.nature.com/subjects/physical-sciences/ncomms",
        user_agent="PaperDigestTest/1.0",
        keywords=["spintronics", "spin-orbit torque", "antiferromagnet", "mram"],
    )


def test_match_keywords_uses_title_and_abstract() -> None:
    fetcher = ArxivFetcher(_config())

    matched = fetcher._match_keywords(
        title="Novel Device Architecture",
        keywords=["spintronics", "spin-orbit torque", "mram"],
        abstract="We demonstrate spin-orbit torque switching in MRAM cells.",
    )

    assert matched == ["spin-orbit torque", "mram"]


def test_parse_date_handles_common_inputs() -> None:
    fetcher = ArxivFetcher(_config())

    assert fetcher._parse_date("2024-01-15T12:00:00Z") == "2024-01-15"
    assert fetcher._parse_date("15 Jan 2024") == "2024-01-15"
    assert fetcher._parse_date("2024-01-15") == "2024-01-15"


@patch("paper_digest.fetchers.arxiv.requests.get")
def test_fetch_uses_user_agent_and_returns_only_keyword_matches(mock_get: Mock) -> None:
    html = """
    <html>
      <body>
        <dl>
          <dt><a href="/abs/2401.00001">arXiv:2401.00001</a></dt>
          <dd>
            <div class="list-title mathjax">Title: Spin-Orbit Torque in Devices</div>
            <div class="list-authors"><a>Alice</a><a>Bob</a></div>
            <p class="mathjax">Abstract: We study MRAM switching.</p>
            <div class="list-date">Submitted on 15 Jan 2024</div>
          </dd>
          <dt><a href="/abs/2401.00002">arXiv:2401.00002</a></dt>
          <dd>
            <div class="list-title mathjax">Title: Thermal conduction in films</div>
            <div class="list-authors"><a>Carol</a></div>
            <p class="mathjax">Abstract: No relevant keywords.</p>
            <div class="list-date">Submitted on 16 Jan 2024</div>
          </dd>
        </dl>
      </body>
    </html>
    """
    response = Mock()
    response.text = html
    response.raise_for_status = Mock()
    mock_get.return_value = response

    config = _config()
    fetcher = ArxivFetcher(config)

    papers = fetcher.fetch()

    mock_get.assert_called_once_with(
        config.arxiv_url,
        headers={"User-Agent": config.user_agent},
        timeout=30,
    )
    assert len(papers) == 1
    assert papers[0].title == "Spin-Orbit Torque in Devices"
    assert papers[0].source == "arxiv"
    assert papers[0].published_date == "2024-01-15"
    assert papers[0].keywords_matched == ["spin-orbit torque", "mram"]
