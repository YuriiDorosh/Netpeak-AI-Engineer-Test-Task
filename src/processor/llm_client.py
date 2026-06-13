import json
import logging
import os
from typing import Any

import httpx

from src.processor.validator import RequestAnalysis

logger = logging.getLogger(__name__)

LLM_URL = os.getenv("LLAMA_CPP_URL", "http://llm:8080")
MAX_RETRIES = 2
REQUEST_TIMEOUT = 120.0

_SYSTEM_PROMPT = """\
You are an AI request classifier for an AI solutions team at a digital marketing agency.
Analyze the internal request (written in Ukrainian) and return a JSON object.

Return ONLY valid JSON with these exact fields — no markdown, no explanation:
{
  "category": one of exactly: "автоматизація" | "інтеграція" | "звіт/аналітика" | "баг/підтримка" | "питання/консультація" | "поза скоупом",
  "target_department": string (department name) or null if unclear,
  "priority": exactly one of: "low" | "medium" | "high",
  "short_summary": string (one sentence, max 120 chars, in Ukrainian),
  "requested_actions": array of strings (concrete actions requested; empty array if none),
  "needs_clarification": boolean (true if too vague to act on without follow-up),
  "confidence_score": float 0.0–1.0 (your confidence in the classification)
}

Priority rules:
  high   — urgent language present: ГОРИТЬ, терміново, сьогодні, ASAP, негайно
  low    — theoretical question, no deadline, no concrete action needed
  medium — everything else
"""

_SCHEMA = RequestAnalysis.model_json_schema()


def _build_payload(user_text: str, use_json_schema: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": "qwen",
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": 512,
        "temperature": 0.05,
    }
    if use_json_schema:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "request_analysis",
                "strict": True,
                "schema": _SCHEMA,
            },
        }
    else:
        payload["response_format"] = {"type": "json_object"}
    return payload


async def analyze_request(
    row: dict[str, Any],
    client: httpx.AsyncClient,
) -> RequestAnalysis:
    user_text = row["raw_text"]
    url = f"{LLM_URL}/v1/chat/completions"
    use_json_schema = True

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            payload = _build_payload(user_text, use_json_schema)
            resp = await client.post(url, json=payload, timeout=REQUEST_TIMEOUT)

            if resp.status_code == 422 and use_json_schema:
                logger.warning("Server rejected json_schema mode, switching to json_object")
                use_json_schema = False
                continue

            resp.raise_for_status()
            data = resp.json()
            content: str = data["choices"][0]["message"]["content"]
            return RequestAnalysis.model_validate_json(content)

        except Exception as exc:
            last_error = exc
            logger.warning(
                "Attempt %d/%d failed for row %s: %s",
                attempt, MAX_RETRIES, row.get("id"), exc,
            )

    raise ValueError(
        f"All {MAX_RETRIES} attempts failed for row {row.get('id')}: {last_error}"
    )
