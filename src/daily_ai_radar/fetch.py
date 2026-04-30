from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from re import sub

import feedparser
import requests
from dateutil import parser as date_parser

from daily_ai_radar.models import Article, Feed

USER_AGENT = "daily-ai-radar/0.1 (+https://github.com/mestrovicjozo/daily-ai-radar)"


def fetch_articles(feeds: list[Feed], *, since: datetime, timeout: int = 20) -> list[Article]:
    articles: list[Article] = []
    seen_urls: set[str] = set()

    for feed in feeds:
        try:
            response = requests.get(
                feed.url,
                timeout=timeout,
                headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, text/xml"},
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Skipping feed {feed.name}: {exc}")
            continue

        parsed = feedparser.parse(response.content)
        for entry in parsed.entries:
            article = _entry_to_article(feed, entry)
            if article is None or article.published_at < since:
                continue
            if article.url in seen_urls or not _looks_english(article):
                continue
            seen_urls.add(article.url)
            articles.append(article)

    return articles


def _entry_to_article(feed: Feed, entry: feedparser.FeedParserDict) -> Article | None:
    title = _clean_text(entry.get("title", ""))
    url = entry.get("link", "")
    published_at = _parse_date(entry)
    summary = _clean_text(entry.get("summary", "") or entry.get("description", ""))

    if not title or not url or published_at is None:
        return None

    return Article(
        category=feed.category,
        category_title=feed.category_title,
        source=feed.name,
        title=title,
        url=url,
        published_at=published_at,
        summary=summary,
    )


def _parse_date(entry: feedparser.FeedParserDict) -> datetime | None:
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if not value:
            continue
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            try:
                parsed = date_parser.parse(value)
            except (TypeError, ValueError, date_parser.ParserError):
                continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    return datetime.now(UTC) - timedelta(days=1)


def _clean_text(value: str) -> str:
    without_tags = sub(r"<[^>]+>", " ", value)
    normalized = sub(r"\s+", " ", unescape(without_tags)).strip()
    return normalized


def _looks_english(article: Article) -> bool:
    text = f"{article.title} {article.summary}".lower()
    common_words = {"the", "and", "for", "with", "from", "that", "this", "has", "are", "will", "new", "ai"}
    tokens = set(sub(r"[^a-z\s]", " ", text).split())
    ascii_ratio = sum(1 for char in text if ord(char) < 128) / max(len(text), 1)
    return ascii_ratio > 0.92 and len(common_words & tokens) >= 1
