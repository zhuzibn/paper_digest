# pyright: reportImplicitOverride=false

from dataclasses import dataclass, field
from typing import TypedDict


class PaperDict(TypedDict):
    title: str
    authors: list[str]
    link: str
    published_date: str
    source: str
    keywords_matched: list[str]


@dataclass(eq=False)
class Paper:
    title: str
    authors: list[str]
    link: str
    published_date: str
    source: str
    keywords_matched: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.link = self._normalize_link(self.link)

    @staticmethod
    def _normalize_link(link: str) -> str:
        return link.strip()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Paper):
            return False
        return self.link == other.link

    def __hash__(self) -> int:
        return hash(self.link)

    def to_dict(self) -> PaperDict:
        return {
            "title": self.title,
            "authors": self.authors,
            "link": self.link,
            "published_date": self.published_date,
            "source": self.source,
            "keywords_matched": self.keywords_matched,
        }

    @classmethod
    def from_dict(cls, data: PaperDict) -> "Paper":
        return cls(
            title=data["title"],
            authors=data["authors"],
            link=data["link"],
            published_date=data["published_date"],
            source=data["source"],
            keywords_matched=data.get("keywords_matched", []),
        )
