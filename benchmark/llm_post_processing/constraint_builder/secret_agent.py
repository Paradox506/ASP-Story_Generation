from typing import Dict, List

from benchmark.asp.action_utils import ActionMapper

from .base import ConstraintBuilder


class SecretAgentConstraintBuilder(ConstraintBuilder):
    def __init__(self, mapper: ActionMapper):
        super().__init__(mapper)

    def build(self, actions: List[Dict]) -> str:
        lines: List[str] = []
        for i, action in enumerate(actions):
            subj = action["subject"]
            aid = action["actionId"]
            params = action.get("parameters", [])
            functor = self.mapper.to_asp_functor(aid, params)
            lines.append(f":- not act({subj}, {functor}, {i}).")
        return "\n".join(lines)
