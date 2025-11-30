from typing import Dict, List

from benchmark.asp.action_utils import ActionMapper


class ConstraintBuilder:
    def __init__(self, mapper: ActionMapper):
        self.mapper = mapper

    def build(self, actions: List[Dict]) -> str:  # pragma: no cover - interface
        raise NotImplementedError
