import sys
from importlib import import_module
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def load_config_module():
    return import_module("paper_digest.config")


def test_env_example_exists():
    assert Path(".env.example").exists()


def test_requirements_has_core_dependencies():
    content = Path("requirements.txt").read_text(encoding="utf-8")
    assert "requests" in content
    assert "beautifulsoup4" in content


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
    monkeypatch.setenv("USER_AGENT", "paper-digest-test")
    monkeypatch.setenv("KEYWORDS", " Spintronics,  MRAM ,spin-orbit torque,,   ")

    config = config_module.Config.from_env()

    assert config.smtp_host == "smtp.example.com"
    assert config.smtp_port == 2525
    assert config.keywords == ["spintronics", "mram", "spin-orbit torque"]


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
    assert str(config_module.STATE_FILE).endswith("paper_digest/state/seen_papers.json")
