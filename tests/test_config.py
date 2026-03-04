import sys
import importlib
from pathlib import Path
from typing import Protocol, cast

from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import paper_digest.config as config_module


class ConfigProtocol(Protocol):
    def __init__(
        self,
        *,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        email_from: str,
        email_to: str,
        arxiv_url: str,
        nature_url: str,
        user_agent: str,
        keywords: list[str],
        rss_feeds: list[tuple[str, str]] | None = None,
        aps_prl_rss_url: str = "https://feeds.aps.org/rss/recent/prl.xml",
        aps_prl_section_filter: str = "Condensed Matter and Materials",
        nature_journal_rss_url: str = "https://www.nature.com/nature/current_issue/rss",
        nature_journal_category_allowlist: list[str] | None = None,
        rss_max_entries: int = 200,
    ) -> None: ...

    smtp_host: str
    smtp_port: int
    keywords: list[str]
    rss_feeds: list[tuple[str, str]]
    nature_url: str
    aps_prl_rss_url: str
    aps_prl_section_filter: str
    nature_journal_rss_url: str
    nature_journal_category_allowlist: list[str]
    rss_max_entries: int

    @classmethod
    def from_env(cls) -> "ConfigProtocol": ...


class ConfigModuleProtocol(Protocol):
    Config: type[ConfigProtocol]
    STATE_DIR: Path
    STATE_FILE: Path

    def get_config(self) -> ConfigProtocol: ...


def load_config_module():
    module = importlib.reload(config_module)
    return cast(ConfigModuleProtocol, cast(object, module))


def test_env_example_exists():
    assert Path(".env.example").exists()


def test_requirements_has_core_dependencies():
    content = Path("requirements.txt").read_text(encoding="utf-8")
    assert "requests" in content
    assert "beautifulsoup4" in content
    assert "feedparser" in content


def test_from_env_parses_and_normalizes_keywords(monkeypatch: MonkeyPatch):
    config_module = load_config_module()
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("EMAIL_FROM", "from@example.com")
    monkeypatch.setenv("EMAIL_TO", "to@example.com")
    monkeypatch.setenv("ARXIV_URL", "https://arxiv.example/new")
    monkeypatch.setenv("NATURE_URL", "https://nature.example/new")
    monkeypatch.setenv("APS_PRL_RSS_URL", "https://aps.example/prl.rss")
    monkeypatch.setenv("APS_PRL_SECTION_FILTER", "  Quantum Matter  ")
    monkeypatch.setenv("NATURE_JOURNAL_RSS_URL", "https://nature.example/journal.rss")
    monkeypatch.setenv(
        "NATURE_JOURNAL_CATEGORY_ALLOWLIST",
        " Research Highlights, Physics, ,  condensed matter  ",
    )
    monkeypatch.setenv("RSS_MAX_ENTRIES", "321")
    monkeypatch.setenv("USER_AGENT", "paper-digest-test")
    monkeypatch.setenv("KEYWORDS", " Spintronics,  MRAM ,spin-orbit torque,,   ")

    config = config_module.Config.from_env()

    assert config.smtp_host == "smtp.example.com"
    assert config.smtp_port == 2525
    assert config.keywords == ["spintronics", "mram", "spin-orbit torque"]
    assert config.aps_prl_rss_url == "https://aps.example/prl.rss"
    assert config.aps_prl_section_filter == "Quantum Matter"
    assert config.nature_journal_rss_url == "https://nature.example/journal.rss"
    assert config.nature_journal_category_allowlist == [
        "research highlights",
        "physics",
        "condensed matter",
    ]
    assert config.rss_max_entries == 321


def test_from_env_defaults_include_rss_fields(monkeypatch: MonkeyPatch):
    config_module = load_config_module()
    monkeypatch.delenv("NATURE_URL", raising=False)
    monkeypatch.delenv("APS_PRL_RSS_URL", raising=False)
    monkeypatch.delenv("APS_PRL_SECTION_FILTER", raising=False)
    monkeypatch.delenv("NATURE_JOURNAL_RSS_URL", raising=False)
    monkeypatch.delenv("NATURE_JOURNAL_CATEGORY_ALLOWLIST", raising=False)
    monkeypatch.delenv("RSS_MAX_ENTRIES", raising=False)

    config = config_module.Config.from_env()

    assert config.aps_prl_rss_url == "https://feeds.aps.org/rss/recent/prl.xml"
    assert config.nature_url == "https://www.nature.com/ncomms.rss"
    assert config.aps_prl_section_filter == "Condensed Matter and Materials"
    assert (
        config.nature_journal_rss_url
        == "https://www.nature.com/nature/current_issue/rss"
    )
    assert config.nature_journal_category_allowlist == []
    assert config.rss_max_entries == 200


def test_from_env_defaults_rss_feeds_when_unset(monkeypatch: MonkeyPatch):
    # RSS_FEEDS unset -> Config.rss_feeds should be empty for backward compatibility
    config_module = load_config_module()
    monkeypatch.delenv("RSS_FEEDS", raising=False)
    config = config_module.Config.from_env()

    # Should be empty by default when RSS_FEEDS environment variable is unset
    assert len(config.rss_feeds) == 0


def test_from_env_empty_rss_feeds_when_empty_string(monkeypatch: MonkeyPatch):
    # RSS_FEEDS="" -> Config.rss_feeds should be empty
    config_module = load_config_module()
    monkeypatch.setenv("RSS_FEEDS", "")
    config = config_module.Config.from_env()

    # If RSS_FEEDS is set to empty string, rss_feeds should be empty list
    assert config.rss_feeds == []


