from benchmark.asp.action_utils import ActionMapper

from .aladdin_constraint_builder import AladdinConstraintBuilder
from .secret_agent_constraint_builder import SecretAgentConstraintBuilder
from .western_constraint_builder import WesternConstraintBuilder
from .constraint_builder import ConstraintBuilder


def get_constraint_builder(domain: str, mapper: ActionMapper) -> ConstraintBuilder:
    if domain == "aladdin":
        return AladdinConstraintBuilder(mapper)
    if domain == "western":
        return WesternConstraintBuilder(mapper)
    if domain == "secret_agent":
        return SecretAgentConstraintBuilder(mapper)
    raise ValueError(f"Unsupported domain {domain}")
