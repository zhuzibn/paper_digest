# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false

from unittest.mock import Mock, patch

from paper_digest.config import Config
from paper_digest.fetchers.nature import NatureFetcher


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


def test_match_keywords_uses_title_and_summary() -> None:
    fetcher = NatureFetcher(_config())

    matched = fetcher._match_keywords(
        title="Novel Device Architecture",
        keywords=["spin-orbit torque", "antiferromagnet", "mram"],
        summary="We demonstrate spin-orbit torque switching in antiferromagnet-based MRAM cells.",
    )

    assert matched == ["spin-orbit torque", "antiferromagnet", "mram"]


def test_parse_date_handles_common_inputs() -> None:
    fetcher = NatureFetcher(_config())

    assert fetcher._parse_date("15 January 2024") == "2024-01-15"
    assert fetcher._parse_date("2024-01-15T12:00:00Z") == "2024-01-15"
    assert fetcher._parse_date("2024-01-15") == "2024-01-15"


@patch("paper_digest.fetchers.nature.requests.get")
def test_fetch_uses_subject_url_and_returns_only_keyword_matches(
    mock_get: Mock,
) -> None:
    html = """
    <html>
      <body>
        <article class="c-article-item">
          <h3 class="c-article-item__title">
            <a href="/articles/s41586-024-12345">Spin-orbit torque in antiferromagnetic devices</a>
          </h3>
          <p class="c-article-item__description">A route to MRAM-compatible switching.</p>
          <ul class="c-article-item__authors"><li>Alice</li><li>Bob</li></ul>
          <time class="c-article-item__date">15 January 2024</time>
        </article>
        <article class="c-article-item">
          <h3 class="c-article-item__title">
            <a href="/articles/s41586-024-54321">Thermal transport in thin films</a>
          </h3>
          <p class="c-article-item__description">No matching terms here.</p>
          <ul class="c-article-item__authors"><li>Carol</li></ul>
          <time class="c-article-item__date">16 January 2024</time>
        </article>
      </body>
    </html>
    """
    response = Mock()
    response.text = html
    response.raise_for_status = Mock()
    mock_get.return_value = response

    config = _config()
    fetcher = NatureFetcher(config)

    papers = fetcher.fetch()

    mock_get.assert_called_once_with(
        config.nature_url,
        headers={"User-Agent": config.user_agent},
        timeout=30,
    )
    assert len(papers) == 1
    assert papers[0].title == "Spin-orbit torque in antiferromagnetic devices"
    assert papers[0].authors == ["Alice", "Bob"]
    assert papers[0].link == "https://www.nature.com/articles/s41586-024-12345"
    assert papers[0].published_date == "2024-01-15"
    assert papers[0].source == "nature"
    assert papers[0].keywords_matched == [
        "spin-orbit torque",
        "antiferromagnet",
        "mram",
    ]
