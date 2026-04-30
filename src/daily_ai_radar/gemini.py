from __future__ import annotations

import json
import os

from google import genai

from daily_ai_radar.models import Article, ArticleSummary, NewsletterCopy, Selection

DEFAULT_MODEL = "gemini-2.5-flash"


def generate_newsletter_copy(selection: Selection, *, model: str = DEFAULT_MODEL) -> NewsletterCopy:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required to generate the newsletter")

    articles = _selected_articles(selection)
    prompt = _build_prompt(articles)

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=prompt)
    text = (response.text or "").strip()
    data = _parse_json_response(text)

    summaries: dict[str, ArticleSummary] = {}
    for item in data["articles"]:
        summaries[item["id"]] = ArticleSummary(
            headline=item["headline"].strip(),
            summary=item["summary"].strip(),
            why_it_matters=item["why_it_matters"].strip(),
        )

    expected_ids = {article_id for article_id, _ in articles}
    missing = expected_ids - summaries.keys()
    if missing:
        raise RuntimeError(f"Gemini response omitted summaries for: {', '.join(sorted(missing))}")

    return NewsletterCopy(intro=data["intro"].strip(), article_summaries=summaries)


def _selected_articles(selection: Selection) -> list[tuple[str, Article]]:
    ordered: list[tuple[str, Article]] = []
    for category in ("general_ai", "llms", "ai_tools"):
        ordered.append((f"{category}_top", selection.winners[category]))
    for category in ("general_ai", "llms", "ai_tools"):
        ordered.append((f"{category}_mention", selection.honorable_mentions[category]))
    return ordered


def _build_prompt(articles: list[tuple[str, Article]]) -> str:
    payload = [
        {
            "id": article_id,
            "category": article.category_title,
            "source": article.source,
            "title": article.title,
            "url": article.url,
            "published_at": article.published_at.isoformat(),
            "feed_summary": article.summary[:1200],
        }
        for article_id, article in articles
    ]

    return f"""
You are the editor of a professional daily AI newsletter.

Write concise, readable English copy for the selected real articles. Do not invent facts beyond the provided titles and feed summaries. Keep the tone polished and newsletter-like.

Return only valid JSON with this exact shape:
{{
  "intro": "One sentence previewing the issue.",
  "articles": [
    {{
      "id": "article id from input",
      "headline": "Short newsletter headline, not clickbait",
      "summary": "2 sentences summarizing the article",
      "why_it_matters": "1 sentence explaining practical significance"
    }}
  ]
}}

Articles:
{json.dumps(payload, ensure_ascii=False, indent=2)}
""".strip()


def _parse_json_response(text: str) -> dict:
    cleaned = text
    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").removesuffix("```").strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").removesuffix("```").strip()

    data = json.loads(cleaned)
    if not isinstance(data, dict) or "intro" not in data or "articles" not in data:
        raise RuntimeError("Gemini returned an invalid newsletter payload")
    return data
