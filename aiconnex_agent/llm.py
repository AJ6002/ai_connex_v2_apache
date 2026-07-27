"""
aiconnex_agent/llm.py - Ollama LLM Client Helper
=================================================
Initializes local Ollama LLM client for LangGraph agent node calls.
Reads OLLAMA_MODEL (default: llama3) and OLLAMA_BASE_URL (default: http://localhost:11434)
from environment variables or .env file.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

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
    """
    model_name = model or os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
    host_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    logger.info(f"[OllamaLLM] Initializing Ollama client model='{model_name}' host='{host_url}'")
    return Ollama(
        model=model_name,
        base_url=host_url,
        temperature=temperature,
    )
