"""Prompt logging utility: persists model prompts/inputs/outputs to JSON files."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4


def _default_logs_dir() -> Path:
    env_value = os.getenv("AUDIT_LOGS_DIR", "").strip()
    if env_value:
        return Path(env_value)
    # backend/utils/logs.py -> repo root/logs
    return Path(__file__).resolve().parents[2] / "logs"


def save_prompt_log(
    system_prompt: str,
    user_prompt: str,
    structured_model_input: Dict[str, Any],
    raw_model_output: str,
    logs_dir: Path | None = None,
) -> str:
    """Save prompt log payload to a timestamped JSON file and return path string."""
    output_dir = logs_dir or _default_logs_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"audit_{timestamp}_{uuid4().hex[:8]}.json"
    file_path = output_dir / filename

    payload = {
        "timestamp_utc": timestamp,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "structured_model_input": structured_model_input,
        "raw_model_output": raw_model_output,
    }

    file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return str(file_path)
