from __future__ import annotations

import argparse
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from daily_ai_radar.config import load_feeds
from daily_ai_radar.fetch import fetch_articles
from daily_ai_radar.gemini import generate_newsletter_copy
from daily_ai_radar.ranking import rank_and_select
from daily_ai_radar.render import render_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Daily AI Radar Markdown newsletter.")
    parser.add_argument("--config", type=Path, default=Path("config/feeds.yml"))
    parser.add_argument("--output-dir", type=Path, default=Path("digests"))
    parser.add_argument("--date", type=_parse_date, default=datetime.now(UTC).date())
    parser.add_argument("--lookback-hours", type=int, default=36)
    parser.add_argument("--model", default="gemini-2.5-flash")
    args = parser.parse_args(argv)

    since = datetime.now(UTC) - timedelta(hours=args.lookback_hours)

    feeds = load_feeds(args.config)
    articles = fetch_articles(feeds, since=since)
    print(f"Fetched {len(articles)} recent articles.")

    selection = rank_and_select(articles, now=datetime.now(UTC))
    newsletter_copy = generate_newsletter_copy(selection, model=args.model)
    markdown = render_markdown(selection, newsletter_copy, issue_date=args.date)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"{args.date.isoformat()}.md"
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)
