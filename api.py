"""FastAPI entrypoint: exposes a lightweight /audit endpoint for single-page website audits."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

from ai_analysis import analyze_with_llm
from metrics import compute_metrics
from scraper import scrape_page
from utils.logs import save_prompt_log

app = FastAPI(title="AI Website Audit Tool", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"


class AuditRequest(BaseModel):
    url: HttpUrl


@app.get("/", include_in_schema=False)
def serve_ui() -> FileResponse:
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(INDEX_FILE)


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/audit")
def audit_website(payload: AuditRequest) -> Dict[str, Any]:
    """Run a complete single-page audit and return JSON metrics plus AI recommendations."""
    try:
        scraped = scrape_page(str(payload.url))
        metrics = compute_metrics(
            soup=scraped["soup"],
            text=scraped["text"],
            base_url=scraped["final_url"],
        )

        structured_input = {
            "url": metrics["url"],
            "metrics": metrics,
            # Keep model context compact for lower token usage.
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
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audit failed: {exc}") from exc