def test_from_env_filtered_invalid_segments_rss_feeds(monkeypatch: MonkeyPatch):
    # RSS_FEEDS with invalid segments -> valid segments parsed, invalid ones skipped
    config_module = load_config_module()
    # Include valid pairs and malformed segments
    bad_segment_env = "aps-prb=https://feeds.aps.org/rss/recent/prb.xml;badsegment;science=https://www.science.org/action/showFeed?type=axatoc&feed=rss&jc=science"
    monkeypatch.setenv("RSS_FEEDS", bad_segment_env)
    config = config_module.Config.from_env()

    # Should parse valid segments and skip malformed ones
    # At least 2 valid pairs (aps-prb and science) should be present, invalid "badsegment" should be skipped
    assert (
        len([feed for feed in config.rss_feeds if feed[0] in ["aps-prb", "science"]])
        >= 2
    )
    # Invalid segment like "badsegment" should be filtered out (it doesn't contain \"=\")


def test_from_env_rss_feeds_overrides_builtin_urls(monkeypatch: MonkeyPatch):
    config_module = load_config_module()
    monkeypatch.setenv("NATURE_URL", "https://legacy.example.com/nature.rss")
    monkeypatch.setenv("APS_PRL_RSS_URL", "https://legacy.example.com/aps-prl.rss")
    monkeypatch.setenv(
        "NATURE_JOURNAL_RSS_URL",
        "https://legacy.example.com/nature-journal.rss",
    )
    monkeypatch.setenv(
        "RSS_FEEDS",
        "nature=https://override.example.com/nature.rss;"
        + "aps-prl=https://override.example.com/aps-prl.rss;"
        + "nature-journal=https://override.example.com/nature-journal.rss;"
        + "custom=https://override.example.com/custom.rss",
    )

    config = config_module.Config.from_env()

    assert config.nature_url == "https://override.example.com/nature.rss"
    assert config.aps_prl_rss_url == "https://override.example.com/aps-prl.rss"
    assert (
        config.nature_journal_rss_url
        == "https://override.example.com/nature-journal.rss"
    )
    assert ("custom", "https://override.example.com/custom.rss") in config.rss_feeds


def test_from_env_rss_feeds_invalid_builtin_override_falls_back_to_default(
    monkeypatch: MonkeyPatch,
    caplog: LogCaptureFixture,
):
    config_module = load_config_module()
    monkeypatch.setenv("APS_PRL_RSS_URL", "https://legacy.example.com/aps-prl.rss")
    monkeypatch.setenv("RSS_FEEDS", "aps-prl=notaurl")

    config = config_module.Config.from_env()

    assert config.aps_prl_rss_url == "https://legacy.example.com/aps-prl.rss"
    assert "Invalid built-in override URL for aps-prl" in caplog.text


def test_from_env_rss_feeds_excludes_builtin_ids_from_additional_feeds(
    monkeypatch: MonkeyPatch,
):
    config_module = load_config_module()
    monkeypatch.setenv("NATURE_URL", "https://legacy.example.com/nature.rss")
    monkeypatch.setenv("APS_PRL_RSS_URL", "https://legacy.example.com/aps-prl.rss")
    monkeypatch.setenv(
        "NATURE_JOURNAL_RSS_URL",
        "https://legacy.example.com/nature-journal.rss",
    )
    monkeypatch.setenv(
        "RSS_FEEDS",
        "nature=https://override.example.com/nature.rss;"
        + "aps-prl=https://override.example.com/aps-prl.rss;"
        + "nature-journal=https://override.example.com/nature-journal.rss;"
        + "custom=https://override.example.com/custom.rss",
    )

    config = config_module.Config.from_env()

    assert ("nature", "https://override.example.com/nature.rss") not in config.rss_feeds
    assert (
        "aps-prl",
        "https://override.example.com/aps-prl.rss",
    ) not in config.rss_feeds
    assert (
        "nature-journal",
        "https://override.example.com/nature-journal.rss",
    ) not in config.rss_feeds
    assert ("custom", "https://override.example.com/custom.rss") in config.rss_feeds


def test_get_config_returns_config_from_env(monkeypatch: MonkeyPatch):
    config_module = load_config_module()
    monkeypatch.setenv("KEYWORDS", "antiferromagnet")
    config = config_module.get_config()
    assert isinstance(config, config_module.Config)
    assert config.keywords == ["antiferromagnet"]


def test_state_paths_are_defined_under_project_state_dir():
    config_module = load_config_module()
    assert config_module.STATE_DIR.name == "state"
    assert config_module.STATE_FILE.name == "seen_papers.json"
    assert config_module.STATE_FILE.parent == config_module.STATE_DIR
    # The state file should be in the project root's state directory
    assert config_module.STATE_DIR.name == "state"
    assert str(config_module.STATE_FILE).endswith("state/seen_papers.json")


def test_config_can_be_constructed_without_rss_fields():
    """Regression test: Config can be instantiated without new RSS fields."""
    config_module = load_config_module()
    # Old-style construction without RSS fields (like existing tests use)
    config = config_module.Config(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="user@example.com",
        smtp_password="secret",
        email_from="from@example.com",
        email_to="to@example.com",
        arxiv_url="https://arxiv.org/list/cond-mat/new",
        nature_url="https://www.nature.com/subjects/physical-sciences/ncomms",
        user_agent="PaperDigestTest/1.0",
        keywords=["spintronics"],
    )
    # RSS fields should have default values
    assert config.aps_prl_rss_url == "https://feeds.aps.org/rss/recent/prl.xml"
    assert config.aps_prl_section_filter == "Condensed Matter and Materials"
    assert (
        config.nature_journal_rss_url
        == "https://www.nature.com/nature/current_issue/rss"
    )
    assert config.nature_journal_category_allowlist == []
    assert config.rss_max_entries == 200
