# AI-Powered Website Audit Tool

Lightweight FastAPI application that audits a single webpage and returns factual metrics, compact AI insights, and prioritized recommendations.

## What This App Does
- Accepts one URL per audit request.
- Scrapes one page only.
- Computes deterministic metrics:
  - Total word count
  - Heading counts (`H1`, `H2`, `H3`)
  - CTA count (buttons + action-like links)
  - Internal vs external links
  - Number of images
  - Percentage of images missing alt text
  - Meta title and meta description
- Sends only structured data to the LLM for analysis.
- Returns JSON with:
  - `metrics`
  - `ai_insights`
  - `recommendations`
- Logs model interactions for auditability in `logs/`.

## Current Project Structure

```
AI-Powered-Web-site-Audit-Tool/
├─ api.py
├─ scraper.py
├─ metrics.py
├─ ai_analysis.py
├─ index.html
├─ requirements.txt
├─ .env.example
├─ .env
├─ logs/
└─ utils/
   └─ logs.py
```

## Prerequisites
- Python 3.10+
- OpenRouter API key

## Setup and Run (Windows)

1. Create and activate a virtual environment:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Configure environment:

```powershell
copy .env.example .env
```

4. Open `.env` and set your key:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-4.1-mini
OPENROUTER_MAX_TOKENS=420
OPENROUTER_RETRY_MAX_TOKENS=700
OPENROUTER_TEMPERATURE=0.1
```

5. Start the app:

```powershell
uvicorn api:app --reload
```

## How to Use (UI)

1. Open: `http://127.0.0.1:8000/`
2. Enter a full URL (for example, `https://example.com`).
3. Click `Analyze`.
4. Review results in three widget sections:
   - Metrics
   - AI Insights
   - Recommendations

The UI is served directly by FastAPI at `/`.

## How to Use (API)

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

### Audit Endpoint

```bash
curl -X POST http://127.0.0.1:8000/audit \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://example.com\"}"
```

### Response Shape

```json
{
  "metrics": {
    "url": "https://example.com",
    "word_count": 0,
    "heading_counts": {"h1": 0, "h2": 0, "h3": 0},
    "cta_count": 0,
    "internal_links": 0,
    "external_links": 0,
    "images": 0,
    "images_missing_alt_pct": 0,
    "meta_title": "",
    "meta_description": ""
  },
  "ai_insights": {
    "seo_structure": "...",
    "messaging_clarity": "...",
    "cta_usage": "...",
    "content_depth": "...",
    "ux_concerns": "..."
  },
  "recommendations": [
    {
      "priority": "high",
      "issue": "...",
      "action": "...",
      "rationale": "..."
    }
  ]
}
```

## Logs

Each audit writes a JSON log file in `logs/` containing:
- `system_prompt`
- `user_prompt`
- `structured_model_input`
- `raw_model_output`

## Efficiency Notes
- LLM input is compact and structured.
- Only a limited text excerpt is sent for analysis.
- JSON-only output is requested from the model.
- Default generation settings are low-temperature and token-bounded.
- If output is truncated, a controlled retry with higher token budget is attempted.

## Troubleshooting
- `OPENROUTER_API_KEY is missing`:
  - Set your key in `.env` and restart server.
- UI loads but Analyze fails:
  - Confirm backend is running on `http://127.0.0.1:8000`.
- 400 JSON parse errors from model:
  - Ensure retry token config is present (`OPENROUTER_RETRY_MAX_TOKENS`).
  - Retry the request once; some pages produce larger outputs.
