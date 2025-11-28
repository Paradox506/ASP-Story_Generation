import os
import time
from typing import Dict

import requests


class OpenRouterClient:
    """
    Minimal OpenRouter chat client.
    """

    def __init__(self, model: str, api_key: str | None = None, temperature: float = 0.7, max_tokens: int = 2000):
        self.model = model
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, prompt: str) -> Dict:
        if not self.api_key:
            return {"success": False, "error": "OPENROUTER_API_KEY not set"}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        start = time.time()
        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            elapsed = time.time() - start
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return {
                "success": True,
                "content": content,
                "completion_tokens": usage.get("completion_tokens"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "elapsed": elapsed,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "elapsed": time.time() - start}
