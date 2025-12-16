import re
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
    def numeric_key(path):
        m = re.search(r"\d+", path.name)
        return int(m.group(0)) if m else 10**12

    def instance_key(path):
        m = re.search(r"\d+", path.name)
        return int(m.group(0)) if m else 10**12

    def finder(domains_root: Path) -> List[Path]:
        instance_root = domains_root / domain / "instances"
        if not instance_root.exists():
            return []

        top_level_dirs = sorted(
            (p for p in instance_root.iterdir() if p.is_dir()),
            key=numeric_key,
        )
        if not top_level_dirs:
            return []

        first_group_dir = top_level_dirs[0]
        instance_dirs = sorted(
            (p for p in first_group_dir.iterdir() if p.is_dir()),
            key=instance_key,
        )
        if not instance_dirs:
            return []

        first_instance_dir = instance_dirs[0]
        if (first_instance_dir / "instance.lp").exists():
            return [first_instance_dir]

        candidates = sorted(first_group_dir.rglob("instance.lp"), key=lambda p: instance_key(p.parent))
        return [candidates[0].parent] if candidates else []
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
