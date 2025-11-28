import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_api_key(config_path: Optional[Path] = None) -> str:
    """
    Load OPENROUTER_API_KEY from environment or optional YAML file.
    YAML format example:
    openrouter:
      api_key: "sk-xxxx"
    """
    env_key = os.getenv("OPENROUTER_API_KEY")
    if env_key:
        return env_key
    if config_path and config_path.exists():
        data = yaml.safe_load(config_path.read_text()) or {}
        return data.get("openrouter", {}).get("api_key", "") or ""
    # fallback: ~/.openrouter.yaml
    default_path = Path.home() / ".openrouter.yaml"
    if default_path.exists():
        data = yaml.safe_load(default_path.read_text()) or {}
        return data.get("openrouter", {}).get("api_key", "") or ""
    return ""
