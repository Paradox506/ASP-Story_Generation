from pathlib import Path

from .aladdin_plan_parser import AladdinPlanParser
from .base_plan_parser import BasePlanParser
from .secret_agent_plan_parser import SecretAgentPlanParser
from .western_plan_parser import WesternPlanParser


def get_plan_parser(domain: str, domain_dir: Path, instance_dir: Path) -> BasePlanParser:
    if domain == "aladdin":
        return AladdinPlanParser(domain, domain_dir, instance_dir)
    if domain == "secret_agent":
        return SecretAgentPlanParser(domain, domain_dir, instance_dir)
    if domain == "western":
        return WesternPlanParser(domain, domain_dir, instance_dir)
    raise ValueError(f"Unsupported domain {domain}")
