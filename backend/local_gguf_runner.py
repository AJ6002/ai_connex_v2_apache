import os
import sys
import logging
import urllib.request
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))
os.makedirs(MODELS_DIR, exist_ok=True)

# Direct Hugging Face GGUF Download URLs
MODEL_URLS = {
    "qwen3-4b-q4": {
        "filename": "qwen3-4b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF/resolve/main/qwen2.5-coder-3b-instruct-q4_k_m.gguf",
        "size_mb": 2450,
        "role": "Primary / General Model"
    },
    "phi-4-mini-q4": {
        "filename": "Phi-4-mini-instruct-Q4_K_M.gguf",
        "url": "https://huggingface.co/microsoft/Phi-4-mini-instruct-GGUF/resolve/main/Phi-4-mini-instruct-Q4_K_M.gguf",
        "size_mb": 2490,
        "role": "Reasoning Specialist"
    },
    "qwen2.5-coder-3b-q4": {
        "filename": "qwen2.5-coder-3b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF/resolve/main/qwen2.5-coder-3b-instruct-q4_k_m.gguf",
        "size_mb": 2020,
        "role": "Coding & SQL Specialist"
    },
    "qwen2.5-coder-1.5b-q4": {
        "filename": "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
        "size_mb": 1120,
        "role": "Edge Telemetry Guard"
    },
    "qwen2.5-coder-7b-q4": {
        "filename": "qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "size_mb": 4680,
        "role": "High-Capacity Coder"
    }
}

def get_model_search_dirs() -> List[str]:
    """
    Returns list of candidate directories to search for GGUF model files (including USB drives).
    """
    dirs = []
    # 1. Environment Variable Override
    env_dir = os.environ.get("EXTERNAL_GGUF_DIR")
    if env_dir and os.path.exists(env_dir):
        dirs.append(os.path.abspath(env_dir))

    # 2. External USB Drive & Parent Directory Search Candidates
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "aiconnex_models"))
    dirs.append(parent_dir)

    for drive in ["E", "F", "G", "D", "H", "C"]:
        usb_path = os.path.abspath(f"{drive}:\\aiconnex_models")
        dirs.append(usb_path)

    # 3. Default Internal Directory
    dirs.append(MODELS_DIR)
    return dirs

def get_model_path(model_key: str = "qwen3-4b-q4") -> str:
    """Returns absolute path to local GGUF model file across internal and external USB directories."""
    info = MODEL_URLS.get(model_key, MODEL_URLS["qwen3-4b-q4"])
    primary_filename = info["filename"]
    
    # Check primary filename and variants (including HuggingFace repo prefixes like microsoft_)
    candidate_names = [
        primary_filename,
        primary_filename.lower(),
        primary_filename.replace("Phi-4", "phi-4"),
        f"microsoft_{primary_filename}",
        f"microsoft_{primary_filename.lower()}",
        f"Qwen_{primary_filename}",
    ]
    if model_key == "phi-4-mini-q4":
        candidate_names.extend([
            "microsoft_Phi-4-mini-instruct-Q4_K_M.gguf",
            "microsoft_phi-4-mini-instruct-q4_k_m.gguf",
            "Phi-4-mini-instruct-Q4_K_M.gguf",
            "phi-4-mini-instruct-q4_k_m.gguf",
        ])
    if model_key == "qwen3-4b-q4":
        candidate_names.extend([
            "Qwen3-4B-Q4_K_M.gguf",
            "qwen3-4b-q4_k_m.gguf",
            "qwen3-4b-instruct-q4_k_m.gguf",
            "Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf",
            "qwen2.5-coder-3b-instruct-q4_k_m.gguf",
        ])

    for d in get_model_search_dirs():
        for fname in candidate_names:
            candidate = os.path.join(d, fname)
            if os.path.exists(candidate) and os.path.getsize(candidate) > 100 * 1024 * 1024:
                return candidate

    # Fallback to internal models dir
    return os.path.join(MODELS_DIR, primary_filename)

def is_model_downloaded(model_key: str = "qwen3-4b-q4") -> bool:
    """Checks if specified GGUF model file exists in any internal or external USB directory."""
    path = get_model_path(model_key)
    return os.path.exists(path) and os.path.getsize(path) > 100 * 1024 * 1024

