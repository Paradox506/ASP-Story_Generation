from benchmark.asp.action_utils import ActionMapper

from .aladdin import AladdinConstraintBuilder
from .secret_agent import SecretAgentConstraintBuilder
from .western import WesternConstraintBuilder
from .base import ConstraintBuilder


def get_constraint_builder(domain: str, mapper: ActionMapper, use_default_intention: bool = False) -> ConstraintBuilder:
    if domain == "aladdin":
        return AladdinConstraintBuilder(mapper, use_default_intention=use_default_intention)
    if domain == "western":
        return WesternConstraintBuilder(mapper, use_default_intention=use_default_intention)
    if domain == "secret_agent":
        return SecretAgentConstraintBuilder(mapper)
    raise ValueError(f"Unsupported domain {domain}")
