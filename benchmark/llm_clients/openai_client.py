import os
from typing import Dict, Any, Optional
import time

import openai


class OpenAIClient:
    """
    Minimal OpenAI Chat Completions client using the official SDK.
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        # OpenAI SDK uses max_completion_tokens
        self.max_output_tokens = max_output_tokens
        key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not key:
            raise ValueError("OPENAI_API_KEY not set")
        # configure client
        self.client = openai.OpenAI(api_key=key, base_url=base_url) if base_url else openai.OpenAI(api_key=key)

    def generate(self, prompt: str) -> Dict[str, Any]:
        start = time.time()
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_output_tokens or self.max_tokens,
                stream=False,
            )
            elapsed = time.time() - start
            choice = resp.choices[0]
            content = choice.message.content if hasattr(choice, "message") else choice["message"]["content"]
            usage = resp.usage
            return {
                "success": True,
                "content": content,
                "completion_tokens": usage.completion_tokens if usage else None,
                "prompt_tokens": usage.prompt_tokens if usage else None,
                "elapsed": elapsed,
                "raw_response": resp.model_dump() if hasattr(resp, "model_dump") else resp,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "content": "", "elapsed": time.time() - start}
