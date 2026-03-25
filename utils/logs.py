"""Logging utility: stores LLM prompt context and raw output as JSON files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4


def save_prompt_log(
    system_prompt: str,
    user_prompt: str,
    structured_model_input: Dict[str, Any],
    raw_model_output: str,
    logs_dir: str = "logs",
) -> str:
    """Persist prompt and output payloads to a timestamped JSON log file."""
    output_dir = Path(logs_dir)
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
