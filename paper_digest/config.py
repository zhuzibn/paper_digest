import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_ = load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"
STATE_FILE = STATE_DIR / "seen_papers.json"


@dataclass
class Config:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    email_from: str
    email_to: str
    arxiv_url: str
    nature_url: str
    user_agent: str
    keywords: list[str]

    @classmethod
    def from_env(cls) -> "Config":
        keywords_raw = os.getenv("KEYWORDS", "")
        keywords = [
            part.strip().lower() for part in keywords_raw.split(",") if part.strip()
        ]

        return cls(
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            email_from=os.getenv("EMAIL_FROM", ""),
            email_to=os.getenv("EMAIL_TO", ""),
            arxiv_url=os.getenv("ARXIV_URL", "https://arxiv.org/list/cond-mat/new"),
            nature_url=os.getenv(
                "NATURE_URL", "https://www.nature.com/subjects/physical-sciences/ncomms"
            ),
            user_agent=os.getenv(
                "USER_AGENT", "Mozilla/5.0 (compatible; PaperDigest/1.0)"
            ),
            keywords=keywords,
        )


def get_config() -> Config:
    return Config.from_env()
