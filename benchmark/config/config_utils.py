import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass
from typing import List

import yaml


DEFAULT_CONFIG: Dict[str, Any] = {
    "experiment": {
        "domain": "aladdin",
        "asp_version": "original",
        "mode": "one-off",
        "models": ["openai/gpt-4o"],
        "maxstep": 12,
        "output_dir": "results",
        "instances": [],
        "runs_per_instance": 1,
        "workers": 1,
    },
    "asp": {"clingo_path": "clingo"},
    "openrouter": {"api_key": ""},
    "llm": {
        "max_tokens": None,
        "model_max_tokens": {},
        "max_output_tokens": None,
        "model_max_output_tokens": {},
    },
}


@dataclass
class LlmConfig:
    models: List[str]
    max_tokens: Optional[int]
    max_output_tokens: Optional[int]
    model_max_tokens: Dict[str, int]
    model_max_output_tokens: Dict[str, int]


@dataclass
class ExperimentConfig:
    domain: str
    asp_version: str
    mode: str
    models: List[str]
    runs_per_instance: int
    instances: List[str]
    maxstep: int
    output_dir: str
    workers: int

    llm: LlmConfig


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
    Additionally, if config.default.yaml exists in repo root, it is merged before user config.
    """
    cfg = DEFAULT_CONFIG.copy()
    # optional repo-level default file
    # repo root (../../.. from config_utils.py)
    repo_default = Path(__file__).resolve().parents[2] / "config.default.yaml"
    if repo_default.exists():
        base_cfg = yaml.safe_load(repo_default.read_text()) or {}
        cfg = _deep_merge(cfg, base_cfg)
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
