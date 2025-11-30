from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from benchmark.prompt_builders.prompt_builder import get_prompt_builder
from benchmark.evaluators.secret_agent_evaluator import SecretAgentEvaluator
from benchmark.evaluators.western_evaluator import WesternEvaluator
from benchmark.evaluators.aladdin_evaluator import AladdinEvaluator


@dataclass
class DomainAdapter:
    name: str
    prompt_builder: Callable[[Path, Path, str], str]
    evaluator_factory: Callable[[], Optional[object]]
    default_instance_dirs: Callable[[Path, str], List[Path]]


def _prompt_builder(domain: str):
    def builder(base: Path, instance: Path, asp_version: str) -> str:
        return get_prompt_builder(domain, asp_version).build_prompt(base, instance)

    return builder


def _default_instances(domain: str):
    def finder(base: Path, asp_version: str) -> List[Path]:
        candidate = base / domain / asp_version
        if candidate.exists():
            return [candidate]
        # Secret agent special handling
        if domain == "secret_agent":
            inst_root = base / domain / "instances"
            if inst_root.exists():
                paths = sorted(inst_root.glob("*/*/*/"))
                if paths:
                    return [paths[0]]
        fallback = base / domain / "base"
        return [fallback] if fallback.exists() else []

    return finder


DOMAIN_ADAPTERS = {
    "aladdin": DomainAdapter(
        name="aladdin",
        prompt_builder=_prompt_builder("aladdin"),
        evaluator_factory=lambda: AladdinEvaluator(),
        default_instance_dirs=_default_instances("aladdin"),
    ),
    "western": DomainAdapter(
        name="western",
        prompt_builder=_prompt_builder("western"),
        evaluator_factory=lambda: WesternEvaluator(),
        default_instance_dirs=_default_instances("western"),
    ),
    "secret_agent": DomainAdapter(
        name="secret_agent",
        prompt_builder=_prompt_builder("secret_agent"),
        evaluator_factory=lambda: SecretAgentEvaluator(),
        default_instance_dirs=_default_instances("secret_agent"),
    ),
}


def get_adapter(domain: str) -> DomainAdapter:
    if domain not in DOMAIN_ADAPTERS:
        raise ValueError(f"Unsupported domain {domain}")
    return DOMAIN_ADAPTERS[domain]
