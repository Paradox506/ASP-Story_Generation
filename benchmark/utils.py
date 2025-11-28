import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ActionSchema:
    name: str
    arity: int


class ActionMapper:
    """
    Centralized actionId -> ASP functor mapping for all domains.
    """

    def __init__(self, domain: str):
        self.domain = domain
        self._schemas: Dict[int, ActionSchema] = self._build_schema(domain)

    def _build_schema(self, domain: str) -> Dict[int, ActionSchema]:
        if domain == "secret_agent":
            return {
                1: ActionSchema("move", 1),
                2: ActionSchema("move_through_guards", 2),
                3: ActionSchema("kill", 2),
                4: ActionSchema("pickup", 1),
            }
        if domain == "aladdin":
            return {
                0: ActionSchema("do_nothing", 0),
                1: ActionSchema("cast_love_spell", 2),
                2: ActionSchema("pillage", 2),
                3: ActionSchema("kill", 1),
                4: ActionSchema("marry", 1),
                5: ActionSchema("give", 2),
                6: ActionSchema("move", 1),
                7: ActionSchema("fall_in_love", 1),
                8: ActionSchema("appear_threatening", 0),
                9: ActionSchema("order_to_kill", 2),
                10: ActionSchema("order_to_obtain", 2),
            }
        if domain == "western":
            return {
                1: ActionSchema("bitten_by_snake", 0),
                2: ActionSchema("move", 1),
                3: ActionSchema("take_meds_from_carl", 0),
                4: ActionSchema("take_meds_from_char", 1),
                5: ActionSchema("use_meds_on", 1),
            }
        raise ValueError(f"Unsupported domain {domain}")

    def schema(self, action_id: int) -> ActionSchema:
        return self._schemas[action_id]

    def to_asp_functor(self, action_id: int, params: List[str]) -> str:
        schema = self.schema(action_id)
        if len(params) != schema.arity:
            raise ValueError(
                f"Action {action_id} expects {schema.arity} params, got {len(params)}"
            )
        if schema.arity == 0:
            return schema.name
        if schema.arity == 1:
            return f"{schema.name}({params[0]})"
        if schema.arity == 2:
            return f"{schema.name}({params[0]}, {params[1]})"
        raise ValueError(f"Unhandled arity {schema.arity}")


INTENTION_PATTERNS: List[Tuple[str, str]] = [
    (r"dead\(\s*([^)]+)\)", "dead({})"),
    (r"marry\(\s*([^)]+)\)", "marry({})"),
    (r"possessed_by\(\s*lamp\s*,\s*([^)]+)\)", "possessed_by(lamp, {})"),
]


def extract_intention(character_plan: str) -> Optional[str]:
    """
    Pull the first intention-like predicate from a character_plan string.
    Accepts loose formats and returns a normalized ASP term or None.
    """
    if not character_plan:
        return None
    lowered = character_plan.lower()
    for pattern, template in INTENTION_PATTERNS:
        m = re.search(pattern, lowered)
        if m:
            arg = m.group(1).strip()
            arg = arg.replace(" ", "_")
            return template.format(arg)
    return None
