from typing import Dict

from benchmark.evaluators.base import BaseEvaluator

class WesternEvaluator(BaseEvaluator):
    """
    Evaluator for Western conflict planning.
    """

    def extra_metrics(self, asp_result: Dict, parse_result: Dict, expected_conflicts: int = 0) -> Dict:
        conflicts = asp_result.get("conflicts", []) or []
        conflicts_found = len(conflicts)
        score = (
            min(1.0, conflicts_found / expected_conflicts) if expected_conflicts else (1.0 if conflicts_found == 0 else 0.0)
        )
        return {
            "conflict_score": score,
            "conflicts_found": conflicts_found,
            "conflicts": conflicts,
        }
