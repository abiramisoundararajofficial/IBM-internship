"""Minimal Ollama HTTP client wrapper.

Uses the local Ollama server (configurable via environment variables).
This wrapper keeps requests minimal to save tokens/credits.
"""
from typing import Optional
import os
import requests
from dotenv import load_dotenv


load_dotenv()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
# Optional API key (keep in .env; do NOT commit)
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")


def generate(prompt: str, model: Optional[str] = None, max_tokens: int = 256) -> str:
    """Call Ollama's generate endpoint and return text output.

    Falls back to a short error string on failure.
    """
    model = model or DEFAULT_MODEL
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens}
    try:
        headers = {"Content-Type": "application/json"}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
        resp = requests.post(url, json=payload, timeout=30, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        # Ollama's response may contain 'response' or 'results'; be tolerant
        if isinstance(data, dict) and data.get("response"):
            return data["response"]
        if isinstance(data, dict) and data.get("results"):
            # join text parts
            parts = []
            for item in data["results"]:
                if isinstance(item, dict) and item.get("content"):
                    parts.append(item.get("content"))
            return "".join(parts)
        # Fallback: return full json
        return str(data)
    except Exception as e:
        return f"[Ollama error: {e}]"
