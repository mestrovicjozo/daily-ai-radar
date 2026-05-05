from __future__ import annotations

import json
import os
import time

from google import genai
from google.genai import errors as genai_errors

from daily_ai_radar.models import Article, ArticleSummary, NewsletterCopy, Selection

DEFAULT_MODEL = "gemini-2.5-flash"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 5
INITIAL_BACKOFF_SECONDS = 4.0
BACKOFF_MULTIPLIER = 2.0
FALLBACK_MODELS = ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash")


def generate_newsletter_copy(selection: Selection, *, model: str = DEFAULT_MODEL) -> NewsletterCopy:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required to generate the newsletter")

    articles = _selected_articles(selection)
    prompt = _build_prompt(articles)

    client = genai.Client(api_key=api_key)
    response = _generate_with_retry(client, prompt, model=model)
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


def _generate_with_retry(client: "genai.Client", prompt: str, *, model: str):
    models_to_try: list[str] = [model]
    for fallback in FALLBACK_MODELS:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    last_error: Exception | None = None
    for current_model in models_to_try:
        backoff = INITIAL_BACKOFF_SECONDS
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return client.models.generate_content(model=current_model, contents=prompt)
            except genai_errors.APIError as exc:
                status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                last_error = exc
                if status not in RETRYABLE_STATUS:
                    raise
                if attempt == MAX_ATTEMPTS:
                    print(
                        f"Gemini {current_model} returned {status} after {attempt} attempts; "
                        "trying next fallback model."
                    )
                    break
                print(
                    f"Gemini {current_model} returned {status} "
                    f"(attempt {attempt}/{MAX_ATTEMPTS}); retrying in {backoff:.1f}s."
                )
                time.sleep(backoff)
                backoff *= BACKOFF_MULTIPLIER

    assert last_error is not None
    raise RuntimeError(
        f"Gemini API was unavailable after retries across models {models_to_try}: {last_error}"
    ) from last_error


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
