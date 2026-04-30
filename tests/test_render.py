from datetime import UTC, datetime

from daily_ai_radar.models import Article, ArticleSummary, NewsletterCopy, Selection
from daily_ai_radar.render import render_markdown


def _article(category: str, title: str) -> Article:
    titles = {
        "general_ai": "General AI",
        "llms": "LLMs",
        "ai_tools": "AI Tools",
    }
    return Article(
        category=category,
        category_title=titles[category],
        source="Example Source",
        title=title,
        url=f"https://example.com/{category}",
        published_at=datetime(2026, 4, 30, tzinfo=UTC),
        summary="Summary",
    )


def test_render_markdown_has_required_newsletter_sections():
    selection = Selection(
        winners={
            "general_ai": _article("general_ai", "General winner"),
            "llms": _article("llms", "LLM winner"),
            "ai_tools": _article("ai_tools", "Tools winner"),
        },
        honorable_mentions={
            "general_ai": _article("general_ai", "General mention"),
            "llms": _article("llms", "LLM mention"),
            "ai_tools": _article("ai_tools", "Tools mention"),
        },
    )
    copy = NewsletterCopy(
        intro="Today in AI.",
        article_summaries={
            key: ArticleSummary(
                headline=f"Headline {key}",
                summary="A concise two-sentence summary. It is readable.",
                why_it_matters="It matters because teams need signal.",
            )
            for key in (
                "general_ai_top",
                "llms_top",
                "ai_tools_top",
                "general_ai_mention",
                "llms_mention",
                "ai_tools_mention",
            )
        },
    )

    markdown = render_markdown(selection, copy, issue_date=datetime(2026, 4, 30).date())

    assert markdown.startswith("# Daily AI Radar - 2026-04-30")
    assert markdown.count("### General AI:") == 2
    assert markdown.count("### LLMs:") == 2
    assert markdown.count("### AI Tools:") == 2
    assert "## Honorable Mentions" in markdown
