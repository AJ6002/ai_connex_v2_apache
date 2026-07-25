"""
intelligence/llm_client.py - Structured JSON LLM Client (Ollama)
=================================================================
Single choke point for every LLM call in the intelligence layer.

Design contract:
  - All calls request STRUCTURED JSON output (Ollama format="json").
  - Malformed JSON is repaired (fenced block extraction, brace balancing)
    before giving up.
  - Model fallback chain: tries each model in order until one returns
    parseable JSON.
  - Failures are surfaced explicitly via LLMUnavailableError, never silently
    swallowed - callers decide whether to degrade or abort.
  - No dataset-specific knowledge lives here. Prompts are supplied by callers.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_MODEL_CHAIN = [
    "gpt-oss:120b-cloud",
    "qwen3-coder:480b-cloud",
    "qwen2.5-coder:7b",
]


class LLMUnavailableError(RuntimeError):
    """Raised when no model in the chain produced a usable JSON response."""


@dataclass
class LLMResponse:
    data: Dict[str, Any]
    model_used: str
    raw_text: str
    duration_seconds: float


#: Env var that force-disables all LLM usage (used by tests and air-gapped runs).
DISABLE_ENV_VAR = "AICONNEX_DISABLE_LLM"

#: Process-wide availability cache keyed by server URL, so repeated compiler
#: runs in one process do not re-probe (and re-timeout) on every construction.
_AVAILABILITY_CACHE: Dict[str, bool] = {}

AVAILABILITY_PROBE_TIMEOUT = 4


def llm_disabled_by_env() -> bool:
    """True when the environment explicitly disables LLM usage."""
    return os.getenv(DISABLE_ENV_VAR, "").strip().lower() in ("1", "true", "yes", "on")


def reset_availability_cache() -> None:
    """Clear the process-wide availability cache (used by tests)."""
    _AVAILABILITY_CACHE.clear()


class LLMClient:
    """
    JSON-mode Ollama client with model fallback and response repair.

    Parameters
    ----------
    ollama_url : str, optional
        Defaults to env OLLAMA_HOST or http://localhost:11434.
    model_chain : list of str, optional
        Models tried in order. First one returning parseable JSON wins.
    timeout : int
        Per-request timeout in seconds.
    num_ctx : int
        Context window requested from the model.
    """

    def __init__(
        self,
        ollama_url: Optional[str] = None,
        model_chain: Optional[List[str]] = None,
        timeout: int = 180,
        num_ctx: int = 16384,
    ) -> None:
        self.ollama_url = (ollama_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self.model_chain = model_chain or list(DEFAULT_MODEL_CHAIN)
        self.timeout = timeout
        self.num_ctx = num_ctx

    # -- Public API ---------------------------------------------------------

    def is_available(self, force_recheck: bool = False) -> bool:
        """
        Ping the Ollama server, caching the result process-wide per URL.

        Returns False immediately when AICONNEX_DISABLE_LLM is set.
        """
        if llm_disabled_by_env():
            return False

        if not force_recheck and self.ollama_url in _AVAILABILITY_CACHE:
            return _AVAILABILITY_CACHE[self.ollama_url]

        available = False
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=AVAILABILITY_PROBE_TIMEOUT) as response:
                available = response.status == 200
        except Exception as e:
            logger.warning(f"[LLMClient] Ollama not reachable at {self.ollama_url}: {e}")

        _AVAILABILITY_CACHE[self.ollama_url] = available
        return available

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_attempts_per_model: int = 2,
    ) -> LLMResponse:
        """
        Request a JSON object from the model chain.

        Raises
        ------
        LLMUnavailableError
            If every model in the chain failed to produce parseable JSON.
        """
        errors: List[str] = []

        for model in self.model_chain:
            for attempt in range(1, max_attempts_per_model + 1):
                t0 = time.time()
                try:
                    raw_text = self._post_generate(
                        model=model,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=temperature,
                    )
                except Exception as e:
                    errors.append(f"{model} attempt {attempt}: transport error {e}")
                    logger.debug(f"[LLMClient] {model} attempt {attempt} transport error: {e}")
                    continue

                parsed = self._parse_json_lenient(raw_text)
                if parsed is not None:
                    duration = round(time.time() - t0, 3)
                    logger.info(f"[LLMClient] '{model}' returned valid JSON in {duration}s")
                    return LLMResponse(
                        data=parsed,
                        model_used=model,
                        raw_text=raw_text,
                        duration_seconds=duration,
                    )

                errors.append(f"{model} attempt {attempt}: unparseable JSON")
                logger.debug(f"[LLMClient] {model} attempt {attempt}: unparseable response")

        raise LLMUnavailableError(
            "No model produced parseable JSON. Attempts: " + " | ".join(errors[:8])
        )

    # -- Internals ---------------------------------------------------------

    def _post_generate(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ) -> str:
        payload = {
            "model": model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "format": "json",  # Ollama structured-output mode
            "options": {
                "temperature": temperature,
                "num_ctx": self.num_ctx,
            },
        }

        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))

        return body.get("response", "") or ""

    @staticmethod
    def _parse_json_lenient(text: str) -> Optional[Dict[str, Any]]:
        """
        Best-effort JSON object extraction.

        Order of attempts:
          1. Direct json.loads
          2. Fenced ```json block extraction
          3. First balanced {...} span
        """
        if not text or not text.strip():
            return None

        candidate = text.strip()

        # 1. Direct parse
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else {"result": parsed}
        except json.JSONDecodeError:
            pass

        # 2. Fenced code block
        fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL)
        if fence_match:
            inner = fence_match.group(1).strip()
            try:
                parsed = json.loads(inner)
                return parsed if isinstance(parsed, dict) else {"result": parsed}
            except json.JSONDecodeError:
                candidate = inner

        # 3. First balanced brace span
        start = candidate.find("{")
        if start == -1:
            return None

        depth = 0
        in_string = False
        escaped = False
        for idx in range(start, len(candidate)):
            ch = candidate[idx]

            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue

            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    span = candidate[start : idx + 1]
                    try:
                        parsed = json.loads(span)
                        return parsed if isinstance(parsed, dict) else {"result": parsed}
                    except json.JSONDecodeError:
                        return None

        return None
