# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownParameterType=false, reportUnknownMemberType=false

import json
import logging
from pathlib import Path

from paper_digest.models import Paper

logger = logging.getLogger(__name__)


class PaperStorage:
    def __init__(self, state_file: Path):
        self.state_file: Path = state_file
        self._ensure_state_file()
        self._seen_links: set[str] = self._load_seen_links()

    def _ensure_state_file(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_file.exists():
            self._write_state([])

    def _load_seen_links(self) -> set[str]:
        try:
            raw = self.state_file.read_text(encoding="utf-8")
            loaded: object = json.loads(raw)  # pyright: ignore[reportAny]
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load state file, starting fresh: %s", exc)
            self._write_state([])
            return set()

        if not isinstance(loaded, dict):
            logger.warning(
                "Failed to load state file, starting fresh: invalid structure"
            )
            self._write_state([])
            return set()

        links_obj: object = loaded.get("seen_links", [])
        if not isinstance(links_obj, list):
            return set()

        seen_links: set[str] = set()
        for link in links_obj:
            if isinstance(link, str):
                seen_links.add(link)
        return seen_links

    def _write_state(self, seen_links: list[str]) -> None:
        payload = json.dumps({"seen_links": seen_links}, indent=2)
        _ = self.state_file.write_text(payload, encoding="utf-8")

    def is_seen(self, paper: Paper) -> bool:
        link = str(paper.link)  # pyright: ignore[reportUnknownArgumentType]
        return link in self._seen_links

    def mark_seen(self, paper: Paper) -> None:
        link = str(paper.link)  # pyright: ignore[reportUnknownArgumentType]
        if link in self._seen_links:
            return

        self._seen_links.add(link)
        self._write_state(sorted(self._seen_links))
