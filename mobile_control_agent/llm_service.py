"""Robust LLM invocation service with exponential backoff, jitter, and schema validation.

Handles:
- HTTP 503 UNAVAILABLE (high demand)
- HTTP 429 RESOURCE_EXHAUSTED (rate limits)
- Transient network and socket timeouts
- Malformed JSON cleanup and schema validation
"""

import json
import os
import random
import re
import time
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types, errors


class LLMService:
    """Provides resilient multimodal inference with retry policies and structured JSON output."""

    def __init__(self, model_name: Optional[str] = None, max_retries: int = 4):
        self.model_name = model_name or os.environ.get("MOBILE_AGENT_MODEL", "gemini-3.1-flash-lite")
        self.max_retries = max_retries
        self.client = genai.Client()

    def generate_action(
        self,
        contents: List[Any],
        system_instruction: str,
        temperature: float = 0.2,
    ) -> Optional[Dict[str, Any]]:
        """Invokes the model with exponential backoff and jitter.

        Returns validated JSON dict or None if all retries are exhausted.
        """
        base_delay = 2.0

        for attempt in range(self.max_retries + 1):
            try:
                resp = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=temperature,
                    ),
                )
                if not resp or not resp.text:
                    raise ValueError("Empty response received from model.")

                parsed = self._parse_json(resp.text)
                if parsed and isinstance(parsed, dict) and "action" in parsed:
                    return parsed
                else:
                    raise ValueError(f"Response missing required 'action' key: {resp.text[:100]}")

            except Exception as e:
                err_str = str(e)
                is_transient = any(
                    kw in err_str.lower()
                    for kw in (
                        "503",
                        "unavailable",
                        "high demand",
                        "429",
                        "resource_exhausted",
                        "quota",
                        "timeout",
                        "connection reset",
                        "server error",
                    )
                )

                if is_transient and attempt < self.max_retries:
                    delay = (base_delay * (2 ** attempt)) + random.uniform(0.5, 1.5)
                    print(
                        f"[LLM Warning] Transient API error ({e.__class__.__name__}). "
                        f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})..."
                    )
                    time.sleep(delay)
                    continue

                print(f"[LLM Error] Non-retryable error or retries exhausted: {e}")
                return None

        return None

    @staticmethod
    def _parse_json(text: str) -> Optional[Dict[str, Any]]:
        """Cleans and extracts JSON object from model response text."""
        cleaned = text.strip()

        # Remove markdown code fences
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        # Find first { and last }
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback regex for common JSON trailing comma syntax error
            try:
                fixed = re.sub(r",\s*([}\]])", r"\1", cleaned)
                return json.loads(fixed)
            except Exception:
                return None
