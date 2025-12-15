import os
from pathlib import Path
from typing import Optional

import yaml


def load_api_key(config_path: Optional[Path] = None, provider: str = "openrouter") -> str:
    """Loads API key from env or a YAML config file."""
    env_var = {
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }.get(provider, "")
    if not env_var:
        return ""

    env_key = os.getenv(env_var)
    if env_key:
        return env_key

    data = {}
    if config_path and config_path.exists():
        data = yaml.safe_load(config_path.read_text()) or {}

    if not data and provider == "openrouter":
        fallback_path = Path.home() / ".openrouter.yaml"
        if fallback_path.exists():
            data = yaml.safe_load(fallback_path.read_text()) or {}

    return (data.get(provider, {}) or {}).get("api_key", "") or ""
