from __future__ import annotations

from pathlib import Path

import yaml

from daily_ai_radar.models import Feed


def load_feeds(path: Path) -> list[Feed]:
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    categories = raw.get("categories", {})
    feeds: list[Feed] = []
    for category, category_config in categories.items():
        category_title = category_config["title"]
        for feed_config in category_config.get("feeds", []):
            feeds.append(
                Feed(
                    category=category,
                    category_title=category_title,
                    name=feed_config["name"],
                    url=feed_config["url"],
                )
            )

    if not feeds:
        raise ValueError(f"No feeds configured in {path}")

    return feeds
