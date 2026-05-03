from __future__ import annotations

import argparse
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from daily_ai_radar.config import load_feeds
from daily_ai_radar.fetch import fetch_articles
from daily_ai_radar.gemini import generate_newsletter_copy
from daily_ai_radar.models import Article, Feed
from daily_ai_radar.ranking import rank_and_select
from daily_ai_radar.render import render_markdown

MIN_ARTICLES_PER_CATEGORY = 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Daily AI Radar Markdown newsletter.")
    parser.add_argument("--config", type=Path, default=Path("config/feeds.yml"))
    parser.add_argument("--output-dir", type=Path, default=Path("digests"))
    parser.add_argument("--date", type=_parse_date, default=datetime.now(UTC).date())
    parser.add_argument("--lookback-hours", type=int, default=36)
    parser.add_argument("--max-lookback-hours", type=int, default=168)
    parser.add_argument("--model", default="gemini-2.5-flash")
    args = parser.parse_args(argv)

    feeds = load_feeds(args.config)
    articles = _fetch_with_fallback(
        feeds,
        initial_lookback_hours=args.lookback_hours,
        max_lookback_hours=args.max_lookback_hours,
    )

    source_history = _recent_source_counts(args.output_dir, now=datetime.now(UTC))
    if source_history:
        print(f"Source-diversity penalties from past 7 days: {source_history}")

    selection = rank_and_select(
        articles, now=datetime.now(UTC), source_history=source_history
    )
    newsletter_copy = generate_newsletter_copy(selection, model=args.model)
    markdown = render_markdown(selection, newsletter_copy, issue_date=args.date)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"{args.date.isoformat()}.md"
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _fetch_with_fallback(
    feeds: list[Feed],
    *,
    initial_lookback_hours: int,
    max_lookback_hours: int,
) -> list[Article]:
    required_categories = {feed.category for feed in feeds}
    lookback = max(1, initial_lookback_hours)
    max_lookback = max(lookback, max_lookback_hours)
    articles: list[Article] = []

    while True:
        since = datetime.now(UTC) - timedelta(hours=lookback)
        articles = fetch_articles(feeds, since=since)
        per_category = Counter(a.category for a in articles)
        insufficient = sorted(
            cat for cat in required_categories if per_category[cat] < MIN_ARTICLES_PER_CATEGORY
        )

        if not insufficient or lookback >= max_lookback:
            print(f"Fetched {len(articles)} articles (lookback={lookback}h).")
            if insufficient:
                print(
                    "Warning: still under-supplied after extending lookback for: "
                    f"{', '.join(insufficient)}"
                )
            return articles

        new_lookback = min(max_lookback, max(lookback * 2, lookback + 24))
        print(
            f"Insufficient articles in {insufficient} at lookback={lookback}h; "
            f"extending to {new_lookback}h."
        )
        lookback = new_lookback


def _recent_source_counts(
    output_dir: Path, *, now: datetime, days: int = 7
) -> dict[str, int]:
    if not output_dir.exists():
        return {}
    cutoff = (now - timedelta(days=days)).date()
    counts: Counter[str] = Counter()
    prefix = "**Source:** "
    for md in output_dir.glob("*.md"):
        try:
            issue_date = date.fromisoformat(md.stem)
        except ValueError:
            continue
        if issue_date < cutoff:
            continue
        for line in md.read_text(encoding="utf-8").splitlines():
            if line.startswith(prefix):
                counts[line[len(prefix):].strip()] += 1
    return dict(counts)
