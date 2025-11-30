from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class LlmConfig:
    provider: str
    models: List[str]
    max_tokens: Optional[int]
    max_output_tokens: Optional[int]
    model_max_tokens: Dict[str, int]
    model_max_output_tokens: Dict[str, int]
    domain_max_output_tokens: Dict[str, int]


@dataclass
class ExperimentConfig:
    domain: str
    asp_version: str
    mode: str
    runs_per_instance: int
    instances: List[str]
    maxstep: int
    output_dir: str
    workers: int
    domains_root: str


def load_combined_config(default_path: Path, user_path: Optional[Path]) -> Dict:
    cfg: Dict = {}
    if default_path.exists():
        cfg = yaml.safe_load(default_path.read_text()) or {}
    if user_path and user_path.exists():
        user_cfg = yaml.safe_load(user_path.read_text()) or {}
        cfg = _deep_merge(cfg, user_cfg)
    return cfg


def to_experiment_config(cfg: Dict) -> (ExperimentConfig, LlmConfig):
    exp = cfg.get("experiment", {})
    llm_cfg = cfg.get("llm", {})
    exp_cfg = ExperimentConfig(
        domain=exp.get("domain", "aladdin"),
        asp_version=exp.get("asp_version", "original"),
        mode=exp.get("mode", "one-off"),
        runs_per_instance=exp.get("runs_per_instance", 1),
        instances=exp.get("instances", []),
        maxstep=exp.get("maxstep", 12),
        output_dir=exp.get("output_dir", "results"),
        workers=exp.get("workers", 1),
        domains_root=cfg.get("domains_root", "benchmark/domains"),
    )
    llm = LlmConfig(
        provider=llm_cfg.get("provider", "openrouter"),
        models=exp.get("models", ["openai/gpt-4o"]),
        max_tokens=llm_cfg.get("max_tokens"),
        max_output_tokens=llm_cfg.get("max_output_tokens"),
        model_max_tokens=llm_cfg.get("model_max_tokens", {}) or {},
        model_max_output_tokens=llm_cfg.get("model_max_output_tokens", {}) or {},
        domain_max_output_tokens=llm_cfg.get("domain_max_output_tokens", {}) or {},
    )
    return exp_cfg, llm


def _deep_merge(base: Dict, override: Dict) -> Dict:
    merged = dict(base)
    for k, v in override.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged
