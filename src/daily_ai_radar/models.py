from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Feed:
    category: str
    category_title: str
    name: str
    url: str


@dataclass(frozen=True)
class Article:
    category: str
    category_title: str
    source: str
    title: str
    url: str
    published_at: datetime
    summary: str
    score: float = 0.0


@dataclass(frozen=True)
class Selection:
    winners: dict[str, Article]
    honorable_mentions: dict[str, Article]


@dataclass(frozen=True)
class ArticleSummary:
    headline: str
    summary: str
    why_it_matters: str


@dataclass(frozen=True)
class NewsletterCopy:
    intro: str
    article_summaries: dict[str, ArticleSummary]
