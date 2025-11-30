from benchmark.asp.action_utils import ActionMapper

from .aladdin import AladdinConstraintBuilder
from .secret_agent import SecretAgentConstraintBuilder
from .western import WesternConstraintBuilder
from .base import ConstraintBuilder


def get_constraint_builder(domain: str, mapper: ActionMapper) -> ConstraintBuilder:
    if domain == "aladdin":
        return AladdinConstraintBuilder(mapper)
    if domain == "western":
        return WesternConstraintBuilder(mapper)
    if domain == "secret_agent":
        return SecretAgentConstraintBuilder(mapper)
    raise ValueError(f"Unsupported domain {domain}")
