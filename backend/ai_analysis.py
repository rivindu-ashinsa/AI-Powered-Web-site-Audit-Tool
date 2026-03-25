"""AI analysis module: sends compact structured payloads to an LLM and parses JSON output."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from openai import OpenAI

BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")
load_dotenv(REPO_ROOT / ".env")

DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
DEFAULT_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "420"))
DEFAULT_RETRY_MAX_TOKENS = int(os.getenv("OPENROUTER_RETRY_MAX_TOKENS", "700"))
DEFAULT_TEMPERATURE = float(os.getenv("OPENROUTER_TEMPERATURE", "0.1"))


def _build_prompts(structured_input: Dict[str, Any]) -> Tuple[str, str]:
    system_prompt = (
        "You are an expert website auditor. Return ONLY JSON with keys: ai_insights and recommendations. "
        "ai_insights must include seo_structure, messaging_clarity, cta_usage, content_depth, ux_concerns. "
        "Each insight must be <= 35 words. "
        "recommendations must contain exactly 3 prioritized items (high to low). "
        "Each recommendation item must have: priority, issue, action, rationale. "
        "Ground all claims in provided metrics. No markdown. No extra keys."
    )

    user_prompt = (
        "Analyze this single-page website audit payload and return required JSON only:\n"
        + json.dumps(structured_input, separators=(",", ":"))
    )
    return system_prompt, user_prompt


def _extract_json_object(raw_output: str) -> str:
    start = raw_output.find("{")
    end = raw_output.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return raw_output
    return raw_output[start : end + 1]


def _safe_json_parse(raw_output: str) -> Dict[str, Any]:
    parsed = json.loads(raw_output)
    if not isinstance(parsed, dict):
        raise ValueError("Model output must be a JSON object")
    return parsed


def _request_json(client: OpenAI, system_prompt: str, user_prompt: str, max_tokens: int) -> Tuple[str, str]:
    completion = client.chat.completions.create(
        model=DEFAULT_MODEL,
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw_output = completion.choices[0].message.content or "{}"
    finish_reason = completion.choices[0].finish_reason or "unknown"
    return raw_output, finish_reason


def analyze_with_llm(structured_input: Dict[str, Any]) -> Dict[str, Any]:
    """Call OpenRouter-compatible chat completion API and return parsed audit insights."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing. Add it to backend/.env.")

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    system_prompt, user_prompt = _build_prompts(structured_input)

    raw_output, finish_reason = _request_json(client, system_prompt, user_prompt, DEFAULT_MAX_TOKENS)

    try:
        parsed = _safe_json_parse(_extract_json_object(raw_output))
    except Exception:
        if finish_reason != "length":
            raise ValueError("Failed to parse model output as JSON.")
        raw_output, _ = _request_json(client, system_prompt, user_prompt, DEFAULT_RETRY_MAX_TOKENS)
        parsed = _safe_json_parse(_extract_json_object(raw_output))

    ai_insights = parsed.get("ai_insights", {})
    recommendations = parsed.get("recommendations", [])

    if not isinstance(ai_insights, dict):
        raise ValueError("ai_insights must be a JSON object")
    if not isinstance(recommendations, list):
        raise ValueError("recommendations must be a JSON array")

    clean_recommendations: List[Dict[str, Any]] = []
    for item in recommendations:
        if isinstance(item, dict):
            clean_recommendations.append(item)

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "structured_model_input": structured_input,
        "raw_model_output": raw_output,
        "ai_insights": ai_insights,
        "recommendations": clean_recommendations[:5],
    }