def download_gguf_model(model_key: str = "qwen2.5-coder-3b-q4", target_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Downloads GGUF model directly from Hugging Face into specified external or internal models directory.
    """
    info = MODEL_URLS.get(model_key, MODEL_URLS["qwen2.5-coder-3b-q4"])
    
    if target_dir:
        dest_dir = os.path.abspath(target_dir)
        os.makedirs(dest_dir, exist_ok=True)
        target_path = os.path.join(dest_dir, info["filename"])
    else:
        target_path = get_model_path(model_key)

    if is_model_downloaded(model_key):
        logger.info(f"[GGUF Runner] Model {info['filename']} already downloaded at {target_path}")
        return {"status": "already_exists", "file_path": target_path, "filename": info["filename"]}

    logger.info(f"[GGUF Runner] Starting download of {info['filename']} ({info['size_mb']} MB) from Hugging Face...")
    
    try:
        def _reporthook(blocknum, blocksize, totalsize):
            readSoFar = blocknum * blocksize
            if totalsize > 0:
                percent = readSoFar * 100 / totalsize
                if blocknum % 1000 == 0:
                    sys.stdout.write(f"\rDownloading {info['filename']}: {percent:.1f}% ({readSoFar/(1024*1024):.1f} MB)")
                    sys.stdout.flush()

        urllib.request.urlretrieve(info["url"], target_path, reporthook=_reporthook)
        print(f"\n[GGUF Runner] Successfully downloaded {info['filename']} to {target_path}")
        return {"status": "success", "file_path": target_path, "filename": info["filename"]}
    except Exception as exc:
        logger.error(f"[GGUF Runner] Download failed: {exc}")
        return {"status": "error", "message": str(exc), "file_path": target_path}

def generate_local_gguf_response(
    user_prompt: str = "",
    context: Optional[Dict[str, Any]] = None,
    model_key: str = "qwen2.5-coder-3b-q4",
    prompt: Optional[str] = None
) -> str:
    """
    Generates LLM inference locally using local GGUF model, local Ollama daemon, or grounded Knowledge Base.
    """
    actual_prompt = (user_prompt or prompt or "").strip()
    model_path = get_model_path(model_key)
    
    # 1. Attempt llama-cpp-python inference if installed and model file present
    if is_model_downloaded(model_key):
        try:
            from llama_cpp import Llama
            llm = Llama(model_path=model_path, n_ctx=2048, verbose=False)
            output = llm(
                f"<|im_start|>system\nYou are Jane, AIConnex Autonomous MLOps Assistant.<|im_end|>\n<|im_start|>user\n{actual_prompt}<|im_end|>\n<|im_start|>assistant\n",
                max_tokens=350,
                stop=["<|im_end|>"]
            )
            text = output["choices"][0]["text"].strip()
            if text:
                return text
        except Exception as exc:
            logger.warning(f"[GGUF Runner] llama-cpp direct inference fallback: {exc}")

    # 2. Attempt Local Ollama daemon if available
    try:
        import urllib.request
        ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=json.dumps({
                "model": os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:3b"),
                "prompt": actual_prompt,
                "stream": False
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            resp_text = data.get("response", "").strip()
            if resp_text:
                return resp_text
    except Exception:
        pass

    # 3. Grounded Knowledge Base (RAG) extraction for technical Q&A
    rag_text = context.get("rag", "") if context else ""
    greetings = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "yo"}
    
    # Extract exact user query portion from system prompt payload
    raw_user_query = actual_prompt.split("[USER QUERY]:")[-1].strip().lower() if "[USER QUERY]:" in actual_prompt else actual_prompt.lower().strip()
    clean_query = raw_user_query.strip(" .!?,")
    
    if rag_text and "[Doc:" in rag_text and len(clean_query) > 10 and clean_query not in greetings:
        import re
        snippets = re.findall(r'"([^"]{30,})"', rag_text)
        if snippets:
            clean_evidence = "\n".join(f"• {s.strip()}" for s in snippets[:3])
            return (
                f"Based on **AIConnex Technical & Engineering Documentation**:\n\n"
                f"{clean_evidence}\n\n"
                f"Let me know if you would like more details or want to configure a pipeline stage around this."
            )

    # 4. Universal Context-Aware Fallback Engine
    return (
        "Hi! I'm **Jane**, Lead Solutions Architect for AIConnex. "
        "I can answer questions on ML architecture, industrial telemetry analytics, feature engineering, and platform navigation. "
        "How can I help with your dataset or project today?"
    )
