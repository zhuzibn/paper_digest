# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false

from unittest.mock import Mock, patch

from paper_digest.config import Config
from paper_digest.fetchers.aps_prl_rss import ApsPrlRssFetcher


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
        keywords=["spintronics", "spin-orbit torque", "mram"],
        aps_prl_rss_url="https://feeds.aps.org/rss/recent/prl.xml",
        aps_prl_section_filter="Condensed Matter and Materials",
        rss_max_entries=50,
    )


@patch("paper_digest.fetchers.aps_prl_rss.fetch_feed_entries")
def test_fetch_returns_only_matching_prl_section_entries(mock_fetch: Mock) -> None:
    mock_fetch.return_value = [
        {
            "title": "Spin-orbit torque switching",
            "link": "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.1",
            "published": "2024-01-15",
            "authors": ["Alice", "Bob"],
            "summary": "MRAM-relevant physics in condensed matter systems.",
            "categories": ["Condensed Matter and Materials"],
            "raw": {},
        },
        {
            "title": "Optics with keyword spintronics",
            "link": "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.2",
            "published": "2024-01-16",
            "authors": ["Carol"],
            "summary": "Has keyword but wrong section.",
            "categories": ["Quantum Optics"],
            "raw": {},
        },
    ]

    config = _config()
    papers = ApsPrlRssFetcher(config).fetch()

    mock_fetch.assert_called_once_with(
        config.aps_prl_rss_url,
        config.user_agent,
        max_entries=config.rss_max_entries,
    )
    assert len(papers) == 1
    assert papers[0].title == "Spin-orbit torque switching"
    assert papers[0].authors == ["Alice", "Bob"]
    assert papers[0].published_date == "2024-01-15"
    assert papers[0].source == "aps-prl"
    assert papers[0].keywords_matched == ["spin-orbit torque", "mram"]


@patch("paper_digest.fetchers.aps_prl_rss.fetch_feed_entries")
def test_fetch_uses_raw_field_fallbacks_for_section_date_and_authors(
    mock_fetch: Mock,
) -> None:
    mock_fetch.return_value = [
        {
            "title": "Spintronics in layered structures",
            "link": "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.3",
            "published": "",
            "authors": [],
            "summary": "New approach for MRAM writing.",
            "categories": [],
            "raw": {
                "prism_section": "condensed matter and materials",
                "dc_date": "Mon, 22 Jan 2024 12:00:00 GMT",
                "dc_creator": "Dana and Evan, Frank",
            },
        }
    ]

    papers = ApsPrlRssFetcher(_config()).fetch()

    assert len(papers) == 1
    assert papers[0].authors == ["Dana", "Evan", "Frank"]
    assert papers[0].published_date == "2024-01-22"
    assert papers[0].source == "aps-prl"
    assert papers[0].keywords_matched == ["spintronics", "mram"]
