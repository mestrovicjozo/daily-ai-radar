# Daily AI Radar

Daily AI Radar generates a polished Markdown newsletter every morning with:

1. One top article about **General AI**
2. One top article about **LLMs**
3. One top article about **AI Tools**
4. Honorable mentions with the next-best article from each category

The digest is produced by a scheduled GitHub Actions workflow. It fetches real
English-language articles from RSS/Atom feeds, ranks recent candidates, uses
Google Gemini to summarize and polish the issue, then commits the generated
Markdown back into the repository.

Generated newsletters are written to [`digests/`](digests/).

## Repository Layout

```txt
daily-ai-radar/
├── .github/workflows/daily-ai-radar.yml
├── config/feeds.yml
├── digests/
├── src/daily_ai_radar/
└── tests/
```

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Required Secret

Add this GitHub Actions repository secret:

```txt
GEMINI_API_KEY
```

The workflow uses the secret to call the Google Gemini API.

## Manual Run

```bash
python -m daily_ai_radar --date 2026-04-30
```

Without `--date`, the current UTC date is used.
