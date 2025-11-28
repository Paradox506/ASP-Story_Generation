from typing import Dict


class CausalEvaluator:
    """
    Simple evaluator for Secret Agent causal planning.
    """

    def evaluate(self, asp_result: Dict, parse_result: Dict) -> Dict:
        nonexec = asp_result.get("nonexec_feedback", []) or []
        causal_sound = asp_result.get("satisfiable", False) and len(nonexec) == 0
        goal_achieved = asp_result.get("satisfiable", False)
        actions = parse_result.get("actions", []) if parse_result else []
        return {
            "causal_sound": causal_sound,
            "goal_achieved": goal_achieved,
            "nonexec_count": len(nonexec),
            "nonexec_details": nonexec,
            "plan_length": len(actions),
        }
