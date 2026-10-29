"""Atomic metadata ledger for paper discovery and review decisions."""

import json
import logging
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import TypedDict

from paper_digest.identity import identity_keys
from paper_digest.identity import paper_id
from paper_digest.models import Paper
from paper_digest.models import PaperDict

logger = logging.getLogger(__name__)


class Decision(TypedDict):
    status: str
    at: str


class PaperRecord(TypedDict):
    paper: PaperDict
    aliases: list[str]
    discovered_at: str
    decision: str
    decisions: list[Decision]


class SourceRecord(TypedDict):
    url: str
    last_attempt: str
    last_success: str
    status: str
    error: str
    matched: int


class TrackingState(TypedDict):
    version: int
    seen_links: list[str]
    papers: dict[str, PaperRecord]
    sources: dict[str, SourceRecord]


def utc_now() -> str:
    """Return a timezone-aware timestamp for state events."""
    return datetime.now(timezone.utc).isoformat()


def _strings(value: object) -> bool:
    """Check a list of strings at the persisted-data boundary."""
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


class PaperStorage:
    def __init__(self, state_file: Path) -> None:
        """Load existing history, preserving malformed files for manual recovery."""
        self.state_file: Path = state_file
        self.state: TrackingState = {
            "version": 3, "seen_links": [], "papers": {}, "sources": {},
        }
        try:
            if state_file.exists():
                loaded = json.loads(state_file.read_text(encoding="utf-8"))
                self._validate(loaded)
                if loaded.get("version") == 2:
                    # Keep all paper identities and decisions when retiring delivery.
                    loaded["version"] = 3
                    loaded.pop("delivery_error", None)
                    for record in loaded["papers"].values():
                        record.pop("emailed_at", None)
                self.state.update(loaded)
            else:
                self.save()
        except (OSError, ValueError, TypeError):
            logger.exception("Cannot load tracking state; existing file preserved")
            raise
        self._legacy_keys: set[str] = {
            key for link in self.state["seen_links"] for key in identity_keys(link)
        }
        self._aliases: dict[str, str] = {}
        for item_id, record in self.state["papers"].items():
            for key in record["aliases"]:
                if key in self._aliases and self._aliases[key] != item_id:
                    raise ValueError("Conflicting paper aliases in tracking state")
                self._aliases[key] = item_id

    @staticmethod
    def _validate(data: object) -> None:
        """Validate both legacy exclusions and versioned tracking records."""
        if not isinstance(data, dict) or not _strings(data.get("seen_links")):
            raise ValueError("Invalid tracking state: expected seen_links list")
        if set(data) == {"seen_links"}:
            return
        if (data.get("version") not in (2, 3)
                or not isinstance(data.get("papers"), dict)
                or not isinstance(data.get("sources"), dict)):
            raise ValueError("Unsupported or incomplete tracking state")
        for item_id, record in data["papers"].items():
            if not isinstance(record, dict) or not isinstance(item_id, str):
                raise ValueError("Invalid paper record")
            paper = record.get("paper")
            if (not isinstance(paper, dict)
                    or not all(isinstance(paper.get(key), str) for key in
                               ("title", "link", "published_date", "source", "doi"))
                    or not paper["link"] or not _strings(paper.get("authors"))
                    or not _strings(paper.get("keywords_matched"))
                    or not _strings(record.get("aliases")) or not record["aliases"]
                    or not isinstance(record.get("decision"), str)
                    or record["decision"] not in {"pending", "accepted", "skipped"}
                    or not isinstance(record.get("discovered_at"), str)
                    or not isinstance(record.get("decisions"), list)):
                raise ValueError("Invalid paper metadata or decision")
            for event in record["decisions"]:
                if (not isinstance(event, dict)
                        or not isinstance(event.get("status"), str)
                        or event["status"] not in {"accepted", "skipped"}
                        or not isinstance(event.get("at"), str)):
                    raise ValueError("Invalid decision history")
            expected = record["decisions"][-1]["status"] if record["decisions"] else "pending"
            if expected != record["decision"]:
                raise ValueError("Decision does not match recorded history")
        for record in data["sources"].values():
            if (not isinstance(record, dict)
                    or not all(isinstance(record.get(key), str) for key in
                               ("url", "last_attempt", "last_success", "status", "error"))
                    or record["status"] not in {"success", "failed", "partial"}
                    or not isinstance(record.get("matched"), int)):
                raise ValueError("Invalid source outcome")

    def save(self) -> None:
        """Replace the whole ledger atomically, never leaving a partial JSON file."""
        temporary: Path | None = None
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.state_file.parent,
                prefix=self.state_file.name + ".", suffix=".tmp", delete=False,
            ) as handle:
                temporary = Path(handle.name)
                json.dump(self.state, handle, indent=2, ensure_ascii=False)
                _ = handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            _ = temporary.replace(self.state_file)
        except OSError:
            logger.exception("Failed to save tracking state")
            raise
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def discover(self, paper: Paper, at: str) -> str | None:
        """Remember metadata once; return its ID or None for a legacy exclusion."""
        keys = identity_keys(paper.link, paper.doi)
        matches = {self._aliases[key] for key in keys if key in self._aliases}
        if len(matches) > 1:
            raise ValueError("Conflicting paper identities; reconcile state before retrying")
        if matches:
            item_id = matches.pop()
            record = self.state["papers"][item_id]
            record["aliases"] = sorted(set(record["aliases"]) | set(keys))
            if not record["paper"]["doi"] and paper.doi:
                record["paper"]["doi"] = paper.doi
        elif self._legacy_keys.intersection(keys):
            return None
        else:
            item_id = paper_id(paper.link, paper.doi)
            self.state["papers"][item_id] = {
                "paper": paper.to_dict(), "aliases": keys,
                "discovered_at": at, "decision": "pending",
                "decisions": [],
            }
        for key in keys:
            self._aliases[key] = item_id
        return item_id

    def record_source(
        self, source: str, url: str, at: str, status: str, error: str, matched: int,
    ) -> None:
        """Advance successful check timestamps only for a complete source result."""
        previous = self.state["sources"].get(source)
        last_success = previous["last_success"] if previous and previous["url"] == url else ""
        self.state["sources"][source] = {
            "url": url, "last_attempt": at,
            "last_success": at if status == "success" else last_success,
            "status": status, "error": error, "matched": matched,
        }

    def decide(self, item_id: str, decision: str) -> None:
        """Record an explicit selection by exact ID."""
        if decision not in {"accepted", "skipped"}:
            raise ValueError("Decision must be accepted or skipped")
        if item_id not in self.state["papers"]:
            raise ValueError(f"Unknown paper ID: {item_id}")
        record = self.state["papers"][item_id]
        record["decision"] = decision
        record["decisions"].append({"status": decision, "at": utc_now()})
        self.save()


@contextmanager
def locked_storage(state_file: Path) -> Iterator[PaperStorage]:
    """Serialize local runs and decisions; stale locks require manual inspection."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    lock = state_file.with_suffix(state_file.suffix + ".lock")
    try:
        handle = lock.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise RuntimeError(f"Tracking state is locked: {lock}") from exc
    try:
        with handle:
            _ = handle.write(f"pid={os.getpid()}\n")
        yield PaperStorage(state_file)
    finally:
        lock.unlink()
