from pathlib import Path
from typing import Dict, List

from benchmark.llm_post_processing.constraint_builder import SecretAgentConstraintBuilder
from .base_plan_parser import BasePlanParser


class SecretAgentPlanParser(BasePlanParser):
    def __init__(self, domain: str, domain_dir: Path, instance_dir: Path):
        super().__init__(domain, domain_dir, instance_dir)
        self.builder = SecretAgentConstraintBuilder(self.mapper)

    def validate_param_values(self, params: List[str]) -> bool:
        for p in params:
            if p in self.valid_characters or p in self.valid_objects or p in self.valid_places:
                continue
            return False
        return True

    def build_constraints(self, actions: List[Dict], maxstep: int = None) -> str:
        try:
            return self.builder.build(actions, maxstep=maxstep)
        except TypeError:
            return self.builder.build(actions)
