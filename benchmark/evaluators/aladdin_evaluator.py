from typing import Dict

from benchmark.evaluators.base import BaseEvaluator


class AladdinEvaluator(BaseEvaluator):
    def extra_metrics(self, asp_result: Dict, parse_result: Dict) -> Dict:
        satisfiable = asp_result.get("satisfiable", False)
        return {
            "goal_achieved": satisfiable,
        }
