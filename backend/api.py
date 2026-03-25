"""FastAPI backend: exposes health and audit endpoints for the AI Website Audit Tool."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

try:
    from .ai_analysis import analyze_with_llm
    from .metrics import compute_metrics
    from .scraper import scrape_page
    from .utils.logs import save_prompt_log
except ImportError:
    from ai_analysis import analyze_with_llm
    from metrics import compute_metrics
    from scraper import scrape_page
    from utils.logs import save_prompt_log

app = FastAPI(title="AI Website Audit Tool API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuditRequest(BaseModel):
    url: HttpUrl


def _run_audit(url: str) -> Dict[str, Any]:
    scraped = scrape_page(url)
    metrics = compute_metrics(
        soup=scraped["soup"],
        text=scraped["text"],
        base_url=scraped["final_url"],
    )

    structured_input = {
        "url": metrics["url"],
        "metrics": metrics,
        "text_excerpt": scraped["text"][:1500],
    }

    ai_result = analyze_with_llm(structured_input)

    save_prompt_log(
        system_prompt=ai_result["system_prompt"],
        user_prompt=ai_result["user_prompt"],
        structured_model_input=ai_result["structured_model_input"],
        raw_model_output=ai_result["raw_model_output"],
    )

    return {
        "metrics": metrics,
        "ai_insights": ai_result["ai_insights"],
        "recommendations": ai_result["recommendations"],
    }


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health endpoint for uptime checks."""
    return {"status": "ok"}


@app.get("/audit")
def audit_website_get(url: HttpUrl = Query(..., description="Target page URL")) -> Dict[str, Any]:
    """Audit endpoint for query-string based clients (e.g., static frontend)."""
    try:
        return _run_audit(str(url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audit failed: {exc}") from exc


@app.post("/audit")
def audit_website_post(payload: AuditRequest) -> Dict[str, Any]:
    """Audit endpoint for JSON body clients."""
    try:
        return _run_audit(str(payload.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audit failed: {exc}") from exc
