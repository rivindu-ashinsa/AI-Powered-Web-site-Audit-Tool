"""AI analysis module: generates compact structured insights from factual metrics."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
DEFAULT_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "420"))
DEFAULT_TEMPERATURE = float(os.getenv("OPENROUTER_TEMPERATURE", "0.1"))
RETRY_MAX_TOKENS = int(os.getenv("OPENROUTER_RETRY_MAX_TOKENS", "700"))


def _build_prompts(structured_input: Dict[str, Any]) -> tuple[str, str]:
    system_prompt = (
        "You are an expert website auditor. Return ONLY compact JSON with keys: "
        "ai_insights and recommendations. "
        "ai_insights must include seo_structure, messaging_clarity, cta_usage, content_depth, ux_concerns. "
        "Each ai_insights field must be under 35 words. "
        "recommendations must be 3 items ordered by priority (high to low). "
        "Each recommendation item must contain: priority, issue, action, rationale. "
        "Keep each recommendation concise. "
        "Ground every statement in provided metrics. No markdown. No extra keys."
    )

    user_prompt = (
        "Analyze this single-page website audit payload and produce the required JSON only:\n"
        + json.dumps(structured_input, separators=(",", ":"))
    )
    return system_prompt, user_prompt


def _safe_json_parse(raw_output: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(raw_output)
        if not isinstance(parsed, dict):
            raise ValueError("Model output must be a JSON object")
        return parsed
    except Exception as exc:
        raise ValueError(f"Failed to parse model output as JSON: {exc}") from exc


def _extract_json_object(raw_output: str) -> str:
    """Extract the largest object-like slice from model output when wrappers are present."""
    start = raw_output.find("{")
    end = raw_output.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return raw_output
    return raw_output[start : end + 1]


def _request_json(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> tuple[str, str]:
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
    """Send structured audit data to OpenRouter and return parsed AI insights and recommendations."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing. Add it to your .env file.")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    system_prompt, user_prompt = _build_prompts(structured_input)

    raw_output, finish_reason = _request_json(
        client=client,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=DEFAULT_MAX_TOKENS,
    )

    try:
        parsed = _safe_json_parse(_extract_json_object(raw_output))
    except ValueError:
        if finish_reason == "length":
            raw_output, _ = _request_json(
                client=client,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max(DEFAULT_MAX_TOKENS + 120, RETRY_MAX_TOKENS),
            )
            parsed = _safe_json_parse(_extract_json_object(raw_output))
        else:
            raise

    ai_insights = parsed.get("ai_insights", {})
    recommendations = parsed.get("recommendations", [])

    if not isinstance(ai_insights, dict):
        raise ValueError("ai_insights must be a JSON object")
    if not isinstance(recommendations, list):
        raise ValueError("recommendations must be a JSON array")

    cleaned_recommendations: List[Dict[str, Any]] = []
    for item in recommendations:
        if isinstance(item, dict):
            cleaned_recommendations.append(item)

    cleaned_recommendations = cleaned_recommendations[:5]

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "structured_model_input": structured_input,
        "raw_model_output": raw_output,
        "ai_insights": ai_insights,
        "recommendations": cleaned_recommendations,
    }
