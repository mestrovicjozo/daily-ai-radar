from __future__ import annotations

from datetime import date

from daily_ai_radar.models import Article, NewsletterCopy, Selection

CATEGORY_ORDER = ("general_ai", "llms", "ai_tools")


def render_markdown(selection: Selection, copy: NewsletterCopy, *, issue_date: date) -> str:
    lines = [
        f"# Daily AI Radar - {issue_date.isoformat()}",
        "",
        copy.intro,
        "",
        "## Top Stories",
        "",
    ]

    for category in CATEGORY_ORDER:
        article = selection.winners[category]
        article_copy = copy.article_summaries[f"{category}_top"]
        lines.extend(_render_article(article, article_copy.headline, article_copy.summary, article_copy.why_it_matters))

    lines.extend(["## Honorable Mentions", ""])
    for category in CATEGORY_ORDER:
        article = selection.honorable_mentions[category]
        article_copy = copy.article_summaries[f"{category}_mention"]
        lines.extend(
            [
                f"### {article.category_title}: [{article_copy.headline}]({article.url})",
                "",
                f"**Source:** {article.source}",
                "",
                article_copy.summary,
                "",
                f"**Why it matters:** {article_copy.why_it_matters}",
                "",
            ]
        )

    lines.extend(
        [
            "---",
            "",
            "_Generated automatically by Daily AI Radar._",
            "",
        ]
    )
    return "\n".join(lines)


def _render_article(article: Article, headline: str, summary: str, why_it_matters: str) -> list[str]:
    return [
        f"### {article.category_title}: [{headline}]({article.url})",
        "",
        f"**Source:** {article.source}",
        "",
        summary,
        "",
        f"**Why it matters:** {why_it_matters}",
        "",
    ]
