from typing import Dict

from benchmark.evaluators.base import BaseEvaluator

class WesternEvaluator(BaseEvaluator):
    """
    Evaluator for Western conflict planning.
    """

    def evaluate(self, asp_result: Dict, parse_result: Dict, expected_conflicts: int = 0) -> Dict:
        conflicts = asp_result.get("conflicts", []) or []
        nonexec = asp_result.get("nonexec_feedback", []) or []
        causal_sound = asp_result.get("satisfiable", False) and len(nonexec) == 0
        conflicts_found = len(conflicts)
        score = (
            min(1.0, conflicts_found / expected_conflicts) if expected_conflicts else (1.0 if conflicts_found == 0 else 0.0)
        )
        actions = parse_result.get("actions", []) if parse_result else []
        executed = [a for a in actions if a.get("executed", True)]
        nonexecuted = [a for a in actions if not a.get("executed", True)]
        return {
            "causal_sound": causal_sound,
            "conflict_score": score,
            "conflicts_found": conflicts_found,
            "conflicts": conflicts,
            "nonexec_count": len(nonexec),
            "nonexec_details": nonexec,
            "executed_actions": len(executed),
            "nonexecuted_actions": len(nonexecuted),
            "plan_length": len(actions),
        }
