import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


DEFAULT_CONFIG: Dict[str, Any] = {
    "experiment": {
        "domain": "aladdin",
        "asp_version": "original",
        "mode": "one-off",
        "models": ["openai/gpt-4o"],
        "maxstep": 12,
        "output_dir": "results",
    },
    "asp": {"clingo_path": "clingo"},
    "openrouter": {"api_key": ""},
}


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
    data = {}
    if config_path and config_path.exists():
        data = yaml.safe_load(config_path.read_text()) or {}
    if not data:
        default_path = Path.home() / ".openrouter.yaml"
        if default_path.exists():
            data = yaml.safe_load(default_path.read_text()) or {}
    return (data.get("openrouter", {}) or {}).get("api_key", "") or ""


def load_config(path: Optional[Path]) -> Dict[str, Any]:
    """
    Load YAML config and merge onto DEFAULT_CONFIG. Missing file falls back to defaults.
    """
    cfg = DEFAULT_CONFIG.copy()
    if path and path.exists():
        user_cfg = yaml.safe_load(path.read_text()) or {}
        cfg = _deep_merge(cfg, user_cfg)
    return cfg


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for k, v in override.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged
