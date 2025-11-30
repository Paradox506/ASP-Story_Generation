from pathlib import Path

from .aladdin_plan_parser import AladdinPlanParser
from .base_plan_parser import BasePlanParser
from .secret_agent_plan_parser import SecretAgentPlanParser
from .western_plan_parser import WesternPlanParser


def get_plan_parser(domain: str, domain_dir: Path, instance_dir: Path, use_author_style: bool = False) -> BasePlanParser:
    if use_author_style:
        from benchmark.llm_post_processing.author_plan_parser import AuthorStylePlanParser

        return AuthorStylePlanParser(domain, domain_dir, instance_dir)
    if domain == "aladdin":
        return AladdinPlanParser(domain, domain_dir, instance_dir)
    if domain == "secret_agent":
        # Use dedicated secret agent parser outside this package
        from benchmark.llm_post_processing.secret_agent_plan_parser import SecretAgentPlanParser as SAPlanParser

        return SAPlanParser(domain_dir, instance_dir)
    if domain == "western":
        return WesternPlanParser(domain, domain_dir, instance_dir)
    raise ValueError(f"Unsupported domain {domain}")
