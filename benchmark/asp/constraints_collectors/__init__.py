from pathlib import Path
from typing import Optional

from benchmark.asp.constraints_collectors.base import BaseConstraintsCollector
from benchmark.asp.constraints_collectors.secret_agent import SecretAgentConstraintsCollector
from benchmark.asp.constraints_collectors.western import WesternConstraintsCollector
from benchmark.asp.constraints_collectors.aladdin import AladdinConstraintsCollector


def get_collector(domain: str, domain_dir: Path, instance_dir: Path, collector: Optional[BaseConstraintsCollector] = None) -> BaseConstraintsCollector:
    """
    Factory to obtain the proper collector per domain.
    """
    if collector is not None:
        return collector
    if domain == "secret_agent":
        return SecretAgentConstraintsCollector(domain_dir, instance_dir)
    if domain == "western":
        return WesternConstraintsCollector(domain_dir, instance_dir)
    if domain == "aladdin":
        return AladdinConstraintsCollector(domain_dir, instance_dir)
    raise NotImplementedError(f"Constraints collector not implemented for domain: {domain}")


__all__ = [
    "BaseConstraintsCollector",
    "get_collector",
    "SecretAgentConstraintsCollector",
    "WesternConstraintsCollector",
    "AladdinConstraintsCollector",
]
