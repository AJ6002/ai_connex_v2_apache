"""
aiconnex_agent/llm.py - LLM Backend Switch (Ollama / OpenAI)
================================================================
Provides a single entry point, get_llm(), that returns the configured LLM
client for LangGraph agent node calls. The backend is selected via the
AICONNEX_LLM_BACKEND environment variable:

  AICONNEX_LLM_BACKEND=ollama  (default) - uses get_ollama_llm()
  AICONNEX_LLM_BACKEND=openai            - uses get_openai_llm()

This lets the agent switch LLM providers by changing one .env value, with
no code changes anywhere that calls get_llm(). langchain_openai is an
OPTIONAL dependency - it is only imported when AICONNEX_LLM_BACKEND=openai
is explicitly set, so the default Ollama path never requires it to be
installed (same guarded-import pattern used for mem0ai in
aiconnex_agent/memory/backends/mem0_adapter.py).

Ollama config (OLLAMA_MODEL / OLLAMA_BASE_URL) is unchanged and still
defaults to the gpt-oss:120b-cloud Ollama Cloud model - chosen deliberately
for model quality over local latency. Note this requires an active
ollama.com sign-in (`ollama signin`) since it is a cloud-hosted model, not
a locally-run one, even though requests go through localhost:11434.
"""

from __future__ import annotations

import os
import logging
from typing import Any, Optional

from dotenv import load_dotenv
from langchain_community.llms import Ollama

logger = logging.getLogger(__name__)

# Load local .env if present
load_dotenv()


def get_ollama_llm(
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.1,
) -> Ollama:
    """
    Returns an initialized LangChain Ollama LLM client.

    Defaults to OLLAMA_MODEL=gpt-oss:120b-cloud (Ollama Cloud) - requires
    `ollama signin`. Set OLLAMA_MODEL to a non "-cloud" tag (e.g. llama3.1)
    for a fully local model instead.
    """
    model_name = model or os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
    host_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    logger.info(f"[OllamaLLM] Initializing Ollama client model='{model_name}' host='{host_url}'")
    return Ollama(
        model=model_name,
        base_url=host_url,
        temperature=temperature,
    )


def get_openai_llm(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.1,
) -> Any:
    """
    Returns an initialized LangChain ChatOpenAI client.

    Requires `pip install langchain-openai` and an OPENAI_API_KEY (env var
    or passed explicitly). Raises a clear, actionable RuntimeError if the
    optional dependency is missing, rather than letting an ImportError
    propagate from module import time.
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise RuntimeError(
            "langchain-openai is not installed. Install with: pip install langchain-openai\n"
            "Also set OPENAI_API_KEY in your .env or environment."
        ) from exc

    model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to .env or the environment "
            "before using AICONNEX_LLM_BACKEND=openai."
        )

    logger.info(f"[OpenAILLM] Initializing ChatOpenAI client model='{model_name}'")
    return ChatOpenAI(
        model=model_name,
        api_key=key,
        temperature=temperature,
    )


def get_llm(**kwargs: Any) -> Any:
    """
    Returns the configured LLM client per AICONNEX_LLM_BACKEND ("ollama"
    default, "openai" opt-in). This is the single entry point agent nodes
    should call instead of get_ollama_llm()/get_openai_llm() directly, so
    the backend can be swapped via .env with no code changes.
    """
    backend = os.getenv("AICONNEX_LLM_BACKEND", "ollama").strip().lower()

    if backend == "ollama":
        return get_ollama_llm(**kwargs)
    if backend == "openai":
        return get_openai_llm(**kwargs)

    raise ValueError(
        f"Unknown AICONNEX_LLM_BACKEND='{backend}'. Expected 'ollama' or 'openai'."
    )
