from datetime import UTC, datetime, timedelta

from daily_ai_radar.models import Article
from daily_ai_radar.ranking import rank_and_select


def _article(category: str, title: str, hours_old: int, summary: str = "AI news and analysis") -> Article:
    titles = {
        "general_ai": "General AI",
        "llms": "LLMs",
        "ai_tools": "AI Tools",
    }
    return Article(
        category=category,
        category_title=titles[category],
        source="Test Feed",
        title=title,
        url=f"https://example.com/{category}/{hours_old}/{title.replace(' ', '-').lower()}",
        published_at=datetime.now(UTC) - timedelta(hours=hours_old),
        summary=summary,
    )


def test_rank_and_select_picks_top_and_honorable_for_each_category():
    articles = [
        _article("general_ai", "AI regulation update", 2, "Artificial intelligence policy and safety news"),
        _article("general_ai", "AI research note", 6, "Artificial intelligence research news"),
        _article("llms", "New LLM reasoning model", 2, "Language model reasoning and token improvements"),
        _article("llms", "Claude model update", 8, "LLM assistant update"),
        _article("ai_tools", "AI workflow automation tool", 2, "Automation app for productivity workflows"),
        _article("ai_tools", "New assistant app", 8, "AI assistant tool update"),
    ]

    selection = rank_and_select(articles, now=datetime.now(UTC))

    assert set(selection.winners) == {"general_ai", "llms", "ai_tools"}
    assert set(selection.honorable_mentions) == {"general_ai", "llms", "ai_tools"}
    assert selection.winners["llms"].title == "New LLM reasoning model"
    assert selection.honorable_mentions["ai_tools"].title == "New assistant app"
