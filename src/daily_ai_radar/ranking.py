from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from daily_ai_radar.models import Article, Selection

CATEGORY_KEYWORDS = {
    "general_ai": {
        "ai",
        "artificial intelligence",
        "research",
        "policy",
        "safety",
        "robotics",
        "startup",
        "regulation",
    },
    "llms": {
        "llm",
        "language model",
        "gpt",
        "claude",
        "gemini",
        "openai",
        "anthropic",
        "mistral",
        "llama",
        "reasoning",
        "token",
    },
    "ai_tools": {
        "tool",
        "app",
        "agent",
        "workflow",
        "automation",
        "productivity",
        "github copilot",
        "notion",
        "zapier",
        "assistant",
    },
}


SOURCE_REPEAT_PENALTY = 0.6


def rank_and_select(
    articles: list[Article],
    *,
    now: datetime | None = None,
    source_history: dict[str, int] | None = None,
) -> Selection:
    now = now or datetime.now(UTC)
    history = source_history or {}
    ranked_by_category: dict[str, list[Article]] = defaultdict(list)

    for article in articles:
        ranked_by_category[article.category].append(
            _score_article(article, now=now, source_history=history)
        )

    winners: dict[str, Article] = {}
    honorable_mentions: dict[str, Article] = {}

    for category, ranked in ranked_by_category.items():
        ranked.sort(key=lambda item: item.score, reverse=True)
        if not ranked:
            continue
        winner = ranked[0]
        winners[category] = winner
        mention = next((c for c in ranked[1:] if c.source != winner.source), None)
        if mention is None and len(ranked) > 1:
            mention = ranked[1]
        if mention is not None:
            honorable_mentions[category] = mention

    missing = {"general_ai", "llms", "ai_tools"} - winners.keys()
    if missing:
        missing_names = ", ".join(sorted(missing))
        raise RuntimeError(f"Not enough recent articles to select winners for: {missing_names}")

    missing_mentions = {"general_ai", "llms", "ai_tools"} - honorable_mentions.keys()
    if missing_mentions:
        missing_names = ", ".join(sorted(missing_mentions))
        raise RuntimeError(f"Not enough recent articles to select honorable mentions for: {missing_names}")

    return Selection(winners=winners, honorable_mentions=honorable_mentions)


def _score_article(
    article: Article,
    *,
    now: datetime,
    source_history: dict[str, int],
) -> Article:
    age_hours = max((now - article.published_at).total_seconds() / 3600, 0)
    recency_score = max(0, 48 - age_hours) / 48

    text = f"{article.title} {article.summary}".lower()
    keyword_score = sum(1 for keyword in CATEGORY_KEYWORDS.get(article.category, set()) if keyword in text)
    title_bonus = 0.25 if any(keyword in article.title.lower() for keyword in CATEGORY_KEYWORDS.get(article.category, set())) else 0
    detail_score = min(len(article.summary) / 500, 1)
    repeat_penalty = SOURCE_REPEAT_PENALTY * source_history.get(article.source, 0)

    score = (
        (recency_score * 3.0)
        + (keyword_score * 0.7)
        + title_bonus
        + (detail_score * 0.5)
        - repeat_penalty
    )
    return Article(
        category=article.category,
        category_title=article.category_title,
        source=article.source,
        title=article.title,
        url=article.url,
        published_at=article.published_at,
        summary=article.summary,
        score=round(score, 4),
    )
