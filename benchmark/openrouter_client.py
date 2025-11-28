import os
import time
from typing import Dict

import requests


class OpenRouterClient:
    """
    Minimal OpenRouter chat client.
    """

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        max_output_tokens: int | None = None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_output_tokens = max_output_tokens
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, prompt: str) -> Dict:
        if not self.api_key:
            return {"success": False, "error": "OPENROUTER_API_KEY not set", "content": ""}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        if self.max_output_tokens is not None:
            payload["max_output_tokens"] = self.max_output_tokens
        start = time.time()
        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            elapsed = time.time() - start
            content = ""
            usage = data.get("usage", {})
            try:
                content = data["choices"][0]["message"]["content"]
            except Exception:
                # fallback: store full response text for debugging
                content = resp.text
            return {
                "success": True,
                "content": content,
                "completion_tokens": usage.get("completion_tokens"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "elapsed": elapsed,
                "raw_response": data,
            }
        except Exception as e:
            # Capture response text if available for debugging
            elapsed = time.time() - start
            err_text = ""
            if "resp" in locals():
                try:
                    err_text = resp.text
                except Exception:
                    err_text = ""
            return {"success": False, "error": str(e), "elapsed": elapsed, "content": err_text}
