from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from benchmark.evaluators.aladdin_evaluator import AladdinEvaluator
from benchmark.evaluators.secret_agent_evaluator import SecretAgentEvaluator
from benchmark.evaluators.western_evaluator import WesternEvaluator


@dataclass
class DomainAdapter:
    name: str
    evaluator_factory: Callable[[], Optional[object]]
    default_instance_dirs: Callable[[Path], List[Path]]


def default_instances_finder(domain: str):
    def finder(domains_root: Path) -> List[Path]:
        instance_root = domains_root / domain / "instances"
        if instance_root.exists():
            candidates = sorted(p.parent for p in instance_root.rglob("instance.lp"))
            if candidates:
                return [candidates[0]]
        return []

    return finder


DOMAIN_ADAPTERS = {
    "aladdin": DomainAdapter(
        name="aladdin",
        evaluator_factory=lambda: AladdinEvaluator(),
        default_instance_dirs=default_instances_finder("aladdin"),
    ),
    "western": DomainAdapter(
        name="western",
        evaluator_factory=lambda: WesternEvaluator(),
        default_instance_dirs=default_instances_finder("western"),
    ),
    "secret_agent": DomainAdapter(
        name="secret_agent",
        evaluator_factory=lambda: SecretAgentEvaluator(),
        default_instance_dirs=default_instances_finder("secret_agent"),
    ),
}


def get_adapter(domain: str) -> DomainAdapter:
    adapter = DOMAIN_ADAPTERS.get(domain)
    if adapter is None:
        raise ValueError(f"Unsupported domain {domain}")
    return adapter
